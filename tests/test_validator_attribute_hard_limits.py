# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from validator_test_case import ValidatorTestCase, run_python

from newton_usd_schemas import validators

ERROR = "AttributeOutsideHardLimits"


class TestAttributeHardLimitsValidator(ValidatorTestCase):
    validator_name = validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        self.prim.ApplyAPI("NewtonCollisionAPI")
        self.gap: Usd.Attribute = self.prim.GetAttribute("newton:contactGap")

    def test_unauthored_value(self):
        self.assertFalse(self.gap.HasAuthoredValue())
        self.assertEqual(self.validate(self.prim), [])

    def test_sentinel_fallback(self):
        self.assertEqual(self.gap.GetHardLimits().GetMinimum(), 0.0)
        self.gap.Set(-math.inf)
        self.assertEqual(self.validate(self.prim), [])

    def test_at_minimum(self):
        self.gap.Set(0.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_above_minimum(self):
        self.gap.Set(0.01)
        self.assertEqual(self.validate(self.prim), [])

    def test_infinity_without_maximum(self):
        self.gap.Set(math.inf)
        self.assertEqual(self.validate(self.prim), [])

    def test_below_minimum(self):
        self.gap.Set(-0.01)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.gap.GetPath())])

    def test_nan(self):
        self.gap.Set(math.nan)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.gap.GetPath())])

    def test_at_maximum(self):
        scene = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()
        scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = scene.GetAttribute("newton:xpbd:softBodyRelaxation")
        self.assertEqual(attr.GetHardLimits().GetMaximum(), 1.0)
        attr.Set(1.0)
        self.assertEqual(self.validate(scene), [])

    def test_above_maximum(self):
        scene = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()
        scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = scene.GetAttribute("newton:xpbd:softBodyRelaxation")
        attr.Set(1.5)
        self.assertEqual(self.validate(scene), [(ERROR, attr.GetPath())])

    def test_integer_within_limits(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        self.prim.GetAttribute("newton:sdfMaxResolution").Set(8)
        self.assertEqual(self.validate(self.prim), [])

    def test_integer_outside_limits(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfMaxResolution")
        attr.Set(0)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_soft_limits_are_not_validated(self):
        margin = self.prim.GetAttribute("newton:contactMargin")
        self.assertEqual(margin.GetSoftLimits().GetMinimum(), 0.0)
        margin.Set(-0.01)
        self.assertEqual(self.validate(self.prim), [])

    def test_inherited_by_mesh_collision_api(self):
        prim = UsdGeom.Mesh.Define(self.stage, "/Mesh").GetPrim()
        prim.ApplyAPI("NewtonMeshCollisionAPI")
        gap = prim.GetAttribute("newton:contactGap")
        gap.Set(-1.0)
        self.assertEqual(self.validate(prim), [(ERROR, gap.GetPath())])

    def test_inherited_by_sdf_collision_api(self):
        prim = UsdGeom.Mesh.Define(self.stage, "/Mesh").GetPrim()
        prim.ApplyAPI("NewtonSDFCollisionAPI")
        gap = prim.GetAttribute("newton:contactGap")
        gap.Set(-1.0)
        self.assertEqual(self.validate(prim), [(ERROR, gap.GetPath())])

    def test_time_samples(self):
        self.gap.Set(0.0, 0.0)
        self.gap.Set(-1.0, 1.0)
        self.gap.Set(-2.0, 2.0)
        errors = self.validator.Validate(self.prim)
        self.assertEqual(len(errors), 1)
        self.assertIn("at time 1.0", errors[0].GetMessage())

    def test_custom_attribute_within_limits(self):
        attr = self.prim.CreateAttribute("custom:value", Sdf.ValueTypeNames.Float)
        attr.GetHardLimits().SetMinimum(0.0)
        attr.GetHardLimits().SetMaximum(1.0)
        attr.Set(0.5)
        self.assertEqual(self.validate(self.prim), [])

    def test_custom_attribute_outside_limits(self):
        attr = self.prim.CreateAttribute("custom:value", Sdf.ValueTypeNames.Float)
        attr.GetHardLimits().SetMinimum(0.0)
        attr.GetHardLimits().SetMaximum(1.0)
        attr.Set(-math.inf)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_multiple_attributes(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        self.gap.Set(-1.0)
        resolution = self.prim.GetAttribute("newton:sdfMaxResolution")
        resolution.Set(0)
        self.assertEqual(sorted(self.validate(self.prim)), sorted([(ERROR, self.gap.GetPath()), (ERROR, resolution.GetPath())]))

    def test_selected_by_keyword(self):
        self.gap.Set(-1.0)
        self.assertEqual(self.validate_with_keywords("AttributeLimits"), [ERROR])

    def test_defers_to_openusd_validator(self):
        result = run_python("""
            from pxr import Sdf, Usd, UsdGeom, UsdValidation

            def openusd_task(prim, time_range):
                site = UsdValidation.ValidationErrorSite(prim.GetStage(), prim.GetPath())
                return [UsdValidation.ValidationError("FromOpenUSD", UsdValidation.ValidationErrorType.Error, [site], "")]

            registry = UsdValidation.ValidationRegistry()
            registry.RegisterPrimValidator(UsdValidation.ValidatorMetadata(name="usdValidation:AttributeHardLimits"), openusd_task)

            import newton_usd_schemas.validators

            stage = Usd.Stage.CreateInMemory()
            prim = UsdGeom.Cube.Define(stage, "/Cube").GetPrim()
            validator = registry.GetOrLoadValidatorByName(newton_usd_schemas.validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR)
            names = [error.GetName() for error in validator.Validate(prim)]
            assert names == ["FromOpenUSD"], names
            """)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
