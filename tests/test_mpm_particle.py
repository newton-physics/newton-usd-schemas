# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import pathlib
import tempfile
import unittest

from pxr import Plug, Usd, UsdGeom, UsdShade, Vt

import newton_usd_schemas  # noqa: F401


class TestNewtonMPMParticleAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.points: Usd.Prim = UsdGeom.Points.Define(self.stage, "/Particles").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMPMParticleAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMPMParticleAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMPMParticleAPI")
        self.assertEqual(schema_type, "NewtonMPMParticleAPI")

    def test_api_application_and_limitations(self):
        self.assertTrue(self.points.CanApplyAPI("NewtonMPMParticleAPI"))
        self.points.ApplyAPI("NewtonMPMParticleAPI")
        self.assertTrue(self.points.HasAPI("NewtonMPMParticleAPI"))

        prim: Usd.Prim = self.stage.DefinePrim("/NotPoints", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonMPMParticleAPI"))

    def test_api_is_an_attribute_free_marker(self):
        property_names = set(self.points.GetPropertyNames())
        self.points.ApplyAPI("NewtonMPMParticleAPI")
        self.assertEqual(set(self.points.GetPropertyNames()), property_names)

    def test_point_geom_subset_can_bind_a_physics_material(self):
        self.points.ApplyAPI("NewtonMPMParticleAPI")
        UsdGeom.Points(self.points).CreatePointsAttr([(0, 0, 0), (1, 0, 0)])
        material = UsdShade.Material.Define(self.stage, "/Material")
        material.GetPrim().ApplyAPI("NewtonMPMMaterialAPI")

        points_binding = UsdShade.MaterialBindingAPI.Apply(self.points)
        subset = points_binding.CreateMaterialBindSubset("MaterialA", Vt.IntArray([1]), UsdGeom.Tokens.point)
        subset_binding = UsdShade.MaterialBindingAPI.Apply(subset.GetPrim())
        self.assertTrue(subset_binding.Bind(material, materialPurpose="physics"))

        self.assertEqual(subset.GetElementTypeAttr().Get(), UsdGeom.Tokens.point)
        self.assertEqual(subset.GetFamilyNameAttr().Get(), UsdShade.Tokens.materialBind)
        self.assertEqual(points_binding.GetMaterialBindSubsetsFamilyType(), UsdGeom.Tokens.nonOverlapping)
        bound_material, _relationship = subset_binding.ComputeBoundMaterial("physics")
        self.assertEqual(bound_material.GetPath(), material.GetPath())

    def test_sand_fixture_round_trip(self):
        fixture = pathlib.Path(__file__).parent / "assets" / "sand.usda"
        stage = Usd.Stage.Open(fixture.as_posix())
        self.assertTrue(stage)

        scene = stage.GetPrimAtPath("/World/PhysicsScene")
        particles = stage.GetPrimAtPath("/World/Sand")
        material = stage.GetPrimAtPath("/World/SandMaterial")
        self.assertTrue(scene.HasAPI("NewtonMPMSceneAPI"))
        self.assertTrue(particles.HasAPI("NewtonMPMParticleAPI"))
        self.assertTrue(material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertEqual(len(UsdGeom.Points(particles).GetPointsAttr().Get()), 4)

        bound_material, _relationship = UsdShade.MaterialBindingAPI(particles).ComputeBoundMaterial("physics")
        self.assertEqual(bound_material.GetPath(), material.GetPath())

        with tempfile.TemporaryDirectory() as directory:
            exported = pathlib.Path(directory) / "sand_round_trip.usda"
            self.assertTrue(stage.Export(exported.as_posix()))
            reopened = Usd.Stage.Open(exported.as_posix())
            reopened_particles = reopened.GetPrimAtPath("/World/Sand")
            self.assertTrue(reopened_particles.HasAPI("NewtonMPMParticleAPI"))
            self.assertEqual(
                UsdGeom.Points(reopened_particles).GetPointsAttr().Get(),
                UsdGeom.Points(particles).GetPointsAttr().Get(),
            )
            self.assertEqual(
                reopened.GetPrimAtPath("/World/PhysicsScene").GetAttribute("newton:mpm:rheologySolvers").Get(),
                Vt.TokenArray(["cg", "gs"]),
            )


if __name__ == "__main__":
    unittest.main()
