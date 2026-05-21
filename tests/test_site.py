# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdGeom

import newton_usd_schemas  # noqa: F401


class TestNewtonSiteAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Sphere.Define(self.stage, "/Site").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsSiteAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsSiteAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsSiteAPI")
        self.assertEqual(schema_type, "NewtonSiteAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonSiteAPI"))
        self.prim.ApplyAPI("NewtonSiteAPI")
        self.assertTrue(self.prim.HasAPI("NewtonSiteAPI"))

    def test_presence_only(self):
        self.prim.ApplyAPI("NewtonSiteAPI")
        site_attrs = [a for a in self.prim.GetAttributes() if a.GetName().startswith("newton:")]
        self.assertEqual(len(site_attrs), 0)

    def test_does_not_inherit_collision(self):
        self.prim.ApplyAPI("NewtonSiteAPI")
        self.assertFalse(self.prim.HasAPI("PhysicsCollisionAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonCollisionAPI"))

    def test_api_limitations(self):
        xform: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/InvalidType").GetPrim()
        self.assertFalse(xform.CanApplyAPI("NewtonSiteAPI"))

    def test_applies_to_various_gprims(self):
        cube = UsdGeom.Cube.Define(self.stage, "/Cube").GetPrim()
        self.assertTrue(cube.CanApplyAPI("NewtonSiteAPI"))
        cube.ApplyAPI("NewtonSiteAPI")
        self.assertTrue(cube.HasAPI("NewtonSiteAPI"))

        mesh = UsdGeom.Mesh.Define(self.stage, "/Mesh").GetPrim()
        self.assertTrue(mesh.CanApplyAPI("NewtonSiteAPI"))

        capsule = UsdGeom.Capsule.Define(self.stage, "/Capsule").GetPrim()
        self.assertTrue(capsule.CanApplyAPI("NewtonSiteAPI"))

    def test_removal(self):
        self.prim.ApplyAPI("NewtonSiteAPI")
        self.assertTrue(self.prim.HasAPI("NewtonSiteAPI"))
        self.prim.RemoveAPI("NewtonSiteAPI")
        self.assertFalse(self.prim.HasAPI("NewtonSiteAPI"))


if __name__ == "__main__":
    unittest.main()
