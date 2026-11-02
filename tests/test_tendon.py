# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import pathlib
import unittest

from pxr import Gf, Plug, Sdf, Usd, UsdGeom, UsdPhysics

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class _SchemaAssertions:
    def check_registration(self, name):
        self.assertEqual(
            Plug.Registry().FindTypeByName(name.replace("Newton", "NewtonPhysics", 1)).typeName, name.replace("Newton", "NewtonPhysics", 1)
        )
        self.assertEqual(Usd.SchemaRegistry().GetSchemaTypeName(name.replace("Newton", "NewtonPhysics", 1)), name)

    def check_property(self, api, name, fallback, value, *, minimum=None, maximum=None, tokens=None):
        self.assertFalse(self.prim.HasAttribute(name))
        self.assertTrue(self.prim.ApplyAPI(api))
        attr = self.prim.GetAttribute(name)
        self.assertTrue(attr)
        self.assertFalse(attr.IsCustom())
        types = {bool: Sdf.ValueTypeNames.Bool, int: Sdf.ValueTypeNames.Int, float: Sdf.ValueTypeNames.Float, str: Sdf.ValueTypeNames.Token}
        self.assertEqual(attr.GetTypeName(), types[type(value)])
        self.assertFalse(attr.HasAuthoredValue())
        if isinstance(fallback, float):
            self.assertAlmostEqual(attr.Get(), fallback)
        else:
            self.assertEqual(attr.Get(), fallback)
        self.assertTrue(attr.Set(value))
        self.assertTrue(attr.HasAuthoredValue())
        if isinstance(value, float):
            self.assertAlmostEqual(attr.Get(), value)
        else:
            self.assertEqual(attr.Get(), value)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        if tokens is not None:
            self.assertEqual(list(attr.GetMetadata("allowedTokens")), tokens)
        if USD_HAS_LIMITS and (minimum is not None or maximum is not None):
            limits = attr.GetHardLimits()
            self.assertTrue(limits.IsValid())
            self.assertEqual(limits.GetMinimum(), minimum)
            self.assertEqual(limits.GetMaximum(), maximum)

    def check_api(self, name, properties):
        self.check_registration(name)
        self.assertFalse(self.prim.HasAPI(name))
        self.assertTrue(self.prim.CanApplyAPI(name))
        self.assertTrue(self.prim.ApplyAPI(name))
        self.assertTrue(self.prim.HasAPI(name))
        definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition(name)
        self.assertEqual(sorted(definition.GetPropertyNames()), sorted(properties))
        for prop in properties:
            self.assertTrue(self.prim.HasProperty(prop), prop)
        for prim_type in ("Xform", "Sphere", "NewtonTendon", "PhysicsScene"):
            other = self.stage.DefinePrim(f"/NotGuide{prim_type}", prim_type)
            self.assertFalse(other.CanApplyAPI(name))


class TestNewtonTendon(_SchemaAssertions, unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = self.stage.DefinePrim("/Tendon", "NewtonTendon")

    def test_registration(self):
        """Register the native tendon independently of provider schemas."""
        self.check_registration("NewtonTendon")
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonTendon")
        self.assertEqual(sorted(definition.GetPropertyNames()), ["newton:tendon:guides", "physics:simulationOwner"])

    def test_guides(self):
        """Preserve explicitly authored route order rather than sorting paths."""
        before = self.stage.DefinePrim("/Before", "Scope")
        self.assertFalse(before.HasRelationship("newton:tendon:guides"))
        rel = self.prim.GetRelationship("newton:tendon:guides")
        self.assertTrue(rel)
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])
        paths = [Sdf.Path(f"/Tendon/{name}") for name in ("Start", "ZRoller", "APinhole", "End")]
        for path in paths:
            self.stage.DefinePrim(path, "NewtonTendonGuide")
        self.assertTrue(rel.SetTargets(paths))
        self.assertTrue(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), paths)

    def test_simulation_owner(self):
        """Associate a tendon with a scene without serializing world indices."""
        self.assertFalse(self.stage.DefinePrim("/Before", "Scope").HasRelationship("physics:simulationOwner"))
        rel = self.prim.GetRelationship("physics:simulationOwner")
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])
        scene = UsdPhysics.Scene.Define(self.stage, "/Scene")
        self.assertTrue(rel.SetTargets([scene.GetPath()]))
        self.assertEqual(rel.GetTargets(), [scene.GetPath()])

    def test_no_collision_geometry(self):
        """Keep tendon and guide prims independent of imageable collision geometry."""
        guide = self.stage.DefinePrim("/Tendon/Guide", "NewtonTendonGuide")
        for prim in (self.prim, guide):
            self.assertFalse(prim.IsA(UsdGeom.Imageable))
            self.assertFalse(prim.IsA(UsdGeom.Xformable))
            self.assertFalse(prim.HasAPI(UsdPhysics.CollisionAPI))
        root = self.stage.DefinePrim("/World", "Xform")
        self.stage.DefinePrim("/World/Tendon", "NewtonTendon")
        self.stage.DefinePrim("/World/Tendon/Guide", "NewtonTendonGuide")
        cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_])
        self.assertTrue(cache.ComputeWorldBound(root).GetRange().IsEmpty())


class TestNewtonTendonGuide(_SchemaAssertions, unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = self.stage.DefinePrim("/Guide", "NewtonTendonGuide")

    def test_registration(self):
        """Register only the common body and pose properties on a guide."""
        self.check_registration("NewtonTendonGuide")
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonTendonGuide")
        self.assertEqual(sorted(definition.GetPropertyNames()), ["newton:tendon:body", "newton:tendon:localPos", "newton:tendon:localRot"])

    def test_body(self):
        """Represent world attachment with an empty body relationship."""
        self.assertFalse(self.stage.DefinePrim("/Before", "Scope").HasRelationship("newton:tendon:body"))
        rel = self.prim.GetRelationship("newton:tendon:body")
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])
        body = UsdGeom.Xform.Define(self.stage, "/Body").GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(body)
        self.assertTrue(rel.SetTargets([body.GetPath()]))
        self.assertTrue(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [body.GetPath()])
        self.assertTrue(rel.SetTargets([]))
        self.assertEqual(rel.GetTargets(), [])

    def test_broken_body_target(self):
        """Preserve a broken body reference so an importer can distinguish it from world attachment."""
        rel = self.prim.GetRelationship("newton:tendon:body")
        path = Sdf.Path("/MissingBody")
        rel.SetTargets([path])
        self.assertEqual(rel.GetTargets(), [path])
        self.assertFalse(self.stage.GetPrimAtPath(path))

    def test_local_position(self):
        """Store the guide point or profile origin in its attachment frame."""
        self.assertFalse(self.stage.DefinePrim("/Before", "Scope").HasAttribute("newton:tendon:localPos"))
        attr = self.prim.GetAttribute("newton:tendon:localPos")
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Point3f)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), Gf.Vec3f(0))
        self.assertTrue(attr.Set(Gf.Vec3f(1, 2, 3)))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), Gf.Vec3f(1, 2, 3))
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)

    def test_local_rotation(self):
        """Store a full orientation whose local Z axis defines the roller normal."""
        self.assertFalse(self.stage.DefinePrim("/Before", "Scope").HasAttribute("newton:tendon:localRot"))
        attr = self.prim.GetAttribute("newton:tendon:localRot")
        self.assertEqual(attr.GetTypeName(), Sdf.ValueTypeNames.Quatf)
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), Gf.Quatf(1))
        rotation = Gf.Quatf(math.sqrt(0.5), math.sqrt(0.5), 0, 0)
        self.assertTrue(attr.Set(rotation))
        self.assertTrue(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), rotation)
        self.assertEqual(attr.GetVariability(), Sdf.VariabilityUniform)
        self.assertTrue(Gf.IsClose(attr.Get().Transform(Gf.Vec3f(0, 0, 1)), Gf.Vec3f(0, -1, 0), 1e-6))

    def test_anchor_api(self):
        """Mark an anchor without adding roller or material parameters."""
        self.check_api("NewtonTendonAnchorAPI", [])
        self.assertFalse(self.prim.HasAttribute("newton:tendon:friction"))
        self.assertFalse(self.prim.HasAttribute("newton:roller:radius"))
        self.assertFalse(self.prim.HasAttribute("newton:tendon:span:compliance"))

    def test_pinhole_api(self):
        """Add only capstan friction to a pinhole guide."""
        self.check_api("NewtonTendonPinholeAPI", ["newton:tendon:friction"])
        self.assertFalse(self.prim.HasAttribute("newton:roller:radius"))

    def test_pinhole_friction(self):
        """Define zero friction by default and permit finite capstan friction."""
        self.check_property("NewtonTendonPinholeAPI", "newton:tendon:friction", 0.0, 0.25, minimum=0.0)

    def test_roller_api(self):
        """Separate roller behavior from the independently applied profile."""
        self.check_api("NewtonTendonRollerAPI", ["newton:tendon:friction", "newton:tendon:winding", "newton:tendon:dynamic"])
        self.assertFalse(self.prim.HasAttribute("newton:roller:radius"))

    def test_roller_friction(self):
        """Define the roller's dimensionless capstan friction coefficient."""
        self.check_property("NewtonTendonRollerAPI", "newton:tendon:friction", 0.0, 0.3, minimum=0.0)

    def test_winding(self):
        """Author the native winding sign independently of the guide rotation."""
        self.check_property("NewtonTendonRollerAPI", "newton:tendon:winding", 1, -1, minimum=-1, maximum=1)

    def test_dynamic(self):
        """Opt into routing activation without changing the attached body's dynamics."""
        self.check_property("NewtonTendonRollerAPI", "newton:tendon:dynamic", False, True)

    def test_circle_api(self):
        """Register a separate circular profile rather than a collision shape."""
        self.check_api("NewtonRollerCircleAPI", ["newton:roller:radius"])
        self.assertFalse(self.prim.HasAPI(UsdPhysics.CollisionAPI))

    def test_radius(self):
        """Require an authored circular radius instead of an arbitrary fallback size."""
        self.check_property("NewtonRollerCircleAPI", "newton:roller:radius", None, 0.02, minimum=0.0)

    def test_span_api(self):
        """Add incoming-span properties independently of the guide kind."""
        self.check_api("NewtonTendonSpanAPI", ["newton:tendon:span:restLength", "newton:tendon:span:compliance", "newton:tendon:span:damping"])

    def test_rest_length(self):
        """Default to geometry-measured rest length and permit explicit pre-tension."""
        self.check_property("NewtonTendonSpanAPI", "newton:tendon:span:restLength", -1.0, 0.2)
        if USD_HAS_LIMITS:
            limits = self.prim.GetAttribute("newton:tendon:span:restLength").GetSoftLimits()
            self.assertEqual(limits.GetMinimum(), 0.0)
            self.assertIsNone(limits.GetMaximum())

    def test_compliance(self):
        """Default to an inextensible span and allow positive compliance."""
        self.check_property("NewtonTendonSpanAPI", "newton:tendon:span:compliance", 0.0, 0.001, minimum=0.0)

    def test_damping(self):
        """Default to no damping and allow nonnegative span damping."""
        self.check_property("NewtonTendonSpanAPI", "newton:tendon:span:damping", 0.0, 0.1, minimum=0.0)


class TestNewtonTendonSceneAPI(_SchemaAssertions, unittest.TestCase):
    def setUp(self):
        self.stage = Usd.Stage.CreateInMemory()
        self.prim = UsdPhysics.Scene.Define(self.stage, "/Scene").GetPrim()

    def test_registration(self):
        """Register shared settings for the native tendon-capable solvers."""
        self.check_registration("NewtonTendonSceneAPI")

    def test_application(self):
        """Compose shared tendon settings alongside either XPBD or VBD settings."""
        self.prim.ApplyAPI("NewtonTendonSceneAPI")
        self.assertTrue(self.prim.HasAPI("NewtonSceneAPI"))
        names = {"materialSolver", "maxSweeps", "settleTolerance", "settleAbsoluteTolerance", "activationTolerance"}
        definition = Usd.SchemaRegistry().FindAppliedAPIPrimDefinition("NewtonTendonSceneAPI")
        self.assertEqual(
            {name for name in definition.GetPropertyNames() if name.startswith("newton:tendon:")}, {f"newton:tendon:{name}" for name in names}
        )
        for solver_api in ("NewtonXpbdSceneAPI", "NewtonVbdSceneAPI"):
            with self.subTest(solver=solver_api):
                prim = UsdPhysics.Scene.Define(self.stage, f"/{solver_api}").GetPrim()
                self.assertFalse(prim.HasAPI("NewtonTendonSceneAPI"))
                self.assertTrue(prim.CanApplyAPI("NewtonTendonSceneAPI"))
                prim.ApplyAPI(solver_api)
                prim.ApplyAPI("NewtonTendonSceneAPI")
                self.assertTrue(prim.HasAPI(solver_api))
                self.assertTrue(prim.HasAPI("NewtonSceneAPI"))
                self.assertTrue(prim.HasAPI("NewtonTendonSceneAPI"))
                for prop in names:
                    self.assertTrue(prim.HasAttribute(f"newton:tendon:{prop}"))

    def test_applicability(self):
        """Keep solver controls off tendons, guides, and bodies."""
        for prim_type in ("Xform", "NewtonTendon", "NewtonTendonGuide"):
            self.assertFalse(self.stage.DefinePrim(f"/NotScene{prim_type}", prim_type).CanApplyAPI("NewtonTendonSceneAPI"))

    def test_material_solver(self):
        """Expose only the implemented sweeps mode in the initial schema."""
        self.check_property("NewtonTendonSceneAPI", "newton:tendon:materialSolver", "sweeps", "sweeps", tokens=["sweeps"])

    def test_max_sweeps(self):
        """Represent the positive sweep budget without freezing a runtime-specific cap."""
        self.check_property("NewtonTendonSceneAPI", "newton:tendon:maxSweeps", 256, 64, minimum=1)

    def test_activation_tolerance(self):
        """Express activation hysteresis as a radius-relative gap."""
        self.check_property("NewtonTendonSceneAPI", "newton:tendon:activationTolerance", 0.002, 0.005, minimum=0.0, maximum=1.0)

    def test_settle_tolerance(self):
        """Author the dimensionless relative force-residual tolerance."""
        self.check_property("NewtonTendonSceneAPI", "newton:tendon:settleTolerance", 0.001, 0.0, minimum=0.0)

    def test_settle_absolute_tolerance(self):
        """Author the absolute force-residual tolerance separately from relative tolerance."""
        self.check_property("NewtonTendonSceneAPI", "newton:tendon:settleAbsoluteTolerance", 1e-6, 1e-5, minimum=0.0)


class TestNewtonTendonAsset(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).parent / "assets" / "tendon.usda"
        self.stage = Usd.Stage.Open(self.path.as_posix())

    def test_authored_route(self):
        """Read all guide kinds in authored order with material data only on incoming spans."""
        tendon = self.stage.GetPrimAtPath("/Rig/Cable")
        self.assertEqual(tendon.GetTypeName(), "NewtonTendon")
        paths = tendon.GetRelationship("newton:tendon:guides").GetTargets()
        self.assertEqual([path.name for path in paths], ["Start", "Pinhole", "Roller", "End"])
        self.assertEqual(len(paths), len(set(paths)))
        expected = ["NewtonTendonAnchorAPI", "NewtonTendonPinholeAPI", "NewtonTendonRollerAPI", "NewtonTendonAnchorAPI"]
        kinds = set(expected)
        for index, (path, kind) in enumerate(zip(paths, expected, strict=True)):
            prim = self.stage.GetPrimAtPath(path)
            self.assertEqual(prim.GetTypeName(), "NewtonTendonGuide")
            self.assertEqual(set(prim.GetAppliedSchemas()) & kinds, {kind})
            self.assertEqual(prim.HasAPI("NewtonTendonSpanAPI"), index > 0)
            if index > 0:
                self.assertEqual(prim.GetAttribute("newton:tendon:span:restLength").Get(), -1.0)
                self.assertGreater(prim.GetAttribute("newton:tendon:span:compliance").Get(), 0)
                self.assertGreater(prim.GetAttribute("newton:tendon:span:damping").Get(), 0)
        roller = self.stage.GetPrimAtPath(paths[2])
        self.assertTrue(roller.HasAPI("NewtonRollerCircleAPI"))
        self.assertGreater(roller.GetAttribute("newton:roller:radius").Get(), 0)
        self.assertTrue(roller.GetAttribute("newton:tendon:dynamic").Get())
        self.assertGreater(roller.GetAttribute("newton:tendon:friction").Get(), 0)

    def test_attachments_and_units(self):
        """Distinguish authored world/body attachment and declare the fixture's physical units."""
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(self.stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(self.stage), 1.0)
        self.assertEqual(UsdGeom.GetStageUpAxis(self.stage), "Y")
        for name in ("Start", "Pinhole", "Roller"):
            self.assertEqual(self.stage.GetPrimAtPath(f"/Rig/Cable/{name}").GetRelationship("newton:tendon:body").GetTargets(), [])
        end = self.stage.GetPrimAtPath("/Rig/Cable/End")
        targets = end.GetRelationship("newton:tendon:body").GetTargets()
        self.assertEqual(targets, [Sdf.Path("/Rig/Load")])
        self.assertTrue(self.stage.GetPrimAtPath(targets[0]).HasAPI(UsdPhysics.RigidBodyAPI))
        for path in ("/Rig/Cable", "/Rig/Load"):
            self.assertEqual(self.stage.GetPrimAtPath(path).GetRelationship("physics:simulationOwner").GetTargets(), [Sdf.Path("/Rig/Scene")])

    def test_reference_remapping(self):
        """Remap route, body and scene relationships independently in two referenced copies."""
        stage = Usd.Stage.CreateInMemory()
        for name in ("CopyB", "CopyA"):
            prim = stage.DefinePrim(f"/{name}")
            self.assertTrue(prim.GetReferences().AddReference(self.path.as_posix()))
            tendon = stage.GetPrimAtPath(f"/{name}/Cable")
            self.assertEqual(
                tendon.GetRelationship("newton:tendon:guides").GetTargets(),
                [Sdf.Path(f"/{name}/Cable/{guide}") for guide in ("Start", "Pinhole", "Roller", "End")],
            )
            self.assertEqual(tendon.GetRelationship("physics:simulationOwner").GetTargets(), [Sdf.Path(f"/{name}/Scene")])
            end = stage.GetPrimAtPath(f"/{name}/Cable/End")
            self.assertEqual(end.GetRelationship("newton:tendon:body").GetTargets(), [Sdf.Path(f"/{name}/Load")])
            start = stage.GetPrimAtPath(f"/{name}/Cable/Start")
            self.assertEqual(start.GetRelationship("newton:tendon:body").GetTargets(), [])

    def test_round_trip(self):
        """Preserve route order, APIs, fallbacks and authored values through a flattened USDA round trip."""
        layer = Sdf.Layer.CreateAnonymous("roundtrip.usda")
        self.assertTrue(layer.ImportFromString(self.stage.Flatten().ExportToString()))
        reopened = Usd.Stage.Open(layer)
        for prim in self.stage.Traverse():
            other = reopened.GetPrimAtPath(prim.GetPath())
            self.assertTrue(other)
            self.assertEqual(other.GetTypeName(), prim.GetTypeName())
            self.assertEqual(other.GetAppliedSchemas(), prim.GetAppliedSchemas())
            for rel in prim.GetRelationships():
                self.assertEqual(other.GetRelationship(rel.GetName()).GetTargets(), rel.GetTargets())
            for attr in prim.GetAttributes():
                self.assertEqual(other.GetAttribute(attr.GetName()).Get(), attr.Get())


if __name__ == "__main__":
    unittest.main()
