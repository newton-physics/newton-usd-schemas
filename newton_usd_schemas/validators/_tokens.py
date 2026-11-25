# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Sdf, Usd

from ._registration import SUPPORTS_PYTHON_VALIDATORS, Finding, TimeRange, UsdValidation, native_prim_task, register_prim_validator, validator_name

ATTRIBUTE_ALLOWED_TOKENS_VALIDATOR = validator_name("AttributeAllowedTokensValidator")

# OpenUSD's own allowed tokens validator, proposed in PixarAnimationStudios/OpenUSD#4317. Once the minimum supported
# OpenUSD release includes it, deprecate this validator, and later remove it along with its plugInfo.json entry.
OPENUSD_ALLOWED_TOKENS_VALIDATOR = "usdValidation:AttributeAllowedTokens"

# The value types OpenUSD's validator checks, along with arrays of them
_TOKEN_TYPES = (Sdf.ValueTypeNames.Token, Sdf.ValueTypeNames.String)


def _disallowed_token(value: str | list[str], allowed_tokens: list[str]) -> str | None:
    """Return the first token in the value that is not one of the allowed tokens, or None if there is none."""
    tokens = [value] if isinstance(value, str) else value
    return next((token for token in tokens if token not in allowed_tokens), None)


def check_attribute_allowed_tokens(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    findings = []
    definition = prim.GetPrimDefinition()
    for attr in prim.GetAuthoredAttributes():
        allowed_tokens = attr.GetMetadata("allowedTokens")
        if not allowed_tokens or attr.GetTypeName().scalarType not in _TOKEN_TYPES:
            continue
        allowed_tokens = [str(token) for token in allowed_tokens]
        # A fallback that is not one of the allowed tokens is a sentinel, otherwise every prim that does not author the
        # attribute would be invalid
        fallback = definition.GetAttributeFallbackValue(attr.GetName())
        times = [Usd.TimeCode.Default()] if time_range.include_default else []
        times += [Usd.TimeCode(t) for t in attr.GetTimeSamplesInInterval(time_range.interval)]
        for time in times:
            value = attr.Get(time)
            if value is None or (fallback is not None and value == fallback):
                continue
            token = _disallowed_token(value, allowed_tokens)
            if token is None:
                continue
            when = "" if time.IsDefault() else f" at time {time.GetValue()}"
            verb = "is" if isinstance(value, str) else "contains"
            allowed = ", ".join(f"'{allowed_token}'" for allowed_token in allowed_tokens)
            findings.append(
                Finding(
                    "AttributeTokenNotAllowed",
                    attr,
                    f"{attr.GetName()} on <{prim.GetPath()}> {verb} '{token}'{when}, which is not one of its allowed tokens [{allowed}].",
                )
            )
            break
    return findings


def _task():
    if not SUPPORTS_PYTHON_VALIDATORS:
        return None
    registry = UsdValidation.ValidationRegistry()
    if not registry.GetValidatorMetadata(OPENUSD_ALLOWED_TOKENS_VALIDATOR):
        return native_prim_task(check_attribute_allowed_tokens)
    # Defer to OpenUSD's validator where it exists, so that selecting this validator by keyword keeps working
    openusd_validator = registry.GetOrLoadValidatorByName(OPENUSD_ALLOWED_TOKENS_VALIDATOR)
    return lambda prim, time_range: openusd_validator.Validate(prim, time_range)


register_prim_validator("AttributeAllowedTokensValidator", _task())
