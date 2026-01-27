# 0.1.0a2

## Fixes

- Add Python 3.13 support
  - Verified via CI test coverage for Python [3.10, 3.11, 3.12, 3.13]
  - Note Linux aarch64 verification for 3.13 is skipped due to dev dependency limitations, though the wheel should still support it

# 0.1.0a1

## Features

- Added a USD plugin which registers on module import
  - Important: Schemas must be registered _before_ the `Usd.SchemaRegistry` is initialized. Make sure to import the module very early in the process.
- Added `NewtonSceneAPI`, which applies on top of a `PhysicsScene` Prim, providing general attributes to control a Newton Solver
- Added `NewtonXpbdSceneAPI`, which further extends a `PhysicsScene` with Newton's XPBD (eXtended Position-Based Dynamics) solver configuration
  - Applying `NewtonXpbdSceneAPI` implicitly applies the `NewtonSceneAPI` as well
- Added `NewtonCollisionAPI`, which extends `PhysicsCollisionAPI` with a contact margin (distance threshold below which contacts are detected)
  - Applying `NewtonCollisionAPI` implicitly applies `PhysicsCollisionAPI` as well
- Added `NewtonMeshCollisionAPI`, which extends `PhysicsMeshCollisionAPI` with attributes to control mesh approximation algorithms
  - Only `convexHull` attributes exist for now
  - Applying `NewtonMeshCollisionAPI` implicitly applies all 3 of the other collision APIs as well
- Added `NewtonMaterialAPI`, which extends `PhysicsMaterialAPI` with additional torsional and rolling friction attributes
  - These are currently used by both the mujoco & xpbd solvers, though may be ignored by other solvers.
  - Applying `NewtonMaterialAPI` implicitly applies `PhysicsMaterialAPI` as well
