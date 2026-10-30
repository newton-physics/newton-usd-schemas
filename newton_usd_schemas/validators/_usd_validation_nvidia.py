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
from usd_validation_nvidia import (
    BaseRuleChecker,
    Suggestion,
    UsdValidatorAdapter,
    register_capabilities,
    register_features,
    register_profiles,
    register_requirements,
    register_rule,
    unregister_capabilities,
    unregister_features,
    unregister_profiles,
    unregister_requirements,
    unregister_rule,
)

from ._collision import SDF_MAX_RESOLUTION_VALIDATOR, check_sdf_max_resolution, round_sdf_max_resolution
from ._joints import MIMIC_JOINT_VALIDATOR, check_mimic_joint
from ._limits import ATTRIBUTE_HARD_LIMITS_VALIDATOR, check_attribute_hard_limits
from ._registration import TimeRange
from ._requirements import Capabilities, Features, Profiles, Requirement, Requirements

__all__ = [
    "AttributeHardLimitsChecker",
    "MimicJointChecker",
    "Plugin",
    "SdfMaxResolutionChecker",
]


class _NewtonRule(UsdValidatorAdapter):
    """Uses the native `UsdValidation` validator when it is registered, and otherwise runs the same check in Python."""

    check = None

    def _CheckPrim(self, prim: Usd.Prim) -> None:  # noqa: N802
        for finding in self.check(prim, TimeRange()):
            self._AddFailedCheck(finding.message, at=finding.site, requirement=self._get_requirement(None))


class SdfMaxResolutionChecker(_NewtonRule):
    """`newton:sdfMaxResolution` must be divisible by 8."""

    check = staticmethod(check_sdf_max_resolution)

    @classmethod
    def validator_name(cls) -> str:
        return SDF_MAX_RESOLUTION_VALIDATOR

    @staticmethod
    def round_max_resolution(stage: Usd.Stage, attr: Usd.Attribute) -> None:
        attr.Set(round_sdf_max_resolution(attr.Get()))

    def GetIssues(self):  # noqa: N802
        # UsdValidatorAdapter does not convert UsdValidation fixers into suggestions
        suggestion = Suggestion(callable=self.round_max_resolution, message="Round newton:sdfMaxResolution to the nearest multiple of 8.")
        return [issue if issue.suggestions else replace(issue, suggestion=suggestion) for issue in super().GetIssues()]


class MimicJointChecker(_NewtonRule):
    """`newton:mimicJoint` must target exactly one other joint of the same type."""

    check = staticmethod(check_mimic_joint)

    @classmethod
    def validator_name(cls) -> str:
        return MIMIC_JOINT_VALIDATOR


class AttributeHardLimitsChecker(_NewtonRule):
    """Authored attribute values must lie within their hard limits, unless they equal the schema fallback value.

    usd-validation-nvidia proposes an equivalent generic rule. Once the minimum supported usd-validation-nvidia release
    includes it, deprecate this rule, and later remove it along with its requirement page.
    """

    check = staticmethod(check_attribute_hard_limits)

    @classmethod
    def validator_name(cls) -> str:
        return ATTRIBUTE_HARD_LIMITS_VALIDATOR


class Plugin:
    """Registers the Newton rules, requirements, capabilities, features, and profiles with `usd-validation-nvidia`."""

    rules: tuple[tuple[str, type[BaseRuleChecker], Requirement], ...] = (
        ("NewtonCollision", SdfMaxResolutionChecker, Requirements.SDF_001),
        ("NewtonJoints", MimicJointChecker, Requirements.MIMIC_001),
        ("Basic", AttributeHardLimitsChecker, Requirements.LIMITS_001),
    )

    def on_startup(self) -> None:
        register_capabilities(Capabilities)
        for category, rule, requirement in self.rules:
            register_requirements(requirement)(rule)
            register_rule(category)(rule)
        register_features(Features)
        register_profiles(Profiles)

    def on_shutdown(self) -> None:
        unregister_profiles(Profiles)
        unregister_features(Features)
        for _, rule, _ in self.rules:
            unregister_rule(rule)
            unregister_requirements(rule)
        unregister_capabilities(Capabilities)
