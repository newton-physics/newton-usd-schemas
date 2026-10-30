# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import importlib.util
import pathlib
import re
import subprocess
import sys

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

PACKAGE = "newton_usd_schemas.validators._requirements"

GENERATOR_HEADER = re.compile(
    r"\A# SPDX-FileCopyrightText: Copyright \(c\) [0-9-]+ NVIDIA CORPORATION & AFFILIATES\. All rights reserved\.\n"
    r"# SPDX-License-Identifier: Apache-2\.0\n#\n"
)
NEWTON_HEADER = "# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers\n# SPDX-License-Identifier: Apache-2.0\n"


class CustomBuildHook(BuildHookInterface):
    """Generate the `newton_usd_schemas.validators._requirements` package from the validation specs in `docs/specs`."""

    def initialize(self, version: str, build_data: dict) -> None:
        root = pathlib.Path(self.root)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "usd_profiles_nvidia.codegen",
                "--docs-root",
                (root / "docs" / "specs").as_posix(),
                "--destination-dir",
                root.as_posix(),
                "--package-name",
                PACKAGE,
                "--reverse-domain",
                "org.newton-physics",
            ],
            check=True,
        )
        relabel_rendered_modules(root.joinpath(*PACKAGE.split(".")))


def relabel_rendered_modules(package_dir: pathlib.Path) -> None:
    """Replace the generator's copyright header on the modules it renders from our specs.

    The generator also copies its own `_api` package and `_protocols.py` unchanged, which keep their NVIDIA headers.
    """
    # usd_profiles_nvidia.codegen.resources cannot be imported: its __init__.py imports a missing module
    templates = pathlib.Path(importlib.util.find_spec("usd_profiles_nvidia.codegen").submodule_search_locations[0]) / "resources"
    for template in templates.iterdir():
        if not template.name.endswith(".py.jinja2"):
            continue
        module = package_dir / template.name.removesuffix(".jinja2")
        content, count = GENERATOR_HEADER.subn(NEWTON_HEADER, module.read_text(encoding="utf-8"), count=1)
        if count != 1:
            raise RuntimeError(f"{module} does not start with the expected usd-profiles-nvidia copyright header")
        module.write_text(content, encoding="utf-8")
