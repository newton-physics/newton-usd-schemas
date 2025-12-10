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
        self.assertFalse(self.scene.HasAttribute("newton:enableGravity"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:enableGravity")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)


if __name__ == "__main__":
    unittest.main()
