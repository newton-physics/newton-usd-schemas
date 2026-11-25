# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import SUPPORTS_PYTHON_VALIDATORS, Finding, TimeRange, UsdValidation, native_prim_task, register_prim_validator, validator_name

API_SCHEMA_APPLICABILITY_VALIDATOR = validator_name("APISchemaApplicabilityValidator")

# OpenUSD's own API schema applicability validator, proposed in PixarAnimationStudios/OpenUSD#4356. Once the
# minimum supported OpenUSD release includes it, deprecate this validator, and later remove it along with its
# plugInfo.json entry.
OPENUSD_API_SCHEMA_APPLICABILITY_VALIDATOR = "usdValidation:APISchemaApplicability"


def why_not_applicable(prim: Usd.Prim, schema: str) -> str | None:
    """Return why the applied API schema cannot be applied to the prim, or None if it can be.

    Schemas that are not registered applied API schemas, and malformed instance names, are not checked.
    """
    name, instance = Usd.SchemaRegistry.GetTypeNameAndInstance(schema)
    kind = Usd.SchemaRegistry.GetSchemaKind(name)
    schema_type = Usd.SchemaRegistry.GetAPITypeFromSchemaTypeName(name)
    if kind == Usd.SchemaKind.SingleApplyAPI and not instance:
        result = prim.CanApplyAPI(schema_type)
    elif kind == Usd.SchemaKind.MultipleApplyAPI and instance:
        result = prim.CanApplyAPI(schema_type, instance)
    else:
        return None
    return None if result else result.whyNot


# Only the API schemas authored on the prim are checked, as content does not choose the ones built into its type or
# into other schemas, nor the ones applied automatically
def check_api_schema_applicability(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    findings = []
    for schema in prim.GetPrimTypeInfo().GetAppliedAPISchemas():
        why_not = why_not_applicable(prim, schema)
        if why_not is not None:
            message = f"API schema '{schema}' is applied to prim <{prim.GetPath()}>, but cannot be applied to it. {why_not}"
            findings.append(Finding("APISchemaNotApplicable", prim, message))
    return findings


def _task():
    if not SUPPORTS_PYTHON_VALIDATORS:
        return None
    registry = UsdValidation.ValidationRegistry()
    if not registry.GetValidatorMetadata(OPENUSD_API_SCHEMA_APPLICABILITY_VALIDATOR):
        return native_prim_task(check_api_schema_applicability)
    # Defer to OpenUSD's validator where it exists, so that selecting this validator by keyword keeps working
    openusd_validator = registry.GetOrLoadValidatorByName(OPENUSD_API_SCHEMA_APPLICABILITY_VALIDATOR)
    return lambda prim, time_range: openusd_validator.Validate(prim, time_range)


register_prim_validator("APISchemaApplicabilityValidator", _task())
