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
scene: UsdPhysics.Scene = UsdPhysics.Scene.Define(stage, "/scene")
scene.GetGravityMagnitudeAttr().Set(9.81)

# apply a Newton schema and set some of its attributes
prim: Usd.Prim = scene.GetPrim()
prim.ApplyAPI("NewtonSceneAPI")
prim.GetAttribute("newton:timeStep").Set(0.002)

stage.Export("/tmp/my_robot.usd")
```

Once a USD layer is authored to storage, it can be loaded into a Newton runtime using [Newton's USD Parsing](https://newton-physics.github.io/newton/concepts/usd_parsing.html) mechanism.

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
