# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdPhysics, Vt

import newton_usd_schemas  # noqa: F401


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
        self.assertFalse(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertFalse(self.scene.HasAPI("NewtonMPMSceneAPI"))
        self.assertTrue(self.scene.CanApplyAPI("NewtonMPMSceneAPI"))
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonMPMSceneAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMSceneAPI"))

    def _get_attribute(self, name):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        attr = self.scene.GetAttribute(name)
        self.assertIsNotNone(attr)
        self.assertFalse(attr.HasAuthoredValue())
        return attr

    def test_max_solver_iterations(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        self.assertEqual(self.scene.GetAttribute("newton:maxSolverIterations").Get(), -1)
        self.assertFalse(self.scene.HasAttribute("newton:mpm:maxIterations"))

    def test_tolerance(self):
        attr = self._get_attribute("newton:mpm:tolerance")
        self.assertAlmostEqual(attr.Get(), 1.0e-4)
        self.assertTrue(attr.Set(1.0e-3))
        self.assertAlmostEqual(attr.Get(), 1.0e-3)

    def test_rheology_solvers(self):
        attr = self._get_attribute("newton:mpm:rheologySolvers")
        self.assertEqual(attr.Get(), Vt.TokenArray(["auto"]))
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {"auto", "gauss-seidel", "gauss-seidel-soa", "gauss-seidel-batched", "jacobi", "cg", "cr", "gmres"},
        )
        self.assertTrue(attr.Set(Vt.TokenArray(["cg", "gauss-seidel"])))
        self.assertEqual(attr.Get(), Vt.TokenArray(["cg", "gauss-seidel"]))

    def test_voxel_size(self):
        attr = self._get_attribute("newton:mpm:voxelSize")
        self.assertEqual(attr.Get(), -math.inf)
        self.assertTrue(attr.Set(0.05))
        self.assertAlmostEqual(attr.Get(), 0.05)

    def test_grid_type(self):
        attr = self._get_attribute("newton:mpm:gridType")
        self.assertEqual(attr.Get(), "sparse")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"sparse", "dense", "fixed"})
        self.assertTrue(attr.Set("dense"))
        self.assertEqual(attr.Get(), "dense")

    def test_grid_padding(self):
        attr = self._get_attribute("newton:mpm:gridPadding")
        self.assertEqual(attr.Get(), 0)
        self.assertTrue(attr.Set(1))
        self.assertEqual(attr.Get(), 1)

    def test_max_active_cell_count(self):
        attr = self._get_attribute("newton:mpm:maxActiveCellCount")
        self.assertEqual(attr.Get(), -1)
        self.assertTrue(attr.Set(1024))
        self.assertEqual(attr.Get(), 1024)

    def test_transfer_scheme(self):
        attr = self._get_attribute("newton:mpm:transferScheme")
        self.assertEqual(attr.Get(), "apic")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"apic", "pic"})
        self.assertTrue(attr.Set("pic"))
        self.assertEqual(attr.Get(), "pic")

    def test_integration_scheme(self):
        attr = self._get_attribute("newton:mpm:integrationScheme")
        self.assertEqual(attr.Get(), "pic")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"pic", "gimp"})
        self.assertTrue(attr.Set("gimp"))
        self.assertEqual(attr.Get(), "gimp")

    def test_critical_fraction(self):
        attr = self._get_attribute("newton:mpm:criticalFraction")
        self.assertAlmostEqual(attr.Get(), 0.0)
        self.assertTrue(attr.Set(0.5))
        self.assertAlmostEqual(attr.Get(), 0.5)

    def test_air_drag(self):
        attr = self._get_attribute("newton:mpm:airDrag")
        self.assertEqual(attr.Get(), -math.inf)
        self.assertTrue(attr.Set(0.1))
        self.assertAlmostEqual(attr.Get(), 0.1)

    def test_collider_basis_type(self):
        attr = self._get_attribute("newton:mpm:colliderBasisType")
        self.assertEqual(attr.Get(), "serendipity")
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {"linear", "trilinear", "bspline", "serendipity", "particle"},
        )
        self.assertTrue(attr.Set("trilinear"))
        self.assertEqual(attr.Get(), "trilinear")

    def test_collider_basis_order(self):
        attr = self._get_attribute("newton:mpm:colliderBasisOrder")
        self.assertEqual(attr.Get(), 2)
        self.assertTrue(attr.Set(1))
        self.assertEqual(attr.Get(), 1)

    def test_collider_discontinuous_basis(self):
        attr = self._get_attribute("newton:mpm:colliderDiscontinuousBasis")
        self.assertFalse(attr.Get())
        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.Get())

    def test_strain_basis_type(self):
        attr = self._get_attribute("newton:mpm:strainBasisType")
        self.assertEqual(attr.Get(), "linear")
        self.assertEqual(
            set(attr.GetMetadata("allowedTokens")),
            {"linear", "trilinear", "bspline", "serendipity", "particle"},
        )
        self.assertTrue(attr.Set("trilinear"))
        self.assertEqual(attr.Get(), "trilinear")

    def test_strain_basis_order(self):
        attr = self._get_attribute("newton:mpm:strainBasisOrder")
        self.assertEqual(attr.Get(), 0)
        self.assertTrue(attr.Set(1))
        self.assertEqual(attr.Get(), 1)

    def test_strain_discontinuous_basis(self):
        attr = self._get_attribute("newton:mpm:strainDiscontinuousBasis")
        self.assertFalse(attr.Get())
        self.assertTrue(attr.Set(True))
        self.assertTrue(attr.Get())

    def test_velocity_basis(self):
        attr = self._get_attribute("newton:mpm:velocityBasis")
        self.assertEqual(attr.Get(), "Q1")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"Q1", "B2", "B3"})
        self.assertTrue(attr.Set("B2"))
        self.assertEqual(attr.Get(), "B2")


if __name__ == "__main__":
    unittest.main()
