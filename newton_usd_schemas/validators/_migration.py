# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Sdf, Usd

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
RENAMED_API_SCHEMAS_VALIDATOR = validator_name("RenamedAPISchemasValidator")
RENAMED_API_SCHEMA_ERROR = "RenamedAPISchema"

# Renamed attributes, by the API schema that defines their new names. The validator's schemaTypes
# and keywords in plugInfo.json must list the same schemas.
RENAMED_ATTRIBUTES: dict[str, dict[str, str]] = {
    "NewtonPointsDeformableSimAPI": {"physics:masses": "newton:masses"},
}


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
    other opinions also author it. Returns False, without authoring anything, if the values cannot be moved.
    """
    prim = attr.GetPrim()
    new_attr = prim.GetAttribute(new_name)
    if attr.GetTypeName() != new_attr.GetTypeName():
        return False
    # Gather every value before authoring any, so a migration cannot stop part way and look complete when retried
    values = []
    if not new_attr.HasAuthoredValue():
        # Only an authored default needs to move, and only if the new attribute's fallback would not resolve to it
        if attr.GetResolveInfo(Usd.TimeCode.Default()).GetSource() == Usd.ResolveInfoSourceDefault:
            default = attr.Get(Usd.TimeCode.Default())
            if default != prim.GetPrimDefinition().GetAttributeFallbackValue(new_name):
                values.append((Usd.TimeCode.Default(), default))
        for time in attr.GetTimeSamples():
            value = attr.Get(time)
            values.append((Usd.TimeCode(time), Sdf.ValueBlock() if value is None else value))
    # Removing the old attribute only suppresses opinions authored on this prim in the edit target, not ones that
    # arrive through references, even from the same layer
    path = edit_target.MapToSpecPath(attr.GetPath())
    local = all(spec.layer == edit_target.GetLayer() and spec.path == path for spec in attr.GetPropertyStack())
    with Usd.EditContext(prim.GetStage(), edit_target):
        for time, value in values:
            new_attr.Set(value, time)
        if local:
            return prim.RemoveProperty(attr.GetName())
        attr.Block()
    return True


def _attribute_fixers() -> list | None:
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


register_prim_validator("RenamedAttributesValidator", native_prim_task(check_renamed_attributes), _attribute_fixers())


# Renamed API schemas, from their old names to their new ones. Attributes that a renamed schema
# also renames belong in RENAMED_ATTRIBUTES, under the new schema name.
RENAMED_API_SCHEMAS: dict[str, str] = {}


def authored_api_schemas(prim: Usd.Prim) -> list[str]:
    """Return the API schemas that layers apply to the prim, excluding those built into other schemas."""
    schemas: list[str] = []
    for spec in reversed(prim.GetPrimStack()):
        if spec.HasInfo("apiSchemas"):
            schemas = list(spec.GetInfo("apiSchemas").ApplyOperations(schemas))
    return schemas


def check_renamed_api_schemas(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    findings = []
    for old in authored_api_schemas(prim):
        new = RENAMED_API_SCHEMAS.get(old)
        if new is None:
            continue
        if Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(old):
            message = f"{old} on <{prim.GetPath()}> is deprecated. Use {new} instead."
            findings.append(Finding(RENAMED_API_SCHEMA_ERROR, prim, message, UsdValidation.ValidationErrorType.Warn))
        else:
            message = f"{old} on <{prim.GetPath()}> was renamed to {new}, so it no longer applies."
            findings.append(Finding(RENAMED_API_SCHEMA_ERROR, prim, message))
    return findings


def _replace_in_list_op(list_op: Sdf.TokenListOp, old: str, new: str) -> bool:
    replaced = False
    for field in ("explicitItems", "prependedItems", "appendedItems"):
        items = list(getattr(list_op, field))
        if old in items:
            setattr(list_op, field, list(dict.fromkeys(new if item == old else item for item in items)))
            replaced = True
    return replaced


def rename_api_schema(prim: Usd.Prim, old: str, new: str, edit_target: Usd.EditTarget) -> bool:
    """Replace a renamed API schema with its new name, authoring in the edit target.

    Where the edit target applies the old schema, the new one takes its place in the list. If other layers also apply
    it, the edit target deletes the old schema and prepends the new one.
    """
    layer = edit_target.GetLayer()
    path = edit_target.MapToSpecPath(prim.GetPath())
    spec = layer.GetPrimAtPath(path)
    if spec and spec.HasInfo("apiSchemas"):
        list_op = spec.GetInfo("apiSchemas")
        if _replace_in_list_op(list_op, old, new):
            spec.SetInfo("apiSchemas", list_op)
    schemas = authored_api_schemas(prim)
    if old in schemas:
        spec = spec or Sdf.CreatePrimInLayer(layer, path)
        list_op = spec.GetInfo("apiSchemas") if spec.HasInfo("apiSchemas") else Sdf.TokenListOp()
        list_op.deletedItems = [*list_op.deletedItems, old]
        if new not in schemas:
            list_op.prependedItems = [new, *list_op.prependedItems]
        spec.SetInfo("apiSchemas", list_op)
    return old not in authored_api_schemas(prim)


def _api_schema_fixers() -> list | None:
    if not SUPPORTS_PYTHON_FIXERS:
        return None

    def renamed(prim: Usd.Prim) -> list[str]:
        return [schema for schema in authored_api_schemas(prim) if schema in RENAMED_API_SCHEMAS] if prim else []

    def can_fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        return bool(renamed(error.GetSites()[0].GetPrim()))

    def fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        prim = error.GetSites()[0].GetPrim()
        return all(rename_api_schema(prim, old, RENAMED_API_SCHEMAS[old], edit_target) for old in renamed(prim))

    return [
        UsdValidation.ValidationFixer(
            name="RenameAPISchema",
            description="Replace a renamed API schema with its new name.",
            fixerImplFn=fix,
            canApplyFn=can_fix,
            errorName=RENAMED_API_SCHEMA_ERROR,
        )
    ]


register_prim_validator("RenamedAPISchemasValidator", native_prim_task(check_renamed_api_schemas), _api_schema_fixers())
