# attribute-hard-limits

| Code          | LIMITS.001               |
|---------------|--------------------------|
| Version       | 1.0.0                    |
| Compatibility | {compatibility}`OpenUSD` |
| Tags          | {tag}`correctness`       |

## Summary

Authored attribute values must lie within the attribute's hard `limits`, unless they equal the schema fallback value.

## Description

The `limits` metadata declares soft limits, the typical useful range of an attribute's values, and hard limits, the range its values must lie within. This requirement applies to every authored value at the default time and at each time sample. NaN never lies within the hard limits.

A schema may declare a fallback value outside the hard limits to act as a sentinel. For example, `newton:contactGap` has a hard minimum of 0 and a fallback of `-inf`, meaning "use the engine default". A value equal to the schema fallback is always accepted.

Soft limits are only a hint for user interfaces and are not validated.

## Why is it required?

* Values outside the hard limits are not meaningful to the consuming application, which may reject them or behave unpredictably.

## Examples

### Invalid: The value is below the hard minimum

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonCollisionAPI"]
)
{
    float newton:contactGap = -0.01
}
```

### Invalid: The value is NaN

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonCollisionAPI"]
)
{
    float newton:contactGap = nan
}
```

### Valid: The value is within the hard limits

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonCollisionAPI"]
)
{
    float newton:contactGap = 0.01
}
```

### Valid: The value is the sentinel fallback

```usd
#usda 1.0

def Cube "Collider" (
    prepend apiSchemas = ["NewtonCollisionAPI"]
)
{
    float newton:contactGap = -inf
}
```

## How to comply

Author a value within the hard limits, or the schema fallback value.
