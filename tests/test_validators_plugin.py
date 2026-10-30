# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import unittest

from pxr import Plug
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase, run_python

import newton_usd_schemas
from newton_usd_schemas import validators

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation


class TestValidatorsImport(unittest.TestCase):
    def test_schemas_do_not_register_validators(self):
        result = run_python("""
            import sys
            import newton_usd_schemas
            from pxr import Plug

            assert "newton_usd_schemas.validators" not in sys.modules
            assert not Plug.Registry().GetPluginWithName("newton_usd_schemas.validators")
            """)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipIf(SUPPORTS_PYTHON_VALIDATORS, "Python validators are supported")
    def test_plugin_not_registered_without_python_validators(self):
        self.assertIsNone(Plug.Registry().GetPluginWithName("newton_usd_schemas.validators"))

    @unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
    def test_plugin_registered(self):
        plugin = Plug.Registry().GetPluginWithName("newton_usd_schemas.validators")
        self.assertIsInstance(plugin, Plug.Plugin)
        self.assertTrue(plugin.isPythonModule)
        self.assertEqual(plugin.name, validators.PLUGIN_NAME)
        expected = (pathlib.Path(newton_usd_schemas.__file__).parent / "validators").as_posix()
        self.assertEqual(pathlib.Path(plugin.resourcePath).as_posix(), expected)

    @unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
    def test_register_before_registry_created(self):
        result = run_python("""
            import newton_usd_schemas.validators
            from pxr import UsdValidation

            metadata = UsdValidation.ValidationRegistry().GetValidatorMetadata(newton_usd_schemas.validators.MIMIC_JOINT_VALIDATOR)
            assert metadata.plugin, "expected metadata from plugInfo.json"
            """)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
    def test_register_after_registry_created(self):
        result = run_python("""
            from pxr import UsdValidation

            registry = UsdValidation.ValidationRegistry()
            import newton_usd_schemas.validators

            name = newton_usd_schemas.validators.SDF_MAX_RESOLUTION_VALIDATOR
            metadata = registry.GetOrLoadValidatorByName(name).GetMetadata()
            assert not metadata.plugin, "expected explicitly registered metadata"
            assert sorted(metadata.GetKeywords()) == ["NewtonCollision", "NewtonSDFCollisionAPI", "NewtonValidators"], metadata.GetKeywords()
            assert list(metadata.GetSchemaTypes()) == ["NewtonPhysicsSDFCollisionAPI"], metadata.GetSchemaTypes()
            """)
        self.assertEqual(result.returncode, 0, result.stderr)


class TestValidatorMetadata(ValidatorTestCase):
    def metadata(self, name: str):
        return UsdValidation.ValidationRegistry().GetOrLoadValidatorByName(name).GetMetadata()

    def test_sdf_max_resolution(self):
        metadata = self.metadata(validators.SDF_MAX_RESOLUTION_VALIDATOR)
        self.assertEqual(metadata.name, "newton_usd_schemas.validators:SdfMaxResolutionValidator")
        self.assertTrue(metadata.doc)
        self.assertEqual(sorted(metadata.GetKeywords()), ["NewtonCollision", "NewtonSDFCollisionAPI", "NewtonValidators"])
        self.assertEqual(list(metadata.GetSchemaTypes()), ["NewtonPhysicsSDFCollisionAPI"])
        self.assertFalse(metadata.isTimeDependent)

    def test_mimic_joint(self):
        metadata = self.metadata(validators.MIMIC_JOINT_VALIDATOR)
        self.assertEqual(metadata.name, "newton_usd_schemas.validators:MimicJointValidator")
        self.assertTrue(metadata.doc)
        self.assertEqual(sorted(metadata.GetKeywords()), ["NewtonJoints", "NewtonMimicAPI", "NewtonValidators"])
        self.assertEqual(list(metadata.GetSchemaTypes()), ["NewtonPhysicsMimicAPI"])
        self.assertFalse(metadata.isTimeDependent)

    def test_attribute_hard_limits(self):
        metadata = self.metadata(validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR)
        self.assertEqual(metadata.name, "newton_usd_schemas.validators:AttributeHardLimitsValidator")
        self.assertTrue(metadata.doc)
        self.assertEqual(sorted(metadata.GetKeywords()), ["AttributeLimits", "NewtonValidators"])
        self.assertEqual(list(metadata.GetSchemaTypes()), [])
        self.assertTrue(metadata.isTimeDependent)


class TestValidatorKeywords(ValidatorTestCase):
    def names(self, keyword: str) -> list[str]:
        return sorted(metadata.name for metadata in UsdValidation.ValidationRegistry().GetValidatorMetadataForKeyword(keyword))

    def test_newton_validators(self):
        expected = sorted([validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR, validators.MIMIC_JOINT_VALIDATOR, validators.SDF_MAX_RESOLUTION_VALIDATOR])
        self.assertEqual(self.names("NewtonValidators"), expected)

    def test_newton_collision(self):
        self.assertEqual(self.names("NewtonCollision"), [validators.SDF_MAX_RESOLUTION_VALIDATOR])

    def test_newton_joints(self):
        self.assertEqual(self.names("NewtonJoints"), [validators.MIMIC_JOINT_VALIDATOR])

    def test_attribute_limits(self):
        self.assertEqual(self.names("AttributeLimits"), [validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR])

    def test_newton_sdf_collision_api(self):
        self.assertEqual(self.names("NewtonSDFCollisionAPI"), [validators.SDF_MAX_RESOLUTION_VALIDATOR])

    def test_newton_mimic_api(self):
        self.assertEqual(self.names("NewtonMimicAPI"), [validators.MIMIC_JOINT_VALIDATOR])


if __name__ == "__main__":
    unittest.main()
