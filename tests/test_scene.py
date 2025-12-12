# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401


class TestNewtonSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: UsdPhysics.Scene = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsSceneAPI")
        self.assertEqual(schema_type, "NewtonSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonSceneAPI"))

    def test_max_solver_iterations(self):
        self.assertFalse(self.scene.HasAttribute("newton:maxSolverIterations"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:maxSolverIterations")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        success = attr.Set(10)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 10)

    def test_time_steps_per_second(self):
        self.assertFalse(self.scene.HasAttribute("newton:timeStepsPerSecond"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:timeStepsPerSecond")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1000)

        success = attr.Set(10000)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 10000)

        # Test rounding down to the nearest integer
        success = attr.Set(0.9)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

    def test_enable_gravity(self):
        self.assertFalse(self.scene.HasAttribute("newton:gravityEnabled"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:gravityEnabled")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)


class TestNewtonXpbdSceneAPI(unittest.TestCase):
    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonXpbdPhysicsSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonXpbdPhysicsSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonXpbdPhysicsSceneAPI")
        self.assertEqual(schema_type, "NewtonXpbdSceneAPI")

    def test_api_application(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()
        prim.ApplyAPI("NewtonXpbdSceneAPI")
        self.assertTrue(prim.HasAPI("NewtonXpbdSceneAPI"))

    def test_iterations(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        self.assertFalse(prim.HasAttribute("newton:xpbd:iterations"))

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:iterations")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2)

        success = attr.Set(10)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 10)

    def test_soft_body_relaxation(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:softBodyRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

        success = attr.Set(0.8)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.8, places=5)

    def test_soft_contact_relaxation(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:softContactRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

        success = attr.Set(0.75)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.75, places=5)

    def test_joint_linear_relaxation(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:jointLinearRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.7, places=5)

        success = attr.Set(0.5)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.5, places=5)

    def test_joint_angular_relaxation(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:jointAngularRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.4, places=5)

        success = attr.Set(0.3)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.3, places=5)

    def test_joint_linear_compliance(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:jointLinearCompliance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.001)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.001, places=5)

    def test_joint_angular_compliance(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:jointAngularCompliance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.002)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.002, places=5)

    def test_rigid_contact_relaxation(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:rigidContactRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.8, places=5)

        success = attr.Set(0.9)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

    def test_rigid_contact_con_weighting(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:rigidContactConWeighting")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), False)

    def test_angular_damping(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:angularDamping")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.1)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.1, places=5)

    def test_enable_restitution(self):
        stage = Usd.Stage.CreateInMemory()
        scene = UsdPhysics.Scene.Define(stage, "/PhysicsScene")
        prim = scene.GetPrim()

        prim.ApplyAPI("NewtonXpbdSceneAPI")
        attr = prim.GetAttribute("newton:xpbd:enableRestitution")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), False)

        success = attr.Set(True)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), True)


if __name__ == "__main__":
    unittest.main()
