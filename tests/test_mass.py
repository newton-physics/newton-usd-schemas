# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdGeom, Vt

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonMassAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.shape_prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Shape").GetPrim()
        self.body_prim: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/Body").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMassAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMassAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMassAPI")
        self.assertEqual(schema_type, "NewtonMassAPI")

    def test_api_application(self):
        self.assertFalse(self.shape_prim.HasAPI("PhysicsMassAPI"))
        self.assertFalse(self.shape_prim.HasAPI("NewtonMassAPI"))
        self.shape_prim.ApplyAPI("NewtonMassAPI")
        self.assertTrue(self.shape_prim.HasAPI("PhysicsMassAPI"))
        self.assertTrue(self.shape_prim.HasAPI("NewtonMassAPI"))

        self.assertTrue(self.shape_prim.HasAttribute("physics:mass"))  # from PhysicsMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("physics:density"))  # from PhysicsMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("physics:centerOfMass"))  # from PhysicsMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("physics:diagonalInertia"))  # from PhysicsMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("physics:principalAxes"))  # from PhysicsMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("newton:massModel"))  # from NewtonMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("newton:shellThickness"))  # from NewtonMassAPI
        self.assertTrue(self.shape_prim.HasAttribute("newton:inertia"))  # from NewtonMassAPI

        # Also applies to Xform (body prim)
        self.body_prim.ApplyAPI("NewtonMassAPI")
        self.assertTrue(self.body_prim.HasAPI("PhysicsMassAPI"))
        self.assertTrue(self.body_prim.HasAPI("NewtonMassAPI"))

    def test_api_limitations(self):
        scope = self.stage.DefinePrim("/Scope", "Scope")
        self.assertFalse(scope.CanApplyAPI("NewtonMassAPI"))

    def test_mass_model(self):
        self.assertFalse(self.shape_prim.HasAttribute("newton:massModel"))

        self.shape_prim.ApplyAPI("NewtonMassAPI")
        attr = self.shape_prim.GetAttribute("newton:massModel")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "solid")

        allowed = attr.GetMetadata("allowedTokens")
        self.assertIn("solid", allowed)
        self.assertIn("shell", allowed)
        self.assertEqual(len(allowed), 2)

        success = attr.Set("shell")
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "shell")

    def test_shell_thickness(self):
        self.assertFalse(self.shape_prim.HasAttribute("newton:shellThickness"))

        self.shape_prim.ApplyAPI("NewtonMassAPI")
        attr = self.shape_prim.GetAttribute("newton:shellThickness")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(0.002)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.002)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_inertia(self):
        self.assertFalse(self.body_prim.HasAttribute("newton:inertia"))

        self.body_prim.ApplyAPI("NewtonMassAPI")
        attr = self.body_prim.GetAttribute("newton:inertia")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(len(attr.Get()), 0)
        self.assertEqual(attr.GetTypeName(), "double[]")

        if USD_HAS_LIMITS:
            self.assertEqual(attr.GetArraySizeConstraint(), 6)

        tensor = Vt.DoubleArray([1.0, 2.0, 3.0, 0.1, 0.2, 0.3])
        success = attr.Set(tensor)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        value = attr.Get()
        self.assertEqual(len(value), 6)
        self.assertAlmostEqual(value[0], 1.0)
        self.assertAlmostEqual(value[3], 0.1)


if __name__ == "__main__":
    unittest.main()
