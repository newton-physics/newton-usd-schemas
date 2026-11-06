# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import tempfile
import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdPhysics
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


def author_with_new_type(prim: Usd.Prim, schema: str, old: str, new: str) -> Usd.Attribute:
    definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema)
    type_name = definition.GetSchemaAttributeSpec(new).typeName
    attr = prim.CreateAttribute(old, type_name)
    attr.Set(type_name.defaultValue)
    return attr


class TestRenamedAttributesTable(unittest.TestCase):
    def test_plugin_metadata_lists_every_schema(self):
        plug_info = json.loads((pathlib.Path(validators.__file__).parent / "plugInfo.json").read_text())
        metadata = plug_info["Plugins"][0]["Info"]["Validators"]["RenamedAttributesValidator"]
        schema_types = [Usd.SchemaRegistry.GetTypeFromSchemaTypeName(schema).typeName for schema in RENAMED_ATTRIBUTES]
        self.assertEqual(metadata.get("schemaTypes", []), schema_types)
        self.assertEqual(metadata["keywords"], ["NewtonMigration", *RENAMED_ATTRIBUTES])

    def test_new_names_are_defined_by_their_schemas(self):
        for schema, old, new in registered_renames():
            definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema)
            with self.subTest(schema=schema, attribute=new):
                self.assertTrue(definition.GetPropertyDefinition(new))
                self.assertFalse(definition.GetPropertyDefinition(old))


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


class TestRegisteredRenames(ValidatorTestCase):
    """Check every rename in `RENAMED_ATTRIBUTES` end to end, so adding one needs no new tests."""

    validator_name = validators.RENAMED_ATTRIBUTES_VALIDATOR

    def test_reported_by_keyword(self):
        for schema, old, new in registered_renames():
            with self.subTest(schema=schema, attribute=old):
                stage = Usd.Stage.CreateInMemory()
                author_with_new_type(define_prim_with_schema(stage, schema), schema, old, new)
                for keyword in ("NewtonValidators", "NewtonMigration", schema):
                    errors = UsdValidation.ValidationContext(keywords=[keyword]).Validate(stage)
                    self.assertEqual([error.GetName() for error in errors if error.GetName() == ERROR], [ERROR], keyword)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixed(self):
        for schema, old, new in registered_renames():
            with self.subTest(schema=schema, attribute=old), tempfile.TemporaryDirectory() as tmpdir:
                stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
                prim = define_prim_with_schema(stage, schema)
                author_with_new_type(prim, schema, old, new)
                (error,) = self.validator.Validate(prim)
                (fixer,) = error.GetFixersByErrorName()
                self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
                self.assertFalse(prim.HasAttribute(old))
                self.assertTrue(prim.GetAttribute(new).HasAuthoredValue())


if __name__ == "__main__":
    unittest.main()
