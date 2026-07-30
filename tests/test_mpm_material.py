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
        self.assertFalse(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertFalse(self.material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertTrue(self.material.CanApplyAPI("NewtonMPMMaterialAPI"))
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        self.assertTrue(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(self.material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertTrue(self.material.HasAttribute("physics:density"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotMaterial", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMMaterialAPI"))

    def _get_attribute(self, name):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        attr = self.material.GetAttribute(name)
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        return attr

    def test_density(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        density = self.material.GetAttribute("physics:density")
        self.assertFalse(density.HasAuthoredValue())
        self.assertEqual(density.Get(), 0.0)
        self.assertTrue(density.Set(1600.0))
        self.assertAlmostEqual(density.Get(), 1600.0)

    def test_elastic_damping_time(self):
        attr = self._get_attribute("newton:mpm:elasticDampingTime")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.02))
        self.assertAlmostEqual(attr.Get(), 0.02)

    def test_internal_friction(self):
        attr = self._get_attribute("newton:mpm:internalFriction")
        self.assertAlmostEqual(attr.Get(), 0.5)
        self.assertTrue(attr.Set(0.68))
        self.assertAlmostEqual(attr.Get(), 0.68)

    def test_yield_pressure(self):
        attr = self._get_attribute("newton:mpm:yieldPressure")
        self.assertEqual(attr.Get(), -math.inf)
        self.assertTrue(attr.Set(1.0e5))
        self.assertAlmostEqual(attr.Get(), 1.0e5)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_tensile_yield_ratio(self):
        attr = self._get_attribute("newton:mpm:tensileYieldRatio")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5)

    def test_yield_stress(self):
        attr = self._get_attribute("newton:mpm:yieldStress")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(1.0e5))
        self.assertAlmostEqual(attr.Get(), 1.0e5)

    def test_viscosity(self):
        attr = self._get_attribute("newton:mpm:viscosity")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.01))
        self.assertAlmostEqual(attr.Get(), 0.01)

    def test_hardening(self):
        attr = self._get_attribute("newton:mpm:hardening")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.1))
        self.assertAlmostEqual(attr.Get(), 0.1)

    def test_hardening_rate(self):
        attr = self._get_attribute("newton:mpm:hardeningRate")
        self.assertAlmostEqual(attr.Get(), 1.0)
        self.assertTrue(attr.Set(2.0))
        self.assertAlmostEqual(attr.Get(), 2.0)

    def test_softening_rate(self):
        attr = self._get_attribute("newton:mpm:softeningRate")
        self.assertAlmostEqual(attr.Get(), 1.0)
        self.assertTrue(attr.Set(2.0))
        self.assertAlmostEqual(attr.Get(), 2.0)

    def test_dilatancy(self):
        attr = self._get_attribute("newton:mpm:dilatancy")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5)


if __name__ == "__main__":
    unittest.main()
