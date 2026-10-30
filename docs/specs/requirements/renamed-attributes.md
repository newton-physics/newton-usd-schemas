# renamed-attributes

| Code          | MIGRATION.001            |
|---------------|--------------------------|
| Version       | 1.0.0                    |
| Compatibility | {compatibility}`other`   |
| Tags          | {tag}`correctness`       |

## Summary

Attributes that a breaking change to a Newton schema renamed must be authored with their new names.

## Description

When a breaking change renames an attribute of a Newton schema, content authored before the change keeps the old name. This requirement applies to prims with the schema applied, unless another schema applied to the prim defines the old name. It covers these attributes:

| Schema                         | Old name         | New name        |
|--------------------------------|------------------|-----------------|
| `NewtonPointsDeformableSimAPI` | `physics:masses` | `newton:masses` |

## Why is it required?

* Newton only reads the new name, so values authored with the old name are silently ignored.

## Examples

### Invalid: The masses use the old name

```usd
#usda 1.0

def Points "Particles" (
    prepend apiSchemas = ["NewtonPointsDeformableSimAPI"]
)
{
    point3f[] points = [(0, 0, 0), (0, 0, 0.1)]
    float[] physics:masses = [0.2, 0.2]
}
```

### Valid: The masses use the new name

```usd
#usda 1.0

def Points "Particles" (
    prepend apiSchemas = ["NewtonPointsDeformableSimAPI"]
)
{
    point3f[] points = [(0, 0, 0), (0, 0, 0.1)]
    float[] newton:masses = [0.2, 0.2]
}
```

### Valid: The old name is blocked

```usd
#usda 1.0

def Points "Particles" (
    prepend apiSchemas = ["NewtonPointsDeformableSimAPI"]
)
{
    point3f[] points = [(0, 0, 0), (0, 0, 0.1)]
    float[] physics:masses = None
    float[] newton:masses = [0.2, 0.2]
}
```

## How to comply

Rename the attribute. The validators can do this automatically: the `usd-validation-nvidia` rule suggests it, and so does the `UsdValidation` fixer on OpenUSD 26.11 or newer. The fix moves the default value and time samples to the new name, unless it already has authored values, and then removes the old attribute from the edit target, or blocks it if it is also authored in other layers.
