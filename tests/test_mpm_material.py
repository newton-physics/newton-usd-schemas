# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdShade

import newton_usd_schemas  # noqa: F401


class TestNewtonMPMMaterialAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.material: Usd.Prim = UsdShade.Material.Define(self.stage, "/Material").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMPMMaterialAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMPMMaterialAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMPMMaterialAPI")
        self.assertEqual(schema_type, "NewtonMPMMaterialAPI")

    def test_api_application_and_limitations(self):
        self.assertTrue(self.material.CanApplyAPI("NewtonMPMMaterialAPI"))
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        self.assertTrue(self.material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(self.material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertTrue(self.material.HasAttribute("physics:density"))

        prim: Usd.Prim = self.stage.DefinePrim("/NotMaterial", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMMaterialAPI"))

    def test_fallbacks_match_solver_material_attributes(self):
        self.material.ApplyAPI("NewtonMPMMaterialAPI")
        expected = {
            "newton:mpm:youngModulus": 1.0e15,
            "newton:mpm:poissonRatio": 0.3,
            "newton:mpm:damping": 0.0,
            "newton:mpm:friction": 0.5,
            "newton:mpm:yieldPressure": 1.0e15,
            "newton:mpm:tensileYieldRatio": 0.0,
            "newton:mpm:yieldStress": 0.0,
            "newton:mpm:viscosity": 0.0,
            "newton:mpm:hardening": 0.0,
            "newton:mpm:hardeningRate": 1.0,
            "newton:mpm:softeningRate": 1.0,
            "newton:mpm:dilatancy": 0.0,
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                attr = self.material.GetAttribute(name)
                self.assertTrue(attr)
                self.assertFalse(attr.HasAuthoredValue())
                self.assertTrue(math.isclose(attr.Get(), value, rel_tol=1.0e-6, abs_tol=1.0e-8))

        density = self.material.GetAttribute("physics:density")
        self.assertFalse(density.HasAuthoredValue())
        self.assertEqual(density.Get(), 0.0)
        self.assertTrue(density.Set(1600.0))
        self.assertAlmostEqual(density.Get(), 1600.0)


if __name__ == "__main__":
    unittest.main()
