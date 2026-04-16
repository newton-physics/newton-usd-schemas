# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Sdf, Usd

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonActuator(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuator")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuator")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuator")
        self.assertEqual(schema_type, "NewtonActuator")

    def test_prim_is_actuator(self):
        self.assertEqual(self.prim.GetTypeName(), "NewtonActuator")
        self.assertTrue(self.prim.IsValid())
        self.assertTrue(self.prim.HasRelationship("newton:targets"))

    def test_targets_relationship(self):
        rel = self.prim.GetRelationship("newton:targets")
        self.assertFalse(rel.HasAuthoredTargets())
        rel.SetTargets([Sdf.Path("/World/Joint")])
        targets = rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(str(targets[0]), "/World/Joint")


class TestNewtonActuatorDelayAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorDelayAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorDelayAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorDelayAPI")
        self.assertEqual(schema_type, "NewtonActuatorDelayAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorDelayAPI"))
        self.prim.ApplyAPI("NewtonActuatorDelayAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorDelayAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:delaySteps"))

    def test_delay_steps(self):
        self.prim.ApplyAPI("NewtonActuatorDelayAPI")
        attr = self.prim.GetAttribute("newton:delaySteps")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

        attr.Set(5)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 1)
            self.assertIsNone(hard.GetMaximum())

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorDelayAPI"))


class TestNewtonActuatorControlBaseAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorControlBaseAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorControlBaseAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorControlBaseAPI")
        self.assertEqual(schema_type, "NewtonActuatorControlBaseAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonActuatorControlBaseAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorControlBaseAPI"))


class TestNewtonPDControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsPDControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsPDControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsPDControlAPI")
        self.assertEqual(schema_type, "NewtonPDControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonPDControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:kd"))

    def test_kp(self):
        self.prim.ApplyAPI("NewtonPDControlAPI")
        attr = self.prim.GetAttribute("newton:kp")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(50.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 50.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_kd(self):
        self.prim.ApplyAPI("NewtonPDControlAPI")
        attr = self.prim.GetAttribute("newton:kd")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(5.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 5.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


class TestNewtonPIDControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsPIDControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsPIDControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsPIDControlAPI")
        self.assertEqual(schema_type, "NewtonPIDControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonPIDControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonPIDControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonPIDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:kd"))
        self.assertTrue(self.prim.HasAttribute("newton:ki"))
        self.assertTrue(self.prim.HasAttribute("newton:integralMax"))

    def test_kp(self):
        self.prim.ApplyAPI("NewtonPDControlAPI")
        attr = self.prim.GetAttribute("newton:kp")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(50.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 50.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_kd(self):
        self.prim.ApplyAPI("NewtonPDControlAPI")
        attr = self.prim.GetAttribute("newton:kd")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(5.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 5.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_ki(self):
        self.prim.ApplyAPI("NewtonPIDControlAPI")
        attr = self.prim.GetAttribute("newton:ki")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(10.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 10.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_integral_max(self):
        self.prim.ApplyAPI("NewtonPIDControlAPI")
        attr = self.prim.GetAttribute("newton:integralMax")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(100.0)
        self.assertAlmostEqual(attr.Get(), 100.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


class TestNewtonNetworkControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsNetworkControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsNetworkControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsNetworkControlAPI")
        self.assertEqual(schema_type, "NewtonNetworkControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonNetworkControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:networkPath"))

    def test_network_path(self):
        self.prim.ApplyAPI("NewtonNetworkControlAPI")
        attr = self.prim.GetAttribute("newton:networkPath")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        attr.Set("path/to/network.pt")
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "path/to/network.pt")

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonNetworkControlAPI"))


class TestNewtonMLPControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMLPControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMLPControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMLPControlAPI")
        self.assertEqual(schema_type, "NewtonMLPControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonMLPControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonMLPControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:networkPath"))
        self.assertTrue(self.prim.HasAttribute("newton:torqueScale"))
        self.assertTrue(self.prim.HasAttribute("newton:positionScale"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityScale"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityFirst"))
        self.assertTrue(self.prim.HasAttribute("newton:inputIdx"))

    def test_scales(self):
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        self.assertAlmostEqual(self.prim.GetAttribute("newton:positionScale").Get(), 1.0)
        self.assertAlmostEqual(self.prim.GetAttribute("newton:velocityScale").Get(), 1.0)
        self.assertAlmostEqual(self.prim.GetAttribute("newton:torqueScale").Get(), 1.0)

    def test_velocity_first(self):
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        attr = self.prim.GetAttribute("newton:velocityFirst")
        self.assertFalse(attr.Get())

        attr.Set(True)
        self.assertTrue(attr.Get())

    def test_input_idx(self):
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        attr = self.prim.GetAttribute("newton:inputIdx")
        self.assertEqual(list(attr.Get()), [0])

        attr.Set([0, 1, 2])
        self.assertEqual(list(attr.Get()), [0, 1, 2])

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonMLPControlAPI"))


class TestNewtonLSTMControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsLSTMControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsLSTMControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsLSTMControlAPI")
        self.assertEqual(schema_type, "NewtonLSTMControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonLSTMControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonLSTMControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonLSTMControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonNetworkControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:networkPath"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonLSTMControlAPI"))


class TestNewtonActuatorClampingBaseAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorClampingBaseAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorClampingBaseAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorClampingBaseAPI")
        self.assertEqual(schema_type, "NewtonActuatorClampingBaseAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonActuatorClampingBaseAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorClampingBaseAPI"))


class TestNewtonMaxForceClampingAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMaxForceClampingAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMaxForceClampingAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMaxForceClampingAPI")
        self.assertEqual(schema_type, "NewtonMaxForceClampingAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonMaxForceClampingAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonMaxForceClampingAPI")
        self.assertTrue(self.prim.HasAPI("NewtonMaxForceClampingAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))

    def test_max_force(self):
        self.prim.ApplyAPI("NewtonMaxForceClampingAPI")
        attr = self.prim.GetAttribute("newton:maxForce")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(100.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 100.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonMaxForceClampingAPI"))


class TestNewtonDCMotorClampingAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsDCMotorClampingAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsDCMotorClampingAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsDCMotorClampingAPI")
        self.assertEqual(schema_type, "NewtonDCMotorClampingAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonDCMotorClampingAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonDCMotorClampingAPI")
        self.assertTrue(self.prim.HasAPI("NewtonDCMotorClampingAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonMaxForceClampingAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))
        self.assertTrue(self.prim.HasAttribute("newton:saturationEffort"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityLimit"))

    def test_max_force(self):
        self.prim.ApplyAPI("NewtonDCMotorClampingAPI")
        attr = self.prim.GetAttribute("newton:maxForce")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(100.0)
        self.assertAlmostEqual(attr.Get(), 100.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_saturation_effort(self):
        self.prim.ApplyAPI("NewtonDCMotorClampingAPI")
        attr = self.prim.GetAttribute("newton:saturationEffort")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(10.0)
        self.assertAlmostEqual(attr.Get(), 10.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_velocity_limit(self):
        self.prim.ApplyAPI("NewtonDCMotorClampingAPI")
        attr = self.prim.GetAttribute("newton:velocityLimit")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(30.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 30.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonDCMotorClampingAPI"))


class TestNewtonPositionBasedClampingAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsPositionBasedClampingAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsPositionBasedClampingAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsPositionBasedClampingAPI")
        self.assertEqual(schema_type, "NewtonPositionBasedClampingAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonPositionBasedClampingAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonPositionBasedClampingAPI")
        self.assertTrue(self.prim.HasAPI("NewtonPositionBasedClampingAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:lookupAngles"))
        self.assertTrue(self.prim.HasAttribute("newton:lookupTorques"))

    def test_lookup_angles(self):
        self.prim.ApplyAPI("NewtonPositionBasedClampingAPI")
        attr = self.prim.GetAttribute("newton:lookupAngles")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), [])

        attr.Set([0.0, 45.0, 90.0])
        self.assertEqual(attr.Get(), [0.0, 45.0, 90.0])

    def test_lookup_torques(self):
        self.prim.ApplyAPI("NewtonPositionBasedClampingAPI")
        attr = self.prim.GetAttribute("newton:lookupTorques")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), [])

        attr.Set([100.0, 80.0, 50.0])
        self.assertEqual(attr.Get(), [100.0, 80.0, 50.0])

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonPositionBasedClampingAPI"))


if __name__ == "__main__":
    unittest.main()
