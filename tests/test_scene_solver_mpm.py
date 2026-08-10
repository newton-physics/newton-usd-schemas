# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdPhysics, Vt

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonMPMSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMPMSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMPMSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMPMSceneAPI")
        self.assertEqual(schema_type, "NewtonMPMSceneAPI")

    def test_api_application(self):
        self.assertTrue(self.scene.CanApplyAPI("NewtonMPMSceneAPI"))
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonMPMSceneAPI"))
        self.assertTrue(self.scene.HasAttribute("newton:maxSolverIterations"))
        self.assertFalse(self.scene.HasAttribute("newton:mpm:maxIterations"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMSceneAPI"))

    def test_tolerance(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:tolerance")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0e-4, places=7)

        self.assertTrue(attr.Set(1.0e-5))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0e-5, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_rheology_solvers(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:rheologySolvers")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), Vt.TokenArray(["auto"]))

        solvers = Vt.TokenArray(["cg", "auto"])
        self.assertTrue(attr.Set(solvers))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), solvers)
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {
                "auto",
                "gauss-seidel",
                "gauss-seidel-soa",
                "gauss-seidel-batched",
                "jacobi",
                "cg",
                "cr",
                "gmres",
            },
        )

    def test_voxel_size(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:voxelSize")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.05))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.05)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_grid_type(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:gridType")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "sparse")

        self.assertTrue(attr.Set("dense"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "dense")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"sparse", "dense", "fixed"})

    def test_grid_padding(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:gridPadding")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        self.assertTrue(attr.Set(2))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    def test_max_active_cell_count(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:maxActiveCellCount")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(1024))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1024)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

    def test_transfer_scheme(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:transferScheme")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "apic")

        self.assertTrue(attr.Set("pic"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "pic")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"apic", "pic"})

    def test_integration_scheme(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:integrationScheme")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "pic")

        self.assertTrue(attr.Set("gimp"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "gimp")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"pic", "gimp"})

    def test_critical_fraction(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:criticalFraction")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0)

        self.assertTrue(attr.Set(0.25))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.25)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertAlmostEqual(hard.GetMaximum(), 1.0)

    def test_air_drag(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:airDrag")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        self.assertTrue(attr.Set(0.1))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.1)

        if USD_HAS_LIMITS:
            soft = attr.GetSoftLimits()
            self.assertTrue(soft.IsValid())
            self.assertAlmostEqual(soft.GetMinimum(), 0.0)
            self.assertIsNone(soft.GetMaximum())

    def test_collider_basis_type(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:colliderBasisType")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "serendipity")

        self.assertTrue(attr.Set("particle"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "particle")
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {"linear", "trilinear", "bspline", "serendipity", "particle"},
        )

    def test_collider_basis_order(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:colliderBasisOrder")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2)

        self.assertTrue(attr.Set(3))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 3)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    def test_collider_discontinuous_basis(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:colliderDiscontinuousBasis")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_strain_basis_type(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:strainBasisType")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "linear")

        self.assertTrue(attr.Set("trilinear"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "trilinear")
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {"linear", "trilinear", "particle"},
        )

    def test_strain_basis_order(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:strainBasisOrder")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 0)

        self.assertTrue(attr.Set(1))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0)
            self.assertIsNone(hard.GetMaximum())

    def test_strain_discontinuous_basis(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:strainDiscontinuousBasis")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_velocity_basis_type(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:velocityBasisType")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "trilinear")

        self.assertTrue(attr.Set("bspline"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "bspline")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"trilinear", "bspline"})

    def test_velocity_basis_order(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute("newton:mpm:velocityBasisOrder")
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

        self.assertTrue(attr.Set(3))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 3)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 1)
            self.assertEqual(hard.GetMaximum(), 3)


if __name__ == "__main__":
    unittest.main()
