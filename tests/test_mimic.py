# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401


class TestNewtonMimicAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.joint: Usd.Prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Joint").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMimicAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMimicAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMimicAPI")
        self.assertEqual(schema_type, "NewtonMimicAPI")

    def test_api_application(self):
        self.assertFalse(self.joint.HasAPI("NewtonMimicAPI"))
        self.joint.ApplyAPI("NewtonMimicAPI")
        self.assertTrue(self.joint.HasAPI("NewtonMimicAPI"))

        self.assertTrue(self.joint.HasAttribute("newton:mimicEnabled"))
        self.assertTrue(self.joint.HasRelationship("newton:mimicJoint"))
        self.assertTrue(self.joint.HasAttribute("newton:mimicCoef0"))
        self.assertTrue(self.joint.HasAttribute("newton:mimicCoef1"))

    def test_api_application_prismatic(self):
        prismatic = UsdPhysics.PrismaticJoint.Define(self.stage, "/Prismatic").GetPrim()
        self.assertTrue(prismatic.CanApplyAPI("NewtonMimicAPI"))
        prismatic.ApplyAPI("NewtonMimicAPI")
        self.assertTrue(prismatic.HasAPI("NewtonMimicAPI"))

    def test_api_application_spherical(self):
        spherical = UsdPhysics.SphericalJoint.Define(self.stage, "/Spherical").GetPrim()
        self.assertTrue(spherical.CanApplyAPI("NewtonMimicAPI"))
        spherical.ApplyAPI("NewtonMimicAPI")
        self.assertTrue(spherical.HasAPI("NewtonMimicAPI"))

    def test_api_application_d6(self):
        d6 = UsdPhysics.Joint.Define(self.stage, "/D6").GetPrim()
        self.assertTrue(d6.CanApplyAPI("NewtonMimicAPI"))
        d6.ApplyAPI("NewtonMimicAPI")
        self.assertTrue(d6.HasAPI("NewtonMimicAPI"))

    def test_api_limitations(self):
        xform: Usd.Prim = self.stage.DefinePrim("/NotJoint", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonMimicAPI"))

    def test_enabled(self):
        self.assertFalse(self.joint.HasAttribute("newton:mimicEnabled"))

        self.joint.ApplyAPI("NewtonMimicAPI")
        attr = self.joint.GetAttribute("newton:mimicEnabled")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_coef0(self):
        self.assertFalse(self.joint.HasAttribute("newton:mimicCoef0"))

        self.joint.ApplyAPI("NewtonMimicAPI")
        attr = self.joint.GetAttribute("newton:mimicCoef0")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        success = attr.Set(1.5)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.5)

        # Negative offsets are valid
        success = attr.Set(-0.5)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), -0.5)

    def test_coef1(self):
        self.assertFalse(self.joint.HasAttribute("newton:mimicCoef1"))

        self.joint.ApplyAPI("NewtonMimicAPI")
        attr = self.joint.GetAttribute("newton:mimicCoef1")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        success = attr.Set(2.0)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2.0)

        # Negative scale factors are valid (reverse direction)
        success = attr.Set(-1.0)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), -1.0)

        # Zero is valid (constant position/angle)
        success = attr.Set(0.0)
        self.assertTrue(success)
        self.assertAlmostEqual(attr.Get(), 0.0)


if __name__ == "__main__":
    unittest.main()
