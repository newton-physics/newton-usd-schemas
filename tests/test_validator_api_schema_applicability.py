# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

import unittest

from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from validator_test_case import SUPPORTS_PYTHON_VALIDATORS, ValidatorTestCase, run_python

from newton_usd_schemas import validators
from newton_usd_schemas.validators._applicability import OPENUSD_API_SCHEMA_APPLICABILITY_VALIDATOR

ERROR = "APISchemaNotApplicable"

if SUPPORTS_PYTHON_VALIDATORS:
    from pxr import UsdValidation

    HAS_OPENUSD_VALIDATOR = bool(UsdValidation.ValidationRegistry().GetValidatorMetadata(OPENUSD_API_SCHEMA_APPLICABILITY_VALIDATOR))
else:
    HAS_OPENUSD_VALIDATOR = False


def author_api_schemas(prim: Usd.Prim, *schemas: str) -> None:
    """Apply the schemas through the apiSchemas metadata, which does not check whether they can be applied."""
    prim.SetMetadata("apiSchemas", Sdf.TokenListOp.Create(prependedItems=list(schemas)))


class TestAPISchemaApplicabilityValidator(ValidatorTestCase):
    validator_name = validators.API_SCHEMA_APPLICABILITY_VALIDATOR

    def setUp(self):
        super().setUp()
        self.xform: Usd.Prim = UsdGeom.Xform.Define(self.stage, "/Xform").GetPrim()

    def test_applicable_schema(self):
        joint = UsdPhysics.RevoluteJoint.Define(self.stage, "/Joint").GetPrim()
        joint.ApplyAPI("NewtonJointAPI")
        self.assertEqual(self.validate(joint), [])

    def test_schema_applicable_to_a_base_type(self):
        """Accept a schema that can only be applied to a type the prim's type derives from."""
        cube = UsdGeom.Cube.Define(self.stage, "/Cube").GetPrim()
        author_api_schemas(cube, "NewtonCollisionAPI")
        self.assertEqual(self.validate(cube), [])

    def test_inapplicable_schema(self):
        author_api_schemas(self.xform, "NewtonJointAPI")
        self.assertEqual(self.validate(self.xform), [(ERROR, self.xform.GetPath())])
        message = self.validator.Validate(self.xform)[0].GetMessage()
        self.assertIn("'NewtonJointAPI'", message)
        self.assertIn("PhysicsJoint", message)

    def test_typeless_prim(self):
        prim = self.stage.DefinePrim("/Typeless")
        author_api_schemas(prim, "NewtonCollisionAPI")
        self.assertEqual(self.validate(prim), [(ERROR, prim.GetPath())])

    def test_unrestricted_schema(self):
        author_api_schemas(self.xform, "NewtonArticulationRootAPI")
        self.assertEqual(self.validate(self.xform), [])

    def test_each_inapplicable_schema(self):
        """Report every inapplicable schema on the prim."""
        author_api_schemas(self.xform, "NewtonJointAPI", "NewtonArticulationRootAPI", "NewtonMimicAPI")
        errors = self.validator.Validate(self.xform)
        self.assertEqual([error.GetName() for error in errors], [ERROR, ERROR])
        self.assertIn("'NewtonJointAPI'", errors[0].GetMessage())
        self.assertIn("'NewtonMimicAPI'", errors[1].GetMessage())

    def test_built_in_schemas_are_not_checked(self):
        """Check only the authored schemas, not the ones built into them."""
        mesh = UsdGeom.Mesh.Define(self.stage, "/Mesh").GetPrim()
        mesh.ApplyAPI("NewtonMeshCollisionAPI")
        self.assertIn("NewtonCollisionAPI", mesh.GetAppliedSchemas())
        self.assertEqual(self.validate(mesh), [])

    def test_unregistered_schema(self):
        author_api_schemas(self.xform, "UnregisteredAPI")
        self.assertEqual(self.validate(self.xform), [])

    def test_non_applied_schema(self):
        author_api_schemas(self.xform, "ModelAPI")
        self.assertEqual(self.validate(self.xform), [])

    def test_multiple_apply_schema(self):
        author_api_schemas(self.xform, "CollectionAPI:things")
        self.assertEqual(self.validate(self.xform), [])

    def test_instance_proxy(self):
        """Report an inapplicable schema on an instance proxy."""
        prototype = UsdGeom.Xform.Define(self.stage, "/Prototype").GetPrim()
        author_api_schemas(UsdGeom.Xform.Define(self.stage, "/Prototype/Child").GetPrim(), "NewtonJointAPI")
        instance = self.stage.DefinePrim("/Instance")
        instance.GetReferences().AddInternalReference(prototype.GetPath())
        instance.SetInstanceable(True)
        proxy = self.stage.GetPrimAtPath("/Instance/Child")
        self.assertTrue(proxy.IsInstanceProxy())
        self.assertEqual(self.validate(proxy), [(ERROR, proxy.GetPath())])

    def test_selected_by_keyword(self):
        author_api_schemas(self.xform, "NewtonJointAPI")
        self.assertEqual(self.validate_with_keywords("APISchemaApplicability"), [ERROR])

    @unittest.skipIf(HAS_OPENUSD_VALIDATOR, "OpenUSD provides the validator, so the other tests already defer to it")
    def test_defers_to_openusd_validator(self):
        result = run_python("""
            from pxr import Sdf, Usd, UsdGeom, UsdValidation

            def openusd_task(prim, time_range):
                site = UsdValidation.ValidationErrorSite(prim.GetStage(), prim.GetPath())
                return [UsdValidation.ValidationError("FromOpenUSD", UsdValidation.ValidationErrorType.Error, [site], "")]

            registry = UsdValidation.ValidationRegistry()
            registry.RegisterPrimValidator(UsdValidation.ValidatorMetadata(name="usdValidation:APISchemaApplicability"), openusd_task)

            import newton_usd_schemas.validators

            stage = Usd.Stage.CreateInMemory()
            prim = UsdGeom.Cube.Define(stage, "/Cube").GetPrim()
            validator = registry.GetOrLoadValidatorByName(newton_usd_schemas.validators.API_SCHEMA_APPLICABILITY_VALIDATOR)
            names = [error.GetName() for error in validator.Validate(prim)]
            assert names == ["FromOpenUSD"], names
            """)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
