# Validation

Only the Newton schemas can declare what Newton requires of the content that uses them, so they provide their own validators, starting with a subset of the schemas. Each requirement is specified by a page in [`specs/requirements`](specs/requirements), with examples of valid and invalid content, and the requirements are grouped by schema in [`specs/capabilities`](specs/capabilities).

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

With the `validation` extra installed, `usd-validation-nvidia` discovers the Newton rules automatically. Each rule implements one requirement, and belongs to the capability for the schema it checks and to a category for its topic. For example, `MimicJointChecker` implements `org.newton-physics.MIMIC.001`, in the `org.newton-physics.newton_mimic` capability and the `NewtonJoints` category. Rules that are not specific to the Newton schemas, such as `AttributeHardLimitsChecker`, are in the `Basic` category, alongside the other general rules.

### The Newton-Simulation profile

The `org.newton-physics.Newton-Simulation` profile selects everything content needs to simulate correctly in Newton, through its [`newton_simulation`](specs/features/newton_simulation.md) feature: the Newton requirements, and the `UsdPhysics` requirements that Newton relies on, which usd-validation-nvidia checks.

### Command line

Validate against the profile:

```bash
nvidia_usd_validate --profile org.newton-physics.Newton-Simulation /tmp/my_robot.usda
```

Run a single capability:

```bash
nvidia_usd_validate --capability org.newton-physics.newton_mimic /tmp/my_robot.usda
```

Apply the available fixes:

```bash
nvidia_usd_validate --capability org.newton-physics.newton_sdf_collision --fix /tmp/my_robot.usda
```

Run a single requirement:

```bash
nvidia_usd_validate --requirement org.newton-physics.LIMITS.001 /tmp/my_robot.usda
```

Run all of the default rules, including the Newton rules, but skip the Newton joint rules:

```bash
nvidia_usd_validate --disable-category NewtonJoints /tmp/my_robot.usda
```

### Python

A `ValidationEngine` created with default arguments runs every registered rule, including the Newton rules. To validate against the profile:

```python
from usd_validation_nvidia import ProfileRegistry, ValidationEngine

engine = ValidationEngine(init_rules=False)
engine.enable_profile(ProfileRegistry().find("org.newton-physics.Newton-Simulation"))
results = engine.validate("/tmp/my_robot.usda")
```

To run a single capability:

```python
from usd_validation_nvidia import CapabilityRegistry, IssueFixer, ValidationEngine

engine = ValidationEngine(init_rules=False)
engine.enable_capability(CapabilityRegistry().find("org.newton-physics.newton_sdf_collision"))

results = engine.validate("/tmp/my_robot.usda")
for issue in results.issues():
    print(issue.severity.name, issue.requirement.code, issue.message)
```

Apply the available fixes:

```python
fixer = IssueFixer("/tmp/my_robot.usda")
fixer.fix(results.issues())
fixer.save()
```
