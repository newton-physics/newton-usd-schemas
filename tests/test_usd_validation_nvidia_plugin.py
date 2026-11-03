# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import unittest

import newton_usd_schemas  # noqa: F401

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CategoryRuleRegistry

    from newton_usd_schemas.validators._usd_validation_nvidia import AttributeHardLimitsChecker, MimicJointChecker, Plugin, SdfMaxResolutionChecker


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
class TestUsdValidationNvidiaPlugin(unittest.TestCase):
    def test_collision_category(self):
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [SdfMaxResolutionChecker])

    def test_joints_category(self):
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [MimicJointChecker])

    def test_basic_category(self):
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))

    def test_shutdown_and_startup(self):
        plugin = Plugin()
        plugin.on_shutdown()
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [])
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [])
        self.assertNotIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))
        plugin.on_startup()
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonCollision"), [SdfMaxResolutionChecker])
        self.assertEqual(CategoryRuleRegistry().get_rules("NewtonJoints"), [MimicJointChecker])
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))


if __name__ == "__main__":
    unittest.main()
