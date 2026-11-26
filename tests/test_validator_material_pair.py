# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import math
import unittest

from pxr import Sdf, Usd, UsdGeom, UsdPhysics, UsdShade
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase

from newton_usd_schemas import validators

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

TARGET_COUNT_ERROR = "MaterialPairTargetCount"
INVALID_TARGET_ERROR = "MaterialPairInvalidTarget"
NO_COEFFICIENTS_ERROR = "MaterialPairNoCoefficients"
WITHOUT_DEFAULT_ERROR = "MaterialPairCoefficientWithoutDefault"
NOT_FINITE_ERROR = "MaterialPairCoefficientNotFinite"
STATIC_FRICTION_ERROR = "MaterialPairStaticFrictionBelowFriction"
MATERIALS = ("newton:materialPair:material0", "newton:materialPair:material1")
COEFFICIENTS = (
    "newton:materialPair:mu",
    "newton:materialPair:muStatic",
    "newton:materialPair:muTorsional",
    "newton:materialPair:muRolling",
    "newton:materialPair:restitution",
)


class TestMaterialPairValidator(ValidatorTestCase):
    validator_name = validators.MATERIAL_PAIR_VALIDATOR

    def setUp(self):
        super().setUp()
        self.rubber: Usd.Prim = self.define_material("/RubberMaterial")
        self.steel: Usd.Prim = self.define_material("/SteelMaterial")
        self.prim: Usd.Prim = self.define_pair(self.stage, "/RubberOnSteel")
        self.mu: Usd.Attribute = self.prim.GetAttribute("newton:materialPair:mu")
        self.mu_static: Usd.Attribute = self.prim.GetAttribute("newton:materialPair:muStatic")
        self.material0: Usd.Relationship = self.prim.GetRelationship("newton:materialPair:material0")

    def define_material(self, path: str) -> Usd.Prim:
        material = UsdShade.Material.Define(self.stage, path).GetPrim()
        UsdPhysics.MaterialAPI.Apply(material)
        return material

    def define_pair(self, stage: Usd.Stage, path: str) -> Usd.Prim:
        """Define a valid pair of rubber and steel, which overrides the Coulomb friction coefficient."""
        prim = UsdGeom.Scope.Define(stage, path).GetPrim()
        prim.ApplyAPI("NewtonMaterialPairAPI")
        prim.GetRelationship("newton:materialPair:material0").SetTargets(["/RubberMaterial"])
        prim.GetRelationship("newton:materialPair:material1").SetTargets(["/SteelMaterial"])
        prim.GetAttribute("newton:materialPair:mu").Set(0.9)
        return prim

    def test_valid_pair(self):
        """Accept a pair of physics materials with one authored coefficient."""
        self.assertEqual(self.validate(self.prim), [])

    def test_each_coefficient(self):
        """Accept a pair that authors any one coefficient."""
        for name in COEFFICIENTS:
            with self.subTest(attribute=name):
                self.mu.Clear()
                for other in COEFFICIENTS:
                    self.prim.GetAttribute(other).Clear()
                self.prim.GetAttribute(name).Set(0.5)
                self.assertEqual(self.validate(self.prim), [])

    def test_all_coefficients(self):
        """Accept a pair that authors every coefficient."""
        for name in COEFFICIENTS:
            self.prim.GetAttribute(name).Set(0.9)
        self.assertEqual(self.validate(self.prim), [])

    def test_zero_coefficients(self):
        """Accept coefficients of 0, which set the pair's coefficient to 0."""
        for name in COEFFICIENTS:
            self.prim.GetAttribute(name).Set(0.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_same_material(self):
        """Accept a pair of a material with itself."""
        self.material0.SetTargets([self.steel.GetPath()])
        self.assertEqual(self.validate(self.prim), [])

    def test_authored_with_custom_properties(self):
        """Accept a pair authored as in Newton's documentation, with custom properties."""
        self.stage.GetRootLayer().ImportFromString("""#usda 1.0
            def Material "RubberMaterial" (prepend apiSchemas = ["PhysicsMaterialAPI"]) {}
            def Material "SteelMaterial" (prepend apiSchemas = ["PhysicsMaterialAPI"]) {}
            def Scope "RubberOnSteel" (
                prepend apiSchemas = ["NewtonMaterialPairAPI"]
            ) {
                custom rel newton:materialPair:material0 = </RubberMaterial>
                custom rel newton:materialPair:material1 = </SteelMaterial>
                custom float newton:materialPair:mu = 0.9
            }
            """)
        self.assertEqual(self.validate(self.stage.GetPrimAtPath("/RubberOnSteel")), [])

    def test_no_target(self):
        """Report a material relationship without a target."""
        for name in MATERIALS:
            with self.subTest(relationship=name):
                prim = self.define_pair(self.stage, f"/NoTarget{name[-1]}")
                rel = prim.GetRelationship(name)
                rel.ClearTargets(True)
                self.assertEqual(self.validate(prim), [(TARGET_COUNT_ERROR, rel.GetPath())])

    def test_multiple_targets(self):
        """Report a material relationship with more than one target."""
        for name in MATERIALS:
            with self.subTest(relationship=name):
                prim = self.define_pair(self.stage, f"/MultipleTargets{name[-1]}")
                rel = prim.GetRelationship(name)
                rel.SetTargets([self.rubber.GetPath(), self.steel.GetPath()])
                self.assertEqual(self.validate(prim), [(TARGET_COUNT_ERROR, rel.GetPath())])

    def test_missing_target(self):
        """Report a material relationship that targets no prim."""
        for name in MATERIALS:
            with self.subTest(relationship=name):
                prim = self.define_pair(self.stage, f"/MissingTarget{name[-1]}")
                rel = prim.GetRelationship(name)
                rel.SetTargets(["/Missing"])
                self.assertEqual(self.validate(prim), [(INVALID_TARGET_ERROR, rel.GetPath())])

    def test_non_material_target(self):
        """Report a material relationship that targets a prim which is not a Material."""
        xform = UsdGeom.Xform.Define(self.stage, "/Xform").GetPrim()
        UsdPhysics.MaterialAPI.Apply(xform)
        self.material0.SetTargets([xform.GetPath()])
        self.assertEqual(self.validate(self.prim), [(INVALID_TARGET_ERROR, self.material0.GetPath())])

    def test_non_physics_material_target(self):
        """Report a material relationship that targets a Material without PhysicsMaterialAPI."""
        material = UsdShade.Material.Define(self.stage, "/VisualMaterial").GetPrim()
        self.material0.SetTargets([material.GetPath()])
        self.assertEqual(self.validate(self.prim), [(INVALID_TARGET_ERROR, self.material0.GetPath())])

    def test_target_error_messages(self):
        """Report the relationship, the prim, and the problem with its targets."""
        self.material0.ClearTargets(True)
        rel = self.prim.GetRelationship("newton:materialPair:material1")
        rel.SetTargets(["/Missing"])
        count, invalid = self.validator.Validate(self.prim)
        self.assertEqual(count.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["newton:materialPair:material0", "/RubberOnSteel", "0 targets", "exactly 1"]:
            self.assertIn(text, count.GetMessage())
        self.assertEqual(invalid.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["newton:materialPair:material1", "/RubberOnSteel", "/Missing", "Material", "PhysicsMaterialAPI"]:
            self.assertIn(text, invalid.GetMessage())

    def test_no_coefficients(self):
        """Report a pair without an authored coefficient on the prim."""
        self.mu.Clear()
        self.assertEqual(self.validate(self.prim), [(NO_COEFFICIENTS_ERROR, self.prim.GetPath())])

    def test_no_coefficients_message(self):
        """Report the prim and the coefficients it can author."""
        self.mu.Clear()
        (error,) = self.validator.Validate(self.prim)
        self.assertEqual(error.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["NewtonMaterialPairAPI", "/RubberOnSteel", "at least one", *COEFFICIENTS]:
            self.assertIn(text, error.GetMessage())

    def test_blocked_coefficient(self):
        """Report a blocked coefficient, which Newton rejects rather than treating as unauthored."""
        for name in COEFFICIENTS:
            with self.subTest(attribute=name):
                prim = self.define_pair(self.stage, f"/Blocked{name.split(':')[-1]}")
                attr = prim.GetAttribute(name)
                attr.Block()
                # A blocked mu is still an opinion, so the pair is not also reported as having no coefficients
                self.assertEqual(self.validate(prim), [(WITHOUT_DEFAULT_ERROR, attr.GetPath())])

    def test_time_sampled_coefficient(self):
        """Report a coefficient with only time samples, as Newton reads only the default time value."""
        for name in COEFFICIENTS:
            with self.subTest(attribute=name):
                prim = self.define_pair(self.stage, f"/TimeSampled{name.split(':')[-1]}")
                attr = prim.GetAttribute(name)
                attr.Clear()
                attr.Set(0.5, 1.0)
                self.assertEqual(self.validate(prim), [(WITHOUT_DEFAULT_ERROR, attr.GetPath())])

    def test_time_sampled_coefficient_with_default(self):
        """Accept time samples alongside a default time value, which Newton reads."""
        self.mu.Set(0.5, 1.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_time_samples_are_not_validated(self):
        """Ignore invalid time samples, as Newton reads only the default time value."""
        self.mu.Set(math.inf, 1.0)
        self.mu_static.Set(1.0)
        self.mu_static.Set(0.1, 1.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_without_default_messages(self):
        """Report the coefficient, the prim, and why Newton cannot read it."""
        self.mu.Block()
        self.mu_static.Set(1.0, 1.0)
        blocked, sampled = self.validator.Validate(self.prim)
        for text in ["newton:materialPair:mu ", "/RubberOnSteel", "blocked", "default time"]:
            self.assertIn(text, blocked.GetMessage())
        for text in ["newton:materialPair:muStatic", "/RubberOnSteel", "time samples", "default time"]:
            self.assertIn(text, sampled.GetMessage())

    def test_infinite_coefficient(self):
        """Report an authored infinite coefficient."""
        for name in COEFFICIENTS:
            for value in (math.inf, -math.inf):
                with self.subTest(attribute=name, value=value):
                    prim = self.define_pair(self.stage, f"/Infinite{name.split(':')[-1]}{'Pos' if value > 0 else 'Neg'}")
                    attr = prim.GetAttribute(name)
                    attr.Set(value)
                    self.assertEqual(self.validate(prim), [(NOT_FINITE_ERROR, attr.GetPath())])

    def test_infinite_coefficient_message(self):
        """Report the coefficient, the prim, and its value."""
        self.mu.Set(-math.inf)
        (error,) = self.validator.Validate(self.prim)
        self.assertEqual(error.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["newton:materialPair:mu", "/RubberOnSteel", "-inf", "finite"]:
            self.assertIn(text, error.GetMessage())

    def test_negative_and_nan_coefficients(self):
        """Leave negative and NaN coefficients to the hard limits validator."""
        self.mu.Set(-1.0)
        self.mu_static.Set(math.nan)
        self.assertEqual(self.validate(self.prim), [])
        hard_limits = UsdValidation.ValidationRegistry().GetOrLoadValidatorByName(validators.ATTRIBUTE_HARD_LIMITS_VALIDATOR)
        self.assertEqual(sorted(error.GetName() for error in hard_limits.Validate(self.prim)), ["AttributeOutsideHardLimits"] * 2)

    def test_static_friction_above_friction(self):
        """Accept a static friction coefficient greater than or equal to the Coulomb friction coefficient."""
        for value in (0.9, 1.2):
            with self.subTest(value=value):
                self.mu_static.Set(value)
                self.assertEqual(self.validate(self.prim), [])

    def test_static_friction_without_friction(self):
        """Accept a static friction coefficient when the Coulomb friction coefficient is unauthored."""
        self.mu.Clear()
        self.mu_static.Set(0.1)
        self.assertEqual(self.validate(self.prim), [])

    def test_static_friction_below_friction(self):
        """Report a static friction coefficient less than the Coulomb friction coefficient."""
        self.mu_static.Set(0.5)
        self.assertEqual(self.validate(self.prim), [(STATIC_FRICTION_ERROR, self.mu_static.GetPath())])

    def test_static_friction_below_negative_friction(self):
        """Leave the comparison to the hard limits validator when either coefficient is negative."""
        self.mu.Set(0.5)
        self.mu_static.Set(-1.0)
        self.assertEqual(self.validate(self.prim), [])

    def test_static_friction_message(self):
        """Report both coefficients, the prim, and their values."""
        self.mu_static.Set(0.5)
        (error,) = self.validator.Validate(self.prim)
        self.assertEqual(error.GetType(), UsdValidation.ValidationErrorType.Error)
        for text in ["newton:materialPair:muStatic", "newton:materialPair:mu ", "/RubberOnSteel", "0.5", "0.9"]:
            self.assertIn(text, error.GetMessage())

    def test_multiple_findings(self):
        """Report every problem with a pair."""
        self.material0.ClearTargets(True)
        rel = self.prim.GetRelationship("newton:materialPair:material1")
        rel.SetTargets(["/Missing"])
        self.mu.Clear()
        self.assertEqual(
            self.validate(self.prim),
            [(TARGET_COUNT_ERROR, self.material0.GetPath()), (INVALID_TARGET_ERROR, rel.GetPath()), (NO_COEFFICIENTS_ERROR, self.prim.GetPath())],
        )

    def test_requires_api(self):
        """Ignore material pair properties on a prim without the API."""
        prim = UsdGeom.Scope.Define(self.stage, "/NotAPair").GetPrim()
        prim.CreateRelationship("newton:materialPair:material0", custom=True)
        prim.CreateAttribute("newton:materialPair:mu", Sdf.ValueTypeNames.Float, custom=True).Set(math.inf)
        self.assertEqual(self.validate(prim), [])

    def test_ignores_materials(self):
        """Ignore the physics materials a pair targets."""
        self.assertEqual(self.validate(self.rubber), [])

    def test_selected_by_schema_keyword(self):
        """Select the validator through the material pair API keyword."""
        self.mu_static.Set(0.5)
        self.assertEqual(self.validate_with_keywords("NewtonMaterialPairAPI"), [STATIC_FRICTION_ERROR])

    def test_selected_by_topic_keyword(self):
        """Select the validator through the materials topic keyword."""
        self.mu.Clear()
        self.assertEqual(self.validate_with_keywords("NewtonMaterials"), [NO_COEFFICIENTS_ERROR])


if __name__ == "__main__":
    unittest.main()
