# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonKaminoSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsKaminoSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsKaminoSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsKaminoSceneAPI")
        self.assertEqual(schema_type, "NewtonKaminoSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonKaminoSceneAPI"))

    def test_padmm_primal_tolerance(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:primalTolerance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

    def test_padmm_dual_tolerance(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:dualTolerance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

    def test_padmm_complementarity_tolerance(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:complementarityTolerance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

    def test_padmm_warmstart(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:warmstart")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), "containers")

        success = attr.Set("none")
        self.assertTrue(success)
        self.assertEqual(attr.Get(), "none")

    def test_padmm_acceleration(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:acceleration")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), False)

    def test_constraints_alpha(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:alpha")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

    def test_constraints_beta(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:beta")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

    def test_constraints_gamma(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:gamma")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

    def test_constraints_delta(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:delta")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

    def test_constraints_precond(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:precond")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), False)

    def test_joint_correction(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:jointCorrection")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), "twopi")

        success = attr.Set("none")
        self.assertTrue(success)
        self.assertEqual(attr.Get(), "none")


if __name__ == "__main__":
    unittest.main()
