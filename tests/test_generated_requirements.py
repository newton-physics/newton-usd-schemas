# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import unittest

import newton_usd_schemas.validators._requirements as requirements

NEWTON_HEADER = "# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers\n# SPDX-License-Identifier: Apache-2.0\n"
NVIDIA_COPYRIGHT = "NVIDIA CORPORATION & AFFILIATES"


class TestGeneratedRequirements(unittest.TestCase):
    """Check the copyright headers of the package that the build generates from docs/specs."""

    def setUp(self):
        self.package_dir = pathlib.Path(requirements.__file__).parent

    def test_rendered_modules_are_newton_licensed(self):
        rendered = [module for module in self.package_dir.glob("*.py") if module.name != "_protocols.py"]
        self.assertGreater(len(rendered), 0)
        for module in rendered:
            with self.subTest(module=module.name):
                content = module.read_text(encoding="utf-8")
                self.assertTrue(content.startswith(NEWTON_HEADER))
                self.assertNotIn(NVIDIA_COPYRIGHT, content)

    def test_copied_modules_keep_their_copyright(self):
        copied = [self.package_dir / "_protocols.py", *(self.package_dir / "_api").glob("*.py")]
        for module in copied:
            with self.subTest(module=module.relative_to(self.package_dir).as_posix()):
                self.assertIn(NVIDIA_COPYRIGHT, module.read_text(encoding="utf-8").splitlines()[0])


if __name__ == "__main__":
    unittest.main()
