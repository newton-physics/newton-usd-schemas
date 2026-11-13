# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import tempfile
import unittest

from pxr import Sdf, Usd, UsdPhysics
from validator_test_case import SUPPORTS_PYTHON_FIXERS, SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase

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

    def test_warning_explains_correction(self):
        """Warn with the affected property, prim, and both authoring remedies."""
        self.apply_base_first()
        (finding,) = self.validator.Validate(self.prim)
        self.assertEqual(finding.GetType(), UsdValidation.ValidationErrorType.Warn)
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

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        """Register the explicit SCC selection fixer for this warning."""
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["SelectKaminoSccSolver"])
        fixer = self.validator.GetFixerByName("SelectKaminoSccSolver")
        self.assertEqual(fixer.errorName, ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_authors_in_requested_layer(self):
        """Author SCC in the supplied edit target and save that layer."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            target = Sdf.Layer.CreateNew((root / "settings.usda").as_posix())
            stage.GetRootLayer().subLayerPaths.append(target.identifier)
            stage.GetRootLayer().Save()
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(finding, Usd.EditTarget(target)))
            self.assertTrue(fixer.ApplyFix(finding, Usd.EditTarget(target)))
            self.assertEqual(attr.Get(), "scc")
            self.assertTrue(attr.HasAuthoredValue())
            self.assertEqual(target.GetAttributeAtPath(attr.GetPath()).default, "scc")
            self.assertIsNone(stage.GetRootLayer().GetAttributeAtPath(attr.GetPath()))
            self.assertEqual(stage.GetEditTarget().GetLayer(), stage.GetRootLayer())
            self.assertFalse(target.dirty)
            self.assertEqual(self.validator.Validate(prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_preserves_later_authored_choice(self):
        """Decline a stale warning after the user authors a solver choice."""
        with tempfile.TemporaryDirectory() as directory:
            stage = Usd.Stage.CreateNew((pathlib.Path(directory) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            attr.Set("padmm")
            self.assertFalse(fixer.CanApplyFix(finding, stage.GetEditTarget()))
            self.assertFalse(fixer.ApplyFix(finding, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), "padmm")

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_read_only_target(self):
        """Decline a target layer that cannot be edited."""
        with tempfile.TemporaryDirectory() as directory:
            stage = Usd.Stage.CreateNew((pathlib.Path(directory) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            stage.GetRootLayer().SetPermissionToEdit(False)
            self.assertFalse(fixer.CanApplyFix(finding, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), "padmm")

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_unsaveable_target(self):
        """Decline a layer that the native fixer cannot save."""
        self.apply_base_first()
        (finding,) = self.validator.Validate(self.prim)
        (fixer,) = finding.GetFixersByErrorName()
        self.assertFalse(fixer.CanApplyFix(finding, self.stage.GetEditTarget()))

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_weaker_target_below_block(self):
        """Avoid reporting success for a layer shadowed by a stronger value block."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            target = Sdf.Layer.CreateNew((root / "settings.usda").as_posix())
            stage.GetRootLayer().subLayerPaths.append(target.identifier)
            attr.Block()
            stage.GetRootLayer().Save()
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertFalse(fixer.CanApplyFix(finding, Usd.EditTarget(target)))
            self.assertFalse(fixer.ApplyFix(finding, Usd.EditTarget(target)))
            self.assertIsNone(target.GetPrimAtPath(prim.GetPath()))
            self.assertIsNone(attr.Get())

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_replaces_block_in_target(self):
        """Replace a solver value block when the edit target owns it."""
        with tempfile.TemporaryDirectory() as directory:
            stage = Usd.Stage.CreateNew((pathlib.Path(directory) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            attr.Block()
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(finding, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(finding, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), "scc")
            self.assertEqual(self.validator.Validate(prim), [])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_overrides_weaker_block(self):
        """Override a block in a weaker layer without modifying that layer."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            weak = Sdf.Layer.CreateNew((root / "settings.usda").as_posix())
            stage.GetRootLayer().subLayerPaths.append(weak.identifier)
            with Usd.EditContext(stage, weak):
                attr.Block()
            weak.Save()
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(finding, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(finding, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), "scc")
            self.assertIsInstance(weak.GetAttributeAtPath(attr.GetPath()).default, Sdf.ValueBlock)
            self.assertFalse(weak.dirty)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_layer_outside_stage(self):
        """Decline an edit layer that is not part of the stage."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            self.apply_base_first(prim)
            unrelated = Sdf.Layer.CreateNew((root / "unrelated.usda").as_posix())
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertFalse(fixer.CanApplyFix(finding, Usd.EditTarget(unrelated)))

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_authors_through_reference_mapping(self):
        """Honor the supplied edit target's mapping into a referenced asset."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            asset = Usd.Stage.CreateNew((root / "asset.usda").as_posix())
            asset_prim = UsdPhysics.Scene.Define(asset, "/Asset").GetPrim()
            self.apply_base_first(asset_prim)
            asset.GetRootLayer().Save()
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            prim = stage.DefinePrim("/Scene")
            prim.GetReferences().AddReference(asset.GetRootLayer().identifier, "/Asset")
            node = prim.GetPrimIndex().rootNode.children[0]
            target = Usd.EditTarget(asset.GetRootLayer(), node)
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(finding, target))
            self.assertTrue(fixer.ApplyFix(finding, target))
            self.assertEqual(asset_prim.GetAttribute("newton:kamino:dynamicsSolver").Get(), "scc")
            self.assertEqual(self.validator.Validate(prim), [])
            self.assertFalse(asset.GetRootLayer().dirty)
            self.assertIsNone(stage.GetRootLayer().GetAttributeAtPath("/Scene.newton:kamino:dynamicsSolver"))

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_instance_proxy(self):
        """Decline a scene inside an instance where properties cannot be authored."""
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            asset = Usd.Stage.CreateNew((root / "asset.usda").as_posix())
            asset.DefinePrim("/Asset", "Xform")
            self.apply_base_first(UsdPhysics.Scene.Define(asset, "/Asset/Scene").GetPrim())
            asset.GetRootLayer().Save()
            stage = Usd.Stage.CreateNew((root / "scene.usda").as_posix())
            instance = stage.DefinePrim("/Instance", "Xform")
            instance.GetReferences().AddReference(asset.GetRootLayer().identifier, "/Asset")
            instance.SetInstanceable(True)
            prim = stage.GetPrimAtPath("/Instance/Scene")
            self.assertTrue(prim.IsInstanceProxy())
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertFalse(fixer.CanApplyFix(finding, stage.GetEditTarget()))

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_declines_inactive_variant(self):
        """Decline a variant edit target that cannot change the validated scene."""
        with tempfile.TemporaryDirectory() as directory:
            stage = Usd.Stage.CreateNew((pathlib.Path(directory) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            variants = prim.GetVariantSets().AddVariantSet("mode")
            variants.AddVariant("selected")
            variants.AddVariant("other")
            variants.SetVariantSelection("selected")
            target = Usd.EditTarget.ForLocalDirectVariant(stage.GetRootLayer(), Sdf.Path("/Scene{mode=other}"))
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertFalse(fixer.CanApplyFix(finding, target))
            self.assertFalse(fixer.ApplyFix(finding, target))
            self.assertEqual(attr.Get(), "padmm")
            self.assertIsNone(stage.GetRootLayer().GetAttributeAtPath(target.MapToSpecPath(attr.GetPath())))

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_authors_selected_variant(self):
        """Author into an active variant using the supplied edit target."""
        with tempfile.TemporaryDirectory() as directory:
            stage = Usd.Stage.CreateNew((pathlib.Path(directory) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            attr = self.apply_base_first(prim)
            variants = prim.GetVariantSets().AddVariantSet("mode")
            variants.AddVariant("selected")
            variants.SetVariantSelection("selected")
            target = variants.GetVariantEditTarget()
            (finding,) = self.validator.Validate(prim)
            (fixer,) = finding.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(finding, target))
            self.assertTrue(fixer.ApplyFix(finding, target))
            self.assertEqual(attr.Get(), "scc")
            self.assertEqual(stage.GetRootLayer().GetAttributeAtPath(target.MapToSpecPath(attr.GetPath())).default, "scc")
            self.assertFalse(stage.GetRootLayer().dirty)


if __name__ == "__main__":
    unittest.main()
