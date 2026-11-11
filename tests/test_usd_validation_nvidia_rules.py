# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS

import newton_usd_schemas  # noqa: F401

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CategoryRuleRegistry, IssueFixer, IssueSeverity, ValidationEngine

    from newton_usd_schemas.validators._usd_validation_nvidia import AttributeHardLimitsChecker, MimicJointChecker, SdfMaxResolutionChecker

    RULES = (SdfMaxResolutionChecker, MimicJointChecker, AttributeHardLimitsChecker)


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
        stage.Save()

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

    def test_collision_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonCollision"))), {SdfMaxResolutionChecker})

    def test_joints_category(self):
        self.assertEqual(set(self.issues(self.engine_for_category("NewtonJoints"))), {MimicJointChecker})

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


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
@unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
class TestNativeRules(RulesTests, unittest.TestCase):
    def test_native_validators_implemented(self):
        self.assertTrue(SdfMaxResolutionChecker.is_implemented())
        self.assertTrue(MimicJointChecker.is_implemented())
        self.assertTrue(AttributeHardLimitsChecker.is_implemented())


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
