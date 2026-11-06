# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Plug, Sdf, Usd, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonKaminoDviSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        """Register the DVI plugin type and schema identifier."""
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsKaminoDviSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsKaminoDviSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsKaminoDviSceneAPI")
        self.assertEqual(schema_type, "NewtonKaminoDviSceneAPI")

    def test_api_application(self):
        """Compose the existing Kamino and Newton scene APIs with DVI."""
        self.assertTrue(self.scene.CanApplyAPI("NewtonKaminoDviSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoDviSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoDviSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))

    def test_api_limitations(self):
        """Restrict the DVI scene API to PhysicsScene prims."""
        for type_name in ("Xform", "Sphere", "Material", "PhysicsRevoluteJoint"):
            with self.subTest(type_name=type_name):
                prim = self.stage.DefinePrim("/NotScene", type_name)
                self.assertFalse(prim.CanApplyAPI("NewtonKaminoDviSceneAPI"))
                self.stage.RemovePrim("/NotScene")

    def test_max_solver_iterations(self):
        """Author the inherited outer iteration budget with its engine-default sentinel."""
        self.assertFalse(self.scene.HasAttribute("newton:maxSolverIterations"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
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
        """Default to DVI while preserving inherited metadata and explicit solver choices."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dynamicsSolver"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dynamicsSolver")
        self.assertIsNotNone(attr)
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Token)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "dvi")
        base = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("NewtonKaminoSceneAPI")
        self.assertEqual(attr.GetDocumentation(), base.GetSchemaAttributeSpec(attr.GetName()).documentation)
        self.assertTrue(attr.GetDocumentation())
        self.assertEqual(attr.GetCustomData(), {})

        self.assertTrue(attr.Set("dvi"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "dvi")
        self.assertEqual(set(attr.GetMetadata("allowedTokens")), {"padmm", "dvi"})

        self.assertTrue(attr.Set("padmm"))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")

        attr.Clear()
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "dvi")

        self.assertTrue(self.scene.RemoveAPI("NewtonKaminoDviSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSceneAPI"))
        self.assertEqual(attr.Get(), "padmm")
        self.assertFalse(attr.HasAuthoredValue())

        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoDviSceneAPI"))
        # An explicitly listed base API is stronger than the later DVI API.
        self.assertEqual(attr.Get(), "padmm")
        self.assertTrue(self.scene.RemoveAPI("NewtonKaminoSceneAPI"))
        self.assertEqual(attr.Get(), "dvi")
        self.assertTrue(self.scene.HasAPI("NewtonKaminoSceneAPI"))
        self.assertTrue(self.scene.ApplyAPI("NewtonKaminoSceneAPI"))
        # A redundant base API listed after DVI keeps the DVI default.
        self.assertEqual(attr.Get(), "dvi")
        self.assertFalse(attr.HasAuthoredValue())

    def test_constraints_use_preconditioning(self):
        """Inherit the base preconditioning property without a DVI redefinition."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:constraints:usePreconditioning"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
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

    def test_bilateral_numerical_solver(self):
        """Select the concrete bilateral solver while preserving blocked LLT by default."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:bilateral:numericalSolver"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:bilateral:numericalSolver")
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

    def test_no_bilateral_llt_implementation(self):
        """Keep the removed bilateral implementation property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:bilateral:llt:implementation"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:bilateral:llt:implementation"))

    def test_unilateral_numerical_solver(self):
        """Select one numerical method for all unilateral constraints."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:numericalSolver"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:numericalSolver")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:pgs:omega"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:pgs:omega")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:pgs:sweepsPerIteration"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:pgs:sweepsPerIteration")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:apgd:maxIterations"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:apgd:maxIterations")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:apgd:tolerance"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:apgd:tolerance")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:unilateral:apgd:maxNonlinearCorrections"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:unilateral:apgd:maxNonlinearCorrections")
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
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:tolerance"))

        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        attr = self.scene.GetAttribute("newton:kamino:dvi:tolerance")
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

    def test_no_joint_limit_numerical_solver(self):
        """Keep the renamed joint-limit numerical solver property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:numericalSolver"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:numericalSolver"))

    def test_no_joint_limit_pgs_omega(self):
        """Keep the renamed joint-limit pgs omega property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:pgs:omega"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:pgs:omega"))

    def test_no_joint_limit_pgs_sweeps_per_solve(self):
        """Keep the renamed joint-limit pgs sweeps per solve property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:pgs:sweepsPerSolve"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointLimit:pgs:sweepsPerSolve"))

    def test_no_joint_inequality_numerical_solver(self):
        """Keep the removed jointInequality:numericalSolver property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:numericalSolver"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:numericalSolver"))

    def test_no_joint_inequality_pgs_omega(self):
        """Keep the removed jointInequality:pgs:omega property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:pgs:omega"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:pgs:omega"))

    def test_no_joint_inequality_pgs_sweeps_per_solve(self):
        """Keep the removed jointInequality:pgs:sweepsPerSolve property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:pgs:sweepsPerSolve"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:jointInequality:pgs:sweepsPerSolve"))

    def test_no_contact_numerical_solver(self):
        """Keep the removed contact:numericalSolver property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:numericalSolver"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:numericalSolver"))

    def test_no_contact_pgs_omega(self):
        """Keep the removed contact:pgs:omega property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:pgs:omega"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:pgs:omega"))

    def test_no_contact_pgs_sweeps_per_solve(self):
        """Keep the removed contact:pgs:sweepsPerSolve property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:pgs:sweepsPerSolve"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:pgs:sweepsPerSolve"))

    def test_no_contact_apgd_max_iterations(self):
        """Keep the removed contact:apgd:maxIterations property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:apgd:maxIterations"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:apgd:maxIterations"))

    def test_no_contact_apgd_tolerance(self):
        """Keep the removed contact:apgd:tolerance property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:apgd:tolerance"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:apgd:tolerance"))

    def test_no_contact_max_nonlinear_corrections(self):
        """Keep the removed contact:maxNonlinearCorrections property absent."""
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:maxNonlinearCorrections"))
        self.scene.ApplyAPI("NewtonKaminoDviSceneAPI")
        self.assertFalse(self.scene.HasAttribute("newton:kamino:dvi:contact:maxNonlinearCorrections"))


if __name__ == "__main__":
    unittest.main()
