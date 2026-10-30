# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
from collections.abc import Callable
from typing import NamedTuple

from pxr import Gf, Plug, Usd

try:
    from pxr import UsdValidation
except ImportError:  # pragma: no cover
    UsdValidation = None  # pragma: no cover

_PLUGIN_DIR = pathlib.Path(__file__).parent
_PLUGIN_INFO = json.loads((_PLUGIN_DIR / "plugInfo.json").read_text())["Plugins"][0]

PLUGIN_NAME: str = _PLUGIN_INFO["Name"]

# Python validators require OpenUSD 26.05 or newer, and Python fixers require OpenUSD 26.11 or newer
SUPPORTS_PYTHON_VALIDATORS = UsdValidation is not None and hasattr(UsdValidation.ValidationRegistry, "RegisterPluginPrimValidator")
SUPPORTS_PYTHON_FIXERS = SUPPORTS_PYTHON_VALIDATORS and Usd.GetVersion() >= (0, 26, 11)

if SUPPORTS_PYTHON_VALIDATORS:
    # Register the plugin before any validator, so a registry created from now on reads the validator metadata from plugInfo.json
    Plug.Registry().RegisterPlugins([_PLUGIN_DIR.absolute().as_posix()])


class TimeRange(NamedTuple):
    """The times at which to check authored values, independent of the `UsdValidation` version."""

    include_default: bool = True
    interval: Gf.Interval = Gf.Interval.GetFullInterval()


class Finding(NamedTuple):
    """A single validation failure, reported as a `UsdValidation.ValidationError` or a `usd-validation-nvidia` issue."""

    name: str
    site: Usd.Object
    message: str


PrimCheck = Callable[[Usd.Prim, TimeRange], list[Finding]]


def validator_name(key: str) -> str:
    return f"{PLUGIN_NAME}:{key}"


def native_prim_task(check: PrimCheck):
    """Wrap a check as a `UsdValidation` prim task."""

    def task(prim: Usd.Prim, time_range: "UsdValidation.ValidationTimeRange") -> list["UsdValidation.ValidationError"]:
        findings = check(prim, TimeRange(time_range.IncludesTimeCodeDefault(), time_range.GetInterval()))
        return [
            UsdValidation.ValidationError(
                finding.name,
                UsdValidation.ValidationErrorType.Error,
                [UsdValidation.ValidationErrorSite(finding.site.GetStage(), finding.site.GetPath())],
                finding.message,
            )
            for finding in findings
        ]

    return task


def register_prim_validator(key: str, task, fixers: list | None = None) -> None:
    """Register a `UsdValidation` prim validator declared in plugInfo.json, if `UsdValidation` supports Python validators."""
    if not SUPPORTS_PYTHON_VALIDATORS:
        return
    name = validator_name(key)
    registry = UsdValidation.ValidationRegistry()
    if registry.HasValidator(name):
        return
    kwargs = {"fixers": fixers} if fixers else {}
    if registry.GetValidatorMetadata(name):
        registry.RegisterPluginPrimValidator(name, task, **kwargs)
        return
    # The registry reads plugInfo.json only once, when it is first created (PixarAnimationStudios/OpenUSD#4315).
    # If that happened before this plugin was registered with Plug, register the validator explicitly using the same metadata.
    info = _PLUGIN_INFO["Info"]["Validators"][key]
    metadata = UsdValidation.ValidatorMetadata(
        name=name,
        doc=info["doc"],
        keywords=info["keywords"],
        schemaTypes=info.get("schemaTypes", []),
        isTimeDependent=info.get("isTimeDependent", False),
    )
    registry.RegisterPrimValidator(metadata, task, **kwargs)
