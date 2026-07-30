# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

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
        self.assertTrue(self.points.HasRelationship("physics:simulationOwner"))

    def test_api_limitations(self):
        prim: Usd.Prim = self.stage.DefinePrim("/NotPoints", "Xform")
        self.assertFalse(prim.CanApplyAPI("NewtonParticleAPI"))

    def test_simulation_owner(self):
        self.points.ApplyAPI("NewtonParticleAPI")
        relationship = self.points.GetRelationship("physics:simulationOwner")
        self.assertTrue(relationship)
        self.assertEqual(relationship.GetTargets(), [])

        scene = UsdPhysics.Scene.Define(self.stage, "/Scene")
        self.assertTrue(relationship.SetTargets([scene.GetPath()]))
        self.assertEqual(relationship.GetTargets(), [scene.GetPath()])

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
        self.assertAlmostEqual(scene.GetAttribute("newton:mpm:voxelSize").Get(), 0.05)
        self.assertEqual(
            particles.GetRelationship("physics:simulationOwner").GetTargets(),
            [scene.GetPath()],
        )

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

        self.assertAlmostEqual(sand_material.GetAttribute("physics:density").Get(), 1600.0)
        self.assertAlmostEqual(sand_material.GetAttribute("newton:mpm:internalFriction").Get(), 0.68)
        self.assertAlmostEqual(sand_material.GetAttribute("newton:mpm:yieldPressure").Get(), 1.0e5)

        self.assertAlmostEqual(dense_material.GetAttribute("physics:density").Get(), 1900.0)
        self.assertAlmostEqual(
            dense_material.GetAttribute("newton:mpm:elasticDampingTime").Get(),
            0.02,
        )
        self.assertAlmostEqual(dense_material.GetAttribute("newton:mpm:internalFriction").Get(), 0.8)
        self.assertAlmostEqual(dense_material.GetAttribute("newton:mpm:yieldPressure").Get(), 2.0e5)

        points_binding = UsdShade.MaterialBindingAPI(particles)
        parent_material, _relationship = points_binding.ComputeBoundMaterial("physics")
        self.assertEqual(parent_material.GetPath(), sand_material.GetPath())
        self.assertEqual(
            points_binding.GetMaterialBindSubsetsFamilyType(),
            UsdGeom.Tokens.nonOverlapping,
        )
        self.assertEqual(subset.GetElementTypeAttr().Get(), UsdGeom.Tokens.point)
        self.assertEqual(subset.GetFamilyNameAttr().Get(), UsdShade.Tokens.materialBind)
        self.assertEqual(subset.GetIndicesAttr().Get(), Vt.IntArray([2, 3]))

        subset_binding = UsdShade.MaterialBindingAPI(subset.GetPrim())
        subset_material, _relationship = subset_binding.ComputeBoundMaterial("physics")
        self.assertEqual(subset_material.GetPath(), dense_material.GetPath())


if __name__ == "__main__":
    unittest.main()
