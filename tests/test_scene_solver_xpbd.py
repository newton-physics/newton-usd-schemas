# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401


class TestNewtonXpbdSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsXpbdSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsXpbdSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsXpbdSceneAPI")
        self.assertEqual(schema_type, "NewtonXpbdSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonXpbdSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonXpbdSceneAPI"))

    def test_soft_body_relaxation(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:softBodyRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

        success = attr.Set(0.8)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.8, places=5)

    def test_soft_contact_relaxation(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:softContactRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

        success = attr.Set(0.75)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.75, places=5)

    def test_joint_linear_relaxation(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:jointLinearRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.7, places=5)

        success = attr.Set(0.5)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.5, places=5)

    def test_joint_angular_relaxation(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:jointAngularRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.4, places=5)

        success = attr.Set(0.3)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.3, places=5)

    def test_joint_linear_compliance(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:jointLinearCompliance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.001)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.001, places=5)

    def test_joint_angular_compliance(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:jointAngularCompliance")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.002)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.002, places=5)

    def test_rigid_contact_relaxation(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:rigidContactRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.8, places=5)

        success = attr.Set(0.9)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.9, places=5)

    def test_rigid_contact_con_weighting(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:rigidContactConWeighting")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), False)

    def test_angular_damping(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:angularDamping")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=5)

        success = attr.Set(0.1)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.1, places=5)

    def test_restitution_enabled(self):
        self.scene.ApplyAPI("NewtonXpbdSceneAPI")
        attr = self.scene.GetAttribute("newton:xpbd:restitutionEnabled")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), False)

        success = attr.Set(True)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), True)


if __name__ == "__main__":
    unittest.main()
