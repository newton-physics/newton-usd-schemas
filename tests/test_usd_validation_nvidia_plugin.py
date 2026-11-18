# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import json
import pathlib
import unittest

import newton_usd_schemas  # noqa: F401
from newton_usd_schemas import validators
from newton_usd_schemas.validators._registration import validator_name

HAS_USD_VALIDATION_NVIDIA = importlib.util.find_spec("usd_validation_nvidia") is not None

if HAS_USD_VALIDATION_NVIDIA:
    from usd_validation_nvidia import CategoryRuleRegistry

    from newton_usd_schemas.validators._usd_validation_nvidia import (
        AttributeHardLimitsChecker,
        KaminoSccSolverChecker,
        MimicJointChecker,
        Plugin,
        RenamedAPISchemasChecker,
        RenamedAttributesChecker,
        SdfMaxResolutionChecker,
    )

    CATEGORIES = {
        "NewtonCollision": [SdfMaxResolutionChecker],
        "NewtonJoints": [MimicJointChecker],
        "NewtonKamino": [KaminoSccSolverChecker],
        "NewtonMigration": [RenamedAttributesChecker, RenamedAPISchemasChecker],
    }


@unittest.skipUnless(HAS_USD_VALIDATION_NVIDIA, "usd-validation-nvidia is not installed")
class TestUsdValidationNvidiaPlugin(unittest.TestCase):
    def test_newton_categories(self):
        for category, rules in CATEGORIES.items():
            with self.subTest(category=category):
                self.assertEqual(CategoryRuleRegistry().get_rules(category), rules)

    def test_rule_for_every_validator(self):
        """Wrap every validator declared in the validators' plugInfo.json in exactly one rule."""
        plug_info = json.loads((pathlib.Path(validators.__file__).parent / "plugInfo.json").read_text())
        names = [name for name in plug_info["Plugins"][0]["Info"]["Validators"] if name != "keywords"]
        rules = [rule.validator_name() for _, rule in Plugin.rules]
        self.assertCountEqual(rules, [validator_name(name) for name in names])

    def test_basic_category(self):
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))

    def test_shutdown_and_startup(self):
        plugin = Plugin()
        plugin.on_shutdown()
        for category in CATEGORIES:
            self.assertEqual(CategoryRuleRegistry().get_rules(category), [])
        self.assertNotIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))
        plugin.on_startup()
        for category, rules in CATEGORIES.items():
            self.assertEqual(CategoryRuleRegistry().get_rules(category), rules)
        self.assertIn(AttributeHardLimitsChecker, CategoryRuleRegistry().get_rules("Basic"))


if __name__ == "__main__":
    unittest.main()
