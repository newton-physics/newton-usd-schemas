# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
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
        self.assertTrue(self.material.HasAttribute("newton:contactStiffness"))  # from NewtonMaterialAPI
        self.assertTrue(self.material.HasAttribute("newton:contactDamping"))  # from NewtonMaterialAPI
        self.assertTrue(self.material.HasAttribute("newton:contactFrictionStiffness"))  # from NewtonMaterialAPI
        self.assertTrue(self.material.HasAttribute("newton:contactAdhesion"))  # from NewtonMaterialAPI

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotMaterial", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMaterialAPI"))

    def test_torsional_friction(self):
        self.assertFalse(self.material.HasAttribute("newton:torsionalFriction"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:torsionalFriction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.005)

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
        self.assertAlmostEqual(attr.Get(), 0.0001)

        success = attr.Set(0.01)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_contact_stiffness(self):
        self.assertFalse(self.material.HasAttribute("newton:contactStiffness"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:contactStiffness")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(5000.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 5000.0)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_contact_damping(self):
        self.assertFalse(self.material.HasAttribute("newton:contactDamping"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:contactDamping")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(200.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 200.0)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_contact_friction_stiffness(self):
        self.assertFalse(self.material.HasAttribute("newton:contactFrictionStiffness"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:contactFrictionStiffness")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(2000.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2000.0)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_contact_adhesion(self):
        self.assertFalse(self.material.HasAttribute("newton:contactAdhesion"))

        self.material.ApplyAPI("NewtonMaterialAPI")
        attr = self.material.GetAttribute("newton:contactAdhesion")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(0.05)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.05)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())


if __name__ == "__main__":
    unittest.main()
