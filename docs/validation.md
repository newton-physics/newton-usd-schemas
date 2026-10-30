# Validation

Only the Newton schemas can declare what Newton requires of the content that uses them, so they provide their own validators for OpenUSD's [UsdValidation](https://openusd.org/release/api/usd_validation_page_front.html) framework, starting with a subset of the schemas. Each validator's `doc` metadata describes what it checks.

## OpenUSD versions

The validators require OpenUSD 26.05 or newer, and their fixers require OpenUSD 26.11 or newer. With older OpenUSD versions the validators are not registered, and the schemas work as usual.

```bash
pip install newton-usd-schemas[usd]
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

`NewtonValidators` selects all of the validators. To run a subset, use the keyword for a topic, such as `NewtonJoints`, or the name of the schema a validator checks, such as `NewtonMimicAPI`. Schemas that build on some of the Newton schemas can use the schema names to select only the validators for the schemas they use.

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
