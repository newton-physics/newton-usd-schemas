# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonCollisionPipelineAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsCollisionPipelineAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsCollisionPipelineAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsCollisionPipelineAPI")
        self.assertEqual(schema_type, "NewtonCollisionPipelineAPI")

    def test_api_application(self):
        self.assertTrue(self.scene.CanApplyAPI("NewtonCollisionPipelineAPI"))
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonCollisionPipelineAPI"))
        self.assertTrue(self.scene.HasAttribute("newton:maxSolverIterations"))
        self.assertTrue(self.scene.HasAttribute("newton:collisionPipeline:broadPhase"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonCollisionPipelineAPI"))

    def test_broad_phase(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:broadPhase")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "explicit")

        self.assertTrue(attr.Set("sap"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "sap")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"nxn", "sap", "explicit"})

    def test_max_triangle_pairs(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:maxTrianglePairs")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(500000))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 500000)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

    def test_max_rigid_contacts(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:maxRigidContacts")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(2048))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2048)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

    def test_reduce_contacts(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:reduceContacts")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        self.assertTrue(attr.Set(False))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_max_soft_contacts(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:maxSoftContacts")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(4096))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 4096)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

    def test_soft_contact_gap(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:softContactGap")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.02))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.02)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_enable_rigid_soft_full_surface_contact(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:enableRigidSoftFullSurfaceContact")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_requires_grad(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:requiresGrad")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "inherit")

        self.assertTrue(attr.Set("true"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "true")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"inherit", "true", "false"})

    def test_deterministic(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:deterministic")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_include_static_kinematic_pairs(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:includeStaticKinematicPairs")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        self.assertTrue(attr.Set(False))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_max_shape_pairs(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:maxShapePairs")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(4096))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 4096)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

    def test_contact_matching(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:contactMatching")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "disabled")

        self.assertTrue(attr.Set("sticky"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "sticky")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"disabled", "latest", "sticky"})

    def test_contact_matching_pos_threshold(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:contactMatchingPosThreshold")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0005)

        self.assertTrue(attr.Set(0.01))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_contact_matching_normal_dot_threshold(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:contactMatchingNormalDotThreshold")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.995)

        self.assertTrue(attr.Set(0.9))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.9)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), -1.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_contact_report(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:contactReport")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_verify_buffers(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:verifyBuffers")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        self.assertTrue(attr.Set(False))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_contact_reduction_hashtable_size_factor(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:contactReductionHashtableSizeFactor")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.25)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_speculative_max_contact_gap(self):
        self.scene.ApplyAPI("NewtonCollisionPipelineAPI")
        attr = self.scene.GetAttribute("newton:collisionPipeline:maxSpeculativeContactGap")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.1))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())


if __name__ == "__main__":
    unittest.main()
