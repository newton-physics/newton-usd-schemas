# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import Finding, TimeRange, native_prim_task, register_prim_validator, validator_name

MIMIC_JOINT_VALIDATOR = validator_name("MimicJointValidator")


def _is_mimic_disabled(prim: Usd.Prim) -> bool:
    """Whether newton:mimicEnabled is false at the default time and at every time sample."""
    attr = prim.GetAttribute("newton:mimicEnabled")
    samples = attr.GetTimeSamples()
    values = [attr.Get(time) for time in samples]
    if not samples or attr.GetResolveInfo(Usd.TimeCode.Default()).GetSource() == Usd.ResolveInfoSourceDefault:
        values.append(attr.Get(Usd.TimeCode.Default()))
    return not any(values)


def check_mimic_joint(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    if not prim.HasAPI("NewtonMimicAPI") or _is_mimic_disabled(prim):
        return []
    rel = prim.GetRelationship("newton:mimicJoint")
    targets = rel.GetForwardedTargets()
    if len(targets) != 1:
        return [
            Finding("MimicJointTargetCount", rel, f"newton:mimicJoint on <{prim.GetPath()}> has {len(targets)} targets, but must have exactly 1.")
        ]

    leader = prim.GetStage().GetPrimAtPath(targets[0])
    if targets[0] == prim.GetPath() or not leader or not leader.IsA("PhysicsJoint"):
        return [
            Finding(
                "MimicJointInvalidTarget",
                rel,
                f"newton:mimicJoint on <{prim.GetPath()}> targets <{targets[0]}>, which is not another PhysicsJoint.",
            )
        ]

    if leader.GetTypeName() != prim.GetTypeName():
        return [
            Finding(
                "MimicJointTypeMismatch",
                rel,
                f"newton:mimicJoint on <{prim.GetPath()}> targets a {leader.GetTypeName()} <{leader.GetPath()}>, "
                f"but the follower is a {prim.GetTypeName()}. The leader and follower must be the same joint type.",
            )
        ]

    return []


register_prim_validator("MimicJointValidator", native_prim_task(check_mimic_joint))
