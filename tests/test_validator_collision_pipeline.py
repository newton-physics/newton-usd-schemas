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

CAPACITY_ERROR = "CollisionPipelineCapacityZero"
CONTACT_REPORT_ERROR = "CollisionPipelineContactReportWithoutMatching"
CAPACITIES = ("newton:collision:maxTrianglePairs", "newton:collision:maxShapePairs")


class TestCollisionPipelineValidator(ValidatorTestCase):
    validator_name = validators.COLLISION_PIPELINE_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()
        self.prim.ApplyAPI("NewtonCollisionPipelineAPI")
        self.report: Usd.Attribute = self.prim.GetAttribute("newton:collision:contactReport")
        self.matching: Usd.Attribute = self.prim.GetAttribute("newton:collision:contactMatching")

    def test_fallback_values(self):
        """Accept a pipeline with no authored values."""
        self.assertEqual(self.validate(self.prim), [])

    def test_engine_chosen_capacity(self):
        """Accept an authored -1, which lets the engine choose the capacity."""
        for name in CAPACITIES:
            with self.subTest(attribute=name):
                self.prim.GetAttribute(name).Set(-1)
                self.assertEqual(self.validate(self.prim), [])

    def test_positive_capacity(self):
        """Accept an authored positive capacity."""
        for name in CAPACITIES:
            with self.subTest(attribute=name):
                self.prim.GetAttribute(name).Set(4096)
                self.assertEqual(self.validate(self.prim), [])

    def test_zero_capacity(self):
        """Report a capacity of 0 on the attribute that authors it."""
        for name in CAPACITIES:
            with self.subTest(attribute=name):
                stage = Usd.Stage.CreateInMemory()
                prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
                prim.ApplyAPI("NewtonCollisionPipelineAPI")
                attr = prim.GetAttribute(name)
                attr.Set(0)
                self.assertEqual(self.validate(prim), [(CAPACITY_ERROR, attr.GetPath())])

    def test_zero_capacities(self):
        """Report each capacity of 0 separately."""
        attrs = [self.prim.GetAttribute(name) for name in CAPACITIES]
        for attr in attrs:
            attr.Set(0)
        self.assertEqual(self.validate(self.prim), [(CAPACITY_ERROR, attr.GetPath()) for attr in attrs])

    def test_blocked_capacity(self):
        """Accept a blocked capacity, which leaves it to the engine."""
        for name in CAPACITIES:
            with self.subTest(attribute=name):
                self.prim.GetAttribute(name).Block()
                self.assertEqual(self.validate(self.prim), [])

    def test_capacity_error_message(self):
        """Report the capacity, the prim, and the values it must have."""
        self.prim.GetAttribute("newton:collision:maxTrianglePairs").Set(0)
        (error,) = self.validator.Validate(self.prim)
        self.assertEqual(error.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["newton:collision:maxTrianglePairs", "/Scene", "0", "-1", "positive"]:
            self.assertIn(text, error.GetMessage())

    def test_contact_report_with_matching(self):
        """Accept contact reports when contact matching is enabled."""
        self.report.Set(True)
        for mode in ("latest", "sticky"):
            with self.subTest(mode=mode):
                self.matching.Set(mode)
                self.assertEqual(self.validate(self.prim), [])

    def test_contact_report_without_matching(self):
        """Report contact reports when contact matching falls back to disabled."""
        self.report.Set(True)
        self.assertFalse(self.matching.HasAuthoredValue())
        self.assertEqual(self.validate(self.prim), [(CONTACT_REPORT_ERROR, self.report.GetPath())])

    def test_contact_report_with_matching_disabled(self):
        """Report contact reports when contact matching is authored as disabled."""
        self.report.Set(True)
        self.matching.Set("disabled")
        self.assertEqual(self.validate(self.prim), [(CONTACT_REPORT_ERROR, self.report.GetPath())])

    def test_contact_report_with_blocked_matching(self):
        """Report contact reports when a blocked contact matching mode leaves it disabled."""
        self.report.Set(True)
        self.matching.Block()
        self.assertEqual(self.validate(self.prim), [(CONTACT_REPORT_ERROR, self.report.GetPath())])

    def test_contact_report_disabled(self):
        """Accept disabled contact matching when contact reports are off."""
        self.report.Set(False)
        self.matching.Set("disabled")
        self.assertEqual(self.validate(self.prim), [])

    def test_blocked_contact_report(self):
        """Accept a blocked contact report, which leaves it off."""
        self.report.Block()
        self.assertEqual(self.validate(self.prim), [])

    def test_contact_report_error_message(self):
        """Report the contact report, the prim, and the contact matching modes it requires."""
        self.report.Set(True)
        (error,) = self.validator.Validate(self.prim)
        self.assertEqual(error.GetType(), UsdValidation.ValidationErrorType.Error)
        self.assertEqual(error.GetFixersByErrorName(), [])
        for text in ["newton:collision:contactReport", "/Scene", "newton:collision:contactMatching", "disabled", "latest", "sticky"]:
            self.assertIn(text, error.GetMessage())

    def test_requires_api(self):
        """Ignore collision pipeline attributes on a scene without the API."""
        prim = UsdPhysics.Scene.Define(self.stage, "/OtherScene").GetPrim()
        prim.CreateAttribute("newton:collision:maxTrianglePairs", Sdf.ValueTypeNames.Int, custom=False).Set(0)
        prim.CreateAttribute("newton:collision:contactReport", Sdf.ValueTypeNames.Bool, custom=False).Set(True)
        self.assertEqual(self.validate(prim), [])

    def test_selected_by_schema_keyword(self):
        """Select the validator through the collision pipeline API keyword."""
        self.prim.GetAttribute("newton:collision:maxShapePairs").Set(0)
        self.assertEqual(self.validate_with_keywords("NewtonCollisionPipelineAPI"), [CAPACITY_ERROR])

    def test_selected_by_topic_keyword(self):
        """Select the validator through the collision topic keyword."""
        self.report.Set(True)
        self.assertEqual(self.validate_with_keywords("NewtonCollision"), [CONTACT_REPORT_ERROR])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        """Register a fixer for capacities of 0 only."""
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["LetEngineChooseCapacity"])
        fixer = self.validator.GetFixerByName("LetEngineChooseCapacity")
        self.assertEqual(fixer.errorName, CAPACITY_ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer(self):
        """Set a capacity of 0 to -1, so the engine chooses it."""
        # ApplyFix saves the edit target layer, so the stage must be file backed
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "scene.usda").as_posix())
            prim = UsdPhysics.Scene.Define(stage, "/Scene").GetPrim()
            prim.ApplyAPI("NewtonCollisionPipelineAPI")
            attr = prim.GetAttribute("newton:collision:maxTrianglePairs")
            attr.Set(0)
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(error, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), -1)
            self.assertFalse(stage.GetRootLayer().dirty)
            self.assertEqual(self.validator.Validate(prim), [])


if __name__ == "__main__":
    unittest.main()
