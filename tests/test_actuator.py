# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Sdf, Usd, UsdGeom

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
        self.assertTrue(self.prim.HasRelationship("newton:battery"))

    def test_targets_relationship(self):
        rel = self.prim.GetRelationship("newton:targets")
        self.assertFalse(rel.HasAuthoredTargets())
        rel.SetTargets([Sdf.Path("/World/Joint")])
        targets = rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(str(targets[0]), "/World/Joint")

    def test_battery_relationship(self):
        rel = self.prim.GetRelationship("newton:battery")
        self.assertFalse(rel.HasAuthoredTargets())
        rel.SetTargets([Sdf.Path("/World/Battery")])
        self.assertEqual([str(t) for t in rel.GetTargets()], ["/World/Battery"])

    def test_not_imageable(self):
        # Actuators carry a control law bound to a joint; they have no extent and are
        # never rendered, so they derive from UsdTyped rather than UsdGeomImageable.
        self.assertFalse(self.prim.IsA(UsdGeom.Imageable))

        # The prim definition must not advertise Imageable properties it does not have.
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonActuator")
        self.assertIsNotNone(definition)
        self.assertEqual(sorted(definition.GetPropertyNames()), ["newton:battery", "newton:targets"])

    def test_bbox_cache_skips_actuator(self):
        # Regression test: when NewtonActuator declared UsdGeomImageable as its base
        # without baking in the inherited visibility/purpose/proxyPrim properties,
        # UsdGeom.BBoxCache treated the prim as Imageable and then failed to read its
        # visibility attribute, raising from _GetOrCreateVisibilityQuery.
        root = self.stage.DefinePrim("/World", "Xform")
        self.stage.DefinePrim("/World/Actuator", "NewtonActuator")
        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        bound = cache.ComputeWorldBound(root)
        self.assertTrue(bound.GetRange().IsEmpty())


class TestNewtonBattery(unittest.TestCase):
    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsBattery")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsBattery")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsBattery")
        self.assertEqual(schema_type, "NewtonBattery")

    def test_abstract(self):
        self.assertEqual(Usd.SchemaRegistry().GetSchemaKind("NewtonBattery"), Usd.SchemaKind.AbstractTyped)
        self.assertIsNone(Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonBattery"))


class TestNewtonConstantResistanceBattery(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Battery", "NewtonConstantResistanceBattery")

    def test_typed_schema_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsConstantResistanceBattery")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsConstantResistanceBattery")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsConstantResistanceBattery")
        self.assertEqual(schema_type, "NewtonConstantResistanceBattery")

    def test_prim_is_battery(self):
        self.assertEqual(self.prim.GetTypeName(), "NewtonConstantResistanceBattery")
        self.assertTrue(self.prim.IsValid())
        self.assertTrue(self.prim.IsA("NewtonBattery"))

    def test_not_imageable(self):
        self.assertFalse(self.prim.IsA(UsdGeom.Imageable))
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonConstantResistanceBattery")
        self.assertIsNotNone(definition)
        self.assertEqual(
            sorted(definition.GetPropertyNames()),
            ["newton:minVoltage", "newton:nominalVoltage", "newton:resistance"],
        )

    def test_bbox_cache_skips_battery(self):
        root = self.stage.DefinePrim("/World", "Xform")
        self.stage.DefinePrim("/World/Battery", "NewtonConstantResistanceBattery")
        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        self.assertTrue(cache.ComputeWorldBound(root).GetRange().IsEmpty())

    def test_nominal_voltage(self):
        attr = self.prim.GetAttribute("newton:nominalVoltage")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        self.assertTrue(attr.Set(12.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 12.0, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_resistance(self):
        attr = self.prim.GetAttribute("newton:resistance")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_min_voltage(self):
        attr = self.prim.GetAttribute("newton:minVoltage")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(9.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 9.0, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())


class TestNewtonActuatorInputProcessorBaseAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorInputProcessorBaseAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorInputProcessorBaseAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorInputProcessorBaseAPI")
        self.assertEqual(schema_type, "NewtonActuatorInputProcessorBaseAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorInputProcessorBaseAPI"))
        self.prim.ApplyAPI("NewtonActuatorInputProcessorBaseAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorInputProcessorBaseAPI"))

    def test_applied_by_input_processors(self):
        for name in ("NewtonActuatorDelayAPI", "NewtonActuatorEncoderAPI"):
            with self.subTest(name=name):
                prim = self.stage.DefinePrim(f"/{name}", "NewtonActuator")
                prim.ApplyAPI(name)
                self.assertTrue(prim.HasAPI("NewtonActuatorInputProcessorBaseAPI"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorInputProcessorBaseAPI"))


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


class TestNewtonActuatorEncoderAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorEncoderAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorEncoderAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorEncoderAPI")
        self.assertEqual(schema_type, "NewtonActuatorEncoderAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorEncoderAPI"))
        self.prim.ApplyAPI("NewtonActuatorEncoderAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorEncoderAPI"))
        self.assertTrue(self.prim.HasRelationship("newton:outputJoint"))

    def test_output_joint_relationship(self):
        self.prim.ApplyAPI("NewtonActuatorEncoderAPI")
        rel = self.prim.GetRelationship("newton:outputJoint")
        self.assertFalse(rel.HasAuthoredTargets())
        rel.SetTargets([Sdf.Path("/World/OutputJoint")])
        targets = rel.GetTargets()
        self.assertEqual(len(targets), 1)
        self.assertEqual(str(targets[0]), "/World/OutputJoint")

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorEncoderAPI"))


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


class TestNewtonVoltageControlAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsVoltageControlAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsVoltageControlAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsVoltageControlAPI")
        self.assertEqual(schema_type, "NewtonVoltageControlAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonVoltageControlAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))
        self.prim.ApplyAPI("NewtonVoltageControlAPI")
        self.assertTrue(self.prim.HasAPI("NewtonVoltageControlAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorControlBaseAPI"))

    def test_kp(self):
        self.assertFalse(self.prim.HasAttribute("newton:kp"))

        self.prim.ApplyAPI("NewtonVoltageControlAPI")
        attr = self.prim.GetAttribute("newton:kp")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(32.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 32.0, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_error_gain(self):
        self.assertFalse(self.prim.HasAttribute("newton:errorGain"))

        self.prim.ApplyAPI("NewtonVoltageControlAPI")
        attr = self.prim.GetAttribute("newton:errorGain")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        self.assertTrue(attr.Set(0.015625))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.015625, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonVoltageControlAPI"))


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


class TestNewtonActuatorCommandClampingBaseAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorCommandClampingBaseAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorCommandClampingBaseAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorCommandClampingBaseAPI")
        self.assertEqual(schema_type, "NewtonActuatorCommandClampingBaseAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorCommandClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonActuatorCommandClampingBaseAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorCommandClampingBaseAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorCommandClampingBaseAPI"))


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


class TestNewtonCurrentPWMClampingAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsCurrentPWMClampingAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsCurrentPWMClampingAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsCurrentPWMClampingAPI")
        self.assertEqual(schema_type, "NewtonCurrentPWMClampingAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonCurrentPWMClampingAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorCommandClampingBaseAPI"))
        self.prim.ApplyAPI("NewtonCurrentPWMClampingAPI")
        self.assertTrue(self.prim.HasAPI("NewtonCurrentPWMClampingAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorCommandClampingBaseAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonActuatorClampingBaseAPI"))

    def test_max_current(self):
        self.assertFalse(self.prim.HasAttribute("newton:maxCurrent"))

        self.prim.ApplyAPI("NewtonCurrentPWMClampingAPI")
        attr = self.prim.GetAttribute("newton:maxCurrent")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(1.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.5, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_max_pwm(self):
        self.assertFalse(self.prim.HasAttribute("newton:maxPwm"))

        self.prim.ApplyAPI("NewtonCurrentPWMClampingAPI")
        attr = self.prim.GetAttribute("newton:maxPwm")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0)

        self.assertTrue(attr.Set(0.9))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.9, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonCurrentPWMClampingAPI"))


class TestNewtonActuatorMotorBaseAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = self.stage.DefinePrim("/Actuator", "NewtonActuator")

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsActuatorMotorBaseAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsActuatorMotorBaseAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsActuatorMotorBaseAPI")
        self.assertEqual(schema_type, "NewtonActuatorMotorBaseAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonActuatorMotorBaseAPI"))
        self.prim.ApplyAPI("NewtonActuatorMotorBaseAPI")
        self.assertTrue(self.prim.HasAPI("NewtonActuatorMotorBaseAPI"))

    def test_api_limitations(self):
        xform = self.stage.DefinePrim("/NotActuator", "Xform")
        self.assertFalse(xform.CanApplyAPI("NewtonActuatorMotorBaseAPI"))


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
        self.assertFalse(self.prim.HasAPI("NewtonActuatorMotorBaseAPI"))
        self.prim.ApplyAPI("NewtonDCMotorAPI")
        self.assertTrue(self.prim.HasAPI("NewtonDCMotorAPI"))
        self.assertTrue(self.prim.HasAPI("NewtonActuatorMotorBaseAPI"))
        for name in ("kt", "resistance", "vin"):
            self.assertTrue(self.prim.HasAttribute(f"newton:{name}"), name)
        for name in ("maxPwm", "maxCurrent"):
            self.assertFalse(self.prim.HasAttribute(f"newton:{name}"), name)

    def test_kt(self):
        self.assertFalse(self.prim.HasAttribute("newton:kt"))

        self.prim.ApplyAPI("NewtonDCMotorAPI")
        attr = self.prim.GetAttribute("newton:kt")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        self.assertTrue(attr.Set(0.6))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.6, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_resistance(self):
        self.assertFalse(self.prim.HasAttribute("newton:resistance"))

        self.prim.ApplyAPI("NewtonDCMotorAPI")
        attr = self.prim.GetAttribute("newton:resistance")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        self.assertTrue(attr.Set(2.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2.0, places=6)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_vin(self):
        self.assertFalse(self.prim.HasAttribute("newton:vin"))

        self.prim.ApplyAPI("NewtonDCMotorAPI")
        attr = self.prim.GetAttribute("newton:vin")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertIsNone(attr.Get())

        self.assertTrue(attr.Set(12.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 12.0, places=6)

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
