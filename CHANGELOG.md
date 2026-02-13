# 0.1.0rc2

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
- Added `NewtonCollisionAPI`, which extends `PhysicsCollisionAPI` with contact margin & gap (used during collision detection)
  - Applying `NewtonCollisionAPI` implicitly applies `PhysicsCollisionAPI` as well
- Added `NewtonMeshCollisionAPI`, which extends `PhysicsMeshCollisionAPI` with attributes to control mesh approximation algorithms
  - Only `convexHull` attributes exist for now
  - Applying `NewtonMeshCollisionAPI` implicitly applies all 3 of the other collision APIs as well
- Added `NewtonMaterialAPI`, which extends `PhysicsMaterialAPI` with additional torsional and rolling friction attributes
  - These are currently used by both the mujoco & xpbd solvers, though may be ignored by other solvers.
  - Applying `NewtonMaterialAPI` implicitly applies `PhysicsMaterialAPI` as well
- Added `NewtonMimicAPI` for authoring mimic/equality constraints between the DOFs of two `PhysicsJoint` prims
  - The mimic constraint enforces that `joint0 = coef0 + coef1 * joint1` for the joint DOFs, where `joint0` (the follower) is
    the joint to which this API is applied, and `joint1` (the leader) is specified via a `UsdRelationship`
