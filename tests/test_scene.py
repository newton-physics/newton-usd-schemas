# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401


class TestNewtonSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.scene = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsSceneAPI")
        self.assertEqual(schema_type, "NewtonSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))

    def test_max_solver_iterations(self):
        self.assertFalse(self.scene.HasAttribute("newton:maxSolverIterations"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:maxSolverIterations")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 100)

        success = attr.Set(10)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 10)

    def test_time_step(self):
        self.assertFalse(self.scene.HasAttribute("newton:timeStep"))

        self.scene.ApplyAPI("NewtonSceneAPI")
        attr = self.scene.GetAttribute("newton:timeStep")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0.005)

        success = attr.Set(0.001)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0.001)


if __name__ == "__main__":
    unittest.main()
