# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdGeom, UsdPhysics, Vt
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS

import newton_usd_schemas  # noqa: F401
from newton_usd_schemas.validators import _migration

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CategoryRuleRegistry, FixStatus, IssueFixer, IssueSeverity, ValidationEngine

    from newton_usd_schemas.validators._usd_validation_nvidia import (
        AttributeHardLimitsChecker,
        KaminoSccSolverChecker,
        MimicJointChecker,
        RenamedAPISchemasChecker,
        RenamedAttributesChecker,
        SdfMaxResolutionChecker,
    )

    RULES = (
        SdfMaxResolutionChecker,
        MimicJointChecker,
        KaminoSccSolverChecker,
        RenamedAttributesChecker,
        RenamedAPISchemasChecker,
        AttributeHardLimitsChecker,
    )

MASSES = Vt.FloatArray([0.25, 0.5])


class RulesTests:
    """Tests for the usd-validation-nvidia rules, run with and without the native `UsdValidation` validators."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.path = (pathlib.Path(self.tmpdir.name) / "asset.usda").as_posix()
        stage = Usd.Stage.CreateNew(self.path)
        stage.SetDefaultPrim(UsdGeom.Xform.Define(stage, "/World").GetPrim())

        collider = UsdGeom.Cube.Define(stage, "/World/Collider").GetPrim()
        collider.ApplyAPI("NewtonSDFCollisionAPI")
        collider.GetAttribute("newton:sdfMaxResolution").Set(100)
        collider.GetAttribute("newton:contactGap").Set(-0.01)

        leader = UsdPhysics.PrismaticJoint.Define(stage, "/World/Leader").GetPrim()
        follower = UsdPhysics.RevoluteJoint.Define(stage, "/World/Follower").GetPrim()
        follower.ApplyAPI("NewtonMimicAPI")
        follower.GetRelationship("newton:mimicJoint").SetTargets([leader.GetPath()])

        # The base Kamino API is listed first, so its solver default wins over the SCC API's
        scene = UsdPhysics.Scene.Define(stage, "/World/Scene").GetPrim()
        scene.ApplyAPI("NewtonKaminoSceneAPI")
        scene.ApplyAPI("NewtonKaminoSccSceneAPI")

        deformable = UsdGeom.Points.Define(stage, "/World/Deformable").GetPrim()
        deformable.ApplyAPI("NewtonPointsDeformableSimAPI")
        deformable.CreateAttribute("physics:masses", Sdf.ValueTypeNames.FloatArray).Set(MASSES)
        stage.Save()

    def patch_api_schema_renames(self, renames: dict[str, str]) -> None:
        patcher = mock.patch.dict(_migration.RENAMED_API_SCHEMAS, renames, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def apply_api_schema(self, schema: str) -> None:
        stage = Usd.Stage.Open(self.path)
        prim = stage.DefinePrim("/World/Actuator", "NewtonActuator")
        prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=[schema]))
        stage.Save()

    def fix(self, issue) -> "FixStatus":
        fixer = IssueFixer(self.path)
        (result,) = fixer.fix([issue])
        fixer.save()
        layer = Sdf.Layer.FindOrOpen(self.path)
        layer.Reload()
        return result.status

    def issues(self, engine: "ValidationEngine") -> dict:
        return {issue.rule: issue for issue in engine.validate(self.path).issues() if issue.rule in RULES}

    def engine(self, *rules) -> "ValidationEngine":
        engine = ValidationEngine(init_rules=False)
        for rule in rules:
            engine.enable_rule(rule)
        return engine

    def engine_for_category(self, category: str) -> "ValidationEngine":
        return self.engine(*CategoryRuleRegistry().get_rules(category))

    def test_sdf_max_resolution_issue(self):
        issue = self.issues(self.engine(SdfMaxResolutionChecker))[SdfMaxResolutionChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Collider.newton:sdfMaxResolution"))
        self.assertIn("divisible by 8", issue.message)
        self.assertEqual(len(issue.suggestions), 1)

    def test_mimic_joint_issue(self):
        issue = self.issues(self.engine(MimicJointChecker))[MimicJointChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Follower.newton:mimicJoint"))
        self.assertIn("same joint type", issue.message)
        self.assertEqual(issue.suggestions, ())

    def test_attribute_hard_limits_issue(self):
        issue = self.issues(self.engine(AttributeHardLimitsChecker))[AttributeHardLimitsChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Collider.newton:contactGap"))
        self.assertIn("hard limits", issue.message)
        self.assertEqual(issue.suggestions, ())

    def test_kamino_scc_solver_issue(self):
        issue = self.issues(self.engine(KaminoSccSolverChecker))[KaminoSccSolverChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Scene.newton:kamino:dynamicsSolver"))
        self.assertIn("NewtonKaminoSccSceneAPI", issue.message)
        self.assertEqual(issue.suggestions, ())

    def test_renamed_attribute_issue(self):
        issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Deformable.physics:masses"))
        self.assertIn("renamed to newton:masses", issue.message)
        self.assertEqual(len(issue.suggestions), 1)

    def test_deprecated_attribute_issue(self):
        """Report an attribute that its schema still defines as a warning."""
        renames = {"NewtonCollisionAPI": {"newton:contactMargin": "newton:contactGap"}}
        with mock.patch.dict(_migration.RENAMED_ATTRIBUTES, renames, clear=True):
            stage = Usd.Stage.Open(self.path)
            collider = stage.GetPrimAtPath("/World/Collider")
            collider.ApplyAPI("NewtonCollisionAPI")
            collider.GetAttribute("newton:contactMargin").Set(0.01)
            stage.Save()
            issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        self.assertEqual(issue.severity, IssueSeverity.WARNING)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Collider.newton:contactMargin"))
        self.assertIn("deprecated", issue.message)
        self.assertEqual(len(issue.suggestions), 1)

    def test_renamed_api_schema_issue(self):
        self.patch_api_schema_renames({"NewtonLegacyMimicAPI": "NewtonMimicAPI"})
        self.apply_api_schema("NewtonLegacyMimicAPI")
        issue = self.issues(self.engine(RenamedAPISchemasChecker))[RenamedAPISchemasChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Actuator"))
        self.assertIn("renamed to NewtonMimicAPI", issue.message)
        self.assertEqual(len(issue.suggestions), 1)

    def test_deprecated_api_schema_issue(self):
        """Report an API schema that is still registered as a warning."""
        self.patch_api_schema_renames({"NewtonMaxEffortClampingAPI": "NewtonDCMotorClampingAPI"})
        self.apply_api_schema("NewtonMaxEffortClampingAPI")
        issue = self.issues(self.engine(RenamedAPISchemasChecker))[RenamedAPISchemasChecker]
        self.assertEqual(issue.severity, IssueSeverity.WARNING)
        self.assertIn("deprecated", issue.message)

    def test_collision_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonCollision"))), {SdfMaxResolutionChecker})

    def test_joints_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonJoints"))), {MimicJointChecker})

    def test_kamino_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonKamino"))), {KaminoSccSolverChecker})

    def test_migration_category(self):
        self.patch_api_schema_renames({"NewtonLegacyMimicAPI": "NewtonMimicAPI"})
        self.apply_api_schema("NewtonLegacyMimicAPI")
        rules = {RenamedAttributesChecker, RenamedAPISchemasChecker}
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonMigration"))), rules)

    def test_basic_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("Basic"))), {AttributeHardLimitsChecker})

    def test_disable_joints_category(self):
        engine = self.engine(SdfMaxResolutionChecker, MimicJointChecker)
        for rule in CategoryRuleRegistry().get_rules("NewtonJoints"):
            engine.disable_rule(rule)
        self.assertEqual(set(self.issues(engine)), {SdfMaxResolutionChecker})

    def test_disable_collision_category(self):
        engine = self.engine(SdfMaxResolutionChecker, MimicJointChecker)
        for rule in CategoryRuleRegistry().get_rules("NewtonCollision"):
            engine.disable_rule(rule)
        self.assertEqual(set(self.issues(engine)), {MimicJointChecker})

    def test_fix_sdf_max_resolution(self):
        issue = self.issues(self.engine(SdfMaxResolutionChecker))[SdfMaxResolutionChecker]
        fixer = IssueFixer(self.path)
        fixer.fix([issue])
        fixer.save()
        layer = Sdf.Layer.FindOrOpen(self.path)
        layer.Reload()
        self.assertEqual(layer.GetAttributeAtPath("/World/Collider.newton:sdfMaxResolution").default, 104)
        self.assertNotIn(SdfMaxResolutionChecker, self.issues(self.engine(SdfMaxResolutionChecker)))

    def test_fix_renamed_attribute(self):
        issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        self.assertEqual(self.fix(issue), FixStatus.SUCCESS)
        layer = Sdf.Layer.FindOrOpen(self.path)
        self.assertEqual(layer.GetAttributeAtPath("/World/Deformable.newton:masses").default, MASSES)
        self.assertIsNone(layer.GetAttributeAtPath("/World/Deformable.physics:masses"))
        self.assertNotIn(RenamedAttributesChecker, self.issues(self.engine(RenamedAttributesChecker)))

    def test_fix_renamed_attribute_from_another_asset(self):
        """Fail to fix an attribute that the asset's layers cannot override, and author nothing."""
        source = (pathlib.Path(self.tmpdir.name) / "source.usda").as_posix()
        source_stage = Usd.Stage.CreateNew(source)
        points = UsdGeom.Points.Define(source_stage, "/Deformable").GetPrim()
        points.ApplyAPI("NewtonPointsDeformableSimAPI")
        points.CreateAttribute("physics:masses", Sdf.ValueTypeNames.FloatArray).Set(MASSES)
        source_stage.Save()
        stage = Usd.Stage.Open(self.path)
        stage.RemovePrim("/World/Deformable")
        stage.DefinePrim("/World/Instance").GetReferences().AddReference(source, "/Deformable")
        stage.Save()
        layer = Sdf.Layer.FindOrOpen(self.path)
        before = layer.ExportToString()
        issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        (result,) = IssueFixer(self.path).fix_at([issue], layer)
        self.assertEqual(result.status, FixStatus.FAILURE)
        self.assertIn("cannot be migrated", str(result.exception))
        self.assertEqual(layer.ExportToString(), before)

    def test_fix_renamed_api_schema(self):
        self.patch_api_schema_renames({"NewtonLegacyMimicAPI": "NewtonMimicAPI"})
        self.apply_api_schema("NewtonLegacyMimicAPI")
        issue = self.issues(self.engine(RenamedAPISchemasChecker))[RenamedAPISchemasChecker]
        self.assertEqual(self.fix(issue), FixStatus.SUCCESS)
        layer = Sdf.Layer.FindOrOpen(self.path)
        schemas = layer.GetPrimAtPath("/World/Actuator").GetInfo("apiSchemas")
        self.assertEqual(schemas.prependedItems, ["NewtonMimicAPI"])
        self.assertNotIn(RenamedAPISchemasChecker, self.issues(self.engine(RenamedAPISchemasChecker)))


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
@unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
class TestNativeRules(RulesTests, unittest.TestCase):
    def test_native_validators_implemented(self):
        self.assertTrue(SdfMaxResolutionChecker.is_implemented())
        for rule in RULES:
            self.assertTrue(rule.is_implemented())


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
class TestFallbackRules(RulesTests, unittest.TestCase):
    """The rules run their Python fallbacks whenever the native validators are not registered, as with OpenUSD before 26.05."""

    def setUp(self):
        super().setUp()
        for rule in RULES:
            patcher = mock.patch.object(rule, "is_implemented", classmethod(lambda cls: False))
            patcher.start()
            self.addCleanup(patcher.stop)


if __name__ == "__main__":
    unittest.main()
