# Newton Simulation

| Property   | Value   |
|------------|---------|
| Version    | 1.0.0   |
| Dependency | OpenUSD |

## Description

Requirements for content to simulate correctly in Newton. It combines the Newton schema requirements with the `UsdPhysics` requirements that Newton relies on, as checked by usd-validation-nvidia.

## Requirements

| Requirement | Summary |
|-------------|---------|
| [`org.newton-physics.SDF.001`](../requirements/sdf-max-resolution.md) | `newton:sdfMaxResolution` must be divisible by 8. |
| [`org.newton-physics.MIMIC.001`](../requirements/mimic-joint-target.md) | `newton:mimicJoint` must target exactly one other joint, of the same joint type as the follower. |
| [`org.newton-physics.LIMITS.001`](../requirements/attribute-hard-limits.md) | Authored attribute values must lie within the attribute's hard `limits`, unless they equal the schema fallback value. |
| [`com.nvidia.usd.JT.002`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_joints/requirements/joint-body-target-exists.md) | Targets of the `body0` and `body1` relationships of a joint must exist. |
| [`com.nvidia.usd.JT.003`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_joints/requirements/joint-no-multiple-body-targets.md) | The `body0` and `body1` relationships of a joint must not have more than one target. |
| [`com.nvidia.usd.JT.ART.002`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_joints/requirements/articulation-no-nesting.md) | Articulation roots cannot be nested. |
| [`com.nvidia.usd.JT.ART.004`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_joints/requirements/articulation-not-on-static-body.md) | Articulations are not allowed on static bodies. |
| [`com.nvidia.usd.RB.003`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_rigid_bodies/requirements/rigid-body-schema-application.md) | Rigid bodies must be `UsdGeomXformable` prims. |
| [`com.nvidia.usd.RB.009`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_rigid_bodies/requirements/rigid-body-schema-no-skew-matrix.md) | The world transform of a rigid body must not contain skew. |
| [`com.nvidia.usd.RB.COL.004`](https://github.com/NVIDIA-Omniverse/usd-validation-nvidia/blob/v1.23.0/specs/capabilities/physics_bodies/physics_rigid_bodies/requirements/collider-non-uniform-scale.md) | The scale of sphere, capsule, cylinder, cone and points collision shapes must be uniform. |

usd-profiles-nvidia reads the feature from the list below, which only accepts requirement codes and versions. Keep it in sync with the table above.

```{features-table}
SDF.001@1.0.0
MIMIC.001@1.0.0
LIMITS.001@1.0.0
com.nvidia.usd.JT.002@1.0.0
com.nvidia.usd.JT.003@1.0.0
com.nvidia.usd.JT.ART.002@1.0.0
com.nvidia.usd.JT.ART.004@1.0.0
com.nvidia.usd.RB.003@1.0.0
com.nvidia.usd.RB.009@1.0.0
com.nvidia.usd.RB.COL.004@1.0.0
```
