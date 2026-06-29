# NewtonVbdSceneAPI — Design Proposal for Review

This document proposes a USD schema, `NewtonVbdSceneAPI`, that exposes the
configuration of the Newton VBD solver (`SolverVBD`) on a `PhysicsScene` prim.
It is circulated to the solver authors to confirm the parameter classification,
defaults, ranges, and units before the schema is committed.

The reference for the solver surface is `SolverVBD.__init__`
(`newton/_src/solvers/vbd/solver_vbd.py`).

## Scope

This proposal covers the schema artifact only: the codeless schema definition
(`generatedSchema.usda`), its plugin registration (`plugInfo.json`), and a unit
test. The parser that maps these attributes to `SolverVBD` constructor
arguments lives in the `newton` repository (`newton/_src/usd/schemas.py`) and is
a separate change.

## Design decisions

## Draft Proposal

1. **Solver scene API, consistent with existing solvers.** `NewtonVbdSceneAPI`
   is a single-apply, codeless API that applies only to `PhysicsScene` and
   lists `NewtonSceneAPI` as a built-in API. This matches the existing
   `NewtonXpbdSceneAPI` and `NewtonKaminoSceneAPI`.

2. **`iterations` is not redefined.** The base `NewtonSceneAPI` already provides
   `newton:maxSolverIterations`. VBD's `iterations` maps onto it, the same way
   `NewtonXpbdSceneAPI` relies on the base attribute rather than adding its own.

3. **Namespacing by parameter group.** Attributes use `newton:vbd:` for common
   parameters and `newton:vbd:particle:` / `newton:vbd:rigid:` for the particle
   and rigid (AVBD) groups, mirroring Kamino's `newton:kamino:padmm:` /
   `newton:kamino:constraints:` sub-grouping. (Open question 1 below asks whether
   to keep the sub-namespaces or flatten to `newton:vbd:`.)

4. **Attributes are included based on whether they describe the simulation or
   the run.** An attribute belongs in the schema when it describes the physical
   scene or changes the solver's simulation behavior, so that it travels with the
   asset and is portable across applications. An attribute is left to
   application-level configuration when it controls how the engine executes
   rather than what is simulated — memory preallocation, backend acceleration,
   algorithm plumbing, and debug output. These do not change the simulated result
   in a portable way and are better set by the runtime.

5. **`-inf` sentinel for "use solver fallback."** Constructor arguments that
   default to `None` and fall back to another parameter (the alpha and beta
   overrides) are represented with a `-inf` default, meaning "inherit the solver
   default." The sentinel keeps the attribute optional: when it is left
   unauthored, the solver chooses the effective value.

## Parameters included in the schema

All attributes are `uniform`.

### Common (`newton:vbd:`)

| attribute | type | default | range | units |
|---|---|---|---|---|
| `newton:vbd:frictionEpsilon` | float | 0.01 | [0, inf) | distance / seconds |

### Particle (`newton:vbd:particle:`)

| attribute | type | default | range | units |
|---|---|---|---|---|
| `selfContactEnabled` | bool | false | — | — |
| `selfContactRadius` | float | 0.2 | [0, inf) | distance |
| `selfContactMargin` | float | 0.2 | [0, inf) | distance |
| `conservativeBoundRelaxation` | float | 0.85 | [0, 1] | dimensionless |
| `collisionDetectionInterval` | int | 0 | (-inf, inf) | dimensionless |
| `edgeParallelEpsilon` | float | 1e-5 | [0, inf) | dimensionless |
| `topologicalContactFilterThreshold` | int | 2 | [0, inf) | dimensionless |
| `restShapeContactExclusionRadius` | float | 0.0 | [0, inf) | distance |

Notes:
- `selfContactMargin` is expected to be larger than `selfContactRadius` to avoid
  missing contacts; this is a usage guideline, not a hard limit.
- `collisionDetectionInterval` is tri-state: a value `< 0` runs detection once
  before initialization, `0` runs it twice (before and after initialization),
  and `n >= 1` runs it before every `n` iterations. (Open question 2 below.)
- `topologicalContactFilterThreshold`, `restShapeContactExclusionRadius`, and
  the self-contact parameters are only consulted when `selfContactEnabled` is
  true.

### Rigid / AVBD (`newton:vbd:rigid:`)

| attribute | type | default | range | units |
|---|---|---|---|---|
| `avbdAlpha` | float | 0.95 | [0, 1] | dimensionless |
| `avbdJointAlpha` | float | -inf † | [0, 1] | dimensionless |
| `avbdContactAlpha` | float | -inf † | [0, 1] | dimensionless |
| `avbdBeta` | float | 0.0 | [0, inf) | per-iteration ramp ‡ |
| `avbdLinearBeta` | float | -inf † | [0, inf) | force / distance² |
| `avbdAngularBeta` | float | -inf † | [0, inf) | torque / radian² |
| `avbdGamma` | float | 0.999 | [0, 1] | dimensionless |
| `contactHard` | bool | true | — | — |
| `contactHistory` | bool | false | — | — |
| `contactStickMotionEps` | float | 1e-4 | [0, inf) | distance |
| `contactStickFreezeTranslationEps` | float | 1e-4 | [0, inf) | distance |
| `contactStickFreezeAngularEps` | float | 1e-4 | [0, inf) | radians |
| `contactKStart` | float | 100.0 | [0, inf) | force / distance |
| `jointLinearKe` | float | 1e5 | [0, inf) | force / distance |
| `jointAngularKe` | float | 1e5 | [0, inf) | torque / radian |
| `jointLinearKStart` | float | 100.0 | [0, inf) | force / distance |
| `jointAngularKStart` | float | 10.0 | [0, inf) | torque / radian |
| `jointLinearKd` | float | 0.0 | [0, inf) | seconds |
| `jointAngularKd` | float | 0.0 | [0, inf) | seconds |

† `-inf` is the "use solver fallback" sentinel: `avbdJointAlpha` and
`avbdContactAlpha` inherit `avbdAlpha`; `avbdLinearBeta` and `avbdAngularBeta`
inherit `avbdBeta`. These attributes use `soft` limits.

‡ The penalty stiffness is incremented each iteration by `beta` times the
constraint violation (`k += beta * |C|`, clamped to the stiffness ceiling).
`avbdBeta` feeds both the linear and angular ramps, whose units differ
(force/distance² vs. torque/radian²), so it carries no single physical unit.
The per-axis overrides are recommended for production tuning. The per-iteration
update is a behavior, not a unit dimension: `beta` itself has the dimensions
above.

## Parameters excluded from the schema

| constructor argument | classification | rationale |
|---|---|---|
| `iterations` | mapped to base | covered by `newton:maxSolverIterations` on `NewtonSceneAPI` |
| `integrate_with_external_rigid_solver` | application config | describes how the application wires multiple solvers (one-way coupling), not a property of the scene |
| `particle_enable_tile_solve` | application config | backend acceleration toggle; output-equivalent |
| `particle_vertex_contact_buffer_size` | application config | memory preallocation |
| `particle_edge_contact_buffer_size` | application config | memory preallocation |
| `rigid_body_contact_buffer_size` | application config | memory preallocation |
| `rigid_body_particle_contact_buffer_size` | application config | memory preallocation |
| `particle_external_vertex_contact_filtering_map` | separate schema | element-level collision filtering; belongs to a dedicated element collision filter schema, not the solver scene API |
| `particle_external_edge_contact_filtering_map` | separate schema | element-level collision filtering; belongs to a dedicated element collision filter schema, not the solver scene API |
| `rigid_enable_dahl_friction` | deprecated | ignored by the solver; Dahl friction is controlled by model attributes (`model.vbd.dahl_eps_max` / `model.vbd.dahl_tau`) |

The four buffer-size arguments are memory preallocation and the tile-solve
toggle is a backend acceleration switch. Both control how the engine executes
rather than what is simulated, so they are left to application-level
configuration.

The two contact-filtering maps describe per-element collision exclusions, which
is the subject of element collision filtering in the in-progress UsdPhysics
deformables proposal (`PhysicsElementCollisionFilter`). This is per-element pair
data with a solver-agnostic USD home of its own, separate from the VBD solver
scene configuration, so it is out of scope for this schema. Note a granularity
difference: the proposed filter pairs whole elements (triangle-triangle for a
mesh, segment-segment for curves, point-point for points), whereas the solver
maps are vertex-triangle and edge-edge exclusions. A parser would expand
element-level filter pairs into the corresponding vertex-triangle and edge-edge
exclusions rather than map them one to one.

## Open questions 

1. **Namespacing.** Keep the `newton:vbd:particle:` / `newton:vbd:rigid:`
   sub-namespaces, or flatten everything to `newton:vbd:`?
2. **`collisionDetectionInterval`.** Is the tri-state integer the right
   representation, or should the "once" / "twice" / "every n" behavior be split
   into a token plus an interval?
3. **Units to confirm.** Confirm the units marked above, in particular
   `frictionEpsilon` (relative velocity), `edgeParallelEpsilon` (treated as
   dimensionless), and the `avbdBeta` ramp units.
4. **Defaults.** The defaults mirror the current `SolverVBD.__init__` defaults.
   Confirm these are the intended authored defaults for content, or whether any
   should instead default to a sentinel that defers to the solver.
5. **Coverage.** Are any excluded parameters expected to be authored per-scene
   in content pipelines, which would argue for moving them into the schema?
6. **Element collision filtering.** The two contact-filtering maps overlap with
   element collision filtering in the deformables proposal. Should they be driven
   by a dedicated element collision filter schema, and is the vertex-triangle /
   edge-edge vs. element-element granularity difference acceptable for a parser
   to bridge?
