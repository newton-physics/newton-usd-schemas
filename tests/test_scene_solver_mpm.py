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

    def test_api_application_and_limitations(self):
        self.assertTrue(self.scene.CanApplyAPI("NewtonMPMSceneAPI"))
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonMPMSceneAPI"))

        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMSceneAPI"))

    def test_fallbacks_match_solver_config(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")

        expected = {
            "newton:mpm:tolerance": 1.0e-4,
            "newton:mpm:rheologySolvers": Vt.TokenArray(["auto"]),
            "newton:mpm:warmstartMode": "auto",
            "newton:mpm:colliderVelocityMode": "forward",
            "newton:mpm:voxelSize": 0.1,
            "newton:mpm:gridType": "sparse",
            "newton:mpm:gridPadding": 0,
            "newton:mpm:maxActiveCellCount": -1,
            "newton:mpm:maxLeafNodeCount": -1,
            "newton:mpm:maxLowerNodeCount": -1,
            "newton:mpm:maxUpperNodeCount": -1,
            "newton:mpm:transferScheme": "apic",
            "newton:mpm:integrationScheme": "pic",
            "newton:mpm:criticalFraction": 0.0,
            "newton:mpm:airDrag": 1.0,
            "newton:mpm:colliderNormalFromSdfGradient": False,
            "newton:mpm:colliderBasis": "S2",
            "newton:mpm:strainBasis": "P0",
            "newton:mpm:velocityBasis": "Q1",
        }
        for name, value in expected.items():
            with self.subTest(name=name):
                attr = self.scene.GetAttribute(name)
                self.assertTrue(attr)
                self.assertFalse(attr.HasAuthoredValue())
                if isinstance(value, float):
                    self.assertTrue(math.isclose(attr.Get(), value, rel_tol=1.0e-6, abs_tol=1.0e-8))
                else:
                    self.assertEqual(attr.Get(), value)

        # MPM reuses the common scene iteration attribute. The -1 sentinel
        # tells an importer to retain SolverImplicitMPM.Config.max_iterations.
        self.assertEqual(self.scene.GetAttribute("newton:maxSolverIterations").Get(), -1)
        self.assertFalse(self.scene.HasAttribute("newton:mpm:maxIterations"))

    def test_allowed_tokens(self):
        self.scene.ApplyAPI("NewtonMPMSceneAPI")
        expected = {
            "newton:mpm:rheologySolvers": {
                "auto",
                "gs",
                "gauss-seidel",
                "gs-soa",
                "gauss-seidel-soa",
                "gs-batched",
                "gauss-seidel-batched",
                "jacobi",
                "cg",
                "cr",
                "gmres",
            },
            "newton:mpm:warmstartMode": {"none", "auto", "particles", "grid", "smoothed"},
            "newton:mpm:colliderVelocityMode": {"forward", "backward"},
            "newton:mpm:gridType": {"sparse", "dense", "fixed"},
            "newton:mpm:transferScheme": {"apic", "pic"},
            "newton:mpm:integrationScheme": {"pic", "gimp"},
            "newton:mpm:velocityBasis": {"Q1", "B2", "B3"},
        }
        for name, tokens in expected.items():
            with self.subTest(name=name):
                self.assertEqual(set(self.scene.GetAttribute(name).GetMetadata("allowedTokens")), tokens)

        # These basis names are extensible: Newton also accepts arbitrary
        # picN tokens, which cannot be represented by a closed token list.
        for name in ("newton:mpm:colliderBasis", "newton:mpm:strainBasis"):
            with self.subTest(name=name):
                attr = self.scene.GetAttribute(name)
                self.assertIsNone(attr.GetMetadata("allowedTokens"))
                self.assertTrue(attr.Set("pic64"))
                self.assertEqual(attr.Get(), "pic64")


if __name__ == "__main__":
    unittest.main()
