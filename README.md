# newton-usd-schemas

:warning: ***This project is in pre-alpha development.*** :warning:

:warning: ***It is not used by the Newton runtime.*** :warning:

:warning: ***Do not use these schemas yet.*** :warning:

# Overview

Newton USD schemas provide extensions to OpenUSD's [UsdPhysics specification](https://openusd.org/release/api/usd_physics_page_front.html), allowing USD layers to fully specify the [Newton](https://newton-physics.github.io/newton/guide/overview.html) runtime data model.

These schemas can be deployed into any python runtime with USD support, allowing content creators to author Newton compatible robots, props, and environments in any application of their choice, _without requiring the Newton runtime itself_.

This project is part of [Newton](https://github.com/newton-physics), a [Linux Foundation](https://www.linuxfoundation.org) project which is community-built and maintained.

# Get Started

These schemas are [codeless](https://openusd.org/release/tut_generating_new_schema.html#codeless-schemas), in that they contain no compiled code nor any public API of their own. Since codeless schemas do not provide any code, clients do not need to recompile USD to use or update these schemas. They are deployed as a python module via a wheel package for convenience, as all Newton projects use pyproject based dependencies & most USD authoring workflows include a python runtime.

To start using the schemas, install the python wheel into a virtual environment using your favorite package manager:

```bash
python -m venv .venv
source .venv/bin/activate
pip install newton-usd-schemas
```

At runtime, simply import the module to register the schemas with OpenUSD.

> Important: Schemas must be registered _before_ the `Usd.SchemaRegistry` is initialized. Make sure to import the module very early in the process.

```python
import newton_usd_schemas  # this registers the schema
from pxr import Usd, UsdPhysics

stage: Usd.Stage = Usd.Stage.CreateInMemory()

# create a UsdPhysics.Scene and set gravity
prim: Usd.Prim = UsdPhysics.Scene.Define(stage, "/scene").GetPrim()
prim.GetAttribute("physics:gravityMagnitude").Set(9.81)

# TODO: uncomment once we have an API schema to use
# apply a Newton schema and set some of its attributes
# prim.ApplyAPI("NewtonSceneAPI")
# prim.GetAttribute("newton:timeStep").Set(10)

stage.Export("/tmp/my_robot.usd")
```

Once a USD layer is authored to storage, it can be loaded into a Newton runtime using [Newton's USD Parsing](https://newton-physics.github.io/newton/concepts/usd_parsing.html) mechanism.

# Design Principles

Newton schemas follow a minimalist approach to determine which attributes should be included, and are similar to the philosophy that [UsdPhysics](https://openusd.org/release/api/usd_physics_page_front.html#usdPhysics_purpose_and_scope) and the [Newton API](https://newton-physics.github.io/newton/api/newton.html) follow for capturing parameters that generalize across simulators. We view the Newton schemas as a proving and staging ground for physics parameters that should eventually be eligible for promotion into the UsdPhysics standard.

A USD attribute belongs in the Newton schema if it meets one of these criteria:

1. **Clear Physical Meaning**: The attribute represents a physically meaningful quantity rather than a modeling or approximation parameter (e.g., simulation time step `dt`, or gravitational acceleration), and is supported by at least one Newton solver.

2. **Cross-Solver Support**: The attribute has a direct (or transformable) correspondence to parameters supported by at least two Newton solvers. This mainly applies to physical modeling parameters (e.g., a viscous joint friction coefficient).

For solver-specific or workflow-specific parameters that are not in UsdPhysics or the Newton schema, Newton supports solver-specific schemas (e.g., [mjcPhysics](https://github.com/google-deepmind/mujoco/blob/main/src/experimental/usd/mjcPhysics/schema.usda)) or [custom attributes](https://newton-physics.github.io/newton/concepts/usd_parsing.html#custom-attribute-framework).

# Contribution Guidelines

Contributions from the community are welcome. See [CONTRIBUTING.md](https://github.com/newton-physics/newton-usd-schemas/blob/main/CONTRIBUTING.md) to learn about contributing via GitHub issues, as well as building the project from source and our development workflow.

General contribution guidelines for Newton repositories are available [here](https://github.com/newton-physics/newton-governance/blob/main/CONTRIBUTING.md).

# Community

For questions about these newton-usd-schemas, feel free to join or start a [GitHub Discussions](https://github.com/newton-physics/newton-usd-schemas/discussions).

By participating in this community, you agree to abide by the Linux Foundation [Code of Conduct](https://lfprojects.org/policies/code-of-conduct/).

# References

- [Newton documentation](https://newton-physics.github.io/newton/guide/overview.html)
- [OpenUSD API Docs](https://openusd.org/release/api/index.html)
- [OpenUSD User Docs](https://openusd.org/release/index.html)
- [NVIDIA OpenUSD Resources and Learning](https://developer.nvidia.com/usd)

# License

newton-usd-schemas is provided under the [Apache License, Version 2.0](https://www.apache.org/licenses/LICENSE-2.0)
