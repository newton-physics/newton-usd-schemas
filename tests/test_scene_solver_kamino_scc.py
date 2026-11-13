# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Sdf, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonKaminoSccSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        """Register the SCC plugin type and schema identifier."""
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsKaminoSccSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsKaminoSccSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsKaminoSccSceneAPI")
        self.assertEqual(schema_type, "NewtonKaminoSccSceneAPI")

    def test_api_application(self):
        """Compose the existing Kamino and Newton scene APIs with SCC."""
        self.assertTrue(self.scene.CanApplyAPI("NewtonKaminoSccSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSccSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSccSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))

    def test_api_limitations(self):
        """Restrict the SCC scene API to PhysicsScene prims."""
        for type_name in ("Xform", "Sphere", "Material", "PhysicsRevoluteJoint"):
            with self.subTest(type_name=type_name):
                prim = self.stage.DefinePrim("/NotScene", type_name)
                self.assertFalse(prim.CanApplyAPI("NewtonKaminoSccSceneAPI"))
                self.stage.RemovePrim("/NotScene")

    def test_max_solver_iterations(self):
        """Author the inherited outer iteration budget with its engine-default sentinel."""
        self.assertFalse(self.scene.HasAttribute("newton:maxSolverIterations"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:maxSolverIterations")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Int)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

        self.assertTrue(attr.Set(32))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 32)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), -1)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -1)

    def test_dynamics_solver(self):
        """Default to SCC while preserving inherited metadata and explicit solver choices."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dynamicsSolver"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dynamicsSolver")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "scc")
        base = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("NewtonKaminoSceneAPI")
        self.assertEqual(attr.GetDocumentation(), base.GetSchemaAttributeSpec(attr.GetName()).documentation)
        self.assertTrue(attr.GetDocumentation())
        self.assertEqual(attr.GetCustomData(), {})

        self.assertTrue(attr.Set("scc"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "scc")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"padmm", "scc"})

        self.assertTrue(attr.Set("padmm"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "scc")

        self.assertTrue(self.scene.RemoveAPI("NewtonKaminoSccSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSceneAPI"))
        self.assertEqual(attr.Get(), "padmm")
        self.assertFalse(attr.HasAuthoredValue())

        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSccSceneAPI"))
        # An explicitly listed base API is stronger than the later SCC API.
        self.assertEqual(attr.Get(), "padmm")
        self.assertTrue(self.scene.RemoveAPI("NewtonKaminoSceneAPI"))
        self.assertEqual(attr.Get(), "scc")
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSceneAPI"))
        # A redundant base API listed after SCC keeps the SCC default.
        self.assertEqual(attr.Get(), "scc")
        self.assertFalse(attr.HasAuthoredValue())

    def test_constraints_use_preconditioning(self):
        """Inherit the base preconditioning property without an SCC redefinition."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:usePreconditioning"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:constraints:usePreconditioning")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Bool)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)
        base = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("NewtonKaminoSceneAPI")
        self.assertEqual(attr.GetDocumentation(), base.GetSchemaAttributeSpec(attr.GetName()).documentation)
        self.assertTrue(attr.GetDocumentation())
        self.assertNotIn("apiSchemaOverride", attr.GetCustomData())

        self.assertTrue(attr.Set(False))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), False)

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), True)

    def test_warmstarting(self):
        """Select the source of cached constraint impulses with the runtime default."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:warmstarting"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:warmstarting")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "containers")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"none", "internal", "containers"})

        self.assertTrue(attr.Set("none"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "none")
        self.assertTrue(attr.Set("internal"))
        self.assertEqual(attr.Get(), "internal")
        self.assertTrue(attr.Set("containers"))
        self.assertEqual(attr.Get(), "containers")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "containers")

    def test_bilateral_numerical_solver(self):
        """Select the concrete bilateral solver while preserving blocked LLT by default."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:bilateral:numericalSolver"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:bilateral:numericalSolver")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "lltb")

        self.assertTrue(attr.Set("lltbrcm"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "lltbrcm")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"lltb", "lltbrcm"})

        self.assertTrue(attr.Set("lltb"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "lltb")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "lltb")

    def test_unilateral_numerical_solver(self):
        """Select one numerical method for all unilateral constraints."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:numericalSolver"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:numericalSolver")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "pgs")

        self.assertTrue(attr.Set("apgd"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "apgd")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"pgs", "apgd"})

        self.assertTrue(attr.Set("pgs"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "pgs")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "pgs")

    def test_unilateral_pgs_omega(self):
        """Author shared unilateral PGS relaxation with the solver fallback."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:pgs:omega"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:pgs:omega")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0, places=7)

        self.assertTrue(attr.Set(1.2))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.2, places=7)

        self.assertTrue(attr.Set(2.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 2.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertEqual(hard.GetMaximum(), 2.0)

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1.0, places=7)

    def test_unilateral_pgs_sweeps_per_iteration(self):
        """Author the shared PGS sweep count per alternating iteration."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:pgs:sweepsPerIteration"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:pgs:sweepsPerIteration")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Int)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2)

        self.assertTrue(attr.Set(4))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 4)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 1)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 2)

    def test_unilateral_apgd_max_iterations(self):
        """Author the APGD inner iteration budget."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:apgd:maxIterations"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:apgd:maxIterations")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Int)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 64)

        self.assertTrue(attr.Set(128))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 128)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 1)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 64)

    def test_unilateral_apgd_tolerance(self):
        """Author the APGD natural-map tolerance."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:apgd:tolerance"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:apgd:tolerance")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-5, places=7)

        self.assertTrue(attr.Set(1e-6))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-5, places=7)

    def test_unilateral_apgd_max_nonlinear_corrections(self):
        """Author the APGD nonlinear correction budget."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:unilateral:apgd:maxNonlinearCorrections"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:unilateral:apgd:maxNonlinearCorrections")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Int)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

        self.assertTrue(attr.Set(4))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 4)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 1)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), 1)

    def test_tolerance(self):
        """Author the projected-update and full-system convergence tolerance."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:scc:tolerance"))

        self.scene.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:scc:tolerance")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Float)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-5, places=7)

        self.assertTrue(attr.Set(1e-6))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-6, places=7)

        self.assertTrue(attr.Set(0.0))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 0.0, places=7)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), 1e-5, places=7)


if __name__ == "__main__":
    unittest.main()
