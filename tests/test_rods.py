# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Gf, Plug, Usd, UsdGeom, Vt

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonRodAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.rod = self.stage.DefinePrim("/Rod", "Xform")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsRodAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsRodAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsRodAPI")
        self.assertEqual(schema_type, "NewtonRodAPI")

    def test_api_application(self):
        self.assertFalse(self.rod.HasAPI("NewtonRodAPI"))
        self.rod.ApplyAPI("NewtonRodAPI")
        self.assertTrue(self.rod.HasAPI("NewtonRodAPI"))

        self.assertTrue(self.rod.HasAttribute("newton:points"))
        self.assertTrue(self.rod.HasAttribute("newton:radius"))
        self.assertTrue(self.rod.HasAttribute("newton:fixedPoints"))
        self.assertTrue(self.rod.HasAttribute("newton:stretchStiffness"))
        self.assertTrue(self.rod.HasAttribute("newton:stretchDamping"))
        self.assertTrue(self.rod.HasAttribute("newton:bendStiffness"))
        self.assertTrue(self.rod.HasAttribute("newton:bendDamping"))
        self.assertTrue(self.rod.HasAttribute("newton:twistStiffness"))
        self.assertTrue(self.rod.HasAttribute("newton:twistDamping"))
        self.assertTrue(self.rod.HasAttribute("newton:edges"))
        self.assertTrue(self.rod.HasAttribute("newton:closed"))
        self.assertTrue(self.rod.HasAttribute("newton:quaternions"))
        self.assertTrue(self.rod.HasAttribute("newton:wrapInArticulation"))
        self.assertTrue(self.rod.HasAttribute("newton:collisionFilterNeighborDistance"))

    def test_api_limitations(self):
        # API may only be applied to Xform, not BasisCurves or arbitrary prims
        curves = UsdGeom.BasisCurves.Define(self.stage, "/Curves").GetPrim()
        self.assertFalse(curves.CanApplyAPI("NewtonRodAPI"))
        xform = self.stage.DefinePrim("/OtherXform", "Xform")
        self.assertTrue(xform.CanApplyAPI("NewtonRodAPI"))

    # --- scalar defaults ---

    def test_points_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:points")
        self.assertFalse(attr.HasAuthoredValue())
        attr.Set(Vt.Vec3fArray([Gf.Vec3f(0, 0, 0), Gf.Vec3f(0, 0, 1), Gf.Vec3f(0, 0, 2)]))
        self.assertEqual(len(attr.Get()), 3)
        self.assertAlmostEqual(attr.Get()[2][2], 2.0)

    def test_radius_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:radius")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.005)
        attr.Set(0.003)
        self.assertAlmostEqual(attr.Get(), 0.003)

    def test_wrap_in_articulation_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:wrapInArticulation")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertTrue(attr.Get())

        attr.Set(False)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertFalse(attr.Get())

    def test_junction_collision_filter_default(self):
        # junctionCollisionFilter is removed; use collisionFilterNeighborDistance
        self.rod.ApplyAPI("NewtonRodAPI")
        self.assertFalse(self.rod.HasAttribute("newton:junctionCollisionFilter"))

    def test_collision_filter_neighbor_distance_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:collisionFilterNeighborDistance")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

    def test_collision_filter_neighbor_distance_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:collisionFilterNeighborDistance")

        # 0 = no filtering
        attr.Set(0)
        self.assertEqual(attr.Get(), 0)

        # 1 = direct neighbours only (default)
        attr.Set(1)
        self.assertEqual(attr.Get(), 1)

        # 2 = two hops (useful for thick rods)
        attr.Set(2)
        self.assertEqual(attr.Get(), 2)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    # --- array attributes (no schema-level defaults; engine fills them in) ---

    def test_fixed_points_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:fixedPoints")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(Vt.IntArray([0, 5, 10]))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(list(attr.Get()), [0, 5, 10])

    def test_youngs_modulus_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:youngsModulus")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), -1.0)  # sentinel = unset

        attr.Set(2.1e9)  # steel ~2.1 GPa
        self.assertAlmostEqual(attr.Get(), 2.1e9)

    def test_poisson_ratio_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:poissonRatio")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), -1.0)  # sentinel = unset

        attr.Set(0.3)  # steel ~0.3
        self.assertAlmostEqual(attr.Get(), 0.3)

    def test_armature_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:armature")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(1e-4)
        self.assertAlmostEqual(attr.Get(), 1e-4)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_stretch_stiffness_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:stretchStiffness")
        self.assertFalse(attr.HasAuthoredValue())

        # length-1: uniform scalar applied to all segments
        attr.Set(Vt.FloatArray([1e5]))
        self.assertEqual(len(attr.Get()), 1)
        self.assertAlmostEqual(attr.Get()[0], 1e5)

        # length-N: per-segment values
        attr.Set(Vt.FloatArray([1e5, 2e5, 3e5]))
        self.assertEqual(len(attr.Get()), 3)
        self.assertAlmostEqual(attr.Get()[1], 2e5)

    def test_stretch_damping_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:stretchDamping")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(Vt.FloatArray([0.0, 0.0]))
        self.assertEqual(list(attr.Get()), [0.0, 0.0])

    def test_bend_stiffness_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:bendStiffness")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(Vt.FloatArray([1e5, 2e5]))
        result = list(attr.Get())
        self.assertAlmostEqual(result[0], 1e5)
        self.assertAlmostEqual(result[1], 2e5)

    def test_bend_damping_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:bendDamping")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(Vt.FloatArray([1e-3, 1e-3]))
        result = list(attr.Get())
        self.assertAlmostEqual(result[0], 1e-3)

    def test_twist_stiffness_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:twistStiffness")
        self.assertFalse(attr.HasAuthoredValue())

        # length-1: uniform
        attr.Set(Vt.FloatArray([1200.0]))
        self.assertEqual(len(attr.Get()), 1)
        self.assertAlmostEqual(attr.Get()[0], 1200.0)

        # length-N: per-joint
        attr.Set(Vt.FloatArray([800.0, 1200.0, 1600.0]))
        self.assertEqual(len(attr.Get()), 3)
        self.assertAlmostEqual(attr.Get()[1], 1200.0)

    def test_twist_damping_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:twistDamping")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(Vt.FloatArray([0.05]))
        self.assertEqual(len(attr.Get()), 1)
        self.assertAlmostEqual(attr.Get()[0], 0.05)

        attr.Set(Vt.FloatArray([0.01, 0.05, 0.1]))
        self.assertEqual(len(attr.Get()), 3)
        self.assertAlmostEqual(attr.Get()[2], 0.1)

    def test_closed_default(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:closed")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertFalse(attr.Get())

        attr.Set(True)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertTrue(attr.Get())

    def test_edges_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:edges")
        self.assertFalse(attr.HasAuthoredValue())

        # Y-junction: nodes 0,1,2,3 with edges (0,1),(1,2),(1,3)
        attr.Set(Vt.Vec2iArray([Gf.Vec2i(0, 1), Gf.Vec2i(1, 2), Gf.Vec2i(1, 3)]))
        self.assertTrue(attr.HasAuthoredValue())
        result = list(attr.Get())
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1], Gf.Vec2i(1, 2))

    def test_quaternions_roundtrip(self):
        self.rod.ApplyAPI("NewtonRodAPI")
        attr = self.rod.GetAttribute("newton:quaternions")
        self.assertFalse(attr.HasAuthoredValue())

        # Identity quaternion: (i=0, j=0, k=0, w=1)
        identity = Gf.Quatf(1.0, 0.0, 0.0, 0.0)
        attr.Set(Vt.QuatfArray([identity, identity]))
        result = list(attr.Get())
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0].GetReal(), 1.0)


class TestNewtonRodAttachmentAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        rod = self.stage.DefinePrim("/Rod/rod_0", "Xform")
        rod.ApplyAPI("NewtonRodAPI")
        # attachment child prim (plain Xform)
        self.attach = self.stage.DefinePrim("/Rod/rod_0/attach_plug", "Xform")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsRodAttachmentAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsRodAttachmentAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsRodAttachmentAPI")
        self.assertEqual(schema_type, "NewtonRodAttachmentAPI")

    def test_api_application(self):
        self.assertFalse(self.attach.HasAPI("NewtonRodAttachmentAPI"))
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        self.assertTrue(self.attach.HasAPI("NewtonRodAttachmentAPI"))

        self.assertTrue(self.attach.HasAttribute("newton:nodeIndex"))
        self.assertTrue(self.attach.HasAttribute("newton:localPos1"))
        self.assertTrue(self.attach.HasAttribute("newton:localRot0"))
        self.assertTrue(self.attach.HasAttribute("newton:localRot1"))
        self.assertTrue(self.attach.HasRelationship("newton:body"))

    def test_node_index_roundtrip(self):
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        attr = self.attach.GetAttribute("newton:nodeIndex")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set(0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        attr.Set(74)
        self.assertEqual(attr.Get(), 74)

    def test_body_rel_roundtrip(self):
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        # Define a dummy rigid body prim to reference
        body = self.stage.DefinePrim("/World/Plug", "Xform")
        rel = self.attach.GetRelationship("newton:body")
        rel.SetTargets([body.GetPath()])
        targets = rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(str(targets[0]), "/World/Plug")

    def test_local_pos1_default(self):
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        attr = self.attach.GetAttribute("newton:localPos1")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), Gf.Vec3f(0, 0, 0))

        attr.Set(Gf.Vec3f(0.01, -0.02, 0.005))
        self.assertTrue(attr.HasAuthoredValue())

    def test_local_rot_defaults(self):
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        identity = Gf.Quatf(1.0, 0.0, 0.0, 0.0)

        rot0 = self.attach.GetAttribute("newton:localRot0")
        self.assertFalse(rot0.HasAuthoredValue())
        self.assertAlmostEqual(rot0.Get().GetReal(), identity.GetReal())

        rot1 = self.attach.GetAttribute("newton:localRot1")
        self.assertFalse(rot1.HasAuthoredValue())
        self.assertAlmostEqual(rot1.Get().GetReal(), identity.GetReal())

    def test_filter_attachment_collision_default(self):
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        attr = self.attach.GetAttribute("newton:filterAttachmentCollision")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertTrue(attr.Get())  # default = true

        attr.Set(False)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertFalse(attr.Get())

    def test_multiple_attachments(self):
        # Two attachment child prims on the same NewtonRodAPI Xform
        attach2 = self.stage.DefinePrim("/Rod/rod_0/attach_interface", "Xform")
        self.attach.ApplyAPI("NewtonRodAttachmentAPI")
        attach2.ApplyAPI("NewtonRodAttachmentAPI")

        self.attach.GetAttribute("newton:nodeIndex").Set(0)
        attach2.GetAttribute("newton:nodeIndex").Set(74)

        rod = self.stage.GetPrimAtPath("/Rod/rod_0")
        attachment_prims = [c for c in rod.GetChildren() if c.HasAPI("NewtonRodAttachmentAPI")]
        self.assertEqual(len(attachment_prims), 2)
        indices = sorted(c.GetAttribute("newton:nodeIndex").Get() for c in attachment_prims)
        self.assertEqual(indices, [0, 74])


if __name__ == "__main__":
    unittest.main()
