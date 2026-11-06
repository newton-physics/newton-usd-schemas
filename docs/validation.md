# Validation

Only the Newton schemas can declare what Newton requires of the content that uses them, so they provide their own validators, starting with a subset of the schemas. Each validator's `doc` metadata describes what it checks.

The validators can be run in two ways: with OpenUSD's [UsdValidation](https://openusd.org/release/api/usd_validation_page_front.html) framework, or as [usd-validation-nvidia](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia) rules.

## OpenUSD versions

- The UsdValidation validators require OpenUSD 26.05 or newer, and their fixers require OpenUSD 26.11 or newer. With older OpenUSD versions the validators are not registered, and the schemas work as usual.
- The usd-validation-nvidia rules, including their fixes, work with every OpenUSD version the schemas support. They require the `validation` extra:

```bash
pip install 'newton-usd-schemas[usd,validation]'
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

## Validating with usd-validation-nvidia

With the `validation` extra installed, `usd-validation-nvidia` discovers the Newton rules automatically. Each rule runs one of the validators, using the `UsdValidation` validator when it is registered, and otherwise the same check in Python. The rules are grouped by topic into categories, such as `NewtonCollision` and `NewtonJoints`. Rules that are not specific to the Newton schemas, such as `AttributeHardLimitsChecker`, are in the `Basic` category, alongside the other general rules.

### Command line

Run all of the default rules, including the Newton rules:

```bash
nvidia_usd_validate /tmp/my_robot.usda
```

Run only the rules in a category:

```bash
nvidia_usd_validate --no-init-rules --category NewtonJoints /tmp/my_robot.usda
```

Apply the available fixes:

```bash
nvidia_usd_validate --no-init-rules --category NewtonCollision --fix /tmp/my_robot.usda
```

Run all of the default rules, but skip the Newton joint rules:

```bash
nvidia_usd_validate --disable-category NewtonJoints /tmp/my_robot.usda
```

### Python

A `ValidationEngine` created with default arguments runs every registered rule, including the Newton rules. To run only the rules in a category:

```python
from usd_validation_nvidia import CategoryRuleRegistry, IssueFixer, ValidationEngine

engine = ValidationEngine(init_rules=False)
for rule in CategoryRuleRegistry().get_rules("NewtonCollision"):
    engine.enable_rule(rule)

results = engine.validate("/tmp/my_robot.usda")
for issue in results.issues():
    print(issue.severity.name, issue.rule.__name__, issue.message)
```

Apply the available fixes:

```python
fixer = IssueFixer("/tmp/my_robot.usda")
fixer.fix(results.issues())
fixer.save()
```
