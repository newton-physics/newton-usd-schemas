# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonVbdSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsVbdSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsVbdSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsVbdSceneAPI")
        self.assertEqual(schema_type, "NewtonVbdSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonVbdSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonVbdSceneAPI"))

    def test_attribute_defaults(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        expected = {
            "newton:vbd:frictionEpsilon": 0.01,
            "newton:vbd:particle:selfContactEnabled": False,
            "newton:vbd:particle:selfContactRadius": 0.2,
            "newton:vbd:particle:selfContactMargin": 0.2,
            "newton:vbd:particle:conservativeBoundRelaxation": 0.85,
            "newton:vbd:particle:collisionDetectionInterval": 0,
            "newton:vbd:particle:edgeParallelEpsilon": 1e-5,
            "newton:vbd:particle:topologicalContactFilterThreshold": 2,
            "newton:vbd:particle:restShapeContactExclusionRadius": 0.0,
            "newton:vbd:rigid:avbdAlpha": 0.95,
            "newton:vbd:rigid:avbdJointAlpha": float("-inf"),
            "newton:vbd:rigid:avbdContactAlpha": float("-inf"),
            "newton:vbd:rigid:avbdBeta": 0.0,
            "newton:vbd:rigid:avbdLinearBeta": float("-inf"),
            "newton:vbd:rigid:avbdAngularBeta": float("-inf"),
            "newton:vbd:rigid:avbdGamma": 0.999,
            "newton:vbd:rigid:contactHistory": False,
            "newton:vbd:rigid:contactStickMotionEps": 1e-4,
            "newton:vbd:rigid:contactStickFreezeTranslationEps": 1e-4,
            "newton:vbd:rigid:contactStickFreezeAngularEps": 1e-4,
            "newton:vbd:rigid:contactKStart": 100.0,
            "newton:vbd:rigid:jointLinearKe": 100000.0,
            "newton:vbd:rigid:jointAngularKe": 100000.0,
            "newton:vbd:rigid:jointLinearKStart": 100.0,
            "newton:vbd:rigid:jointAngularKStart": 10.0,
            "newton:vbd:rigid:jointLinearKd": 0.0,
            "newton:vbd:rigid:jointAngularKd": 0.0,
        }
        for name, default in expected.items():
            attr = self.scene.GetAttribute(name)
            self.assertIsNotNone(attr, name)
            value = attr.Get()
            if isinstance(default, (bool, int)):
                self.assertEqual(value, default, name)
            elif default == float("-inf"):
                self.assertEqual(float(value), default, name)
            else:
                self.assertAlmostEqual(float(value), float(default), places=5, msg=name)

    def test_attribute_set(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        attr = self.scene.GetAttribute("newton:vbd:particle:selfContactRadius")
        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5, places=5)

        flag = self.scene.GetAttribute("newton:vbd:particle:selfContactEnabled")
        self.assertTrue(flag.Set(True))
        self.assertEqual(flag.Get(), True)

        count = self.scene.GetAttribute("newton:vbd:particle:topologicalContactFilterThreshold")
        self.assertTrue(count.Set(3))
        self.assertEqual(count.Get(), 3)

    @unittest.skipUnless(USD_HAS_LIMITS, "USD build does not expose attribute limits")
    def test_hard_limits(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        # (attribute, minimum, maximum)
        cases = [
            ("newton:vbd:frictionEpsilon", 0.0, None),
            ("newton:vbd:particle:selfContactRadius", 0.0, None),
            ("newton:vbd:particle:conservativeBoundRelaxation", 0.0, 1.0),
            ("newton:vbd:rigid:avbdAlpha", 0.0, 1.0),
            ("newton:vbd:rigid:avbdGamma", 0.0, 1.0),
            ("newton:vbd:rigid:jointLinearKe", 0.0, None),
        ]
        for name, minimum, maximum in cases:
            attr = self.scene.GetAttribute(name)
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid(), name)
            self.assertAlmostEqual(hard.GetMinimum(), minimum, msg=name)
            if maximum is None:
                self.assertIsNone(hard.GetMaximum(), name)
            else:
                self.assertAlmostEqual(hard.GetMaximum(), maximum, msg=name)

    @unittest.skipUnless(USD_HAS_LIMITS, "USD build does not expose attribute limits")
    def test_soft_limits_on_sentinel_overrides(self):
        self.scene.ApplyAPI("NewtonVbdSceneAPI")
        for name in ("newton:vbd:rigid:avbdJointAlpha", "newton:vbd:rigid:avbdLinearBeta"):
            attr = self.scene.GetAttribute(name)
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid(), name)
            self.assertAlmostEqual(soft.GetMinimum(), 0.0, msg=name)


if __name__ == "__main__":
    unittest.main()
