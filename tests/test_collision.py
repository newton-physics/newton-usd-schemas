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
        # SDF/hydro attrs should NOT be present on bare NewtonCollisionAPI
        self.assertFalse(self.prim.HasAttribute("newton:sdfMaxResolution"))
        self.assertFalse(self.prim.HasAttribute("newton:hydroelasticStiffness"))

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
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

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

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


class TestNewtonSDFCollisionAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsSDFCollisionAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsSDFCollisionAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsSDFCollisionAPI")
        self.assertEqual(schema_type, "NewtonSDFCollisionAPI")

    def test_api_application(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        # Should inherit NewtonCollisionAPI and PhysicsCollisionAPI
        self.assertTrue(self.prim.HasAPI("NewtonSDFCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonCollisionAPI"))
        self.assertTrue(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonMeshCollisionAPI"))

        # SDF attrs
        self.assertTrue(self.prim.HasAttribute("newton:sdfMaxResolution"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfTargetVoxelSize"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfNarrowBandInner"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfNarrowBandOuter"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfTextureFormat"))
        # Fractional variants
        self.assertTrue(self.prim.HasAttribute("newton:sdfNarrowBandInnerFraction"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfNarrowBandOuterFraction"))
        self.assertTrue(self.prim.HasAttribute("newton:sdfMarginFraction"))
        # Hydroelastic attrs are folded into this API
        self.assertTrue(self.prim.HasAttribute("newton:hydroelasticEnabled"))
        self.assertTrue(self.prim.HasAttribute("newton:hydroelasticStiffness"))
        # Inherited from NewtonCollisionAPI
        self.assertTrue(self.prim.HasAttribute("newton:contactMargin"))
        self.assertTrue(self.prim.HasAttribute("newton:contactGap"))

    def test_api_limitations(self):
        xform: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/InvalidType").GetPrim()
        self.assertFalse(xform.CanApplyAPI("NewtonSDFCollisionAPI"))

    def test_sdf_max_resolution(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfMaxResolution")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 64)

        attr.Set(128)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 128)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 8)
            self.assertIsNone(hard.GetMaximum())

    def test_sdf_target_voxel_size(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfTargetVoxelSize")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        attr.Set(0.005)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.005)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_sdf_narrow_band_inner(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfNarrowBandInner")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), -0.1)

        attr.Set(-0.02)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), -0.02)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertIsNone(soft.GetMinimum())
            self.assertAlmostEqual(soft.GetMaximum(), 0.0)

    def test_sdf_narrow_band_outer(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfNarrowBandOuter")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        attr.Set(0.02)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.02)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_sdf_texture_format(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfTextureFormat")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "uint16")

        attr.Set("float32")
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "float32")

    def test_sdf_narrow_band_inner_fraction(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfNarrowBandInnerFraction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        attr.Set(-0.01)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), -0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), -1.0)
            self.assertAlmostEqual(hard.GetMaximum(), 0.0)

    def test_sdf_narrow_band_outer_fraction(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfNarrowBandOuterFraction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        attr.Set(0.01)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_sdf_margin_fraction(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:sdfMarginFraction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        attr.Set(0.01)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.01)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_hydroelastic_enabled(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:hydroelasticEnabled")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertFalse(attr.Get())  # opt-in: defaults to false

        attr.Set(True)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertTrue(attr.Get())

    def test_hydroelastic_stiffness(self):
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        attr = self.prim.GetAttribute("newton:hydroelasticStiffness")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e10)

        attr.Set(1e7)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


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
