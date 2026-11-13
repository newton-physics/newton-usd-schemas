# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

from pxr import Usd

from ._registration import SUPPORTS_PYTHON_FIXERS, Finding, TimeRange, UsdValidation, native_prim_task, register_prim_validator, validator_name

KAMINO_SCC_SOLVER_VALIDATOR = validator_name("KaminoSccSolverValidator")
SCC_SOLVER_SELECTION_WARNING = "KaminoSccSolverNotSelected"


def check_kamino_scc_solver(prim: Usd.Prim, time_range: TimeRange) -> list[Finding]:
    if not prim.HasAPI("NewtonKaminoSccSceneAPI"):
        return []
    attr = prim.GetAttribute("newton:kamino:dynamicsSolver")
    value = attr.Get()
    if attr.HasAuthoredValue() or value == "scc":
        return []
    return [
        Finding(
            SCC_SOLVER_SELECTION_WARNING,
            attr,
            f"newton:kamino:dynamicsSolver on <{prim.GetPath()}> is unauthored and resolves to {value!r} "
            "despite NewtonKaminoSccSceneAPI being applied. List NewtonKaminoSccSceneAPI first, "
            'or author newton:kamino:dynamicsSolver = "scc" explicitly to select SCC.',
            severity=UsdValidation.ValidationErrorType.Warn if UsdValidation else None,
        )
    ]


def _fixers() -> list | None:
    if not SUPPORTS_PYTHON_FIXERS:
        return None

    def can_fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        attr = error.GetSites()[0].GetProperty()
        return bool(attr and check_kamino_scc_solver(attr.GetPrim(), TimeRange()))

    def fix(error: UsdValidation.ValidationError, edit_target: Usd.EditTarget, time_code: Usd.TimeCode) -> bool:
        if not can_fix(error, edit_target, time_code):
            return False
        attr = error.GetSites()[0].GetProperty()
        with Usd.EditContext(attr.GetStage(), edit_target):
            return attr.Set("scc")

    return [
        UsdValidation.ValidationFixer(
            name="SelectKaminoSccSolver",
            description='Author newton:kamino:dynamicsSolver = "scc" to select SCC explicitly.',
            fixerImplFn=fix,
            canApplyFn=can_fix,
            errorName=SCC_SOLVER_SELECTION_WARNING,
        )
    ]


register_prim_validator("KaminoSccSolverValidator", native_prim_task(check_kamino_scc_solver), _fixers())
