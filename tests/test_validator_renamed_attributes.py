# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import json
import pathlib
import re
import tempfile
import unittest
from unittest import mock

from pxr import Sdf, Usd, UsdGeom, Vt
from validator_test_case import SUPPORTS_PYTHON_FIXERS, ValidatorTestCase

from newton_usd_schemas import validators
from newton_usd_schemas.validators import _migration
from newton_usd_schemas.validators._migration import RENAMED_ATTRIBUTES, rename_attribute

ERROR = "RenamedAttribute"
MASSES = Vt.FloatArray([0.2, 0.2])
SPECS = pathlib.Path(__file__).parents[1] / "docs" / "specs"


def define_particles(stage: Usd.Stage, path: str = "/Particles") -> Usd.Prim:
    prim = UsdGeom.Points.Define(stage, path).GetPrim()
    prim.ApplyAPI("NewtonPointsDeformableSimAPI")
    return prim


def author_old_masses(prim: Usd.Prim) -> Usd.Attribute:
    return prim.CreateAttribute("physics:masses", Sdf.ValueTypeNames.FloatArray)


class TestRenamedAttributesTable(unittest.TestCase):
    def test_plugin_metadata_lists_every_schema(self):
        plug_info = json.loads((pathlib.Path(validators.__file__).parent / "plugInfo.json").read_text())
        metadata = plug_info["Plugins"][0]["Info"]["Validators"]["RenamedAttributesValidator"]
        schema_types = [Usd.SchemaRegistry.GetTypeFromSchemaTypeName(schema).typeName for schema in RENAMED_ATTRIBUTES]
        self.assertEqual(metadata["schemaTypes"], schema_types)
        self.assertEqual(metadata["keywords"], ["NewtonValidators", "NewtonMigration", *RENAMED_ATTRIBUTES])

    def test_requirement_page_lists_every_rename(self):
        page = (SPECS / "requirements" / "renamed-attributes.md").read_text()
        rows = re.findall(r"^\| `(\w+)` +\| `([\w:]+)` +\| `([\w:]+)` +\|$", page, re.MULTILINE)
        self.assertEqual(rows, [(schema, old, new) for schema, renames in RENAMED_ATTRIBUTES.items() for old, new in renames.items()])

    def test_new_names_are_defined_by_their_schemas(self):
        for schema, renames in RENAMED_ATTRIBUTES.items():
            definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(schema)
            for old, new in renames.items():
                with self.subTest(schema=schema, attribute=new):
                    self.assertTrue(definition.GetPropertyDefinition(new))
                    self.assertFalse(definition.GetPropertyDefinition(old))


class TestRenameAttribute(unittest.TestCase):
    """`rename_attribute` backs both the `UsdValidation` fixer and the usd-validation-nvidia suggestion."""

    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = define_particles(self.stage)
        self.old = author_old_masses(self.prim)
        self.new = self.prim.GetAttribute("newton:masses")

    def test_moves_default(self):
        self.old.Set(MASSES)
        self.assertTrue(rename_attribute(self.old, "newton:masses", self.stage.GetEditTarget()))
        self.assertEqual(self.new.Get(), MASSES)
        self.assertFalse(self.prim.HasAttribute("physics:masses"))

    def test_moves_time_samples(self):
        self.old.Set(MASSES, 1.0)
        self.old.Set(Vt.FloatArray([0.3, 0.3]), 2.0)
        rename_attribute(self.old, "newton:masses", self.stage.GetEditTarget())
        self.assertEqual(self.new.GetTimeSamples(), [1.0, 2.0])
        self.assertEqual(self.new.Get(2.0), Vt.FloatArray([0.3, 0.3]))
        self.assertIsNone(self.new.Get(Usd.TimeCode.Default()))

    def test_keeps_authored_new_name(self):
        self.old.Set(MASSES)
        self.new.Set(Vt.FloatArray([0.5, 0.5]))
        rename_attribute(self.old, "newton:masses", self.stage.GetEditTarget())
        self.assertEqual(self.new.Get(), Vt.FloatArray([0.5, 0.5]))
        self.assertFalse(self.prim.HasAttribute("physics:masses"))

    def test_blocks_old_name_authored_in_another_layer(self):
        weak = Sdf.Layer.CreateAnonymous(".usda")
        root = Sdf.Layer.CreateAnonymous(".usda")
        root.subLayerPaths.append(weak.identifier)
        stage = Usd.Stage.Open(root)
        with Usd.EditContext(stage, Usd.EditTarget(weak)):
            prim = define_particles(stage)
            author_old_masses(prim).Set(MASSES)
        rename_attribute(prim.GetAttribute("physics:masses"), "newton:masses", stage.GetEditTarget())
        self.assertEqual(prim.GetAttribute("newton:masses").Get(), MASSES)
        self.assertFalse(prim.GetAttribute("physics:masses").HasAuthoredValue())
        self.assertIsNotNone(weak.GetAttributeAtPath("/Particles.physics:masses"))
        self.assertIsNotNone(root.GetAttributeAtPath("/Particles.newton:masses"))


class TestRenamedAttributesValidator(ValidatorTestCase):
    validator_name = validators.RENAMED_ATTRIBUTES_VALIDATOR

    def setUp(self):
        super().setUp()
        self.prim = define_particles(self.stage)

    def test_new_name(self):
        self.prim.GetAttribute("newton:masses").Set(MASSES)
        self.assertEqual(self.validate(self.prim), [])

    def test_old_name(self):
        attr = author_old_masses(self.prim)
        attr.Set(MASSES)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_old_name_time_samples(self):
        attr = author_old_masses(self.prim)
        attr.Set(MASSES, 1.0)
        self.assertEqual(self.validate(self.prim), [(ERROR, attr.GetPath())])

    def test_old_name_without_value(self):
        author_old_masses(self.prim)
        self.assertEqual(self.validate(self.prim), [])

    def test_blocked_old_name(self):
        attr = author_old_masses(self.prim)
        attr.Set(MASSES)
        attr.Block()
        self.assertEqual(self.validate(self.prim), [])

    def test_requires_api(self):
        prim = UsdGeom.Points.Define(self.stage, "/NotParticles").GetPrim()
        author_old_masses(prim).Set(MASSES)
        self.assertEqual(self.validate(prim), [])

    def test_old_name_defined_by_another_schema(self):
        self.prim.GetAttribute("points").Set(Vt.Vec3fArray([(0, 0, 0)]))
        with mock.patch.dict(_migration.RENAMED_ATTRIBUTES, {"NewtonPointsDeformableSimAPI": {"points": "newton:masses"}}):
            self.assertEqual(self.validate(self.prim), [])

    def test_selected_by_keyword(self):
        author_old_masses(self.prim).Set(MASSES)
        self.assertEqual(self.validate_with_keywords("NewtonMigration"), [ERROR])
        self.assertEqual(self.validate_with_keywords("NewtonPointsDeformableSimAPI"), [ERROR])

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer_registered(self):
        self.assertEqual([fixer.name for fixer in self.validator.GetFixers()], ["RenameAttribute"])
        fixer = self.validator.GetFixerByName("RenameAttribute")
        self.assertEqual(fixer.errorName, ERROR)
        self.assertTrue(fixer.description)

    @unittest.skipUnless(SUPPORTS_PYTHON_FIXERS, "Python fixers require OpenUSD 26.11 or newer")
    def test_fixer(self):
        # ApplyFix saves the edit target layer, so the stage must be file backed
        with tempfile.TemporaryDirectory() as tmpdir:
            stage = Usd.Stage.CreateNew((pathlib.Path(tmpdir) / "asset.usda").as_posix())
            prim = define_particles(stage)
            author_old_masses(prim).Set(MASSES)
            (error,) = self.validator.Validate(prim)
            (fixer,) = error.GetFixersByErrorName()
            self.assertTrue(fixer.CanApplyFix(error, stage.GetEditTarget()))
            self.assertTrue(fixer.ApplyFix(error, stage.GetEditTarget()))
            self.assertEqual(prim.GetAttribute("newton:masses").Get(), MASSES)
            self.assertFalse(prim.HasAttribute("physics:masses"))
            self.assertFalse(stage.GetRootLayer().dirty)
            self.assertEqual(self.validator.Validate(prim), [])


if __name__ == "__main__":
    unittest.main()
