# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math

from pxr import Usd, UsdPhysics, UsdShade

from ._registration import Finding, TimeRange, native_prim_task, register_prim_validator, validator_name

MATERIAL_PAIR_VALIDATOR = validator_name("MaterialPairValidator")

MATERIAL_PAIR_RELATIONSHIPS = ("newton:materialPair:material0", "newton:materialPair:material1")
MATERIAL_PAIR_COEFFICIENTS = (
    "newton:materialPair:mu",
    "newton:materialPair:muStatic",
    "newton:materialPair:muTorsional",
    "newton:materialPair:muRolling",
    "newton:materialPair:restitution",
)


def _has_default_opinion(attr: Usd.Attribute) -> bool:
    return any(spec.HasDefaultValue() for spec in attr.GetPropertyStack())


# Not time dependent: Newton reads only the default time value of each coefficient, so the check reads it regardless of
# the time range. Negative and NaN coefficients are left to the hard limits validator.
def check_material_pair(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    if not prim.HasAPI("NewtonMaterialPairAPI"):
        return []
    findings = [finding for name in MATERIAL_PAIR_RELATIONSHIPS if (finding := _check_material(prim, name))]

    values = {}
    authored = False
    for name in MATERIAL_PAIR_COEFFICIENTS:
        attr = prim.GetAttribute(name)
        # Newton reads every coefficient with an opinion, including a blocked one or one with only time samples
        if not attr.HasAuthoredValueOpinion():
            continue
        authored = True
        value = attr.Get()
        if value is None:
            findings.append(
                Finding(
                    "MaterialPairCoefficientWithoutDefault",
                    attr,
                    f"{name} on <{prim.GetPath()}> is blocked, but Newton requires a value at the default time for an authored coefficient.",
                )
            )
        elif not _has_default_opinion(attr):
            findings.append(
                Finding(
                    "MaterialPairCoefficientWithoutDefault",
                    attr,
                    f"{name} on <{prim.GetPath()}> has only time samples, but Newton reads only the value at the default time.",
                )
            )
        elif math.isinf(value):
            findings.append(
                Finding(
                    "MaterialPairCoefficientNotFinite",
                    attr,
                    f"{name} on <{prim.GetPath()}> is {value:g}, but an authored coefficient must be finite.",
                )
            )
        elif value >= 0:
            values[name] = (attr, value)

    if not authored:
        findings.append(
            Finding(
                "MaterialPairNoCoefficients",
                prim,
                f"NewtonMaterialPairAPI on <{prim.GetPath()}> has no authored coefficient, but must author at least one of "
                + ", ".join(MATERIAL_PAIR_COEFFICIENTS)
                + ".",
            )
        )

    mu = values.get("newton:materialPair:mu")
    mu_static = values.get("newton:materialPair:muStatic")
    if mu and mu_static and mu_static[1] < mu[1]:
        findings.append(
            Finding(
                "MaterialPairStaticFrictionBelowFriction",
                mu_static[0],
                f"newton:materialPair:muStatic on <{prim.GetPath()}> is {mu_static[1]:g}, which is less than newton:materialPair:mu ({mu[1]:g}). "
                "The static friction coefficient must be greater than or equal to the Coulomb friction coefficient.",
            )
        )
    return findings


def _check_material(prim: Usd.Prim, name: str) -> Finding | None:
    rel = prim.GetRelationship(name)
    targets = rel.GetForwardedTargets()
    if len(targets) != 1:
        return Finding("MaterialPairTargetCount", rel, f"{name} on <{prim.GetPath()}> has {len(targets)} targets, but must have exactly 1.")
    material = prim.GetStage().GetPrimAtPath(targets[0])
    if not material or not material.IsA(UsdShade.Material) or not material.HasAPI(UsdPhysics.MaterialAPI):
        return Finding(
            "MaterialPairInvalidTarget",
            rel,
            f"{name} on <{prim.GetPath()}> targets <{targets[0]}>, which is not a Material with PhysicsMaterialAPI applied.",
        )
    return None


register_prim_validator("MaterialPairValidator", native_prim_task(check_material_pair))
