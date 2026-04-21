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

        attr.Set(0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        attr.Set(5)
        self.assertEqual(attr.Get(), 5)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
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


class TestNewtonNeuralControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsNeuralControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsNeuralControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsNeuralControlAPI")
        self.assertEqual(schema_type, "NewtonNeuralControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonNeuralControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonNeuralControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonNeuralControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:modelPath"))

    def test_model_path(self):
        self.prim.ApplyAPI("NewtonNeuralControlAPI")
        attr = self.prim.GetAttribute("newton:modelPath")
        self.assertFalse(attr.HasAuthoredValue())

        attr.Set("path/to/model.pt")
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get().path, "path/to/model.pt")

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonNeuralControlAPI"))


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


class TestNewtonMaxEffortClampingAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMaxEffortClampingAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMaxEffortClampingAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMaxEffortClampingAPI")
        self.assertEqual(schema_type, "NewtonMaxEffortClampingAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonMaxEffortClampingAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonMaxEffortClampingAPI")
        self.assertTrue(self.prim.HasAPI("NewtonMaxEffortClampingAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:maxEffort"))

    def test_max_effort(self):
        self.prim.ApplyAPI("NewtonMaxEffortClampingAPI")
        attr = self.prim.GetAttribute("newton:maxEffort")
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
        self.assertFalse(xform.CanApplyAPI("NewtonMaxEffortClampingAPI"))


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
        self.assertFalse(self.prim.HasAPI("NewtonMaxEffortClampingAPI"))
        self.assertTrue(self.prim.HasAttribute("newton:maxMotorEffort"))
        self.assertTrue(self.prim.HasAttribute("newton:saturationEffort"))
        self.assertTrue(self.prim.HasAttribute("newton:velocityLimit"))

    def test_max_motor_effort(self):
        self.prim.ApplyAPI("NewtonDCMotorClampingAPI")
        attr = self.prim.GetAttribute("newton:maxMotorEffort")
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
        self.assertTrue(self.prim.HasAttribute("newton:lookupPositions"))
        self.assertTrue(self.prim.HasAttribute("newton:lookupEfforts"))

    def test_lookup_positions(self):
        self.prim.ApplyAPI("NewtonPositionBasedClampingAPI")
        attr = self.prim.GetAttribute("newton:lookupPositions")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), [])

        attr.Set([0.0, 45.0, 90.0])
        self.assertEqual(attr.Get(), [0.0, 45.0, 90.0])

    def test_lookup_efforts(self):
        self.prim.ApplyAPI("NewtonPositionBasedClampingAPI")
        attr = self.prim.GetAttribute("newton:lookupEfforts")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), [])

        attr.Set([100.0, 80.0, 50.0])
        self.assertEqual(attr.Get(), [100.0, 80.0, 50.0])

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonPositionBasedClampingAPI"))


if __name__ == "__main__":
    unittest.main()
