# Validation

Only the Newton schemas can declare what Newton requires of the content that uses them, so they provide their own validators for OpenUSD's [UsdValidation](https://openusd.org/release/api/usd_validation_page_front.html) framework, starting with a subset of the schemas. Each validator's `doc` metadata describes what it checks.

## OpenUSD versions

The validators require OpenUSD 26.05 or newer, and their fixers require OpenUSD 26.11 or newer. With older OpenUSD versions the validators are not registered, and the schemas work as usual.

```bash
pip install 'newton-usd-schemas[usd]'
```

## Validating with UsdValidation

Importing `newton_usd_schemas` only registers the schemas. Import `newton_usd_schemas.validators` to register the validators too, then select them by keyword:

```python
import newton_usd_schemas.validators  # registers the schemas and the validators
from pxr import Usd, UsdValidation

stage: Usd.Stage = Usd.Stage.Open("/tmp/my_robot.usda")
context = UsdValidation.ValidationContext(keywords=["NewtonValidators"])
errors = context.Validate(stage)
for error in errors:
    print(error.GetErrorAsString())
```

The validators report incompatible content as errors, and deprecated content that still works as warnings. `NewtonValidators` selects all of the validators. To run a subset, use the keyword for a topic, such as `NewtonJoints`, or the name of the schema a validator checks, such as `NewtonMimicAPI`. Schemas that build on some of the Newton schemas can use the schema names to select only the validators for the schemas they use.

For Kamino scenes, `KaminoSccSolverValidator` warns when `NewtonKaminoSccSceneAPI` is applied but an unauthored `newton:kamino:dynamicsSolver` does not resolve to `"scc"`. List the SCC API first, omit the redundant base Kamino API, or explicitly author the solver choice. The `SelectKaminoSccSolver` fixer authors `"scc"` in the chosen edit layer. Explicitly authored solver choices are respected. Select this validator with the `NewtonKamino` or `NewtonKaminoSccSceneAPI` keyword.

To run a single validator, load it by name:

```python
registry = UsdValidation.ValidationRegistry()
validator = registry.GetOrLoadValidatorByName("newton_usd_schemas.validators:MimicJointValidator")
print(validator.GetMetadata().doc)
joint_errors = validator.Validate(stage.GetPrimAtPath("/robot/joints/finger_right"))
```

With OpenUSD 26.11 or newer, apply the fixers attached to the errors. Each fixer saves the edit target layer after a successful fix:

```python
edit_target = stage.GetEditTarget()
for error in errors:
    for fixer in error.GetFixersByErrorName():
        if fixer.CanApplyFix(error, edit_target):
            fixer.ApplyFix(error, edit_target)
```

A validation context validates the stage with its current variant selections, so content in other variants is only found, and fixed, when those variants are selected. A fixer that migrates renamed attributes or schemas does so where each old opinion is authored, including inside variants. It is not applied when an opinion comes from a layer that the edit target cannot override, such as another asset that the stage references, which needs to be validated and fixed itself.
