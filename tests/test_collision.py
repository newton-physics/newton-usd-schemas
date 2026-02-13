# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdGeom

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonCollisionAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsCollisionAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsCollisionAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsCollisionAPI")
        self.assertEqual(schema_type, "NewtonCollisionAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonCollisionAPI"))
        self.prim.ApplyAPI("NewtonCollisionAPI")
        self.assertTrue(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonCollisionAPI"))

        self.assertTrue(self.prim.HasAttribute("physics:collisionEnabled"))  # from PhysicsCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:contactMargin"))  # from NewtonCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:contactGap"))  # from NewtonCollisionAPI

    def test_api_limitations(self):
        xform: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/InvalidType").GetPrim()
        self.assertFalse(xform.CanApplyAPI("NewtonCollisionAPI"))

    def test_contact_margin(self):
        self.assertFalse(self.prim.HasAttribute("newton:contactMargin"))

        self.prim.ApplyAPI("NewtonCollisionAPI")
        attr = self.prim.GetAttribute("newton:contactMargin")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        success = attr.Set(0.2)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.2)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_contact_gap(self):
        self.assertFalse(self.prim.HasAttribute("newton:contactGap"))

        self.prim.ApplyAPI("NewtonCollisionAPI")
        attr = self.prim.GetAttribute("newton:contactGap")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(0.1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)


class TestNewtonMeshCollisionAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Mesh.Define(self.stage, "/Collider").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMeshCollisionAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMeshCollisionAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMeshCollisionAPI")
        self.assertEqual(schema_type, "NewtonMeshCollisionAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("PhysicsMeshCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonMeshCollisionAPI"))
        self.prim.ApplyAPI("NewtonMeshCollisionAPI")
        self.assertTrue(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("PhysicsMeshCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonMeshCollisionAPI"))

        self.assertTrue(self.prim.HasAttribute("physics:collisionEnabled"))  # from PhysicsCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:contactMargin"))  # from NewtonCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:contactGap"))  # from NewtonCollisionAPI
        self.assertTrue(self.prim.HasAttribute("physics:approximation"))  # from PhysicsMeshCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:maxHullVertices"))  # from NewtonMeshCollisionAPI

    def test_api_limitations(self):
        sphere: Usd.Prim = UsdGeom.Sphere.Define(self.stage, "/Sphere").GetPrim()
        self.assertFalse(sphere.CanApplyAPI("NewtonMeshCollisionAPI"))

    def test_max_hull_vertices(self):
        self.assertFalse(self.prim.HasAttribute("newton:maxHullVertices"))
        self.prim.ApplyAPI("NewtonMeshCollisionAPI")
        attr = self.prim.GetAttribute("newton:maxHullVertices")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        success = attr.Set(100)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 100)

        # Test rounding down to the nearest integer
        success = attr.Set(0.9)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        # Test setting to -1
        success = attr.Set(-1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())


if __name__ == "__main__":
    unittest.main()
