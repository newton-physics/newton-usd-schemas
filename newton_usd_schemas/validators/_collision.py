# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import SUPPORTS_PYTHON_FIXERS, Finding, TimeRange, UsdValidation, native_prim_task, register_prim_validator, validator_name

SDF_MAX_RESOLUTION_VALIDATOR = validator_name("SdfMaxResolutionValidator")
SDF_MAX_RESOLUTION_ERROR = "SdfMaxResolutionNotDivisibleBy8"


def check_sdf_max_resolution(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    if not prim.HasAPI("NewtonSDFCollisionAPI"):
        return []
    attr = prim.GetAttribute("newton:sdfMaxResolution")
    value = attr.Get()
    if value % 8 == 0:
        return []
    return [Finding(SDF_MAX_RESOLUTION_ERROR, attr, f"newton:sdfMaxResolution on <{prim.GetPath()}> is {value}, which is not divisible by 8.")]


def round_sdf_max_resolution(value: int) -> int:
    """Round to the nearest multiple of 8, rounding ties up, with a minimum of 8."""
    return max(8, (value + 4) // 8 * 8)


def _fixers() -> list | None:
    if not SUPPORTS_PYTHON_FIXERS:
        return None

    def can_fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        return bool(error.GetSites()[0].GetProperty())

    def fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        attr = error.GetSites()[0].GetProperty()
        with Usd.EditContext(attr.GetStage(), edit_target):
            return attr.Set(round_sdf_max_resolution(attr.Get()))

    return [
        UsdValidation.ValidationFixer(
            name="RoundSdfMaxResolution",
            description="Round newton:sdfMaxResolution to the nearest multiple of 8.",
            fixerImplFn=fix,
            canApplyFn=can_fix,
            errorName=SDF_MAX_RESOLUTION_ERROR,
        )
    ]


register_prim_validator("SdfMaxResolutionValidator", native_prim_task(check_sdf_max_resolution), _fixers())
