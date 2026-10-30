# Unreleased

## Features

- Added `NewtonActuatorMotorBaseAPI`, the base of all actuator motors, which turn the motor command into the effort of a motor; at most one motor may be applied to an actuator
- Added `NewtonDCMotorAPI`, a DC motor driven by a PWM voltage following the voltage-controlled servo model of [Rhoban/bam](https://github.com/Rhoban/bam), with `newton:kt`, `newton:resistance` and `newton:vin`, which turns the motor command into the effort of a motor
  - With a motor, the control law must output the motor command (e.g. a voltage from `NewtonVoltageControlAPI`), command clamping bounds that command, and clamping bounds the effort of the motor. Control laws that output an effort, such as `NewtonPDControlAPI`, must not be combined with a motor.
- Added `NewtonVoltageControlAPI`, the firmware position controller of a BAM voltage-controlled servo, with `newton:kp` and `newton:errorGain`, which outputs the voltage of a motor
- Added `NewtonActuatorCommandClampingBaseAPI`, the base of all actuator command clamping, which bounds the motor command before the motor
- Added `NewtonCurrentPWMClampingAPI`, the current and PWM limits of the firmware of a servo, with `newton:maxCurrent` and `newton:maxPwm`, applied in this order to the voltage of a `NewtonDCMotorAPI` whose `newton:kt` and `newton:resistance` it uses
  - Together they reproduce a BAM voltage-controlled servo; friction is not modeled, and the command delay and armature are authored with `NewtonActuatorDelayAPI` and on the joint.
- Added `NewtonActuatorInputProcessorBaseAPI`, the base of all actuator input processors, which transform the inputs of the control law
  - `NewtonActuatorDelayAPI` now applies it implicitly.
- Added `NewtonActuatorEncoderAPI`, an input processor that models the position encoder of an actuator, mounted behind a passive output joint named by the `newton:outputJoint` relationship, e.g. to capture gearbox backlash
- Added `NewtonBattery`, an abstract base for batteries shared by the motors of several actuators, and `NewtonConstantResistanceBattery`, an ideal voltage source behind a constant internal resistance with `newton:nominalVoltage`, `newton:resistance` and `newton:minVoltage`
  - Actuators draw from a battery with the new `newton:battery` relationship on `NewtonActuator`.
  - Motors that provide a supply voltage, such as `NewtonDCMotorAPI`, use the battery's voltage instead of `newton:vin`.

# 0.6.0

## Features

- Added `NewtonVbdSceneAPI`, which further extends a `PhysicsScene` with Newton's VBD (Vertex Block Descent) solver configuration
  - Applying `NewtonVbdSceneAPI` implicitly applies the `NewtonSceneAPI` as well
  - Configures the compliant augmented Lagrangian method (ALM) path for rigid bodies, including body-body contact history for warm-starting and stiffness & damping for non-rod structural joint constraints.
  - Consumers constructing `SolverVBD` must pass `rigid_compliant_alm=True`. This runtime compatibility setting is intentionally not authored in USD.

# 0.5.0

## Features

- Added `NewtonCurvesDeformableMaterialAPI`, which extends the AOUSD proposed `PhysicsCurvesDeformableMaterialAPI` with damping attributes
- Added `NewtonPointsDeformableSimAPI`, which extends the AOUSD proposed Deformables schemas for particle simulation
  - Marks a `Points` prim as deformable simulation geometry. Particle positions, velocities, widths, and stable identifiers use the standard `UsdGeomPoints` `points`, `velocities`, `widths` (or `primvars:widths`), and `ids` attributes. Widths are diameters, so radius is `width / 2`.
  - As with the other `*DeformableSimAPI`, apply `PhysicsDeformableBodyAPI` to this prim or its parent to define the deformable body and associate it with a `Scene` prim via the `physics:simulationOwner` relationship on the body.
- Added `NewtonMPMSceneAPI`, which further extends a `PhysicsScene` with Newton's MPM solver configuration
  - Applying `NewtonMPMSceneAPI` implicitly applies the `NewtonSceneAPI` as well
- Added `NewtonMPMMaterialAPI`, which provides constitutive parameters for Newton's MPM solver
  - Applying this schema also applies `PhysicsMaterialAPI`, but it does not apply `NewtonMaterialAPI`, which describes surface-contact response.

## Fixes

- Document contact friction coefficients as length-dimensioned
  - `newton:torsionalFriction` and `newton:rollingFriction` were previously documented as dimensionless, but both are length-dimensioned in all solvers that use them.

# 0.4.1

## Fixes

- Fixed incorrect base type for `NewtonActuator`, it is now `UsdTyped` rather than a partially implemented `UsdGeomImagable`
  - This means actuators cannot be rendered in Hydra compatible viewers. If actuator manipulators are required, the viewer needs to handle them as a special case, or the content author needs to parent a `UsdGeomImagable` beneath them in the hierarchy.
- Improved `NewtonMimicAPI` documentation to clarify that the leader and follower must be the same joint type.
  - Multi-dof joint behavior remains undefined & unsupported

# 0.4.0

## Features

- Added `newton:jointsAddMobility` attribute to `NewtonArticulationRootAPI`
  - This attribute controls whether joints within this articulation add mobility or constrain it, which affects how engines should parse the articulation into their native formulation.
  - When false (default), joints constrain degrees of freedom between otherwise-free bodies.
  - When true, multiple single-DOF joints connecting the same body pair (stacked joints) add degrees of freedom to bodies that would otherwise be rigidly attached.
- Added `NewtonJointAPI`, which applies on top of a `PhysicsJoint`, providing joint configuration for armature, passive dynamics, and limit spring response
  - All attributes broadcast uniformly to every DOF of the joint.
  - If per-DOF variance is required for a multi-DOF joint, it is recommended to "break apart" the joint into a stack of single-DOF joints (i.e. revolute or prismatic), and set `NewtonArticulationRootAPI.newton:jointsAddMobility = True`.

# 0.3.1

## Fixes

- Renamed `newton:contactFrictionStiffness` to `newton:contactFrictionGain` on `NewtonMaterialAPI`; the parameter is a velocity-dependent friction gain, not a tangential stiffness

# 0.3.0

## Features

- Add contact response attributes (`contactStiffness`, `contactDamping`, `contactFrictionStiffness`, `contactAdhesion`) to `NewtonMaterialAPI` for describing how a material behaves on contact.
- Added `NewtonSiteAPI`, which can be applied to Gprims to declare a non-colliding, massless reference shape used for sensing, attachment, or coordinate queries.
  - `NewtonSiteAPI` and `NewtonCollisionAPI` are mutually exclusive; sites cannot be colliders
- Added `NewtonMassAPI`, which extends `PhysicsMassAPI`.
  - Author the double precision `newton:inertia` tensor to override `physics:diagonalInertia` / `physics:principalAxes`.
  - Author the `newton:massModel` mode as "shell", along with `newton:shellThickness`, when computing implicit mass & inertia of thin shells (hollow geometry). The default "solid" matches current UsdPhysics implicit mass expectations.
  - Applying `NewtonMassAPI` implicitly applies `PhysicsMassAPI` as well.
- Added `NewtonSDFCollisionAPI`, which extends `NewtonCollisionAPI` with attributes that configure SDF-based collision and optional hydroelastic contact.
  - Hydroelastic contact is opt-in via `newton:hydroelasticEnabled` (default `false`) on the same API; no separate hydroelastic API is required.
  - Applying `NewtonSDFCollisionAPI` implicitly applies `NewtonCollisionAPI` and `PhysicsCollisionAPI` as well.

## Fixes

- Removed unused dev dependencies

## Documentation

- Add Experimental Status notice to README.md
  - This project is currently in a v0.x development phase. The schemas are considered experimental & could change in future releases

# 0.2.0

## Features

- Added experimental `NewtonActuator` typed schema for actuating a `PhysicsRevoluteJoint` or `PhysicsPrismaticJoint`
  - Only single-DOF joint actuation is supported at this time.
    - Multi-DOF PhysicsJoints are not supported, even when locked via LimitAPIs to a single axis.
  - Actuators require a single control law via applied API
    - Chose one of `NewtonPDControlAPI`, `NewtonPIDControlAPI`, or `NewtonNeuralControlAPI` when authoring an actuator
    - Custom control laws can be implemented by inheriting `NewtonActuatorControlBaseAPI`
  - Actuators may optionally have any number of clamping operations via applied APIs
    - Apply any of `NewtonMaxEffortClampingAPI`, `NewtonDCMotorClampingAPI`, or `NewtonPositionBasedClampingAPI`
    - Custom clamping can be implemented by inheriting `NewtonActuatorClampingBaseAPI`
  - Control input delay can be added by applying `NewtonActuatorDelayAPI`
  - All actuator attributes use pure SI units (meters, radians, seconds, kg)
    - Rotational attributes use radians, diverging from `UsdPhysicsDriveAPI` which uses degrees

## Fixes

- Realigned torsional and rolling friction fallback values with Newton's ShapeConfig (matching MuJoCo's native defaults).

# 0.1.0

## Features

- Added a USD plugin which registers on module import
  - Important: Schemas must be registered _before_ the `Usd.SchemaRegistry` is initialized. Make sure to import the module very early in the process.
- Added `NewtonSceneAPI`, which applies on top of a `PhysicsScene` Prim, providing general attributes to control a Newton Solver
- Added `NewtonXpbdSceneAPI`, which further extends a `PhysicsScene` with Newton's XPBD (eXtended Position-Based Dynamics) solver configuration
  - Applying `NewtonXpbdSceneAPI` implicitly applies the `NewtonSceneAPI` as well
- Added `NewtonKaminoSceneAPI`, which further extends a `PhysicsScene` with Newton's Kamino solver configuration
  - Applying `NewtonKaminoSceneAPI` implicitly applies the `NewtonSceneAPI` as well
- Added `NewtonArticulationRootAPI`, which extends `PhysicsArticulationRootAPI` by allowing self collisions to be disabled
  - Applying `NewtonArticulationRootAPI` implicitly applies `PhysicsArticulationRootAPI` as well
- Added `NewtonCollisionAPI`, which extends `PhysicsCollisionAPI` with contact margin and gap (used during collision detection)
  - Applying `NewtonCollisionAPI` implicitly applies `PhysicsCollisionAPI` as well
- Added `NewtonMeshCollisionAPI`, which extends `PhysicsMeshCollisionAPI` with attributes to control mesh approximation algorithms
  - Only `convexHull` attributes exist for now
  - Applying `NewtonMeshCollisionAPI` implicitly applies all 3 of the other collision APIs as well
- Added `NewtonMaterialAPI`, which extends `PhysicsMaterialAPI` with additional torsional and rolling friction attributes
  - These are currently used by both the mujoco and xpbd solvers, though may be ignored by other solvers.
  - Applying `NewtonMaterialAPI` implicitly applies `PhysicsMaterialAPI` as well
- Added `NewtonMimicAPI` for authoring mimic/equality constraints between the DOFs of two `PhysicsJoint` prims
  - The mimic constraint enforces that `joint0 = coef0 + coef1 * joint1` for the joint DOFs, where `joint0` (the follower) is
    the joint to which this API is applied, and `joint1` (the leader) is specified via a `UsdRelationship`
