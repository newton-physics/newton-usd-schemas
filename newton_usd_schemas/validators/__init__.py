# SPDX-FileCopyrightText: Copyright (c) 2026 The Newton Developers
# SPDX-License-Identifier: Apache-2.0

"""`UsdValidation` validators for the Newton USD schemas.

Importing this module registers the validators plugin, and its validators, with the `UsdValidation.ValidationRegistry`.
Importing `newton_usd_schemas` alone only registers the schemas. Python validators require OpenUSD 26.05 or newer;
with older OpenUSD versions, nothing is registered.
"""

from ._collision import SDF_MAX_RESOLUTION_VALIDATOR
from ._joints import MIMIC_JOINT_VALIDATOR
from ._limits import ATTRIBUTE_HARD_LIMITS_VALIDATOR
from ._migration import RENAMED_ATTRIBUTES_VALIDATOR
from ._registration import PLUGIN_NAME

__all__ = [
    "ATTRIBUTE_HARD_LIMITS_VALIDATOR",
    "MIMIC_JOINT_VALIDATOR",
    "PLUGIN_NAME",
    "RENAMED_ATTRIBUTES_VALIDATOR",
    "SDF_MAX_RESOLUTION_VALIDATOR",
]
