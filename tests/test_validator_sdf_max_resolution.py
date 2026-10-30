# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import tempfile
import unittest

from pxr import Sdf, Usd, UsdGeom
from validator_test_case import SUPPORTS_PYTHON_FIXERS, ValidatorTestCase

from newton_usd_schemas import validators
from newton_usd_schemas.validators._collision import round_sdf_max_resolution

ERROR = "SdfMaxResolutionNotDivisibleBy8"


class TestRoundSdfMaxResolution(unittest.TestCase):
    def test_rounds_down(self):
        self.assertEqual(round_sdf_max_resolution(9), 8)

    def test_rounds_up(self):
        self.assertEqual(round_sdf_max_resolution(100), 104)

    def test_rounds_ties_up(self):
        self.assertEqual(round_sdf_max_resolution(12), 16)

    def test_minimum_of_8(self):
        self.assertEqual(round_sdf_max_resolution(3), 8)


class TestSdfMaxResolutionValidator(ValidatorTestCase):
    validator_name = validators.SDF_MAX_RESOLUTION_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim: Usd.Prim = UsdGeom.Cube.Define(self.stage, "/Collider").GetPrim()
        self.prim.ApplyAPI("NewtonSDFCollisionAPI")
        self.attr: Usd.Attribute = self.prim.GetAttribute("newton:sdfMaxResolution")

    def test_fallback_value(self):
        self.assertFalse(self.attr.HasAuthoredValue())
        self.assertEqual(self.validate(self.prim), [])

    def test_divisible_by_8(self):
        self.attr.Set(128)
        self.assertEqual(self.validate(self.prim), [])

    def test_not_divisible_by_8(self):
        self.attr.Set(100)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.attr.GetPath())])

    def test_target_voxel_size_does_not_hide_error(self):
        self.prim.GetAttribute("newton:sdfTargetVoxelSize").Set(0.01)
        self.attr.Set(100)
        self.assertEqual(self.validate(self.prim), [(ERROR, self.attr.GetPath())])

    def test_requires_api(self):
        prim = UsdGeom.Cube.Define(self.stage, "/NotSdf").GetPrim()
        prim.ApplyAPI("NewtonCollisionAPI")
        prim.CreateAttribute("newton:sdfMaxResolution", Sdf.ValueTypeNames.Int, custom=False).Set(100)
        self.assertEqual(self.validate(prim), [])

    def test_selected_by_keyword(self):
        self.attr.Set(100)
        self.assertEqual(self.validate_with_keywords("NewtonSDFCollisionAPI"), [ERROR])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["RoundSdfMaxResolution"])
        fixer = self.validator.GetFixerByName("RoundSdfMaxResolution")
        self.assertEqual(fixer.errorName, ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer(self):
        # ApplyFix saves the edit target layer, so the stage must be file backed
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = UsdGeom.Cube.Define(stage, "/Collider").GetPrim()
            prim.ApplyAPI("NewtonSDFCollisionAPI")
            attr = prim.GetAttribute("newton:sdfMaxResolution")
            attr.Set(100)
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(error, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
            self.assertEqual(attr.Get(), 104)
            self.assertFalse(stage.GetRootLayer().dirty)
            self.assertEqual(self.validator.Validate(prim), [])


if __name__ == "__main__":
    unittest.main()
