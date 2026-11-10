# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import tempfile
import unittest
from unittest import mock

from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, Vt
from validator_test_case import SUPPORTS_PYTHON_FIXERS, SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase

from newton_usd_schemas import validators
from newton_usd_schemas.validators import _migration
from newton_usd_schemas.validators._migration import RENAMED_ATTRIBUTES, rename_attribute, renamed_to

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

ERROR = "RenamedAttribute"

# A hypothetical rename, so the behavior tests do not depend on the attributes that have actually been renamed
OLD = "newton:mimicActive"
NEW = "newton:mimicEnabled"


def patch_renames(test: unittest.TestCase, renames: dict[str, dict[str, str]]) -> None:
    patcher = mock.patch.dict(_migration.RENAMED_ATTRIBUTES, renames, clear=True)
    patcher.start()
    test.addCleanup(patcher.stop)


def define_follower(stage: Usd.Stage, path: str = "/Follower") -> Usd.Prim:
    prim = UsdPhysics.RevoluteJoint.Define(stage, path).GetPrim()
    prim.ApplyAPI("NewtonMimicAPI")
    return prim


def author_old(prim: Usd.Prim) -> Usd.Attribute:
    return prim.CreateAttribute(OLD, Sdf.ValueTypeNames.Bool)


def registered_renames() -> list[tuple[str, str, str]]:
    return [(schema, old, new) for schema, renames in RENAMED_ATTRIBUTES.items() for old, new in renames.items()]


def define_prim_with_schema(stage: Usd.Stage, schema: str) -> Usd.Prim:
    prim_types = Usd.SchemaRegistry.GetAPISchemaCanOnlyApplyToTypeNames(schema)
    prim = stage.DefinePrim("/Prim", prim_types[0] if prim_types else "Xform")
    prim.ApplyAPI(schema)
    return prim


# Distinctive values for the attribute types in RENAMED_ATTRIBUTES, so that a migration which loses a value fails
DISTINCTIVE_VALUES = {
    Sdf.ValueTypeNames.Bool: True,
    Sdf.ValueTypeNames.Int: 7,
    Sdf.ValueTypeNames.Float: 0.25,
    Sdf.ValueTypeNames.Double: 0.25,
    Sdf.ValueTypeNames.Token: "distinctive",
    Sdf.ValueTypeNames.FloatArray: Vt.FloatArray([0.25, 0.5]),
    Sdf.ValueTypeNames.DoubleArray: Vt.DoubleArray([0.25, 0.5]),
}


def author_distinctive_value(prim: Usd.Prim, schema: str, old: str, new: str):
    type_name = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema).GetSchemaAttributeSpec(new).typeName
    if type_name not in DISTINCTIVE_VALUES:
        raise AssertionError(f"Add a distinctive {type_name} value to DISTINCTIVE_VALUES")
    prim.CreateAttribute(old, type_name).Set(DISTINCTIVE_VALUES[type_name])
    return DISTINCTIVE_VALUES[type_name]


class TestRenamedAttributesTable(unittest.TestCase):
    def test_new_names_are_defined_by_their_schemas(self):
        for schema, _, new in registered_renames():
            definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema)
            with self.subTest(schema=schema, attribute=new):
                self.assertTrue(definition.GetPropertyDefinition(new))


class TestRenameAttribute(unittest.TestCase):
    """`rename_attribute` backs the `UsdValidation` fixer, and is tested directly so it runs with every OpenUSD version."""

    def setUp(self):
        patch_renames(self, {"NewtonMimicAPI": {OLD: NEW}})
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = define_follower(self.stage)
        self.old = author_old(self.prim)
        self.new = self.prim.GetAttribute(NEW)

    def test_renamed_to(self):
        self.assertEqual(renamed_to(self.prim, OLD), NEW)
        self.assertIsNone(renamed_to(self.prim, "physics:jointEnabled"))
        other = UsdPhysics.RevoluteJoint.Define(self.stage, "/Other").GetPrim()
        self.assertIsNone(renamed_to(other, OLD))

    def test_moves_default(self):
        self.old.Set(False)
        self.assertTrue(rename_attribute(self.old, NEW, self.stage.GetEditTarget()))
        self.assertFalse(self.new.Get())
        self.assertFalse(self.prim.HasAttribute(OLD))

    def test_moves_time_samples(self):
        self.old.Set(True, 1.0)
        self.old.Set(False, 2.0)
        rename_attribute(self.old, NEW, self.stage.GetEditTarget())
        self.assertEqual(self.new.GetTimeSamples(), [1.0, 2.0])
        self.assertFalse(self.new.Get(2.0))
        self.assertFalse(self.stage.GetRootLayer().GetAttributeAtPath(f"/Follower.{NEW}").HasDefaultValue())

    def test_moves_time_samples_of_a_deprecated_attribute(self):
        # The old name is still defined, so it resolves to its fallback value at the default time
        prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        prim.ApplyAPI("NewtonCollisionAPI")
        old = prim.GetAttribute("newton:contactMargin")
        old.Set(0.02, 1.0)
        self.assertIsNotNone(old.Get(Usd.TimeCode.Default()))
        rename_attribute(old, "newton:contactGap", self.stage.GetEditTarget())
        new = self.stage.GetRootLayer().GetAttributeAtPath("/Collider.newton:contactGap")
        self.assertEqual(list(new.GetInfo("timeSamples").keys()), [1.0])
        self.assertFalse(new.HasDefaultValue())

    def test_does_not_author_the_new_fallback(self):
        prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        prim.ApplyAPI("NewtonCollisionAPI")
        old = prim.GetAttribute("newton:contactMargin")
        old.Set(prim.GetPrimDefinition().GetAttributeFallbackValue("newton:contactGap"))
        rename_attribute(old, "newton:contactGap", self.stage.GetEditTarget())
        self.assertFalse(prim.GetAttribute("newton:contactGap").HasAuthoredValue())
        self.assertFalse(prim.GetAttribute("newton:contactMargin").HasAuthoredValue())

    def test_moves_blocked_time_samples(self):
        self.old.Set(True, 1.0)
        self.old.Set(Sdf.ValueBlock(), 2.0)
        self.assertTrue(rename_attribute(self.old, NEW, self.stage.GetEditTarget()))
        self.assertEqual(self.new.GetTimeSamples(), [1.0, 2.0])
        self.assertTrue(self.new.Get(1.0))
        self.assertIsNone(self.new.Get(2.0))

    def test_converts_to_the_new_type(self):
        prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        prim.ApplyAPI("NewtonCollisionAPI")
        old = prim.CreateAttribute("newton:legacyGap", Sdf.ValueTypeNames.Double)
        old.Set(0.1)
        old.Set(0.2, 1.0)
        self.assertTrue(rename_attribute(old, "newton:contactGap", self.stage.GetEditTarget()))
        new = prim.GetAttribute("newton:contactGap")
        self.assertAlmostEqual(new.Get(), 0.1, places=6)
        self.assertAlmostEqual(new.Get(1.0), 0.2, places=6)

    def test_inconvertible_type_authors_nothing(self):
        self.prim.RemoveProperty(OLD)
        old = self.prim.CreateAttribute(OLD, Sdf.ValueTypeNames.Float3)
        old.Set(Gf.Vec3f(1, 2, 3))
        self.assertFalse(rename_attribute(old, NEW, self.stage.GetEditTarget()))
        self.assertFalse(self.new.HasAuthoredValue())
        self.assertEqual(old.Get(), Gf.Vec3f(1, 2, 3))

    def test_old_name_from_an_internal_reference(self):
        source = define_follower(self.stage, "/Source")
        author_old(source).Set(False)
        instance = self.stage.DefinePrim("/Instance")
        instance.GetReferences().AddInternalReference("/Source")
        self.assertTrue(rename_attribute(instance.GetAttribute(OLD), NEW, self.stage.GetEditTarget()))
        self.assertFalse(instance.GetAttribute(NEW).Get())
        self.assertFalse(instance.GetAttribute(OLD).HasAuthoredValue())
        self.assertTrue(source.GetAttribute(OLD).HasAuthoredValue())

    def test_keeps_authored_new_name(self):
        self.old.Set(False)
        self.new.Set(True)
        rename_attribute(self.old, NEW, self.stage.GetEditTarget())
        self.assertTrue(self.new.Get())
        self.assertFalse(self.prim.HasAttribute(OLD))

    def test_blocks_old_name_authored_in_another_layer(self):
        weak = Sdf.Layer.CreateAnonymous(".usda")
        root = Sdf.Layer.CreateAnonymous(".usda")
        root.subLayerPaths.append(weak.identifier)
        stage = Usd.Stage.Open(root)
        with Usd.EditContext(stage, Usd.EditTarget(weak)):
            prim = define_follower(stage)
            author_old(prim).Set(False)
        rename_attribute(prim.GetAttribute(OLD), NEW, stage.GetEditTarget())
        self.assertFalse(prim.GetAttribute(NEW).Get())
        self.assertFalse(prim.GetAttribute(OLD).HasAuthoredValue())
        self.assertIsNotNone(weak.GetAttributeAtPath(f"/Follower.{OLD}"))
        self.assertIsNotNone(root.GetAttributeAtPath(f"/Follower.{NEW}"))


class TestRenamedAttributesValidator(ValidatorTestCase):
    """Validate a hypothetical rename. Validating prims directly does not depend on the validator's `schemaTypes`."""

    validator_name = validators.RENAMED_ATTRIBUTES_VALIDATOR

    def setUp(self):
        super().setUp()
        patch_renames(self, {"NewtonMimicAPI": {OLD: NEW}})
        self.prim = define_follower(self.stage)

    def test_new_name(self):
        self.prim.GetAttribute(NEW).Set(False)
        self.assertEqual(self.validate(self.prim), [])

    def test_old_name(self):
        attr = author_old(self.prim)
        attr.Set(False)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])
        self.assertEqual(self.validate_severities(self.prim), [(ERROR, "Error")])

    def test_deprecated_old_name(self):
        # NewtonCollisionAPI still defines both names, as during a deprecation
        patch_renames(self, {"NewtonCollisionAPI": {"newton:contactMargin": "newton:contactGap"}})
        prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        prim.ApplyAPI("NewtonCollisionAPI")
        attr = prim.GetAttribute("newton:contactMargin")
        attr.Set(0.01)
        self.assertEqual(self.validate(prim), [(ERROR, attr.GetPath())])
        self.assertEqual(self.validate_severities(prim), [(ERROR, "Warn")])

    def test_old_name_time_samples(self):
        attr = author_old(self.prim)
        attr.Set(False, 1.0)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_old_name_without_value(self):
        author_old(self.prim)
        self.assertEqual(self.validate(self.prim), [])

    def test_blocked_old_name(self):
        attr = author_old(self.prim)
        attr.Set(False)
        attr.Block()
        self.assertEqual(self.validate(self.prim), [])

    def test_requires_api(self):
        prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/NotFollower").GetPrim()
        author_old(prim).Set(False)
        self.assertEqual(self.validate(prim), [])

    def test_old_name_defined_by_another_schema(self):
        patch_renames(self, {"NewtonMimicAPI": {"physics:jointEnabled": NEW}})
        self.prim.GetAttribute("physics:jointEnabled").Set(False)
        self.assertEqual(self.validate(self.prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["RenameAttribute"])
        fixer = self.validator.GetFixerByName("RenameAttribute")
        self.assertEqual(fixer.errorName, ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer(self):
        # ApplyFix saves the edit target layer, so the stage must be file backed
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = define_follower(stage)
            author_old(prim).Set(False)
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(error, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
            self.assertFalse(prim.GetAttribute(NEW).Get())
            self.assertFalse(prim.HasAttribute(OLD))
            self.assertFalse(stage.GetRootLayer().dirty)
            self.assertEqual(self.validator.Validate(prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_moves_blocked_time_samples(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = define_follower(stage)
            old = author_old(prim)
            old.Set(True, 1.0)
            old.Set(Sdf.ValueBlock(), 2.0)
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
            new = prim.GetAttribute(NEW)
            self.assertEqual(new.GetTimeSamples(), [1.0, 2.0])
            self.assertIsNone(new.Get(2.0))
            # A retry finds nothing left to migrate
            self.assertEqual(self.validator.Validate(prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_failed_fix_can_be_retried(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = define_follower(stage)
            prim.CreateAttribute(OLD, Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(1, 2, 3))
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertFalse(fixer.ApplyFix(error, stage.GetEditTarget()))
            self.assertFalse(prim.GetAttribute(NEW).HasAuthoredValue())
            self.assertEqual([error.GetName() for error in self.validator.Validate(prim)], [ERROR])


class TestRegisteredRenames(ValidatorTestCase):
    """Check every rename in `RENAMED_ATTRIBUTES` end to end, so adding one needs no new tests."""

    validator_name = validators.RENAMED_ATTRIBUTES_VALIDATOR

    def test_reported_by_keyword(self):
        for schema, old, new in registered_renames():
            with self.subTest(schema=schema, attribute=old):
                stage = Usd.Stage.CreateInMemory()
                author_distinctive_value(define_prim_with_schema(stage, schema), schema, old, new)
                for keyword in ("NewtonValidators", "NewtonMigration", schema):
                    errors = UsdValidation.ValidationContext(keywords=[keyword]).Validate(stage)
                    self.assertEqual([error.GetName() for error in errors if error.GetName() == ERROR], [ERROR], keyword)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixed(self):
        for schema, old, new in registered_renames():
            with self.subTest(schema=schema, attribute=old), tempfile.TemporaryDirectory() as tmpdir:
                path = (pathlib.Path(tmpdir) / "asset.usda").as_posix()
                stage = Usd.Stage.CreateNew(path)
                prim = define_prim_with_schema(stage, schema)
                value = author_distinctive_value(prim, schema, old, new)
                (error,) = self.validator.Validate(prim)
                (fixer,) = error.GetFixersByErrorName()
                self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
                # Reopen the saved asset, rather than the cached layer, to check what was persisted
                saved_stage = Usd.Stage.Open(Sdf.Layer.OpenAsAnonymous(path))
                saved = saved_stage.GetPrimAtPath(prim.GetPath())
                self.assertEqual(saved.GetAttribute(new).Get(), value)
                self.assertFalse(saved.GetAttribute(old).HasAuthoredValue())


if __name__ == "__main__":
    unittest.main()
