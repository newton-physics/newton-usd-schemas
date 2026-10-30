# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import re
import unittest

from pxr import Sdf, Usd

import newton_usd_schemas  # noqa: F401
from newton_usd_schemas.validators._collision import check_sdf_max_resolution
from newton_usd_schemas.validators._joints import check_mimic_joint
from newton_usd_schemas.validators._limits import check_attribute_hard_limits
from newton_usd_schemas.validators._registration import PrimCheck, TimeRange
from newton_usd_schemas.validators._requirements import ExampleResult, Features, Requirement, Requirements

SPECS = pathlib.Path(__file__).parents[1] / "docs" / "specs"


class TestSpecExamples(unittest.TestCase):
    """Validate the examples on each requirement page in docs/specs.

    Each page has "Valid" and "Invalid" examples, which the build parses into the requirement's `examples`. An invalid
    example must produce at least one finding, and a valid example must produce none.
    """

    def assert_examples_match(self, requirement: Requirement, check: PrimCheck) -> None:
        self.assertTrue(requirement.examples, f"{requirement.code} has no examples")
        for example in requirement.examples:
            with self.subTest(example=example.display_name):
                layer = Sdf.Layer.CreateAnonymous(".usda")
                self.assertTrue(layer.ImportFromString(example.snippet.content))
                stage = Usd.Stage.Open(layer)
                findings = [finding.message for prim in stage.Traverse() for finding in check(prim, TimeRange())]
                if example.result == ExampleResult.FAILURE:
                    self.assertNotEqual(findings, [], "expected the invalid example to fail validation")
                else:
                    self.assertEqual(findings, [], "expected the valid example to pass validation")

    def test_sdf_max_resolution(self):
        self.assert_examples_match(Requirements.SDF_001, check_sdf_max_resolution)

    def test_mimic_joint_target(self):
        self.assert_examples_match(Requirements.MIMIC_001, check_mimic_joint)

    def test_attribute_hard_limits(self):
        self.assert_examples_match(Requirements.LIMITS_001, check_attribute_hard_limits)


class TestFeaturePages(unittest.TestCase):
    """Check that the requirements table on each feature page matches the `features-table` the build reads."""

    def test_newton_simulation(self):
        page = (SPECS / "features" / "newton_simulation.md").read_text()
        table = re.findall(r"^\| \[`([^`]+)`\]", page, re.MULTILINE)
        self.assertEqual(table, [requirement.code for requirement in Features.NEWTON_SIMULATION_V1_0_0.requirements])


if __name__ == "__main__":
    unittest.main()
