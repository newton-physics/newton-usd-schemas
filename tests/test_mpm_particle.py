# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import pathlib
import tempfile
import unittest

from pxr import Plug, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

import newton_usd_schemas  # noqa: F401


def _assert_sand_stage(stage):
    scene = stage.GetPrimAtPath("/World/PhysicsScene")
    particles = stage.GetPrimAtPath("/World/Sand")
    sand_material = stage.GetPrimAtPath("/World/SandMaterial")
    dense_material = stage.GetPrimAtPath("/World/DenseSandMaterial")
    subset = UsdGeom.Subset(stage.GetPrimAtPath("/World/Sand/DenseSand"))

    assert scene.HasAPI("NewtonSceneAPI")
    assert scene.HasAPI("NewtonMPMSceneAPI")
    assert particles.HasAPI("NewtonMPMParticleAPI")
    assert sand_material.HasAPI("PhysicsMaterialAPI")
    assert sand_material.HasAPI("NewtonMPMMaterialAPI")
    assert dense_material.HasAPI("PhysicsMaterialAPI")
    assert dense_material.HasAPI("NewtonMPMMaterialAPI")

    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
    assert UsdPhysics.GetStageKilogramsPerUnit(stage) == 1.0
    assert scene.GetAttribute("newton:maxSolverIterations").Get() == 100
    assert scene.GetAttribute("newton:mpm:rheologySolvers").Get() == Vt.TokenArray(["cg", "gs"])
    assert math.isclose(scene.GetAttribute("newton:mpm:voxelSize").Get(), 0.05, rel_tol=1.0e-6)

    points = UsdGeom.Points(particles)
    assert points.GetPointsAttr().Get() == Vt.Vec3fArray(
        [
            (-0.025, -0.025, 0.5),
            (0.025, -0.025, 0.5),
            (-0.025, 0.025, 0.5),
            (0.025, 0.025, 0.5),
        ]
    )
    assert points.GetVelocitiesAttr().Get() == Vt.Vec3fArray([(0, 0, 0)] * 4)
    assert points.GetWidthsAttr().Get() == Vt.FloatArray([0.05] * 4)
    assert points.GetIdsAttr().Get() == Vt.Int64Array([0, 1, 2, 3])

    expected_material_values = {
        sand_material: {
            "physics:density": 1600.0,
            "newton:mpm:internalFriction": 0.68,
            "newton:mpm:poissonsRatio": 0.3,
            "newton:mpm:youngsModulus": 1.0e7,
            "newton:mpm:yieldPressure": 1.0e5,
        },
        dense_material: {
            "physics:density": 1900.0,
            "newton:mpm:elasticDampingTime": 0.02,
            "newton:mpm:internalFriction": 0.8,
            "newton:mpm:poissonsRatio": 0.25,
            "newton:mpm:youngsModulus": 2.0e7,
            "newton:mpm:yieldPressure": 2.0e5,
        },
    }
    for material, values in expected_material_values.items():
        for name, value in values.items():
            assert math.isclose(material.GetAttribute(name).Get(), value, rel_tol=1.0e-6)

    points_binding = UsdShade.MaterialBindingAPI(particles)
    parent_material, _relationship = points_binding.ComputeBoundMaterial("physics")
    assert parent_material.GetPath() == sand_material.GetPath()
    assert points_binding.GetMaterialBindSubsetsFamilyType() == UsdGeom.Tokens.nonOverlapping
    assert subset.GetElementTypeAttr().Get() == UsdGeom.Tokens.point
    assert subset.GetFamilyNameAttr().Get() == UsdShade.Tokens.materialBind
    assert subset.GetIndicesAttr().Get() == Vt.IntArray([2, 3])

    subset_binding = UsdShade.MaterialBindingAPI(subset.GetPrim())
    subset_material, _relationship = subset_binding.ComputeBoundMaterial("physics")
    assert subset_material.GetPath() == dense_material.GetPath()


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
        _assert_sand_stage(stage)

        with tempfile.TemporaryDirectory() as directory:
            exported = pathlib.Path(directory) / "sand_round_trip.usda"
            self.assertTrue(stage.Export(exported.as_posix()))
            reopened = Usd.Stage.Open(exported.as_posix())
            self.assertTrue(reopened)
            _assert_sand_stage(reopened)


if __name__ == "__main__":
    unittest.main()
