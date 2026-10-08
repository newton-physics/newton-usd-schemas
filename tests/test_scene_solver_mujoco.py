# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import unittest

from pxr import Plug, Sdf, Usd, UsdPhysics

import newton_usd_schemas

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)

# (attribute name, default value, hard minimum or None)
ATTRIBUTES = [
    ("newton:mujoco:njmax", -1, -1),
    ("newton:mujoco:njmax_nnz", -1, -1),
    ("newton:mujoco:nconmax", -1, -1),
    ("newton:mujoco:useMujocoCpu", False, None),
    ("newton:mujoco:useMujocoContacts", True, None),
    ("newton:mujoco:enableSleeping", False, None),
    ("newton:mujoco:nvmax", -1, -1),
    ("newton:mujoco:updateDataInterval", 1, 0),
    ("newton:mujoco:includeSites", True, None),
    ("newton:mujoco:skipVisualOnlyGeoms", True, None),
]


class TestNewtonMuJoCoSceneAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.scene: Usd.Prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMuJoCoSceneAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMuJoCoSceneAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMuJoCoSceneAPI")
        self.assertEqual(schema_type, "NewtonMuJoCoSceneAPI")

    def test_api_application(self):
        self.assertTrue(self.scene.CanApplyAPI("NewtonMuJoCoSceneAPI"))
        self.scene.ApplyAPI("NewtonMuJoCoSceneAPI")
        self.assertTrue(self.scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(self.scene.HasAPI("NewtonMuJoCoSceneAPI"))
        self.assertTrue(self.scene.HasAttribute("newton:maxSolverIterations"))

    def test_includes_mjc_scene_api(self):
        # The MjcSceneAPI plugin is not a dependency, so check the declared inclusion rather than the applied schemas.
        layer = Sdf.Layer.FindOrOpen((pathlib.Path(newton_usd_schemas.__file__).parent / "generatedSchema.usda").as_posix())
        api_schemas = layer.GetPrimAtPath("/NewtonMuJoCoSceneAPI").GetInfo("apiSchemas")
        self.assertEqual(list(api_schemas.GetAddedOrExplicitItems()), ["NewtonSceneAPI", "MjcSceneAPI"])

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotScene", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMuJoCoSceneAPI"))

    def test_attribute_defaults(self):
        self.scene.ApplyAPI("NewtonMuJoCoSceneAPI")
        for name, default, _ in ATTRIBUTES:
            with self.subTest(attribute=name):
                attr = self.scene.GetAttribute(name)
                self.assertTrue(attr, f"{name} is not defined")
                self.assertAlmostEqual(attr.Get(), default, places=6)

    def test_attribute_set(self):
        self.scene.ApplyAPI("NewtonMuJoCoSceneAPI")
        for name, default, _ in ATTRIBUTES:
            with self.subTest(attribute=name):
                attr = self.scene.GetAttribute(name)
                value = (not default) if isinstance(default, bool) else default + 5
                self.assertTrue(attr.Set(value))
                self.assertAlmostEqual(attr.Get(), value, places=6)

    def test_deterministic(self):
        self.scene.ApplyAPI("NewtonMuJoCoSceneAPI")
        attr = self.scene.GetAttribute("newton:mujoco:deterministic")
        self.assertEqual(attr.Get(), "inherit")
        for token in ("notGuaranteed", "runToRun", "gpuToGpu"):
            self.assertTrue(attr.Set(token))
            self.assertEqual(attr.Get(), token)

    @unittest.skipUnless(USD_HAS_LIMITS, "Attribute limits require a newer USD")
    def test_attribute_limits(self):
        self.scene.ApplyAPI("NewtonMuJoCoSceneAPI")
        for name, _, minimum in ATTRIBUTES:
            if minimum is None:
                continue
            with self.subTest(attribute=name):
                hard = self.scene.GetAttribute(name).GetHardLimits()
                self.assertTrue(hard.IsValid())
                self.assertAlmostEqual(hard.GetMinimum(), minimum)


if __name__ == "__main__":
    unittest.main()
