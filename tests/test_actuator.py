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
        self.assertTrue(self.prim.HasRelationship("newton:target"))

    def test_target_relationship(self):
        rel = self.prim.GetRelationship("newton:target")
        self.assertFalse(rel.HasAuthoredTargets())
        rel.SetTargets([Sdf.Path("/World/Joint")])
        targets = rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(str(targets[0]), "/World/Joint")


class TestNewtonIdealPDActuator(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/IdealPD", "NewtonIdealPDActuator")

    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsIdealPDActuator")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsIdealPDActuator")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsIdealPDActuator")
        self.assertEqual(schema_type, "NewtonIdealPDActuator")

    def test_prim_is_actuator(self):
        self.assertEqual(self.prim.GetTypeName(), "NewtonIdealPDActuator")
        self.assertTrue(self.prim.IsValid())
        self.assertTrue(self.prim.HasRelationship("newton:target"))

    def test_builtin_apis(self):
        self.assertTrue(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:kd"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))


class TestNewtonDelayedPDActuator(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/DelayedPD", "NewtonDelayedPDActuator")

    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsDelayedPDActuator")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsDelayedPDActuator")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsDelayedPDActuator")
        self.assertEqual(schema_type, "NewtonDelayedPDActuator")

    def test_prim_is_actuator(self):
        self.assertEqual(self.prim.GetTypeName(), "NewtonDelayedPDActuator")
        self.assertTrue(self.prim.IsValid())
        self.assertTrue(self.prim.HasRelationship("newton:target"))

    def test_builtin_apis(self):
        self.assertTrue(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonDelayAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:delaySteps"))


class TestNewtonDCMotorActuator(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/DCMotor", "NewtonDCMotorActuator")

    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsDCMotorActuator")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsDCMotorActuator")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsDCMotorActuator")
        self.assertEqual(schema_type, "NewtonDCMotorActuator")

    def test_prim_is_actuator(self):
        self.assertEqual(self.prim.GetTypeName(), "NewtonDCMotorActuator")
        self.assertTrue(self.prim.IsValid())
        self.assertTrue(self.prim.HasRelationship("newton:target"))

    def test_builtin_apis(self):
        self.assertTrue(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonDCMotorAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:saturationEffort"))


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
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))

    def test_max_force(self):
        self.prim.ApplyAPI("NewtonActuatorControlBaseAPI")
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
        self.assertTrue(self.prim.HasAttribute("newton:constantForce"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))

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

    def test_constant_force(self):
        self.prim.ApplyAPI("NewtonPDControlAPI")
        attr = self.prim.GetAttribute("newton:constantForce")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        attr.Set(-9.81)
        self.assertAlmostEqual(attr.Get(), -9.81, places=6)


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
        self.assertFalse(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonPIDControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonPIDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonPDControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:kp"))
        self.assertTrue(self.prim.HasAttribute("newton:kd"))
        self.assertTrue(self.prim.HasAttribute("newton:ki"))
        self.assertTrue(self.prim.HasAttribute("newton:integralMax"))
        self.assertTrue(self.prim.HasAttribute("newton:constantForce"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))

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
        self.assertTrue(self.prim.HasAttribute("newton:policyPath"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))
        self.assertTrue(self.prim.HasAttribute("newton:torqueScale"))

    def test_policy_path(self):
        self.prim.ApplyAPI("NewtonNetworkControlAPI")
        attr = self.prim.GetAttribute("newton:policyPath")
        self.assertFalse(attr.HasAuthoredValue())

    def test_torque_scale(self):
        self.prim.ApplyAPI("NewtonNetworkControlAPI")
        attr = self.prim.GetAttribute("newton:torqueScale")
        self.assertAlmostEqual(attr.Get(), 1.0)

        attr.Set(0.5)
        self.assertAlmostEqual(attr.Get(), 0.5)


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
        self.assertTrue(self.prim.HasAttribute("newton:policyPath"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))
        self.assertTrue(self.prim.HasAttribute("newton:torqueScale"))
        self.assertTrue(self.prim.HasAttribute("newton:positionScale"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityScale"))
        self.assertTrue(self.prim.HasAttribute("newton:inputOrder"))
        self.assertTrue(self.prim.HasAttribute("newton:inputIdx"))

    def test_scales(self):
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        self.assertAlmostEqual(self.prim.GetAttribute("newton:positionScale").Get(), 1.0)
        self.assertAlmostEqual(self.prim.GetAttribute("newton:velocityScale").Get(), 1.0)

    def test_input_order(self):
        self.prim.ApplyAPI("NewtonMLPControlAPI")
        attr = self.prim.GetAttribute("newton:inputOrder")
        self.assertEqual(attr.Get(), "pos_vel")

        attr.Set("vel_pos")
        self.assertEqual(attr.Get(), "vel_pos")

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
        self.assertTrue(self.prim.HasAttribute("newton:policyPath"))
        self.assertTrue(self.prim.HasAttribute("newton:maxForce"))
        self.assertTrue(self.prim.HasAttribute("newton:torqueScale"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonLSTMControlAPI"))


class TestNewtonDelayAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsDelayAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsDelayAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsDelayAPI")
        self.assertEqual(schema_type, "NewtonDelayAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonDelayAPI"))
        self.prim.ApplyAPI("NewtonDelayAPI")
        self.assertTrue(self.prim.HasAPI("NewtonDelayAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:delaySteps"))

    def test_delay_steps(self):
        self.prim.ApplyAPI("NewtonDelayAPI")
        attr = self.prim.GetAttribute("newton:delaySteps")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        attr.Set(5)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonDelayAPI"))


class TestNewtonGearBoxAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsGearBoxAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsGearBoxAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsGearBoxAPI")
        self.assertEqual(schema_type, "NewtonGearBoxAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonGearBoxAPI"))
        self.prim.ApplyAPI("NewtonGearBoxAPI")
        self.assertTrue(self.prim.HasAPI("NewtonGearBoxAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:gearRatio"))
        self.assertTrue(self.prim.HasAttribute("newton:maxTorqueOutput"))

    def test_gear_ratio(self):
        self.prim.ApplyAPI("NewtonGearBoxAPI")
        attr = self.prim.GetAttribute("newton:gearRatio")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        attr.Set(50.0)
        self.assertAlmostEqual(attr.Get(), 50.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_max_torque_output(self):
        self.prim.ApplyAPI("NewtonGearBoxAPI")
        attr = self.prim.GetAttribute("newton:maxTorqueOutput")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        attr.Set(200.0)
        self.assertAlmostEqual(attr.Get(), 200.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


class TestNewtonDCMotorAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsDCMotorAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsDCMotorAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsDCMotorAPI")
        self.assertEqual(schema_type, "NewtonDCMotorAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonDCMotorAPI"))
        self.prim.ApplyAPI("NewtonDCMotorAPI")
        self.assertTrue(self.prim.HasAPI("NewtonDCMotorAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:saturationEffort"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityLimit"))

    def test_saturation_effort(self):
        self.prim.ApplyAPI("NewtonDCMotorAPI")
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
        self.prim.ApplyAPI("NewtonDCMotorAPI")
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
        self.assertFalse(xform.CanApplyAPI("NewtonDCMotorAPI"))


if __name__ == "__main__":
    unittest.main()
