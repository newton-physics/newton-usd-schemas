# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics, UsdShade

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonMaterialAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.material: UsdPhysics.Material = UsdShade.Material.Define(self.stage, "/Material").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMaterialAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMaterialAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMaterialAPI")
        self.assertEqual(schema_type, "NewtonMaterialAPI")

    def test_api_application(self):
        self.assertFalse(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertFalse(self.material.HasAPI("NewtonMaterialAPI"))
        self.material.ApplyAPI("NewtonMaterialAPI")
        self.assertTrue(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(self.material.HasAPI("NewtonMaterialAPI"))

        self.assertTrue(self.material.HasAttribute("physics:dynamicFriction"))  # from PhysicsMaterialAPI
        self.assertTrue(self.material.HasAttribute("newton:torsionalFriction"))  # from NewtonMaterialAPI

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotMaterial", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMaterialAPI"))

    def test_torsional_friction(self):
        self.assertFalse(self.material.HasAttribute("newton:torsionalFriction"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:torsionalFriction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        success = attr.Set(0.1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rolling_friction(self):
        self.assertFalse(self.material.HasAttribute("newton:rollingFriction"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:rollingFriction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        success = attr.Set(0.01)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


if __name__ == "__main__":
    unittest.main()
