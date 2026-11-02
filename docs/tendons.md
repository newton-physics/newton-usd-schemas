# Native routed tendon schema proposal

**Experimental, for schema review.** This proposal describes native massless routed
tendons for Newton's XPBD and VBD solvers. It is not an agreed standard and does not
implement the Newton importer. Both are tracked in
[Newton #4910](https://github.com/newton-physics/newton/issues/4910).

## Representation

One `NewtonTendon` prim identifies the cable. Its `newton:tendon:guides`
relationship stores the route in order. Each target is an independent
`NewtonTendonGuide` prim with a body relationship and local pose, plus APIs that
describe its behavior and incoming span.

| Schema | Applied to | Responsibility |
| --- | --- | --- |
| `NewtonTendon` | Typed prim | Ordered guides and optional simulation owner |
| `NewtonTendonGuide` | Typed prim | Body attachment, local position and rotation |
| `NewtonTendonAnchorAPI` | Guide | Material attachment at a point |
| `NewtonTendonPinholeAPI` | Guide | Point routing with capstan friction |
| `NewtonTendonRollerAPI` | Guide | Tangential routing, friction, winding, optional activation/bypass |
| `NewtonRollerCircleAPI` | Roller guide | Independent circular profile and radius |
| `NewtonTendonSpanAPI` | Every guide after the first | Incoming straight span's rest length, compliance and damping |
| `NewtonTendonSceneAPI` | `PhysicsScene` | Solver-wide material and activation settings |

The typed prims derive from `UsdTyped`, not a geometry or collision type. They do
not contribute render bounds. A viewer may draw separate visual geometry, but
changing that geometry must not change the physical guide profile.

### Route and span ownership

Author the complete guide list using `SetTargets` or an explicit USDA relationship
list. Consume the composed target order; never sort by name or child traversal.
Each guide is one occurrence in one tendon. To reuse a physical roller in another
route, author another guide with the same body and profile. This keeps incoming-span
ownership unambiguous and permits repeated visits without duplicate targets.

Apply exactly one guide-kind API. Apply `NewtonTendonSpanAPI` on every guide after
the first, including the last anchor. An internal anchor is permitted: it prevents
material from slipping across that point. The first guide has no incoming span
and must not carry the span API or authored span properties.

The guide list remains unchanged when a dynamic roller is bypassed. Activity,
material transfer, and effective span rest lengths belong to runtime state, not
to edits of the USD asset.

### Body and local pose

`newton:tendon:body` has zero or one target. A target must identify a prim carrying
`PhysicsRigidBodyAPI`. No target means world attachment. A broken target is an
error, not world attachment; do not search arbitrary ancestors or serialize body
indices.

`newton:tendon:localPos` is body-relative when a body is present and expressed in
stage world coordinates otherwise. The body frame is its prim frame, not its
center-of-mass frame. `newton:tendon:localRot` is a unit quaternion mapping the
guide frame into that attachment frame. Anchors and pinholes use only the position;
rollers use the full pose. Local XY defines the 2D profile and local +Z its normal.
A circle's origin is its center.

Guide hierarchy does not introduce another transform. Moving an enclosing `Xform`
does not move a world-fixed guide. For a reusable asset that must move with a parent
transform, attach those guides to an explicit stationary rigid body inside the
asset instead. A Newton import placement transform applies once to world guides,
just as builder replication does; body-relative guides move with remapped bodies.
Nonuniform scale and shear that would change a circular profile are outside the
initial importer scope and must be diagnosed, not approximated by a circle.

`physics:simulationOwner` can select one physics scene for the tendon. All attached
bodies must agree. Without it, infer their common scene, or use the sole scene for
an all-world route. Multiple possible scenes require an explicit owner. This also
selects solver settings for all-world tendons.

### Guide behavior and profiles

An anchor has no routing parameters. A pinhole adds `newton:tendon:friction`.
A roller adds that coefficient, `newton:tendon:winding` (`+1` or `-1`, matching
`TendonGuide.orientation`), and `newton:tendon:dynamic`. The latter allows the cable
to bypass the roller; it does not control whether the body moves.

Apply `NewtonRollerCircleAPI` to a roller and author a positive
`newton:roller:radius`. There is no fallback to collision geometry or an arbitrary
radius. Authoring tools can default to choosing the circle API, but assets must
state the profile explicitly.

Future ellipse and circular-sector APIs can live on the same guide with their own
semiaxes or radius/opening-angle properties. Only one profile may apply. Those APIs
are not registered by this proposal. No unused ellipse/sector parameters are added
to circles, anchors, or pinholes; the common rotation already provides in-plane
orientation.

### Material properties and units

The incoming-span API uses linear per-span compliance, not Young's modulus or
whole-tendon stiffness. Wrapped arc material is handled by the native model; do not
include it again in an authored straight-span rest length.

Let `L` be stage `metersPerUnit` and `M` be stage `kilogramsPerUnit`. Physics time
is seconds, not animation frames. The proposed importer converts values as follows:

| Property | Fallback | Stage units | Conversion to SI |
| --- | --- | --- | --- |
| `newton:tendon:localPos` | `(0, 0, 0)` | distance | multiply by `L` |
| `newton:tendon:localRot` | identity | dimensionless | no scaling |
| `newton:roller:radius` | none; required | distance | multiply by `L` |
| `newton:tendon:span:restLength` | `-1` | distance | multiply nonnegative values by `L`; preserve negative automatic sentinel |
| `newton:tendon:span:compliance` | `0` | second² / mass | divide by `M` |
| `newton:tendon:span:damping` | `0` | mass / second | multiply by `M` |
| `newton:tendon:friction` | `0` | dimensionless | no scaling |
| `newton:tendon:settleAbsoluteTolerance` | `1e-6` | force | multiply by `M * L` |

A negative rest length requests measurement from initial geometry. A shorter
explicit length can preload the cable. Zero compliance requests an inextensible
span; XPBD supports this, while VBD currently approximates it with a small positive
compliance. The schema does not claim identical solver trajectories.

All properties are initial configuration, not actuator commands or serialized
simulation state. The initial importer reads default-time values and rejects
time-sampled configuration rather than silently turning animation into a static asset.

### Scene controls

`NewtonTendonSceneAPI` composes with either `NewtonXpbdSceneAPI` or
`NewtonVbdSceneAPI` and includes `NewtonSceneAPI`. It does not choose the body solver.

| Property suffix under `newton:tendon:` | Fallback | Meaning |
| --- | --- | --- |
| `materialSolver` | `sweeps` | Only supported token initially; direct solving is a later extension |
| `maxSweeps` | `256` | Positive budget per outer solver iteration, not a convergence guarantee |
| `settleTolerance` | `0.001` | Relative final capstan-force residual tolerance |
| `settleAbsoluteTolerance` | `1e-6` | Absolute residual tolerance in stage force units |
| `activationTolerance` | `0.002` | Radius-relative activation gap; finite and in `[0, 1)` |

The proposed criterion is `error <= atol + rtol * max(T_left, T_right)` at every
guide, respecting the applicable capstan boundary and feasible transfer directions.
Zero `settleTolerance` disables early-out, including the absolute term.

**Importer dependency:** these semantics require the correction in
[Newton #5051](https://github.com/newton-physics/newton/pull/5051). Do not map them to
the older incremental-transfer stopping criterion. The older runtime also caps
sweeps at 256; the schema does not freeze that implementation limit. An unsupported
value must produce an error, not clamping.

## Validation contract

These schemas are codeless. USD exposes applicability metadata, property types,
allowed tokens and numeric limits, but does not enforce this full contract. The
native importer must validate a complete route before changing the builder. The
tests here check schema declarations and USD composition, not importer enforcement.

Reject:

- Missing, invalid, inactive, unloaded, or non-guide route targets; fewer than two
  guides; relationship forwarding; shared guide occurrences; and branching/cycles.
- Missing/conflicting guide-kind or profile APIs. A bare guide is not implicitly
  an anchor, and a roller without a profile is not implicitly a circle.
- Authored guide-family properties inapplicable to the selected kind/profile,
  including custom attributes with those names. Unrelated application metadata may coexist.
- Span data on the first guide, or a missing span API on a later guide.
- Invalid/multiple body or scene targets, cross-scene routes, or ambiguous ownership.
  Empty relationships are valid defaults; broken relationships are not.
- Nonfinite values, negative compliance/damping/friction, nonpositive radius,
  non-unit rotations, winding other than ±1, or activation tolerance outside `[0, 1)`.
- Unsupported time sampling, scale/shear, material solver/profile types, or routing
  topology. Dynamic rollers must initially be circular, internal and isolated.

Geometry must also satisfy the native solver's tangent and wrap restrictions.
This schema does not add negative wraps, wraps beyond 180°, multiple full turns,
or automatic route reordering.

## Relationship to spatial MjcTendon

The comparison uses the [MuJoCo schema definitions](https://github.com/google-deepmind/mujoco/blob/main/src/experimental/usd/mjcPhysics/schema.usda)
and [Newton's provider import path](https://newton-physics.github.io/newton/latest/concepts/usd_parsing.html).

| Concern | Spatial `MjcTendon` | Native proposal |
| --- | --- | --- |
| Identity | One stable tendon prim | Same general pattern; a distinct typed prim |
| Path | `mjc:path` plus optional indices, repeated visits and divided subpaths | Ordered unique guide occurrences; one open route |
| Point guide | Site prim | Guide with explicit body and local pose |
| Wrapping | Geom references and optional side sites | Independent 2D roller profile and winding sign |
| Material | Whole-tendon spring/stiffness and damping | Per-span rest length, compliance and damping, with material transfer |
| Friction | Tendon frictionloss | Guide capstan friction and rolling material transport; not equivalent |
| Solver | MuJoCo provider data | Native XPBD/VBD route data |

Reuse path resolution, body mapping, units, and scene-association machinery where
semantics match. Keep provider-specific path decoding separate: native guides do
not use `mjc:path:indices`, pulley divisors, or fixed joint-coordinate tendons.
There is no general lossless material/friction conversion. Neither importer should
reinterpret the other prim type.

## Review and implementation split

The [authoring fixture](../tests/assets/tendon.usda) contains all three guide kinds,
world/body attachments, finite friction and a dynamic circular roller. It opens in
USD, but is not yet a runnable Newton import example.

Review with Andrew Kaufman before implementing the importer. Confirm the typed
guide plus applied-API split, explicit circle profile, world-frame/asset-placement
rules, incoming-span ownership, and shared scene controls. The earlier Google Doc
is background; this PR is the proposed review surface.

The follow-up Newton PR must add atomic route validation and conversion to
`TendonGuide`, unit/frame and invalid-asset tests, reference/placement/copy coverage,
and an end-to-end XPBD/VBD example. Keep the existing MuJoCo importer unchanged.
