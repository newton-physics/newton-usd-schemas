# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import subprocess
import sys
import textwrap
import unittest

from pxr import Sdf, Usd

import newton_usd_schemas  # noqa: F401
from newton_usd_schemas.validators._registration import SUPPORTS_PYTHON_FIXERS, SUPPORTS_PYTHON_VALIDATORS

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

__all__ = [
    "SUPPORTS_PYTHON_FIXERS",
    "SUPPORTS_PYTHON_VALIDATORS",
    "ValidatorTestCase",
    "run_python",
]


def run_python(code: str) -> subprocess.CompletedProcess:
    """Run code in a fresh interpreter, for tests that depend on what has been imported or registered."""
    return subprocess.run([sys.executable, "-c", textwrap.dedent(code)], capture_output=True, text=True, check=False)


@unittest.skipUnless(SUPPORTS_PYTHON_VALIDATORS, "Python validators require OpenUSD 26.05 or newer")
class ValidatorTestCase(unittest.TestCase):
    """Base class for tests of a single `UsdValidation` validator."""

    validator_name: str = ""

    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.validator = UsdValidation.ValidationRegistry().GetOrLoadValidatorByName(self.validator_name)

    def validate(self, prim: Usd.Prim) -> list[tuple[str, Sdf.Path]]:
        """Return the name and site of each error the validator reports for the prim."""
        return [(error.GetName(), error.GetSites()[0].GetProperty().GetPath()) for error in self.validator.Validate(prim)]

    def validate_with_keywords(self, *keywords: str) -> list[str]:
        """Return the names of the errors reported for the stage by the validators with the keywords."""
        context = UsdValidation.ValidationContext(keywords=list(keywords))
        return sorted(error.GetName() for error in context.Validate(self.stage))
