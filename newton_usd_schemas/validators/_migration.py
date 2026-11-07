# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import (
    SUPPORTS_PYTHON_FIXERS,
    Finding,
    TimeRange,
    UsdValidation,
    native_prim_task,
    register_prim_validator,
    validator_name,
)

RENAMED_ATTRIBUTES_VALIDATOR = validator_name("RenamedAttributesValidator")
RENAMED_ATTRIBUTE_ERROR = "RenamedAttribute"

# Renamed attributes, by the API schema that defines their new names. The validator's schemaTypes
# and keywords in plugInfo.json must list the same schemas.
RENAMED_ATTRIBUTES: dict[str, dict[str, str]] = {}


def renamed_to(prim: Usd.Prim, name: str) -> str | None:
    """Return the new name of the attribute, if an API schema applied to the prim renamed it."""
    for schema, renames in RENAMED_ATTRIBUTES.items():
        if name in renames and prim.HasAPI(schema):
            return renames[name]
    return None


def check_renamed_attributes(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    findings = []
    definition = prim.GetPrimDefinition()
    for schema, renames in RENAMED_ATTRIBUTES.items():
        if not prim.HasAPI(schema):
            continue
        schema_definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema)
        for old, new in renames.items():
            attr = prim.GetAttribute(old)
            if not attr or not attr.HasAuthoredValue():
                continue
            if schema_definition.GetPropertyDefinition(old):
                message = f"{old} on <{prim.GetPath()}> is deprecated by {schema}. Use {new} instead."
                findings.append(Finding(RENAMED_ATTRIBUTE_ERROR, attr, message, UsdValidation.ValidationErrorType.Warn))
            # Otherwise, the old name may still belong to another schema applied to the prim
            elif not definition.GetPropertyDefinition(old):
                message = f"{old} on <{prim.GetPath()}> was renamed to {new} by {schema}, so its value is ignored."
                findings.append(Finding(RENAMED_ATTRIBUTE_ERROR, attr, message))
    return findings


def rename_attribute(attr: Usd.Attribute, new_name: str, edit_target: Usd.EditTarget) -> bool:
    """Move the authored values of a renamed attribute to its new name, authoring in the edit target.

    Values already authored on the new name are kept. The old attribute is removed from the edit target, or blocked if
    it is also authored in other layers.
    """
    prim = attr.GetPrim()
    new_attr = prim.GetAttribute(new_name)
    with Usd.EditContext(prim.GetStage(), edit_target):
        if not new_attr.HasAuthoredValue():
            # Only an authored default needs to move, and only if the new attribute's fallback would not resolve to it
            if attr.GetResolveInfo(Usd.TimeCode.Default()).GetSource() == Usd.ResolveInfoSourceDefault:
                default = attr.Get(Usd.TimeCode.Default())
                if default != prim.GetPrimDefinition().GetAttributeFallbackValue(new_name):
                    new_attr.Set(default)
            for time in attr.GetTimeSamples():
                new_attr.Set(attr.Get(time), time)
        if all(spec.layer == edit_target.GetLayer() for spec in attr.GetPropertyStack()):
            return prim.RemoveProperty(attr.GetName())
        attr.Block()
    return True


def _fixers() -> list | None:
    if not SUPPORTS_PYTHON_FIXERS:
        return None

    def can_fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        attr = error.GetSites()[0].GetProperty()
        return bool(attr) and renamed_to(attr.GetPrim(), attr.GetName()) is not None

    def fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        attr = error.GetSites()[0].GetProperty()
        return rename_attribute(attr, renamed_to(attr.GetPrim(), attr.GetName()), edit_target)

    return [
        UsdValidation.ValidationFixer(
            name="RenameAttribute",
            description="Move the values of a renamed attribute to its new name.",
            fixerImplFn=fix,
            canApplyFn=can_fix,
            errorName=RENAMED_ATTRIBUTE_ERROR,
        )
    ]


register_prim_validator("RenamedAttributesValidator", native_prim_task(check_renamed_attributes), _fixers())
