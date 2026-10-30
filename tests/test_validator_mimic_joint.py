# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Usd, UsdGeom, UsdPhysics
from validator_test_case import ValidatorTestCase

from newton_usd_schemas import validators


class TestMimicJointValidator(ValidatorTestCase):
    validator_name = validators.MIMIC_JOINT_VALIDATOR

    def setUp(self):
        super().setUp()
        self.leader: Usd.Prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Leader").GetPrim()
        self.follower: Usd.Prim = UsdPhysics.RevoluteJoint.Define(self.stage, "/Follower").GetPrim()
        self.follower.ApplyAPI("NewtonMimicAPI")
        self.rel: Usd.Relationship = self.follower.GetRelationship("newton:mimicJoint")

    def test_revolute_leader(self):
        self.rel.SetTargets([self.leader.GetPath()])
        self.assertEqual(self.validate(self.follower), [])

    def test_prismatic_leader(self):
        leader = UsdPhysics.PrismaticJoint.Define(self.stage, "/PrismaticLeader").GetPrim()
        follower = UsdPhysics.PrismaticJoint.Define(self.stage, "/PrismaticFollower").GetPrim()
        follower.ApplyAPI("NewtonMimicAPI")
        follower.GetRelationship("newton:mimicJoint").SetTargets([leader.GetPath()])
        self.assertEqual(self.validate(follower), [])

    def test_disabled_mimic_is_not_validated(self):
        self.follower.GetAttribute("newton:mimicEnabled").Set(False)
        self.assertEqual(self.validate(self.follower), [])

    def test_enabled_mimic_is_validated(self):
        self.follower.GetAttribute("newton:mimicEnabled").Set(True)
        self.assertEqual(self.validate(self.follower), [("MimicJointTargetCount", self.rel.GetPath())])

    def test_disabled_at_every_time_sample_is_not_validated(self):
        enabled = self.follower.GetAttribute("newton:mimicEnabled")
        enabled.Set(False, 0.0)
        enabled.Set(False, 1.0)
        self.assertEqual(self.validate(self.follower), [])

    def test_enabled_at_a_time_sample_is_validated(self):
        enabled = self.follower.GetAttribute("newton:mimicEnabled")
        enabled.Set(False, 0.0)
        enabled.Set(True, 1.0)
        self.assertEqual(self.validate(self.follower), [("MimicJointTargetCount", self.rel.GetPath())])

    def test_enabled_by_default_is_validated(self):
        enabled = self.follower.GetAttribute("newton:mimicEnabled")
        enabled.Set(True)
        enabled.Set(False, 0.0)
        self.assertEqual(self.validate(self.follower), [("MimicJointTargetCount", self.rel.GetPath())])

    def test_no_target(self):
        self.assertEqual(self.validate(self.follower), [("MimicJointTargetCount", self.rel.GetPath())])

    def test_multiple_targets(self):
        other = UsdPhysics.RevoluteJoint.Define(self.stage, "/Other").GetPrim()
        self.rel.SetTargets([self.leader.GetPath(), other.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointTargetCount", self.rel.GetPath())])

    def test_missing_target(self):
        self.rel.SetTargets(["/Missing"])
        self.assertEqual(self.validate(self.follower), [("MimicJointInvalidTarget", self.rel.GetPath())])

    def test_non_joint_target(self):
        xform = UsdGeom.Xform.Define(self.stage, "/Xform").GetPrim()
        self.rel.SetTargets([xform.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointInvalidTarget", self.rel.GetPath())])

    def test_self_target(self):
        self.rel.SetTargets([self.follower.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointInvalidTarget", self.rel.GetPath())])

    def test_prismatic_leader_for_revolute_follower(self):
        leader = UsdPhysics.PrismaticJoint.Define(self.stage, "/PrismaticLeader").GetPrim()
        self.rel.SetTargets([leader.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointTypeMismatch", self.rel.GetPath())])

    def test_spherical_leader_for_revolute_follower(self):
        leader = UsdPhysics.SphericalJoint.Define(self.stage, "/SphericalLeader").GetPrim()
        self.rel.SetTargets([leader.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointTypeMismatch", self.rel.GetPath())])

    def test_generic_leader_for_revolute_follower(self):
        leader = UsdPhysics.Joint.Define(self.stage, "/GenericLeader").GetPrim()
        self.rel.SetTargets([leader.GetPath()])
        self.assertEqual(self.validate(self.follower), [("MimicJointTypeMismatch", self.rel.GetPath())])

    def test_requires_api(self):
        joint = UsdPhysics.RevoluteJoint.Define(self.stage, "/NotMimic").GetPrim()
        joint.CreateRelationship("newton:mimicJoint", custom=False)
        self.assertEqual(self.validate(joint), [])

    def test_selected_by_keyword(self):
        self.assertEqual(self.validate_with_keywords("NewtonMimicAPI"), ["MimicJointTargetCount"])


if __name__ == "__main__":
    unittest.main()
