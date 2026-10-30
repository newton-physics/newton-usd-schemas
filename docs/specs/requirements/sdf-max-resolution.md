# sdf-max-resolution

| Code          | SDF.001                  |
|---------------|--------------------------|
| Version       | 1.0.0                    |
| Compatibility | {compatibility}`other`   |
| Tags          | {tag}`correctness`       |

## Summary

`newton:sdfMaxResolution` must be divisible by 8.

## Description

`NewtonSDFCollisionAPI` configures the signed distance field (SDF) generated for a collision shape. `newton:sdfMaxResolution` is the maximum dimension of the sparse SDF grid, which is allocated in 8x8x8 tiles.

## Why is it required?

* Newton rejects values that are not divisible by 8 and falls back to the default resolution, so the authored resolution is silently ignored.

## Examples

### Invalid: The resolution is not divisible by 8

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonSDFCollisionAPI"]
)
{
    uniform int newton:sdfMaxResolution = 100
}
```

### Valid: The resolution is divisible by 8

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonSDFCollisionAPI"]
)
{
    uniform int newton:sdfMaxResolution = 104
}
```

## How to comply

Round `newton:sdfMaxResolution` to a multiple of 8. The validators can do this automatically: the `usd-validation-nvidia` rule suggests rounding to the nearest multiple of 8, and so does the `UsdValidation` fixer on OpenUSD 26.11 or newer.
