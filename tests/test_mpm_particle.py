# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import pathlib
import unittest

from pxr import Plug, Usd, UsdGeom, UsdPhysics, UsdShade, Vt

import newton_usd_schemas  # noqa: F401


class TestNewtonParticleAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.points: Usd.Prim = UsdGeom.Points.Define(self.stage, "/Particles").GetPrim()

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsParticleAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsParticleAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsParticleAPI")
        self.assertEqual(schema_type, "NewtonParticleAPI")

    def test_api_application(self):
        self.assertTrue(self.points.CanApplyAPI("NewtonParticleAPI"))
        self.points.ApplyAPI("NewtonParticleAPI")
        self.assertTrue(self.points.HasAPI("NewtonParticleAPI"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotPoints", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonParticleAPI"))

    def test_api_defines_simulation_owner(self):
        property_names = set(self.points.GetPropertyNames())
        self.points.ApplyAPI("NewtonParticleAPI")
        self.assertEqual(
            set(self.points.GetPropertyNames()),
            property_names | {"physics:simulationOwner"},
        )

    def test_point_geom_subset_can_bind_a_physics_material(self):
        self.points.ApplyAPI("NewtonParticleAPI")
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

    def test_sand_fixture(self):
        fixture = pathlib.Path(__file__).parent / "assets" / "sand.usda"
        stage = Usd.Stage.Open(fixture.as_posix())
        self.assertTrue(stage)
        scene = stage.GetPrimAtPath("/World/PhysicsScene")
        particles = stage.GetPrimAtPath("/World/Sand")
        sand_material = stage.GetPrimAtPath("/World/SandMaterial")
        dense_material = stage.GetPrimAtPath("/World/DenseSandMaterial")
        subset = UsdGeom.Subset(stage.GetPrimAtPath("/World/Sand/DenseSand"))

        self.assertTrue(scene.HasAPI("NewtonSceneAPI"))
        self.assertTrue(scene.HasAPI("NewtonMPMSceneAPI"))
        self.assertTrue(particles.HasAPI("NewtonParticleAPI"))
        self.assertEqual(
            particles.GetRelationship("physics:simulationOwner").GetTargets(),
            [scene.GetPath()],
        )
        self.assertTrue(sand_material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(sand_material.HasAPI("NewtonMPMMaterialAPI"))
        self.assertTrue(dense_material.HasAPI("PhysicsMaterialAPI"))
        self.assertTrue(dense_material.HasAPI("NewtonMPMMaterialAPI"))

        self.assertEqual(UsdGeom.GetStageMetersPerUnit(stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(stage), 1.0)
        self.assertEqual(scene.GetAttribute("newton:maxSolverIterations").Get(), 100)
        self.assertEqual(
            scene.GetAttribute("newton:mpm:rheologySolvers").Get(),
            Vt.TokenArray(["cg", "gauss-seidel"]),
        )
        self.assertTrue(math.isclose(scene.GetAttribute("newton:mpm:voxelSize").Get(), 0.05, rel_tol=1.0e-6))

        points = UsdGeom.Points(particles)
        self.assertEqual(
            points.GetPointsAttr().Get(),
            Vt.Vec3fArray(
                [
                    (-0.025, -0.025, 0.5),
                    (0.025, -0.025, 0.5),
                    (-0.025, 0.025, 0.5),
                    (0.025, 0.025, 0.5),
                ]
            ),
        )
        self.assertEqual(points.GetVelocitiesAttr().Get(), Vt.Vec3fArray([(0, 0, 0)] * 4))
        self.assertEqual(points.GetWidthsAttr().Get(), Vt.FloatArray([0.05] * 4))
        self.assertEqual(points.GetIdsAttr().Get(), Vt.Int64Array([0, 1, 2, 3]))

        expected_material_values = {
            sand_material: {
                "physics:density": 1600.0,
                "newton:mpm:internalFriction": 0.68,
                "newton:mpm:yieldPressure": 1.0e5,
            },
            dense_material: {
                "physics:density": 1900.0,
                "newton:mpm:elasticDampingTime": 0.02,
                "newton:mpm:internalFriction": 0.8,
                "newton:mpm:yieldPressure": 2.0e5,
            },
        }
        for material, values in expected_material_values.items():
            for name, value in values.items():
                self.assertTrue(math.isclose(material.GetAttribute(name).Get(), value, rel_tol=1.0e-6))

        points_binding = UsdShade.MaterialBindingAPI(particles)
        parent_material, _relationship = points_binding.ComputeBoundMaterial("physics")
        self.assertEqual(parent_material.GetPath(), sand_material.GetPath())
        self.assertEqual(points_binding.GetMaterialBindSubsetsFamilyType(), UsdGeom.Tokens.nonOverlapping)
        self.assertEqual(subset.GetElementTypeAttr().Get(), UsdGeom.Tokens.point)
        self.assertEqual(subset.GetFamilyNameAttr().Get(), UsdShade.Tokens.materialBind)
        self.assertEqual(subset.GetIndicesAttr().Get(), Vt.IntArray([2, 3]))

        subset_binding = UsdShade.MaterialBindingAPI(subset.GetPrim())
        subset_material, _relationship = subset_binding.ComputeBoundMaterial("physics")
        self.assertEqual(subset_material.GetPath(), dense_material.GetPath())


if __name__ == "__main__":
    unittest.main()
