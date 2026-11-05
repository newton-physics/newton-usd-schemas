# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

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
        """Register the guide's reference to a USD placement frame."""
        self.check_registration("NewtonTendonGuide")
        definition = Usd.SchemaRegistry().FindConcretePrimDefinition("NewtonTendonGuide")
        self.assertEqual(list(definition.GetPropertyNames()), ["newton:tendon:frame"])

    def test_frame(self):
        """Author a placement relationship targeting an Xform or an existing site."""
        self.assertFalse(self.stage.DefinePrim("/Before", "Scope").HasRelationship("newton:tendon:frame"))
        rel = self.prim.GetRelationship("newton:tendon:frame")
        self.assertTrue(rel)
        self.assertFalse(rel.IsCustom())
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])
        frame = UsdGeom.Xform.Define(self.stage, "/Frame").GetPrim()
        site = UsdGeom.Sphere.Define(self.stage, "/Site").GetPrim()
        self.assertTrue(site.ApplyAPI("NewtonSiteAPI"))
        for target in (frame, site):
            with self.subTest(target=target.GetPath()):
                self.assertTrue(rel.SetTargets([target.GetPath()]))
                self.assertTrue(rel.HasAuthoredTargets())
                self.assertEqual(rel.GetTargets(), [target.GetPath()])
        # USD can represent empty targets even though this relationship requires a frame.
        self.assertTrue(rel.SetTargets([]))
        self.assertEqual(rel.GetTargets(), [])

    def test_broken_frame_target(self):
        """Preserve authored frame paths even when the target is missing."""
        rel = self.prim.GetRelationship("newton:tendon:frame")
        path = Sdf.Path("/MissingFrame")
        rel.SetTargets([path])
        self.assertEqual(rel.GetTargets(), [path])
        self.assertFalse(self.stage.GetPrimAtPath(path))

    def test_removed_explicit_pose(self):
        """Keep body and pose information on the referenced USD hierarchy."""
        for name in ("body", "localPos", "localRot"):
            self.assertFalse(self.prim.HasProperty(f"newton:tendon:{name}"))

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
        """Check the supported material-solver token."""
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
        self.stage.SetEditTarget(self.stage.GetSessionLayer())

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
            self.assertEqual(prim.GetParent(), tendon)
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
        """Locate world and body frames while retaining guide parameters under the tendon."""
        self.assertEqual(UsdGeom.GetStageMetersPerUnit(self.stage), 1.0)
        self.assertEqual(UsdPhysics.GetStageKilogramsPerUnit(self.stage), 1.0)
        self.assertEqual(UsdGeom.GetStageUpAxis(self.stage), "Y")
        expected = (
            ("Start", "/Rig/Frames/Start", None),
            ("Pinhole", "/Rig/Frames/Pinhole", None),
            ("Roller", "/Rig/Pulley/GuideFrame", "/Rig/Pulley"),
            ("End", "/Rig/Load/AttachmentSite", "/Rig/Load"),
        )
        for name, frame_path, body_path in expected:
            guide = self.stage.GetPrimAtPath(f"/Rig/Cable/{name}")
            targets = guide.GetRelationship("newton:tendon:frame").GetTargets()
            self.assertEqual(targets, [Sdf.Path(frame_path)])
            frame = self.stage.GetPrimAtPath(targets[0])
            self.assertTrue(frame.IsA(UsdGeom.Xformable))
            self.assertFalse(any(prop.GetName().startswith(("newton:tendon:", "newton:roller:")) for prop in frame.GetProperties()))
            body = frame
            while body and not body.HasAPI(UsdPhysics.RigidBodyAPI):
                body = body.GetParent()
            self.assertEqual(str(body.GetPath()) if body else None, body_path)
        self.assertTrue(self.stage.GetPrimAtPath("/Rig/Load/AttachmentSite").HasAPI("NewtonSiteAPI"))
        for path in ("/Rig/Cable", "/Rig/Load", "/Rig/Pulley"):
            self.assertEqual(self.stage.GetPrimAtPath(path).GetRelationship("physics:simulationOwner").GetTargets(), [Sdf.Path("/Rig/Scene")])

    def test_reference_remapping(self):
        """Remap route, frame and scene relationships independently in two referenced copies."""
        stage = Usd.Stage.CreateInMemory()
        for name, offset in (("CopyB", Gf.Vec3d(1, 2, 3)), ("CopyA", Gf.Vec3d(-2, 0, 1))):
            root = UsdGeom.Xform.Define(stage, f"/{name}")
            prim = root.GetPrim()
            self.assertTrue(prim.GetReferences().AddReference(self.path.as_posix()))
            root.AddTranslateOp().Set(offset)
            tendon = stage.GetPrimAtPath(f"/{name}/Cable")
            self.assertEqual(
                tendon.GetRelationship("newton:tendon:guides").GetTargets(),
                [Sdf.Path(f"/{name}/Cable/{guide}") for guide in ("Start", "Pinhole", "Roller", "End")],
            )
            self.assertEqual(tendon.GetRelationship("physics:simulationOwner").GetTargets(), [Sdf.Path(f"/{name}/Scene")])
            for guide_name, frame_suffix in (
                ("Start", "Frames/Start"),
                ("Pinhole", "Frames/Pinhole"),
                ("Roller", "Pulley/GuideFrame"),
                ("End", "Load/AttachmentSite"),
            ):
                guide = stage.GetPrimAtPath(f"/{name}/Cable/{guide_name}")
                self.assertEqual(guide.GetRelationship("newton:tendon:frame").GetTargets(), [Sdf.Path(f"/{name}/{frame_suffix}")])
            cache = UsdGeom.XformCache()
            start = stage.GetPrimAtPath(f"/{name}/Frames/Start")
            self.assertTrue(Gf.IsClose(cache.GetLocalToWorldTransform(start).ExtractTranslation(), offset + Gf.Vec3d(-0.2, 0, 0), 1e-8))
            end = stage.GetPrimAtPath(f"/{name}/Load/AttachmentSite")
            body = stage.GetPrimAtPath(f"/{name}/Load")
            relative, resets = cache.ComputeRelativeTransform(end, body)
            self.assertFalse(resets)
            self.assertTrue(Gf.IsClose(relative.ExtractTranslation(), Gf.Vec3d(0.01, 0.02, 0), 1e-8))

    def test_composed_frame_pose(self):
        """Compose parent placement and recover a body's local guide position and orientation."""
        root = UsdGeom.Xformable(self.stage.GetPrimAtPath("/Rig"))
        root.AddTranslateOp().Set(Gf.Vec3d(2, 3, 4))
        root.AddRotateZOp().Set(90)
        frame = self.stage.GetPrimAtPath("/Rig/Load/AttachmentSite")
        UsdGeom.Xformable(frame).AddOrientOp().Set(Gf.Quatf(Gf.Rotation(Gf.Vec3d(1, 0, 0), 90).GetQuat()))
        body = self.stage.GetPrimAtPath("/Rig/Load")
        UsdPhysics.MassAPI(body).CreateCenterOfMassAttr().Set(Gf.Vec3f(0.03, 0, 0))
        cache = UsdGeom.XformCache()
        world_pose = cache.GetLocalToWorldTransform(frame)
        local_pose, resets = cache.ComputeRelativeTransform(frame, body)
        self.assertFalse(resets)
        self.assertTrue(Gf.IsClose(local_pose.ExtractTranslation(), Gf.Vec3d(0.01, 0.02, 0), 1e-8))
        self.assertTrue(Gf.IsClose(world_pose.ExtractTranslation(), Gf.Vec3d(1.98, 3.16, 4), 1e-8))
        self.assertTrue(Gf.IsClose(local_pose.TransformDir(Gf.Vec3d(0, 0, 1)), Gf.Vec3d(0, -1, 0), 1e-6))
        self.assertTrue(Gf.IsClose(world_pose.TransformDir(Gf.Vec3d(0, 0, 1)), Gf.Vec3d(1, 0, 0), 1e-6))
        self.assertTrue(Gf.IsClose(local_pose * cache.GetLocalToWorldTransform(body), world_pose, 1e-8))
        start = self.stage.GetPrimAtPath("/Rig/Frames/Start")
        self.assertTrue(Gf.IsClose(cache.GetLocalToWorldTransform(start).ExtractTranslation(), Gf.Vec3d(2, 2.8, 4), 1e-8))

    def test_nested_guides_reference_remapping(self):
        """Keep grouped guide definitions and external frame references when copying an asset."""
        tendon = self.stage.GetPrimAtPath("/Rig/Cable")
        grouped = []
        for name, group in (("Start", "Endpoints"), ("Pinhole", "Routing/Points"), ("Roller", "Routing/Rollers"), ("End", "Endpoints")):
            parent = Sdf.Path(f"/Rig/Cable/{group}")
            UsdGeom.Scope.Define(self.stage, parent)
            path = parent.AppendChild(name)
            self.assertTrue(Sdf.CopySpec(self.stage.GetRootLayer(), Sdf.Path(f"/Rig/Cable/{name}"), self.stage.GetSessionLayer(), path))
            grouped.append(path)
        tendon.GetRelationship("newton:tendon:guides").SetTargets(grouped)

        layer = self.stage.Flatten()
        copied = Usd.Stage.CreateInMemory()
        root = UsdGeom.Xform.Define(copied, "/Copy")
        self.assertTrue(root.GetPrim().GetReferences().AddReference(layer.identifier))
        targets = copied.GetPrimAtPath("/Copy/Cable").GetRelationship("newton:tendon:guides").GetTargets()
        self.assertEqual(targets, [path.ReplacePrefix(Sdf.Path("/Rig"), Sdf.Path("/Copy")) for path in grouped])
        for source, target in zip(grouped, targets, strict=True):
            original = self.stage.GetPrimAtPath(source)
            guide = copied.GetPrimAtPath(target)
            self.assertEqual(guide.GetTypeName(), "NewtonTendonGuide")
            self.assertEqual(guide.GetAppliedSchemas(), original.GetAppliedSchemas())
            owner = guide.GetParent()
            while owner and owner.GetTypeName() != "NewtonTendon":
                owner = owner.GetParent()
            self.assertEqual(owner.GetPath(), Sdf.Path("/Copy/Cable"))
            self.assertEqual(
                guide.GetRelationship("newton:tendon:frame").GetTargets(),
                [path.ReplacePrefix(Sdf.Path("/Rig"), Sdf.Path("/Copy")) for path in original.GetRelationship("newton:tendon:frame").GetTargets()],
            )

    def test_scaled_point_frames(self):
        """Compose scaled offsets for both a world anchor and a body-attached site."""
        root = UsdGeom.Xformable(self.stage.GetPrimAtPath("/Rig"))
        root.AddTranslateOp().Set(Gf.Vec3d(2, 3, 4))
        root.AddRotateZOp().Set(90)
        root.AddScaleOp().Set(Gf.Vec3f(2, 3, 4))
        end = self.stage.GetPrimAtPath("/Rig/Load/AttachmentSite")
        UsdGeom.Xformable(end).AddScaleOp().Set(Gf.Vec3f(5, 6, 7))
        cache = UsdGeom.XformCache()
        for name, position in (("Start", Gf.Vec3d(2, 2.6, 4)), ("End", Gf.Vec3d(1.94, 3.32, 4))):
            guide = self.stage.GetPrimAtPath(f"/Rig/Cable/{name}")
            frame = self.stage.GetPrimAtPath(guide.GetRelationship("newton:tendon:frame").GetTargets()[0])
            self.assertTrue(Gf.IsClose(cache.GetLocalToWorldTransform(frame).ExtractTranslation(), position, 1e-8))

    def test_scaled_roller_frame(self):
        """Recover roller axes from a scaled placement frame and retain the authored radius."""
        body = UsdGeom.Xformable(self.stage.GetPrimAtPath("/Rig/Pulley"))
        body.AddRotateZOp().Set(90)
        body.AddScaleOp().Set(Gf.Vec3f(2, 3, 4))
        roller = self.stage.GetPrimAtPath("/Rig/Cable/Roller")
        frame = self.stage.GetPrimAtPath(roller.GetRelationship("newton:tendon:frame").GetTargets()[0])
        UsdGeom.Xformable(frame).AddTranslateOp().Set(Gf.Vec3d(0.01, 0.02, 0))
        UsdGeom.Xformable(frame).AddScaleOp().Set(Gf.Vec3f(5, 6, 7))
        matrix = UsdGeom.XformCache().GetLocalToWorldTransform(frame)
        self.assertTrue(Gf.IsClose(matrix.ExtractTranslation(), Gf.Vec3d(-0.06, 0.02, 0), 1e-8))
        for axis, direction, length in (
            (Gf.Vec3d(1, 0, 0), Gf.Vec3d(0, 1, 0), 10),
            (Gf.Vec3d(0, 1, 0), Gf.Vec3d(-1, 0, 0), 18),
            (Gf.Vec3d(0, 0, 1), Gf.Vec3d(0, 0, 1), 28),
        ):
            transformed = matrix.TransformDir(axis)
            self.assertAlmostEqual(transformed.GetLength(), length)
            self.assertTrue(Gf.IsClose(transformed.GetNormalized(), direction, 1e-8))
        self.assertAlmostEqual(roller.GetAttribute("newton:roller:radius").Get(), 0.03)

    def test_intermediate_frame_transforms(self):
        """Include intermediate transforms and expose a reset below the attached body."""
        mount = UsdGeom.Xform.Define(self.stage, "/Rig/Load/Mount")
        mount.AddTranslateOp().Set(Gf.Vec3d(0, 0.03, 0))
        frame = UsdGeom.Xform.Define(self.stage, "/Rig/Load/Mount/Frame")
        frame.AddTranslateOp().Set(Gf.Vec3d(0.01, 0, 0))
        guide = self.stage.GetPrimAtPath("/Rig/Cable/End")
        guide.GetRelationship("newton:tendon:frame").SetTargets([frame.GetPath()])
        body = self.stage.GetPrimAtPath("/Rig/Load")
        relative, resets = UsdGeom.XformCache().ComputeRelativeTransform(frame.GetPrim(), body)
        self.assertFalse(resets)
        self.assertTrue(Gf.IsClose(relative.ExtractTranslation(), Gf.Vec3d(0.01, 0.03, 0), 1e-8))
        frame.SetResetXformStack(True)
        _, resets = UsdGeom.XformCache().ComputeRelativeTransform(frame.GetPrim(), body)
        self.assertTrue(resets)  # A reset breaks transform inheritance from the attached body.

    def test_shared_frames_keep_separate_parameters(self):
        """Reuse placement frames across tendons with independently authored material data."""
        other = self.stage.DefinePrim("/Rig/OtherCable", "NewtonTendon")
        other.GetRelationship("physics:simulationOwner").SetTargets([Sdf.Path("/Rig/Scene")])
        guides = []
        for name in ("Start", "Pinhole", "Roller", "End"):
            source = Sdf.Path(f"/Rig/Cable/{name}")
            target = Sdf.Path(f"/Rig/OtherCable/{name}")
            self.assertTrue(Sdf.CopySpec(self.stage.GetRootLayer(), source, self.stage.GetSessionLayer(), target))
            guides.append(target)
            self.assertEqual(
                self.stage.GetPrimAtPath(source).GetRelationship("newton:tendon:frame").GetTargets(),
                self.stage.GetPrimAtPath(target).GetRelationship("newton:tendon:frame").GetTargets(),
            )
        other.GetRelationship("newton:tendon:guides").SetTargets(guides)
        roller = self.stage.GetPrimAtPath("/Rig/OtherCable/Roller")
        roller.GetAttribute("newton:tendon:friction").Set(0.6)
        roller.GetAttribute("newton:tendon:span:compliance").Set(0.002)
        original = self.stage.GetPrimAtPath("/Rig/Cable/Roller")
        self.assertAlmostEqual(original.GetAttribute("newton:tendon:friction").Get(), 0.2)
        self.assertAlmostEqual(original.GetAttribute("newton:tendon:span:compliance").Get(), 0.0001)
        self.assertAlmostEqual(roller.GetAttribute("newton:tendon:friction").Get(), 0.6)
        self.assertAlmostEqual(roller.GetAttribute("newton:tendon:span:compliance").Get(), 0.002)

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
