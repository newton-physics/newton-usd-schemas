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

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CapabilityRegistry, CategoryRuleRegistry, IssueFixer, IssueSeverity, ProfileRegistry, ValidationEngine

    from newton_usd_schemas.validators._requirements import Requirements
    from newton_usd_schemas.validators._usd_validation_nvidia import (
        AttributeHardLimitsChecker,
        MimicJointChecker,
        RenamedAttributesChecker,
        SdfMaxResolutionChecker,
    )

    RULES = (SdfMaxResolutionChecker, MimicJointChecker, AttributeHardLimitsChecker, RenamedAttributesChecker)


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

        particles = UsdGeom.Points.Define(stage, "/World/Particles").GetPrim()
        particles.ApplyAPI("NewtonPointsDeformableSimAPI")
        particles.CreateAttribute("physics:masses", Sdf.ValueTypeNames.FloatArray).Set(Vt.FloatArray([0.2, 0.2]))

        # Only the Newton-Simulation profile checks this, through usd-validation-nvidia's UsdPhysics rules
        broken = UsdPhysics.RevoluteJoint.Define(stage, "/World/BrokenJoint")
        broken.CreateBody0Rel().SetTargets(["/World/Missing"])
        stage.Save()

    def issues(self, engine: "ValidationEngine") -> dict:
        return {issue.rule: issue for issue in engine.validate(self.path).issues() if issue.rule in RULES}

    def engine(self, *rules) -> "ValidationEngine":
        engine = ValidationEngine(init_rules=False)
        for rule in rules:
            engine.enable_rule(rule)
        return engine

    def engine_for_capability(self, capability_id: str) -> "ValidationEngine":
        engine = ValidationEngine(init_rules=False)
        engine.enable_capability(CapabilityRegistry().find(capability_id))
        return engine

    def test_sdf_max_resolution_issue(self):
        issue = self.issues(self.engine(SdfMaxResolutionChecker))[SdfMaxResolutionChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Collider.newton:sdfMaxResolution"))
        self.assertEqual(issue.requirement, Requirements.SDF_001)
        self.assertEqual(len(issue.suggestions), 1)

    def test_mimic_joint_issue(self):
        issue = self.issues(self.engine(MimicJointChecker))[MimicJointChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Follower.newton:mimicJoint"))
        self.assertEqual(issue.requirement, Requirements.MIMIC_001)
        self.assertIn("same joint type", issue.message)
        self.assertEqual(issue.suggestions, ())

    def test_attribute_hard_limits_issue(self):
        issue = self.issues(self.engine(AttributeHardLimitsChecker))[AttributeHardLimitsChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Collider.newton:contactGap"))
        self.assertEqual(issue.requirement, Requirements.LIMITS_001)
        self.assertEqual(issue.suggestions, ())

    def test_renamed_attributes_issue(self):
        issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        self.assertEqual(issue.severity, IssueSeverity.FAILURE)
        self.assertEqual(issue.at.path, Sdf.Path("/World/Particles.physics:masses"))
        self.assertEqual(issue.requirement, Requirements.MIGRATION_001)
        self.assertIn("newton:masses", issue.message)
        self.assertEqual(len(issue.suggestions), 1)

    def test_sdf_collision_capability(self):
        self.assertEqual(set(self.issues(self.engine_for_capability("org.newton-physics.newton_sdf_collision"))), {SdfMaxResolutionChecker})

    def test_mimic_capability(self):
        self.assertEqual(set(self.issues(self.engine_for_capability("org.newton-physics.newton_mimic"))), {MimicJointChecker})

    def test_attribute_limits_capability(self):
        self.assertEqual(set(self.issues(self.engine_for_capability("org.newton-physics.attribute_limits"))), {AttributeHardLimitsChecker})

    def test_migration_capability(self):
        self.assertEqual(set(self.issues(self.engine_for_capability("org.newton-physics.newton_migration"))), {RenamedAttributesChecker})

    def test_newton_simulation_profile(self):
        engine = ValidationEngine(init_rules=False)
        engine.enable_profile(ProfileRegistry().find("org.newton-physics.Newton-Simulation"))
        issues = engine.validate(self.path).issues()
        codes = {issue.requirement.code for issue in issues if issue.requirement}
        self.assertEqual(
            codes,
            {
                "org.newton-physics.SDF.001",
                "org.newton-physics.MIMIC.001",
                "org.newton-physics.LIMITS.001",
                "org.newton-physics.MIGRATION.001",
                "com.nvidia.usd.JT.002",
            },
        )

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

    def test_fix_renamed_attributes(self):
        issue = self.issues(self.engine(RenamedAttributesChecker))[RenamedAttributesChecker]
        fixer = IssueFixer(self.path)
        fixer.fix([issue])
        fixer.save()
        layer = Sdf.Layer.FindOrOpen(self.path)
        layer.Reload()
        self.assertEqual(layer.GetAttributeAtPath("/World/Particles.newton:masses").default, Vt.FloatArray([0.2, 0.2]))
        self.assertIsNone(layer.GetAttributeAtPath("/World/Particles.physics:masses"))
        self.assertNotIn(RenamedAttributesChecker, self.issues(self.engine(RenamedAttributesChecker)))


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
@unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
class TestNativeRules(RulesTests, unittest.TestCase):
    def test_native_validators_implemented(self):
        self.assertTrue(SdfMaxResolutionChecker.is_implemented())
        self.assertTrue(MimicJointChecker.is_implemented())
        self.assertTrue(AttributeHardLimitsChecker.is_implemented())
        self.assertTrue(RenamedAttributesChecker.is_implemented())


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
