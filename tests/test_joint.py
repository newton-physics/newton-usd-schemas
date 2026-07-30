# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonJointAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.revolute: Usd.Prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Revolute").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsJointAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsJointAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsJointAPI")
        self.assertEqual(schema_type, "NewtonJointAPI")

    def test_api_application(self):
        self.assertFalse(self.revolute.HasAPI("NewtonJointAPI"))
        self.revolute.ApplyAPI("NewtonJointAPI")
        self.assertTrue(self.revolute.HasAPI("NewtonJointAPI"))

        self.assertTrue(self.revolute.HasAttribute("newton:armature"))
        self.assertTrue(self.revolute.HasAttribute("newton:damping"))
        self.assertTrue(self.revolute.HasAttribute("newton:friction"))
        self.assertTrue(self.revolute.HasAttribute("newton:velocityLimit"))
        self.assertTrue(self.revolute.HasAttribute("newton:limitStiffness"))
        self.assertTrue(self.revolute.HasAttribute("newton:limitDamping"))

    def test_api_application_prismatic(self):
        prismatic = UsdPhysics.PrismaticJoint.Define(self.stage, "/Prismatic").GetPrim()
        self.assertTrue(prismatic.CanApplyAPI("NewtonJointAPI"))
        prismatic.ApplyAPI("NewtonJointAPI")
        self.assertTrue(prismatic.HasAPI("NewtonJointAPI"))

    def test_api_application_spherical(self):
        spherical = UsdPhysics.SphericalJoint.Define(self.stage, "/Spherical").GetPrim()
        self.assertTrue(spherical.CanApplyAPI("NewtonJointAPI"))
        spherical.ApplyAPI("NewtonJointAPI")
        self.assertTrue(spherical.HasAPI("NewtonJointAPI"))

    def test_api_application_d6(self):
        d6 = UsdPhysics.Joint.Define(self.stage, "/D6").GetPrim()
        self.assertTrue(d6.CanApplyAPI("NewtonJointAPI"))
        d6.ApplyAPI("NewtonJointAPI")
        self.assertTrue(d6.HasAPI("NewtonJointAPI"))

    def test_api_limitations(self):
        xform: Usd.Prim = self.stage.DefinePrim("/NotJoint", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonJointAPI"))

    def test_armature(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:armature")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        success = attr.Set(0.01)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_damping(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:damping")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        success = attr.Set(5.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 5.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_friction(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:friction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        success = attr.Set(0.5)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_velocity_limit(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:velocityLimit")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        success = attr.Set(360.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 360.0)

        # Block resets to None
        attr.Block()
        self.assertIsNone(attr.Get())

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_limit_stiffness(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:limitStiffness")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), None)

        success = attr.Set(174.5)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 174.5)

        attr.Block()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), None)

    def test_limit_damping(self):
        self.revolute.ApplyAPI("NewtonJointAPI")
        attr = self.revolute.GetAttribute("newton:limitDamping")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), None)

        success = attr.Set(0.1745)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1745)

        attr.Block()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), None)


if __name__ == "__main__":
    unittest.main()
