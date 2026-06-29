# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
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

    # -- common -------------------------------------------------------------

    def test_friction_epsilon(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:frictionEpsilon")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.01, places=7)

        self.assertTrue(attr.Set(0.05))
        self.assertAlmostEqual(attr.Get(), 0.05, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    # -- particle -----------------------------------------------------------

    def test_particle_self_contact_enabled(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:selfContactEnabled")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertEqual(attr.Get(), True)

    def test_particle_self_contact_radius(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:selfContactRadius")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.2, places=7)

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_particle_self_contact_margin(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:selfContactMargin")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.2, places=7)

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_particle_conservative_bound_relaxation(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:conservativeBoundRelaxation")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.85, places=7)

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_particle_collision_detection_interval(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:collisionDetectionInterval")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), 0)

        self.assertTrue(attr.Set(5))
        self.assertEqual(attr.Get(), 5)

    def test_particle_edge_parallel_epsilon(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:edgeParallelEpsilon")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-5, places=7)

        self.assertTrue(attr.Set(1e-4))
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_particle_topological_contact_filter_threshold(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:topologicalContactFilterThreshold")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), 2)

        self.assertTrue(attr.Set(3))
        self.assertEqual(attr.Get(), 3)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    def test_particle_rest_shape_contact_exclusion_radius(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:restShapeContactExclusionRadius")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(0.1))
        self.assertAlmostEqual(attr.Get(), 0.1, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    # -- rigid / AVBD -------------------------------------------------------

    def test_rigid_avbd_alpha(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdAlpha")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.95, places=7)

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_rigid_avbd_joint_alpha(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdJointAlpha")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), float("-inf"))

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertAlmostEqual(soft.GetMaximum(), 1.0)

    def test_rigid_avbd_contact_alpha(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdContactAlpha")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), float("-inf"))

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertAlmostEqual(soft.GetMaximum(), 1.0)

    def test_rigid_avbd_beta(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdBeta")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(1e5))
        self.assertAlmostEqual(attr.Get(), 1e5, places=3)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_avbd_linear_beta(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdLinearBeta")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), float("-inf"))

        self.assertTrue(attr.Set(1e5))
        self.assertAlmostEqual(attr.Get(), 1e5, places=3)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_rigid_avbd_angular_beta(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdAngularBeta")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), float("-inf"))

        self.assertTrue(attr.Set(1e5))
        self.assertAlmostEqual(attr.Get(), 1e5, places=3)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_rigid_avbd_gamma(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:avbdGamma")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.999, places=7)

        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_rigid_contact_history(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactHistory")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertEqual(attr.Get(), True)

    def test_rigid_contact_stick_motion_eps(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactStickMotionEps")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        self.assertTrue(attr.Set(1e-3))
        self.assertAlmostEqual(attr.Get(), 1e-3, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_contact_stick_freeze_translation_eps(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactStickFreezeTranslationEps")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        self.assertTrue(attr.Set(1e-3))
        self.assertAlmostEqual(attr.Get(), 1e-3, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_contact_stick_freeze_angular_eps(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactStickFreezeAngularEps")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        self.assertTrue(attr.Set(1e-3))
        self.assertAlmostEqual(attr.Get(), 1e-3, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_contact_k_start(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:contactKStart")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100.0, places=4)

        self.assertTrue(attr.Set(200.0))
        self.assertAlmostEqual(attr.Get(), 200.0, places=4)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_linear_ke(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointLinearKe")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100000.0, places=1)

        self.assertTrue(attr.Set(50000.0))
        self.assertAlmostEqual(attr.Get(), 50000.0, places=1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_angular_ke(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointAngularKe")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100000.0, places=1)

        self.assertTrue(attr.Set(50000.0))
        self.assertAlmostEqual(attr.Get(), 50000.0, places=1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_linear_k_start(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointLinearKStart")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 100.0, places=4)

        self.assertTrue(attr.Set(200.0))
        self.assertAlmostEqual(attr.Get(), 200.0, places=4)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_angular_k_start(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointAngularKStart")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 10.0, places=5)

        self.assertTrue(attr.Set(20.0))
        self.assertAlmostEqual(attr.Get(), 20.0, places=5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_linear_kd(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointLinearKd")
        self.assertIsNotNone(attr)
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(1.0))
        self.assertAlmostEqual(attr.Get(), 1.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rigid_joint_angular_kd(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:rigid:jointAngularKd")
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
