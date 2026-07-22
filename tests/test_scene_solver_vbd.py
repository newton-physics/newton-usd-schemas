# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonVbdSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsVbdSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsVbdSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsVbdSceneAPI")
        self.assertEqual(schema_type, "NewtonVbdSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonVbdSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonVbdSceneAPI"))

    # -- rigid / AVBD -------------------------------------------------------

    def test_rigid_contact_history(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactHistory")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertEqual(attr.Get(), True)

    def test_rigid_joint_linear_stiffness(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointLinearStiffness")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100000.0, places=1)

        self.assertTrue(attr.Set(50000.0))
        self.assertAlmostEqual(attr.Get(), 50000.0, places=1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_angular_stiffness(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointAngularStiffness")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100000.0, places=1)

        self.assertTrue(attr.Set(50000.0))
        self.assertAlmostEqual(attr.Get(), 50000.0, places=1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_linear_damping(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointLinearDamping")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(1.0))
        self.assertAlmostEqual(attr.Get(), 1.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_angular_damping(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointAngularDamping")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(1.0))
        self.assertAlmostEqual(attr.Get(), 1.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


if __name__ == "__main__":
    unittest.main()
