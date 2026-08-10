# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdShade

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonMPMMaterialAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.material: Usd.Prim = UsdShade.Material.Define(self.stage, "/Material").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMPMMaterialAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMPMMaterialAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMPMMaterialAPI")
        self.assertEqual(schema_type, "NewtonMPMMaterialAPI")

    def test_api_application(self):
        self.assertTrue(self.material.CanApplyAPI("NewtonMPMMaterialAPI"))
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        self.assertTrue(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(self.material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertTrue(self.material.HasAttribute("physics:density"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotMaterial", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMMaterialAPI"))

    def test_does_not_apply_contact_material_api(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        self.assertFalse(self.material.HasAPI("NewtonMaterialAPI"))

    def test_youngs_modulus(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:youngsModulus")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(1.0e6))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0e6)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_poissons_ratio(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:poissonsRatio")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.3)

        self.assertTrue(attr.Set(0.25))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.25)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), -1.0)
            self.assertAlmostEqual(hard.GetMaximum(), 0.5)

    def test_elastic_damping(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:elasticDamping")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(2000.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2000.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_internal_friction(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:internalFriction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5)

        self.assertTrue(attr.Set(0.68))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.68)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_yield_pressure(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:yieldPressure")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(1.0e5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0e5)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_tensile_yield_ratio(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:tensileYieldRatio")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.25))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.25)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_yield_stress(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:yieldStress")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(1000.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1000.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_viscosity(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:viscosity")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.1))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_initial_plastic_volume_strain(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:initialPlasticVolumeStrain")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        self.assertTrue(attr.Set(0.975))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.975)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_hardening(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:hardening")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.1))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_hardening_rate(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:hardeningRate")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        self.assertTrue(attr.Set(2.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_softening_rate(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:softeningRate")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_dilatancy(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute("newton:mpm:dilatancy")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.2))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.2)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)


if __name__ == "__main__":
    unittest.main()
