# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Sdf, Tf, Usd

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


def _can_override(stage: Usd.Stage, edit_layer: Sdf.Layer, layer: Sdf.Layer) -> bool:
    """Whether authoring in the edit layer, at the paths of the layer's opinions, overrides them."""
    if layer == edit_layer:
        return True
    layers = stage.GetLayerStack()
    return edit_layer in layers and layer in layers and layers.index(edit_layer) < layers.index(layer)


def _convert(values: list, type_name: Sdf.ValueTypeName) -> list | None:
    """Convert the values to the type, as `Usd.Attribute.Set` does, or return None if one cannot be converted."""
    stage = Usd.Stage.CreateInMemory()
    scratch = stage.DefinePrim("/Scratch").CreateAttribute("value", type_name)
    converted = []
    try:
        for value in values:
            if isinstance(value, Sdf.ValueBlock):
                converted.append(value)
            elif scratch.Set(value):
                converted.append(scratch.Get())
            else:
                return None
    except Tf.ErrorException:
        return None
    return converted


def rename_attribute(attr: Usd.Attribute, new_name: str, edit_target: Usd.EditTarget) -> bool:
    """Move the authored values of a renamed attribute to its new name, where they are authored.

    Each opinion on the old name is migrated where it is authored, which may be inside a variant or a referenced prim.
    In the edit target's layer, it is renamed, and in a weaker layer of the stage's layer stack, it is overridden at the
    same path in the edit target's layer. Values already authored on the new name are kept, and values are converted
    to the new attribute's type, as `Usd.Attribute.Set` does. Returns False, without authoring anything, if an opinion
    is authored where the edit target cannot override it, such as another asset, or if a value cannot be converted.
    """
    prim = attr.GetPrim()
    layer = edit_target.GetLayer()
    new_attr = prim.GetAttribute(new_name)
    type_name = new_attr.GetTypeName()
    specs = attr.GetPropertyStack()
    if not all(_can_override(prim.GetStage(), layer, spec.layer) for spec in specs):
        return False
    # Gather and convert every value before authoring any, so a migration cannot stop part way and look complete when
    # retried. Values already authored on the new name win, so nothing moves.
    entries = []
    if not new_attr.HasAuthoredValue():
        defaults = [index for index, spec in enumerate(specs) if spec.HasDefaultValue()]
        fallback = prim.GetPrimDefinition().GetAttributeFallbackValue(new_name)
        for index, spec in enumerate(specs):
            if spec.HasDefaultValue():
                entries.append((index, None, spec.default))
            for time, value in (spec.GetInfo("timeSamples") if spec.HasInfo("timeSamples") else {}).items():
                entries.append((index, time, value))
        converted = _convert([value for _, _, value in entries], type_name)
        if converted is None:
            return False
        # The weakest default does not need to move if the new attribute's fallback already resolves to it
        entries = [
            (index, time, value)
            for (index, time, _), value in zip(entries, converted)
            if not (time is None and index == defaults[-1] and value == fallback)
        ]
    with Sdf.ChangeBlock():
        for index, spec in enumerate(specs):
            owner = layer.GetPrimAtPath(spec.owner.path) or Sdf.CreatePrimInLayer(layer, spec.owner.path)
            moves = [(time, value) for entry_index, time, value in entries if entry_index == index]
            existing = owner.attributes.get(new_name)
            # A new value authored at the same path by a stronger opinion already shadows this one
            if moves and not (existing and (existing.HasDefaultValue() or existing.HasInfo("timeSamples"))):
                new_spec = existing or Sdf.AttributeSpec(owner, new_name, type_name)
                for time, value in moves:
                    if time is None:
                        new_spec.default = value
                    else:
                        layer.SetTimeSample(new_spec.path, time, value)
            if spec.layer == layer:
                owner.RemoveProperty(spec)
            else:
                block = owner.attributes.get(attr.GetName()) or Sdf.AttributeSpec(owner, attr.GetName(), spec.typeName)
                block.ClearInfo("timeSamples")
                block.default = Sdf.ValueBlock()
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
    for field in ("explicitItems", "addedItems", "prependedItems", "appendedItems", "orderedItems"):
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
