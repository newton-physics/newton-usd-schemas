# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math

from pxr import Sdf, Usd

from ._registration import SUPPORTS_PYTHON_VALIDATORS, Finding, TimeRange, UsdValidation, native_prim_task, register_prim_validator, validator_name

ATTRIBUTE_HARD_LIMITS_VALIDATOR = validator_name("AttributeHardLimitsValidator")

# OpenUSD's own hard limits validator, proposed in PixarAnimationStudios/OpenUSD#4317. Once the minimum supported OpenUSD
# release includes it, deprecate this validator, and later remove it along with its plugInfo.json entry and requirement page.
OPENUSD_HARD_LIMITS_VALIDATOR = "usdValidation:AttributeHardLimits"


def hard_limits(attr: Usd.Attribute) -> tuple[float | int | None, float | int | None]:
    """Return the minimum and maximum hard limits of the attribute, either of which may be None."""
    if hasattr(attr, "GetHardLimits"):
        limits = attr.GetHardLimits()
        return limits.GetMinimum(), limits.GetMaximum()
    # Before OpenUSD 25.11, limits is not a registered metadata field, so it is read as an unregistered value
    limits = attr.GetMetadata("limits")
    if isinstance(limits, Sdf.UnregisteredValue):
        limits = limits.value
    hard = (limits or {}).get("hard") or {}
    return hard.get("minimum"), hard.get("maximum")


def check_attribute_hard_limits(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    findings = []
    definition = prim.GetPrimDefinition()
    for attr in prim.GetAuthoredAttributes():
        minimum, maximum = hard_limits(attr)
        if minimum is None and maximum is None:
            continue
        # A fallback outside the hard limits is a sentinel, such as -inf meaning "use the engine default"
        fallback = definition.GetAttributeFallbackValue(attr.GetName())
        times = [Usd.TimeCode.Default()] if time_range.include_default else []
        times += [Usd.TimeCode(t) for t in attr.GetTimeSamplesInInterval(time_range.interval)]
        for time in times:
            value = attr.Get(time)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value == fallback:
                continue
            if math.isnan(value) or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
                when = "" if time.IsDefault() else f" at time {time.GetValue()}"
                low = -math.inf if minimum is None else minimum
                high = math.inf if maximum is None else maximum
                findings.append(
                    Finding(
                        "AttributeOutsideHardLimits",
                        attr,
                        f"{attr.GetName()} on <{prim.GetPath()}> is {value}{when}, which is outside its hard limits [{low}, {high}].",
                    )
                )
                break
    return findings


def _task():
    if not SUPPORTS_PYTHON_VALIDATORS:
        return None
    registry = UsdValidation.ValidationRegistry()
    if not registry.GetValidatorMetadata(OPENUSD_HARD_LIMITS_VALIDATOR):
        return native_prim_task(check_attribute_hard_limits)
    # Defer to OpenUSD's validator where it exists, so that selecting this validator by keyword keeps working
    openusd_validator = registry.GetOrLoadValidatorByName(OPENUSD_HARD_LIMITS_VALIDATOR)
    return lambda prim, time_range: openusd_validator.Validate(prim, time_range)


register_prim_validator("AttributeHardLimitsValidator", _task())
