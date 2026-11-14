# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Sdf, Usd, UsdPhysics
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase

from newton_usd_schemas import validators

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

ERROR = "KaminoSccSolverNotSelected"


class TestKaminoSccSolverValidator(ValidatorTestCase):
    validator_name = validators.KAMINO_SCC_SOLVER_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def apply_base_first(self, prim=None):
        """Apply the base API before SCC to reproduce the fallback conflict."""
        prim = self.prim if prim is None else prim
        prim.ApplyAPI("NewtonKaminoSceneAPI")
        prim.ApplyAPI("NewtonKaminoSccSceneAPI")
        return prim.GetAttribute("newton:kamino:dynamicsSolver")

    def apply_in_layers(self, *, append):
        """Compose a stronger SCC API opinion over a weaker base API opinion."""
        weak = Sdf.Layer.CreateAnonymous()
        self.stage.GetRootLayer().subLayerPaths.append(weak.identifier)
        with Usd.EditContext(self.stage, weak):
            self.prim.ApplyAPI("NewtonKaminoSceneAPI")
        order = Sdf.TokenListOp()
        if append:
            order.appendedItems = ["NewtonKaminoSccSceneAPI"]
        else:
            order.prependedItems = ["NewtonKaminoSccSceneAPI"]
        self.prim.SetMetadata("apiSchemas", order)
        return self.prim.GetAttribute("newton:kamino:dynamicsSolver")

    def test_scc_only(self):
        """Accept SCC's unauthored solver default."""
        self.prim.ApplyAPI("NewtonKaminoSccSceneAPI")
        self.assertEqual(self.validate(self.prim), [])

    def test_base_first(self):
        """Report the solver property when the earlier base API selects PADMM."""
        attr = self.apply_base_first()
        self.assertEqual(attr.Get(), "padmm")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_error_explains_correction(self):
        """Report an error with the affected property, prim, and manual correction."""
        self.apply_base_first()
        (finding,) = self.validator.Validate(self.prim)
        self.assertEqual(finding.GetType(), UsdValidation.ValidationErrorType.Error)
        self.assertEqual(finding.GetFixersByErrorName(), [])
        message = finding.GetMessage()
        for text in ["newton:kamino:dynamicsSolver", "/Scene", "padmm", "NewtonKaminoSccSceneAPI", "first", "author", "scc"]:
            self.assertIn(text, message)

    def test_scc_first(self):
        """Accept the SCC default when its API is listed before the base API."""
        self.prim.ApplyAPI("NewtonKaminoSccSceneAPI")
        self.prim.ApplyAPI("NewtonKaminoSceneAPI")
        self.assertEqual(self.validate(self.prim), [])

    def test_stronger_layer_prepends_scc(self):
        """Accept SCC prepended in a stronger layer."""
        attr = self.apply_in_layers(append=False)
        self.assertEqual(attr.Get(), "scc")
        self.assertEqual(self.validate(self.prim), [])

    def test_stronger_layer_appends_scc(self):
        """Report the base fallback retained when a stronger layer appends SCC."""
        attr = self.apply_in_layers(append=True)
        self.assertEqual(attr.Get(), "padmm")
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_explicit_scc(self):
        """Accept an authored SCC choice regardless of API order."""
        self.apply_base_first().Set("scc")
        self.assertEqual(self.validate(self.prim), [])

    def test_explicit_padmm(self):
        """Respect a deliberately authored PADMM choice."""
        self.apply_base_first().Set("padmm")
        self.assertEqual(self.validate(self.prim), [])

    def test_weaker_layer_authored_choice(self):
        """Respect an authored solver choice in a weaker layer."""
        self.apply_in_layers(append=True)
        weak = Sdf.Layer.Find(self.stage.GetRootLayer().subLayerPaths[0])
        with Usd.EditContext(self.stage, weak):
            self.prim.GetAttribute("newton:kamino:dynamicsSolver").Set("padmm")
        self.assertEqual(self.validate(self.prim), [])

    def test_time_sample_does_not_mask_default_conflict(self):
        """Report the wrong uniform default even when a solver time sample is authored."""
        attr = self.apply_base_first()
        attr.Set("scc", 1.0)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), "padmm")
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_authored_default_with_time_sample(self):
        """Respect an explicit default solver choice when time samples also exist."""
        attr = self.apply_base_first()
        attr.Set("padmm")
        attr.Set("scc", 1.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_blocked_choice(self):
        """Report a blocked solver value that cannot select SCC."""
        self.prim.ApplyAPI("NewtonKaminoSccSceneAPI")
        attr = self.prim.GetAttribute("newton:kamino:dynamicsSolver")
        attr.Block()
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_variant_choice_below_direct_block(self):
        """Report a direct value block that wins over a stronger layer's variant value."""
        attr = self.apply_base_first()
        weak = Sdf.Layer.CreateAnonymous()
        self.stage.GetRootLayer().subLayerPaths.append(weak.identifier)
        with Usd.EditContext(self.stage, weak):
            attr.Block()
        variants = self.prim.GetVariantSets().AddVariantSet("mode")
        variants.AddVariant("selected")
        variants.SetVariantSelection("selected")
        with variants.GetVariantEditContext():
            attr.Set("scc")
        self.assertIsNone(attr.Get(Usd.TimeCode.Default()))
        before = self.stage.GetRootLayer().ExportToString()
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])
        self.assertEqual(self.stage.GetRootLayer().ExportToString(), before)

        attr.Set("scc")
        self.assertEqual(self.validate(self.prim), [])

    def test_time_sample_above_default_block(self):
        """Report a blocked default even when a stronger layer supplies time samples."""
        attr = self.apply_base_first()
        weak = Sdf.Layer.CreateAnonymous()
        self.stage.GetRootLayer().subLayerPaths.append(weak.identifier)
        with Usd.EditContext(self.stage, weak):
            attr.Block()
        attr.Set("scc", 1.0)
        self.assertEqual(attr.Get(1.0), "scc")
        self.assertIsNone(attr.Get(Usd.TimeCode.Default()))
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

        attr.Set("scc")
        self.assertEqual(self.validate(self.prim), [])

    def test_base_only(self):
        """Ignore a scene configured only with the base Kamino API."""
        self.prim.ApplyAPI("NewtonKaminoSceneAPI")
        self.assertEqual(self.validate(self.prim), [])

    def test_requires_api(self):
        """Ignore a solver attribute on a prim without the SCC API."""
        self.prim.CreateAttribute("newton:kamino:dynamicsSolver", Sdf.ValueTypeNames.Token).Set("padmm")
        self.assertEqual(self.validate(self.prim), [])

    def test_selected_by_schema_keyword(self):
        """Select the validator through the SCC scene API keyword."""
        self.apply_base_first()
        self.assertEqual(self.validate_with_keywords("NewtonKaminoSccSceneAPI"), [ERROR])

    def test_selected_by_topic_keyword(self):
        """Select the validator through the Kamino topic keyword."""
        self.apply_base_first()
        self.assertEqual(self.validate_with_keywords("NewtonKamino"), [ERROR])


if __name__ == "__main__":
    unittest.main()
