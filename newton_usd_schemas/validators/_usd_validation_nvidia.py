# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

"""`usd-validation-nvidia` rules for the Newton validators.

This module is never imported by `newton_usd_schemas` or `newton_usd_schemas.validators`, and is not part of their
public API. It is only imported by `usd-validation-nvidia` itself, through the `usd_validation_nvidia` entry point group
declared in pyproject.toml, so the rules are only active when the `newton-usd-schemas[validation]` extra is installed.
"""

from dataclasses import replace

from pxr import Usd

# Not guarded: usd-validation-nvidia is always installed when its entry point imports this module
from usd_validation_nvidia import BaseRuleChecker, Suggestion, UsdValidatorAdapter, register_rule, unregister_rule

from ._collision import SDF_MAX_RESOLUTION_VALIDATOR, check_sdf_max_resolution, round_sdf_max_resolution
from ._joints import MIMIC_JOINT_VALIDATOR, check_mimic_joint
from ._kamino import KAMINO_SCC_SOLVER_VALIDATOR, check_kamino_scc_solver
from ._limits import ATTRIBUTE_HARD_LIMITS_VALIDATOR, check_attribute_hard_limits
from ._migration import (
    RENAMED_API_SCHEMAS,
    RENAMED_API_SCHEMAS_VALIDATOR,
    RENAMED_ATTRIBUTES_VALIDATOR,
    authored_api_schemas,
    check_renamed_api_schemas,
    check_renamed_attributes,
    rename_api_schema,
    rename_attribute,
    renamed_to,
)
from ._registration import TimeRange, UsdValidation

__all__ = [
    "AttributeHardLimitsChecker",
    "KaminoSccSolverChecker",
    "MimicJointChecker",
    "Plugin",
    "RenamedAPISchemasChecker",
    "RenamedAttributesChecker",
    "SdfMaxResolutionChecker",
]


class _NewtonRule(UsdValidatorAdapter):
    """Uses the native `UsdValidation` validator when it is registered, and otherwise runs the same check in Python."""

    check = None
    # The fix for the validator's findings, called with the stage and the site of an issue, and its description
    fix = None
    fix_message = None

    def _CheckPrim(self, prim: Usd.Prim) -> None:  # noqa: N802
        for finding in self.check(prim, TimeRange()):
            if UsdValidation and finding.severity == UsdValidation.ValidationErrorType.Warn:
                self._AddWarning(finding.message, at=finding.site)
            else:
                self._AddFailedCheck(finding.message, at=finding.site)

    def GetIssues(self):  # noqa: N802
        issues = super().GetIssues()
        if self.fix is None:
            return issues
        # UsdValidatorAdapter does not convert UsdValidation fixers into suggestions
        suggestion = Suggestion(callable=self.fix, message=self.fix_message)
        return [issue if issue.suggestions else replace(issue, suggestion=suggestion) for issue in issues]


class SdfMaxResolutionChecker(_NewtonRule):
    """`newton:sdfMaxResolution` must be divisible by 8."""

    check = staticmethod(check_sdf_max_resolution)

    @classmethod
    def validator_name(cls) -> str:
        return SDF_MAX_RESOLUTION_VALIDATOR

    @staticmethod
    def fix(stage: Usd.Stage, attr: Usd.Attribute) -> None:
        attr.Set(round_sdf_max_resolution(attr.Get()))

    fix_message = "Round newton:sdfMaxResolution to the nearest multiple of 8."


class MimicJointChecker(_NewtonRule):
    """`newton:mimicJoint` must target exactly one other joint of the same type."""

    check = staticmethod(check_mimic_joint)

    @classmethod
    def validator_name(cls) -> str:
        return MIMIC_JOINT_VALIDATOR


class AttributeHardLimitsChecker(_NewtonRule):
    """Authored attribute values must lie within their hard limits, unless they equal the schema fallback value.

    usd-validation-nvidia proposes an equivalent generic rule. Once the minimum supported usd-validation-nvidia release
    includes it, deprecate this rule.
    """

    check = staticmethod(check_attribute_hard_limits)

    @classmethod
    def validator_name(cls) -> str:
        return ATTRIBUTE_HARD_LIMITS_VALIDATOR


class KaminoSccSolverChecker(_NewtonRule):
    """With `NewtonKaminoSccSceneAPI`, `newton:kamino:dynamicsSolver` must resolve to `scc`, unless a default is authored."""

    check = staticmethod(check_kamino_scc_solver)

    @classmethod
    def validator_name(cls) -> str:
        return KAMINO_SCC_SOLVER_VALIDATOR


class RenamedAttributesChecker(_NewtonRule):
    """Renamed attributes should be authored with their new names."""

    check = staticmethod(check_renamed_attributes)

    @classmethod
    def validator_name(cls) -> str:
        return RENAMED_ATTRIBUTES_VALIDATOR

    @staticmethod
    def fix(stage: Usd.Stage, attr: Usd.Attribute) -> None:
        if not rename_attribute(attr, renamed_to(attr.GetPrim(), attr.GetName()), stage.GetEditTarget()):
            raise ValueError(f"{attr.GetName()} on <{attr.GetPrim().GetPath()}> cannot be migrated in this layer")

    fix_message = "Move the values of the renamed attribute to its new name."


class RenamedAPISchemasChecker(_NewtonRule):
    """Renamed API schemas should be applied with their new names."""

    check = staticmethod(check_renamed_api_schemas)

    @classmethod
    def validator_name(cls) -> str:
        return RENAMED_API_SCHEMAS_VALIDATOR

    @staticmethod
    def fix(stage: Usd.Stage, prim: Usd.Prim) -> None:
        renamed = [old for old in authored_api_schemas(prim) if old in RENAMED_API_SCHEMAS]
        if not all(rename_api_schema(prim, old, RENAMED_API_SCHEMAS[old], stage.GetEditTarget()) for old in renamed):
            raise ValueError(f"The API schemas of <{prim.GetPath()}> cannot be migrated in this layer")

    fix_message = "Replace the renamed API schemas with their new names."


class Plugin:
    """Registers the Newton rules with `usd-validation-nvidia`."""

    rules: tuple[tuple[str, type[BaseRuleChecker]], ...] = (
        ("NewtonCollision", SdfMaxResolutionChecker),
        ("NewtonJoints", MimicJointChecker),
        ("NewtonKamino", KaminoSccSolverChecker),
        ("NewtonMigration", RenamedAttributesChecker),
        ("NewtonMigration", RenamedAPISchemasChecker),
        ("Basic", AttributeHardLimitsChecker),
    )

    def on_startup(self) -> None:
        for category, rule in self.rules:
            register_rule(category)(rule)

    def on_shutdown(self) -> None:
        for _, rule in self.rules:
            unregister_rule(rule)
