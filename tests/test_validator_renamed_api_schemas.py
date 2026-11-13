# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import tempfile
import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdPhysics
from validator_test_case import SUPPORTS_PYTHON_FIXERS, SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase

from newton_usd_schemas import validators
from newton_usd_schemas.validators import _migration
from newton_usd_schemas.validators._migration import RENAMED_API_SCHEMAS, authored_api_schemas, rename_api_schema

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

ERROR = "RenamedAPISchema"

# Hypothetical renames, so the behavior tests do not depend on the schemas that have actually been renamed
OLD = "NewtonLegacyMimicAPI"
NEW = "NewtonMimicAPI"
DEPRECATED = "NewtonMaxEffortClampingAPI"
REPLACEMENT = "NewtonDCMotorClampingAPI"


def patch_renames(test: unittest.TestCase, renames: dict[str, str]) -> None:
    patcher = mock.patch.dict(_migration.RENAMED_API_SCHEMAS, renames, clear=True)
    patcher.start()
    test.addCleanup(patcher.stop)


def apply_schemas(prim: Usd.Prim, *schemas: str) -> None:
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=list(schemas)))


def assert_saved_schemas(test: unittest.TestCase, stage: Usd.Stage, path: Sdf.Path, applied: list[str], removed: list[str]) -> None:
    """Reopen the saved asset, rather than the cached layer, and check its composed schemas without the migration helpers."""
    saved_stage = Usd.Stage.Open(Sdf.Layer.OpenAsAnonymous(stage.GetRootLayer().realPath))
    saved = saved_stage.GetPrimAtPath(path)
    for schema in applied:
        test.assertTrue(saved.HasAPI(schema), schema)
    composed = saved.GetMetadata("apiSchemas").ApplyOperations([])
    for schema in removed:
        test.assertNotIn(schema, composed)


class TestAuthoredAPISchemas(unittest.TestCase):
    def test_excludes_built_in_schemas(self):
        stage = Usd.Stage.CreateInMemory()
        prim = stage.DefinePrim("/Actuator")
        apply_schemas(prim, "NewtonMaxEffortClampingAPI")
        self.assertIn("NewtonActuatorClampingBaseAPI", prim.GetAppliedSchemas())
        self.assertEqual(authored_api_schemas(prim), ["NewtonMaxEffortClampingAPI"])

    def test_composes_layers(self):
        weak = Sdf.Layer.CreateAnonymous(".usda")
        root = Sdf.Layer.CreateAnonymous(".usda")
        root.subLayerPaths.append(weak.identifier)
        stage = Usd.Stage.Open(root)
        with Usd.EditContext(stage, Usd.EditTarget(weak)):
            apply_schemas(stage.DefinePrim("/Joint"), OLD, "NewtonCollisionAPI")
        prim = stage.GetPrimAtPath("/Joint")
        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(deletedItems=["NewtonCollisionAPI"]))
        self.assertEqual(authored_api_schemas(prim), [OLD])


class TestRenameAPISchema(unittest.TestCase):
    """`rename_api_schema` backs the `UsdValidation` fixer, and is tested directly so it runs with every OpenUSD version."""

    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Joint").GetPrim()

    def test_keeps_position(self):
        apply_schemas(self.prim, "NewtonCollisionAPI", OLD, "NewtonActuatorDelayAPI")
        self.assertTrue(rename_api_schema(self.prim, OLD, NEW, self.stage.GetEditTarget()))
        self.assertEqual(authored_api_schemas(self.prim), ["NewtonCollisionAPI", NEW, "NewtonActuatorDelayAPI"])
        self.assertTrue(self.prim.HasAPI(NEW))

    def test_explicit_list(self):
        self.prim.SetMetadata("apiSchemas", Sdf.TokenListOp.CreateExplicit([OLD, "NewtonCollisionAPI"]))
        rename_api_schema(self.prim, OLD, NEW, self.stage.GetEditTarget())
        list_op = self.prim.GetPrimStack()[0].GetInfo("apiSchemas")
        self.assertTrue(list_op.isExplicit)
        self.assertEqual(list(list_op.explicitItems), [NEW, "NewtonCollisionAPI"])

    def test_legacy_added_items(self):
        list_op = Sdf.TokenListOp()
        list_op.addedItems = [OLD, "NewtonCollisionAPI"]
        self.prim.SetMetadata("apiSchemas", list_op)
        self.assertTrue(rename_api_schema(self.prim, OLD, NEW, self.stage.GetEditTarget()))
        self.assertEqual(list(self.prim.GetPrimStack()[0].GetInfo("apiSchemas").addedItems), [NEW, "NewtonCollisionAPI"])
        self.assertTrue(self.prim.HasAPI(NEW))

    def test_old_schema_from_an_internal_reference(self):
        source = UsdPhysics.RevoluteJoint.Define(self.stage, "/Source").GetPrim()
        apply_schemas(source, OLD)
        instance = self.stage.DefinePrim("/Instance")
        instance.GetReferences().AddInternalReference("/Source")
        self.assertTrue(rename_api_schema(instance, OLD, NEW, self.stage.GetEditTarget()))
        self.assertTrue(instance.HasAPI(NEW))
        # The old schema is replaced where it is applied, which migrates the referenced prim too
        self.assertEqual(authored_api_schemas(source), [NEW])

    def test_migrates_the_selected_variant(self):
        variants = self.prim.GetVariantSets().AddVariantSet("mimic")
        variants.AddVariant("off")
        variants.AddVariant("on")
        variants.SetVariantSelection("on")
        with variants.GetVariantEditContext():
            apply_schemas(self.prim, OLD)
        self.assertTrue(rename_api_schema(self.prim, OLD, NEW, self.stage.GetEditTarget()))
        self.assertTrue(self.prim.HasAPI(NEW))
        self.assertFalse(self.prim.GetPrimStack()[0].HasInfo("apiSchemas"))
        variants.SetVariantSelection("off")
        self.assertFalse(self.prim.HasAPI(NEW))

    def test_refuses_another_asset(self):
        asset = Sdf.Layer.CreateAnonymous(".usda")
        asset_stage = Usd.Stage.Open(asset)
        apply_schemas(UsdPhysics.RevoluteJoint.Define(asset_stage, "/Joint").GetPrim(), OLD)
        instance = self.stage.DefinePrim("/Instance")
        instance.GetReferences().AddReference(asset.identifier, "/Joint")
        before = self.stage.GetRootLayer().ExportToString()
        self.assertFalse(rename_api_schema(instance, OLD, NEW, self.stage.GetEditTarget()))
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), before)

    def test_new_schema_already_applied(self):
        apply_schemas(self.prim, OLD, NEW)
        rename_api_schema(self.prim, OLD, NEW, self.stage.GetEditTarget())
        self.assertEqual(authored_api_schemas(self.prim), [NEW])

    def test_old_schema_applied_in_another_layer(self):
        weak = Sdf.Layer.CreateAnonymous(".usda")
        root = Sdf.Layer.CreateAnonymous(".usda")
        root.subLayerPaths.append(weak.identifier)
        stage = Usd.Stage.Open(root)
        with Usd.EditContext(stage, Usd.EditTarget(weak)):
            apply_schemas(UsdPhysics.RevoluteJoint.Define(stage, "/Joint").GetPrim(), OLD)
        prim = stage.GetPrimAtPath("/Joint")
        self.assertTrue(rename_api_schema(prim, OLD, NEW, stage.GetEditTarget()))
        self.assertEqual(authored_api_schemas(prim), [NEW])
        self.assertEqual(list(weak.GetPrimAtPath("/Joint").GetInfo("apiSchemas").prependedItems), [OLD])
        self.assertEqual(list(root.GetPrimAtPath("/Joint").GetInfo("apiSchemas").deletedItems), [OLD])


class TestRenamedAPISchemasValidator(ValidatorTestCase):
    """Validate hypothetical renames. Validating prims directly does not depend on the validator's `schemaTypes`."""

    validator_name = validators.RENAMED_API_SCHEMAS_VALIDATOR

    def setUp(self):
        super().setUp()
        patch_renames(self, {OLD: NEW, DEPRECATED: REPLACEMENT})
        self.prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Joint").GetPrim()

    def test_new_schema(self):
        apply_schemas(self.prim, NEW)
        self.assertEqual(self.validate(self.prim), [])

    def test_removed_schema(self):
        apply_schemas(self.prim, OLD)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.prim.GetPath())])
        self.assertEqual(self.validate_severities(self.prim), [(ERROR, "Error")])

    def test_deprecated_schema(self):
        apply_schemas(self.prim, DEPRECATED)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.prim.GetPath())])
        self.assertEqual(self.validate_severities(self.prim), [(ERROR, "Warn")])

    def test_each_renamed_schema(self):
        apply_schemas(self.prim, OLD, DEPRECATED)
        self.assertEqual(self.validate_severities(self.prim), [(ERROR, "Error"), (ERROR, "Warn")])

    def test_built_in_schema_is_not_reported(self):
        patch_renames(self, {"NewtonActuatorClampingBaseAPI": NEW})
        apply_schemas(self.prim, "NewtonMaxEffortClampingAPI")
        self.assertEqual(self.validate(self.prim), [])

    def test_schema_deleted_by_a_stronger_layer_is_not_reported(self):
        weak = Sdf.Layer.CreateAnonymous(".usda")
        root = Sdf.Layer.CreateAnonymous(".usda")
        root.subLayerPaths.append(weak.identifier)
        stage = Usd.Stage.Open(root)
        with Usd.EditContext(stage, Usd.EditTarget(weak)):
            apply_schemas(UsdPhysics.RevoluteJoint.Define(stage, "/Joint").GetPrim(), OLD)
        prim = stage.GetPrimAtPath("/Joint")
        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(deletedItems=[OLD]))
        self.assertEqual(self.validate(prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["RenameAPISchema"])
        fixer = self.validator.GetFixerByName("RenameAPISchema")
        self.assertEqual(fixer.errorName, ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer(self):
        # ApplyFix saves the edit target layer, so the stage must be file backed
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = UsdPhysics.RevoluteJoint.Define(stage, "/Joint").GetPrim()
            apply_schemas(prim, OLD, DEPRECATED)
            errors = self.validator.Validate(prim)
            fixer = errors[0].GetFixersByErrorName()[0]
            self.assertTrue(fixer.CanApplyFix(errors[0], stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(errors[0], stage.GetEditTarget()))
            self.assertFalse(stage.GetRootLayer().dirty)
            self.assertEqual(self.validator.Validate(prim), [])
            assert_saved_schemas(self, stage, prim.GetPath(), applied=[NEW, REPLACEMENT], removed=[OLD, DEPRECATED])


class TestRegisteredAPISchemaRenames(ValidatorTestCase):
    """Check every rename in `RENAMED_API_SCHEMAS` end to end, so adding one needs no new tests."""

    validator_name = validators.RENAMED_API_SCHEMAS_VALIDATOR

    def test_new_names_are_registered(self):
        for old, new in RENAMED_API_SCHEMAS.items():
            with self.subTest(schema=old):
                self.assertIsNotNone(Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(new))

    def test_reported_by_keyword(self):
        for old in RENAMED_API_SCHEMAS:
            with self.subTest(schema=old):
                stage = Usd.Stage.CreateInMemory()
                apply_schemas(stage.DefinePrim("/Prim"), old)
                for keyword in ("NewtonValidators", "NewtonMigration"):
                    errors = UsdValidation.ValidationContext(keywords=[keyword]).Validate(stage)
                    self.assertEqual([error.GetName() for error in errors if error.GetName() == ERROR], [ERROR], keyword)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixed(self):
        for old, new in RENAMED_API_SCHEMAS.items():
            with self.subTest(schema=old), tempfile.TemporaryDirectory() as tmpdir:
                stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
                prim = stage.DefinePrim("/Prim")
                apply_schemas(prim, old)
                (error,) = self.validator.Validate(prim)
                (fixer,) = error.GetFixersByErrorName()
                self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
                assert_saved_schemas(self, stage, prim.GetPath(), applied=[new], removed=[old])


if __name__ == "__main__":
    unittest.main()
