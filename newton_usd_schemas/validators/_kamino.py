# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import Finding, TimeRange, native_prim_task, register_prim_validator, validator_name

KAMINO_SCC_SOLVER_VALIDATOR = validator_name("KaminoSccSolverValidator")
SCC_SOLVER_SELECTION_ERROR = "KaminoSccSolverNotSelected"


def check_kamino_scc_solver(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    if not prim.HasAPI("NewtonKaminoSccSceneAPI"):
        return []
    attr = prim.GetAttribute("newton:kamino:dynamicsSolver")
    default_time = Usd.TimeCode.Default()
    value = attr.Get(default_time)
    has_default = attr.GetResolveInfo(default_time).GetSource() == Usd.ResolveInfoSourceDefault
    if has_default or value == "scc":
        return []
    return [
        Finding(
            SCC_SOLVER_SELECTION_ERROR,
            attr,
            f"newton:kamino:dynamicsSolver on <{prim.GetPath()}> has no authored default and resolves to {value!r} "
            'despite NewtonKaminoSccSceneAPI being applied. Explicitly author newton:kamino:dynamicsSolver = "scc" '
            "in a layer where it takes effect, or list NewtonKaminoSccSceneAPI first when schema defaults conflict.",
        )
    ]


register_prim_validator("KaminoSccSolverValidator", native_prim_task(check_kamino_scc_solver))
