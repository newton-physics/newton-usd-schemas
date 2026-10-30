# mimic-joint-target

| Code          | MIMIC.001                |
|---------------|--------------------------|
| Version       | 1.0.0                    |
| Compatibility | {compatibility}`other`   |
| Tags          | {tag}`correctness`       |

## Summary

`newton:mimicJoint` must target exactly one other joint, of the same joint type as the follower.

## Description

`NewtonMimicAPI` constrains a follower joint to track a leader joint, which is the target of the `newton:mimicJoint` relationship. The leader must be a different `PhysicsJoint` prim of the same type as the follower.

A disabled mimic is not validated: when `newton:mimicEnabled` is false at the default time and at every time sample, the constraint has no effect, so its leader does not matter.

## Why is it required?

* Without exactly one leader, the mimic constraint is undefined.
* The mimic coefficients are expressed in the follower's position units, so a leader of a different joint type has no well-defined units.

## Examples

### Invalid: There is no leader

```usd
#usda 1.0

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
}
```

### Invalid: There is more than one leader

```usd
#usda 1.0

def PhysicsRevoluteJoint "Leader"
{
}

def PhysicsRevoluteJoint "OtherLeader"
{
}

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
    rel newton:mimicJoint = [</Leader>, </OtherLeader>]
}
```

### Invalid: The leader is not a joint

```usd
#usda 1.0

def Xform "Leader"
{
}

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
    rel newton:mimicJoint = </Leader>
}
```

### Invalid: The leader is a different joint type

```usd
#usda 1.0

def PhysicsPrismaticJoint "Leader"
{
}

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
    rel newton:mimicJoint = </Leader>
}
```

### Valid: The leader and follower are the same joint type

```usd
#usda 1.0

def PhysicsRevoluteJoint "Leader"
{
}

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
    rel newton:mimicJoint = </Leader>
}
```

### Valid: The mimic is disabled

```usd
#usda 1.0

def PhysicsRevoluteJoint "Follower" (
    prepend apiSchemas = ["NewtonMimicAPI"]
)
{
    bool newton:mimicEnabled = false
}
```

## How to comply

Target exactly one other joint of the same type with `newton:mimicJoint`, or disable the mimic.
