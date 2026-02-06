# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdGeom

import newton_usd_schemas  # noqa: F401


class TestNewtonArticulationRootAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/Articulation").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsArticulationRootAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsArticulationRootAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsArticulationRootAPI")
        self.assertEqual(schema_type, "NewtonArticulationRootAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("PhysicsArticulationRootAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonArticulationRootAPI"))
        self.prim.ApplyAPI("NewtonArticulationRootAPI")
        self.assertTrue(self.prim.HasAPI("PhysicsArticulationRootAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonArticulationRootAPI"))

        self.assertTrue(self.prim.HasAttribute("newton:selfCollisionEnabled"))

    def test_self_collision_enabled(self):
        self.assertFalse(self.prim.HasAttribute("newton:selfCollisionEnabled"))

        self.prim.ApplyAPI("NewtonArticulationRootAPI")
        attr = self.prim.GetAttribute("newton:selfCollisionEnabled")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)


if __name__ == "__main__":
    unittest.main()
