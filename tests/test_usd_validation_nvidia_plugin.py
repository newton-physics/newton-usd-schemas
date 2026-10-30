# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import unittest

import newton_usd_schemas  # noqa: F401

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CapabilityRegistry, CategoryRuleRegistry, FeatureRegistry, ProfileRegistry, RequirementsRegistry

    from newton_usd_schemas.validators._requirements import Requirements
    from newton_usd_schemas.validators._usd_validation_nvidia import (
        AttributeHardLimitsChecker,
        MimicJointChecker,
        Plugin,
        RenamedAttributesChecker,
        SdfMaxResolutionChecker,
    )


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
class TestUsdValidationNvidiaPlugin(unittest.TestCase):
    def test_collision_category(self):
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [SdfMaxResolutionChecker])

    def test_joints_category(self):
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [MimicJointChecker])

    def test_basic_category(self):
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))

    def test_migration_category(self):
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonMigration"), [RenamedAttributesChecker])

    def test_sdf_max_resolution_requirement(self):
        self.assertEqual(Requirements.SDF_001.code, "org.newton-physics.SDF.001")
        self.assertEqual(RequirementsRegistry().get_requirements(SdfMaxResolutionChecker), [Requirements.SDF_001])

    def test_mimic_joint_requirement(self):
        self.assertEqual(Requirements.MIMIC_001.code, "org.newton-physics.MIMIC.001")
        self.assertEqual(RequirementsRegistry().get_requirements(MimicJointChecker), [Requirements.MIMIC_001])

    def test_attribute_hard_limits_requirement(self):
        self.assertEqual(Requirements.LIMITS_001.code, "org.newton-physics.LIMITS.001")
        self.assertEqual(RequirementsRegistry().get_requirements(AttributeHardLimitsChecker), [Requirements.LIMITS_001])

    def test_renamed_attributes_requirement(self):
        self.assertEqual(Requirements.MIGRATION_001.code, "org.newton-physics.MIGRATION.001")
        self.assertEqual(RequirementsRegistry().get_requirements(RenamedAttributesChecker), [Requirements.MIGRATION_001])

    def test_sdf_collision_capability(self):
        capability = CapabilityRegistry().find("org.newton-physics.newton_sdf_collision")
        self.assertEqual([requirement.code for requirement in capability.requirements], ["org.newton-physics.SDF.001"])

    def test_mimic_capability(self):
        capability = CapabilityRegistry().find("org.newton-physics.newton_mimic")
        self.assertEqual([requirement.code for requirement in capability.requirements], ["org.newton-physics.MIMIC.001"])

    def test_attribute_limits_capability(self):
        capability = CapabilityRegistry().find("org.newton-physics.attribute_limits")
        self.assertEqual([requirement.code for requirement in capability.requirements], ["org.newton-physics.LIMITS.001"])

    def test_migration_capability(self):
        capability = CapabilityRegistry().find("org.newton-physics.newton_migration")
        self.assertEqual([requirement.code for requirement in capability.requirements], ["org.newton-physics.MIGRATION.001"])

    def test_newton_simulation_feature(self):
        feature = FeatureRegistry().find("org.newton-physics.newton_simulation")
        self.assertEqual(feature.version, "1.1.0")
        self.assertEqual(
            [requirement.code for requirement in feature.requirements],
            [
                "org.newton-physics.SDF.001",
                "org.newton-physics.MIMIC.001",
                "org.newton-physics.LIMITS.001",
                "org.newton-physics.MIGRATION.001",
                "com.nvidia.usd.JT.002",
                "com.nvidia.usd.JT.003",
                "com.nvidia.usd.JT.ART.002",
                "com.nvidia.usd.JT.ART.004",
                "com.nvidia.usd.RB.003",
                "com.nvidia.usd.RB.009",
                "com.nvidia.usd.RB.COL.004",
            ],
        )

    def test_newton_simulation_profile(self):
        profile = ProfileRegistry().find("org.newton-physics.Newton-Simulation")
        self.assertEqual(profile.version, "1.1.0")
        self.assertEqual([feature.id for feature in profile.features], ["org.newton-physics.newton_simulation"])

    def test_shutdown_and_startup(self):
        plugin = Plugin()
        plugin.on_shutdown()
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [])
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [])
        self.assertNotIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonMigration"), [])
        self.assertEqual(RequirementsRegistry().get_requirements(SdfMaxResolutionChecker), [])
        self.assertIsNone(CapabilityRegistry().find("org.newton-physics.newton_mimic"))
        self.assertIsNone(FeatureRegistry().find("org.newton-physics.newton_simulation"))
        self.assertIsNone(ProfileRegistry().find("org.newton-physics.Newton-Simulation"))
        plugin.on_startup()
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [SdfMaxResolutionChecker])
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [MimicJointChecker])
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonMigration"), [RenamedAttributesChecker])
        self.assertEqual(RequirementsRegistry().get_requirements(SdfMaxResolutionChecker), [Requirements.SDF_001])
        self.assertIsNotNone(CapabilityRegistry().find("org.newton-physics.newton_mimic"))
        self.assertIsNotNone(FeatureRegistry().find("org.newton-physics.newton_simulation"))
        self.assertIsNotNone(ProfileRegistry().find("org.newton-physics.Newton-Simulation"))


if __name__ == "__main__":
    unittest.main()
