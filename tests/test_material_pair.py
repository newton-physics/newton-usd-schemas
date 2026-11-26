# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Plug, Usd, UsdGeom, UsdPhysics, UsdShade

import newton_usd_schemas  # noqa: F401

USD_HAS_LIMITS = Usd.GetVersion() >= (0, 25, 11)


class TestNewtonMaterialPairAPI(unittest.TestCase):
    def setUp(self):
        self.stage: Usd.Stage = Usd.Stage.CreateInMemory()
        self.prim: Usd.Prim = UsdGeom.Scope.Define(self.stage, "/RubberOnSteel").GetPrim()
        self.rubber: Usd.Prim = UsdShade.Material.Define(self.stage, "/RubberMaterial").GetPrim()
        self.steel: Usd.Prim = UsdShade.Material.Define(self.stage, "/SteelMaterial").GetPrim()
        for material in (self.rubber, self.steel):
            UsdPhysics.MaterialAPI.Apply(material)

    def test_api_registered(self):
        plug_type = Plug.Registry().FindTypeByName("NewtonPhysicsMaterialPairAPI")
        self.assertEqual(plug_type.typeName, "NewtonPhysicsMaterialPairAPI")
        schema_type = Usd.SchemaRegistry().GetSchemaTypeName("NewtonPhysicsMaterialPairAPI")
        self.assertEqual(schema_type, "NewtonMaterialPairAPI")

    def test_api_application(self):
        self.assertFalse(self.prim.HasAPI("NewtonMaterialPairAPI"))
        self.prim.ApplyAPI("NewtonMaterialPairAPI")
        self.assertTrue(self.prim.HasAPI("NewtonMaterialPairAPI"))
        # The pair does not apply any material schema to the prim it is authored on
        self.assertFalse(self.prim.HasAPI("PhysicsMaterialAPI"))
        self.assertFalse(self.prim.HasAPI("NewtonMaterialAPI"))

        self.assertTrue(self.prim.HasRelationship("newton:materialPair:material0"))
        self.assertTrue(self.prim.HasRelationship("newton:materialPair:material1"))
        self.assertTrue(self.prim.HasAttribute("newton:materialPair:mu"))
        self.assertTrue(self.prim.HasAttribute("newton:materialPair:muStatic"))
        self.assertTrue(self.prim.HasAttribute("newton:materialPair:muTorsional"))
        self.assertTrue(self.prim.HasAttribute("newton:materialPair:muRolling"))
        self.assertTrue(self.prim.HasAttribute("newton:materialPair:restitution"))

    def test_api_applicability(self):
        """Apply to any prim, as Newton reads a pair from any prim in the imported subtree."""
        self.assertEqual(list(Usd.SchemaRegistry().GetAPISchemaCanOnlyApplyToTypeNames("NewtonMaterialPairAPI")), [])
        prims = [
            self.prim,
            UsdGeom.Xform.Define(self.stage, "/Xform").GetPrim(),
            self.rubber,
            UsdPhysics.Scene.Define(self.stage, "/PhysicsScene").GetPrim(),
            self.stage.DefinePrim("/Typeless"),
        ]
        for prim in prims:
            with self.subTest(prim=prim.GetPath()):
                self.assertTrue(prim.CanApplyAPI("NewtonMaterialPairAPI"))
                prim.ApplyAPI("NewtonMaterialPairAPI")
                self.assertTrue(prim.HasAPI("NewtonMaterialPairAPI"))

    def test_authored_with_custom_properties(self):
        """Read a pair authored as in Newton's documentation, with custom properties."""
        layer = self.stage.GetRootLayer()
        layer.ImportFromString("""#usda 1.0
            def Scope "RubberOnSteel" (
                prepend apiSchemas = ["NewtonMaterialPairAPI"]
            ) {
                custom rel newton:materialPair:material0 = </RubberMaterial>
                custom rel newton:materialPair:material1 = </SteelMaterial>
                custom float newton:materialPair:mu = 0.9
            }
            """)
        prim = self.stage.GetPrimAtPath("/RubberOnSteel")
        self.assertTrue(prim.HasAPI("NewtonMaterialPairAPI"))
        self.assertEqual(prim.GetRelationship("newton:materialPair:material0").GetTargets(), ["/RubberMaterial"])
        self.assertEqual(prim.GetRelationship("newton:materialPair:material1").GetTargets(), ["/SteelMaterial"])
        self.assertAlmostEqual(prim.GetAttribute("newton:materialPair:mu").Get(), 0.9)
        self.assertEqual(prim.GetAttribute("newton:materialPair:muStatic").Get(), -math.inf)

    def test_material0(self):
        self.assertFalse(self.prim.HasRelationship("newton:materialPair:material0"))

        self.prim.ApplyAPI("NewtonMaterialPairAPI")
        rel = self.prim.GetRelationship("newton:materialPair:material0")
        self.assertTrue(rel)
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])

        success = rel.SetTargets([self.rubber.GetPath()])
        self.assertTrue(success)
        self.assertTrue(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [self.rubber.GetPath()])

    def test_material1(self):
        self.assertFalse(self.prim.HasRelationship("newton:materialPair:material1"))

        self.prim.ApplyAPI("NewtonMaterialPairAPI")
        rel = self.prim.GetRelationship("newton:materialPair:material1")
        self.assertTrue(rel)
        self.assertFalse(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [])

        success = rel.SetTargets([self.steel.GetPath()])
        self.assertTrue(success)
        self.assertTrue(rel.HasAuthoredTargets())
        self.assertEqual(rel.GetTargets(), [self.steel.GetPath()])

    def check_coefficient(self, name: str, value: float):
        self.assertFalse(self.prim.HasAttribute(name))

        self.prim.ApplyAPI("NewtonMaterialPairAPI")
        attr = self.prim.GetAttribute(name)
        self.assertTrue(attr)
        self.assertEqual(attr.GetTypeName(), "float")
        self.assertFalse(attr.HasAuthoredValue())
        self.assertEqual(attr.Get(), -math.inf)

        success = attr.Set(value)
        self.assertTrue(success)
        self.assertTrue(attr.HasAuthoredValue())
        self.assertAlmostEqual(attr.Get(), value)

        success = attr.Set(0.0)
        self.assertTrue(success)
        self.assertEqual(attr.Get(), 0.0)

        if USD_HAS_LIMITS:
            hard = attr.GetHardLimits()
            self.assertTrue(hard.IsValid())
            self.assertAlmostEqual(hard.GetMinimum(), 0.0)
            self.assertIsNone(hard.GetMaximum())

    def test_mu(self):
        """Coulomb friction coefficient, unset by default."""
        self.check_coefficient("newton:materialPair:mu", 0.9)

    def test_mu_static(self):
        """Static friction coefficient, unset by default."""
        self.check_coefficient("newton:materialPair:muStatic", 1.1)

    def test_mu_torsional(self):
        """Torsional friction coefficient, unset by default."""
        self.check_coefficient("newton:materialPair:muTorsional", 0.01)

    def test_mu_rolling(self):
        """Rolling friction coefficient, unset by default."""
        self.check_coefficient("newton:materialPair:muRolling", 0.001)

    def test_restitution(self):
        """Restitution coefficient, unset by default."""
        self.check_coefficient("newton:materialPair:restitution", 0.5)


if __name__ == "__main__":
    unittest.main()
