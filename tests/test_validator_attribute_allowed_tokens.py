# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdGeom, UsdPhysics, Vt
from validator_test_case import ValidatorTestCase, run_python

from newton_usd_schemas import validators

ERROR = "AttributeTokenNotAllowed"


class TestAttributeAllowedTokensValidator(ValidatorTestCase):
    validator_name = validators.ATTRIBUTE_ALLOWED_TOKENS_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        self.prim.ApplyAPI("NewtonMassAPI")
        self.model: Usd.Attribute = self.prim.GetAttribute("newton:massModel")
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        self.solvers: Usd.Attribute = self.scene.GetAttribute("newton:mpm:rheologySolvers")

    def custom_attribute(self, type_name: Sdf.ValueTypeName, allowed_tokens: list[str]) -> Usd.Attribute:
        attr = self.prim.CreateAttribute("custom:value", type_name)
        attr.SetMetadata("allowedTokens", Vt.TokenArray(allowed_tokens))
        return attr

    def test_unauthored_value(self):
        self.assertFalse(self.model.HasAuthoredValue())
        self.assertEqual(self.validate(self.prim), [])

    def test_blocked_value(self):
        self.model.Block()
        self.assertEqual(self.validate(self.prim), [])

    def test_allowed_token(self):
        self.model.Set("shell")
        self.assertEqual(self.validate(self.prim), [])

    def test_disallowed_token(self):
        self.model.Set("hollow")
        self.assertEqual(self.validate(self.prim), [(ERROR, self.model.GetPath())])
        message = self.validator.Validate(self.prim)[0].GetMessage()
        self.assertIn("'hollow'", message)
        self.assertIn("['solid', 'shell']", message)

    def test_sentinel_fallback(self):
        """Accept a value equal to the schema fallback, even when it is not one of the allowed tokens."""
        attr = self.custom_attribute(Sdf.ValueTypeNames.Token, ["a", "b"])
        attr.Set("none")
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])
        fallback = Usd.PrimDefinition.GetAttributeFallbackValue
        with mock.patch.object(
            Usd.PrimDefinition, "GetAttributeFallbackValue", lambda definition, name: "none" if name == "custom:value" else fallback(definition, name)
        ):
            self.assertEqual(self.validate(self.prim), [])

    def test_time_samples(self):
        """Report a disallowed time sample once, naming its time."""
        self.model.Set("solid", 0.0)
        self.model.Set("hollow", 1.0)
        self.model.Set("empty", 2.0)
        errors = self.validator.Validate(self.prim)
        self.assertEqual(len(errors), 1)
        self.assertIn("'hollow' at time 1.0", errors[0].GetMessage())

    def test_token_array(self):
        self.solvers.Set(Vt.TokenArray(["jacobi", "conjugate-gradient"]))
        self.assertEqual(self.validate(self.scene), [])

    def test_token_array_with_disallowed_element(self):
        self.solvers.Set(Vt.TokenArray(["jacobi", "multigrid"]))
        self.assertEqual(self.validate(self.scene), [(ERROR, self.solvers.GetPath())])
        self.assertIn("contains 'multigrid'", self.validator.Validate(self.scene)[0].GetMessage())

    def test_token_array_fallback(self):
        self.solvers.Set(Vt.TokenArray(["auto"]))
        self.assertEqual(self.validate(self.scene), [])

    def test_empty_token_array(self):
        self.solvers.Set(Vt.TokenArray())
        self.assertEqual(self.validate(self.scene), [])

    def test_string(self):
        attr = self.custom_attribute(Sdf.ValueTypeNames.String, ["a", "b"])
        attr.Set("b")
        self.assertEqual(self.validate(self.prim), [])
        attr.Set("c")
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_string_array(self):
        attr = self.custom_attribute(Sdf.ValueTypeNames.StringArray, ["a", "b"])
        attr.Set(Vt.StringArray(["a", "b"]))
        self.assertEqual(self.validate(self.prim), [])
        attr.Set(Vt.StringArray(["a", "c"]))
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_without_allowed_tokens(self):
        attr = self.prim.CreateAttribute("custom:value", Sdf.ValueTypeNames.Token)
        attr.Set("anything")
        self.assertEqual(self.validate(self.prim), [])

    def test_empty_allowed_tokens(self):
        attr = self.custom_attribute(Sdf.ValueTypeNames.Token, [])
        attr.Set("anything")
        self.assertEqual(self.validate(self.prim), [])

    def test_other_value_types(self):
        """Ignore allowedTokens on attributes that do not hold tokens or strings."""
        attr = self.custom_attribute(Sdf.ValueTypeNames.Int, ["1"])
        attr.Set(2)
        self.assertEqual(self.validate(self.prim), [])

    def test_multiple_attributes(self):
        self.model.Set("hollow")
        attr = self.custom_attribute(Sdf.ValueTypeNames.Token, ["a"])
        attr.Set("b")
        self.assertEqual(sorted(self.validate(self.prim)), sorted([(ERROR, self.model.GetPath()), (ERROR, attr.GetPath())]))

    def test_selected_by_keyword(self):
        self.model.Set("hollow")
        self.assertEqual(self.validate_with_keywords("AttributeAllowedTokens"), [ERROR])

    def test_defers_to_openusd_validator(self):
        result = run_python("""
            from pxr import Sdf, Usd, UsdGeom, UsdValidation

            def openusd_task(prim, time_range):
                site = UsdValidation.ValidationErrorSite(prim.GetStage(), prim.GetPath())
                return [UsdValidation.ValidationError("FromOpenUSD", UsdValidation.ValidationErrorType.Error, [site], "")]

            registry = UsdValidation.ValidationRegistry()
            registry.RegisterPrimValidator(UsdValidation.ValidatorMetadata(name="usdValidation:AttributeAllowedTokens"), openusd_task)

            import newton_usd_schemas.validators

            stage = Usd.Stage.CreateInMemory()
            prim = UsdGeom.Cube.Define(stage, "/Cube").GetPrim()
            validator = registry.GetOrLoadValidatorByName(newton_usd_schemas.validators.ATTRIBUTE_ALLOWED_TOKENS_VALIDATOR)
            names = [error.GetName() for error in validator.Validate(prim)]
            assert names == ["FromOpenUSD"], names
            """)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
