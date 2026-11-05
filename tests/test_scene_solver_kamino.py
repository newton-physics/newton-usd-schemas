# SPDX-FileCopyrightText: Copyright (c) 2025 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Sdf, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonKaminoSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsKaminoSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsKaminoSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsKaminoSceneAPI")
        self.assertEqual(schema_type, "NewtonKaminoSceneAPI")

    def test_api_application(self):
        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonKaminoSceneAPI"))

    def test_padmm_primal_tolerance(self):
        """Verify the existing padmm primal tolerance property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:padmm:primalTolerance"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:primalTolerance")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 1e-10)
            self.assertIsNone(hard.GetMaximum())

    def test_padmm_dual_tolerance(self):
        """Verify the existing padmm dual tolerance property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:padmm:dualTolerance"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:dualTolerance")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 1e-10)
            self.assertIsNone(hard.GetMaximum())

    def test_padmm_complementarity_tolerance(self):
        """Verify the existing padmm complementarity tolerance property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:padmm:complementarityTolerance"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:complementarityTolerance")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        success = attr.Set(1e-4)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-4, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 1e-10)
            self.assertIsNone(hard.GetMaximum())

    def test_padmm_warmstarting(self):
        """Verify the existing padmm warmstarting property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:padmm:warmstarting"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:warmstarting")
        allowed = attr.GetMetadata("allowedTokens")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "containers")

        success = attr.Set("internal")
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "internal")

        success = attr.Set("none")
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "none")

        success = "containers" in allowed
        self.assertTrue(success)
        success = "internal" in allowed
        self.assertTrue(success)
        success = "none" in allowed
        self.assertTrue(success)
        success = "foobar" in allowed
        self.assertFalse(success)

    def test_padmm_use_acceleration(self):
        """Verify the existing padmm use acceleration property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:padmm:useAcceleration"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:padmm:useAcceleration")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_constraints_use_preconditioning(self):
        """Verify the existing constraints use preconditioning property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:usePreconditioning"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:usePreconditioning")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        success = attr.Set(False)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_constraints_alpha(self):
        """Verify the existing constraints alpha property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:alpha"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:alpha")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_constraints_beta(self):
        """Verify the existing constraints beta property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:beta"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:beta")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_constraints_gamma(self):
        """Verify the existing constraints gamma property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:gamma"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:gamma")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-2, places=7)

        success = attr.Set(1e-1)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-1, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_joint_correction(self):
        """Verify the existing joint correction property."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:jointCorrection"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:jointCorrection")
        allowed = attr.GetMetadata("allowedTokens")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "twopi")

        success = attr.Set("continuous")
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "continuous")

        success = attr.Set("none")
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "none")

        success = "twopi" in allowed
        self.assertTrue(success)
        success = "continuous" in allowed
        self.assertTrue(success)
        success = "none" in allowed
        self.assertTrue(success)
        success = "foobar" in allowed
        self.assertFalse(success)

    def test_dynamics_solver(self):
        """Author the dynamics backend while preserving the PADMM fallback."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dynamicsSolver"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dynamicsSolver")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")

        self.assertTrue(attr.Set("dvi"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "dvi")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"padmm", "dvi"})

        self.assertTrue(attr.Set("padmm"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")

    def test_constraints_joint_recovery_time(self):
        """Author joint recovery time and restore the engine-default sentinel."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:jointRecoveryTime"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:jointRecoveryTime")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.02))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.02, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(-math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

    def test_constraints_joint_recovery_speed(self):
        """Author finite, zero, and uncapped joint recovery speeds."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:jointRecoverySpeed"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:jointRecoverySpeed")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

    def test_constraints_limit_recovery_time(self):
        """Author limit recovery time and restore the engine-default sentinel."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:limitRecoveryTime"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:limitRecoveryTime")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.02))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.02, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(-math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

    def test_constraints_limit_recovery_speed(self):
        """Author finite, zero, and uncapped limit recovery speeds."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:limitRecoverySpeed"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:limitRecoverySpeed")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

    def test_constraints_contact_recovery_time(self):
        """Author contact recovery time and restore the engine-default sentinel."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:contactRecoveryTime"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:contactRecoveryTime")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.02))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.02, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(-math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

    def test_constraints_contact_recovery_speed(self):
        """Author finite, zero, and uncapped contact recovery speeds."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:contactRecoverySpeed"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:contactRecoverySpeed")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        self.assertTrue(attr.Set(0.5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.5, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        self.assertTrue(attr.Set(math.inf))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), math.inf)

    def test_constraints_contact_compliance(self):
        """Opt into compliant contact constraints without changing the hard fallback."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:contactCompliance"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:contactCompliance")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Bool)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

    def test_constraints_limit_compliance(self):
        """Opt into compliant limit constraints without changing the hard fallback."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:limitCompliance"))

        self.scene.ApplyAPI("NewtonKaminoSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:limitCompliance")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Bool)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)


if __name__ == "__main__":
    unittest.main()
