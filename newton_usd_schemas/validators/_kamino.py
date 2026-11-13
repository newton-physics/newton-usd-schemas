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
    has_default = attr.GetResolveInfo(Usd.TimeCode.Default()).GetSource() == Usd.ResolveInfoSourceDefault
    if has_default or value == "scc":
        return []
    return [
        Finding(
            SCC_SOLVER_SELECTION_WARNING,
            attr,
            f"newton:kamino:dynamicsSolver on <{prim.GetPath()}> has no authored default and resolves to {value!r} "
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
        if not attr or not check_kamino_scc_solver(attr.GetPrim(), TimeRange()) or not edit_target.IsValid():
            return False
        layer = edit_target.GetLayer()
        prim = attr.GetPrim()
        path = edit_target.MapToSpecPath(attr.GetPath())
        if not layer.permissionToEdit or not layer.permissionToSave or not path or prim.IsInstanceProxy():
            return False
        stage = attr.GetStage()
        # Keep the index alive while inspecting its node references.
        index = prim.ComputeExpandedPrimIndex()
        nodes = [index.rootNode]
        while nodes:
            node = nodes.pop()
            if node.path == path.GetParentPath() and layer in node.layerStack.layers:
                break
            nodes.extend(node.children)
        else:
            return False
        if attr.GetResolveInfo().ValueIsBlocked():
            # A weaker opinion cannot replace a stronger value block.
            block = next(spec for spec in attr.GetPropertyStack() if spec.HasDefaultValue())
            if block.layer == layer and block.path == path:
                return True
            layers = stage.GetLayerStack()
            return layer in layers and (block.layer not in layers or layers.index(layer) < layers.index(block.layer))
        return True

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
