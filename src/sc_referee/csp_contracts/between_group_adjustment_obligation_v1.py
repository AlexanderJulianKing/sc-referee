"""Manifest for the sole MVP between-group adjustment obligation."""
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


CONTRACT_TYPE = "between_group_adjustment_obligation/v1"
REQUIRED_FIELDS = ("between_group_policy", "may_rely_on_re_exogeneity")
AUTHORIZED_CONSUMER = "confounding_random_intercept_conditional"
VALIDATOR_VERSION = "between-group-obligation-v1"
AUTHORITY_ATTESTATION = "I am responsible for this result's scientific interpretation"
CONSEQUENCE = (
    "Confirmation may allow confounding_random_intercept_conditional to flag this result."
)
PREMISE_TEMPLATE = (
    "Arbitrary differences among {group} groups must be removed, and the analysis may not rely "
    "on random-intercept baseline differences being unrelated to condition. This requires exact "
    "fixed-effect-equivalent projection: a random intercept never satisfies it, however close, "
    "and a tolerance-level fixed-effect sensitivity is not sufficient."
)


def validate_values(values: Mapping[str, object]) -> tuple[str, ...]:
    problems = []
    if values.get("between_group_policy") != "remove_arbitrary":
        problems.append("arbitrary_between_group_differences_not_required_removed")
    if values.get("may_rely_on_re_exogeneity") is not False:
        problems.append("re_exogeneity_is_permitted")
    return tuple(problems)


@dataclass(frozen=True)
class ContractManifest:
    contract_type: str
    required_fields: tuple[str, ...]
    authorized_consumer: str
    validator_version: str
    authority_attestation: str
    consequence: str
    premise_template: str
    teach_back_ids: Mapping[str, str]
    validate_values: object
    scope_field_bindings: Mapping[str, str] = field(default_factory=dict)
    stage: str | None = None
    component_field_groups: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "teach_back_ids", MappingProxyType(dict(self.teach_back_ids)))
        object.__setattr__(self, "scope_field_bindings",
                           MappingProxyType(dict(self.scope_field_bindings)))
        object.__setattr__(self, "component_field_groups",
                           MappingProxyType({key: tuple(value) for key, value
                                             in self.component_field_groups.items()}))


MANIFEST = ContractManifest(
    contract_type=CONTRACT_TYPE,
    required_fields=REQUIRED_FIELDS,
    authorized_consumer=AUTHORIZED_CONSUMER,
    validator_version=VALIDATOR_VERSION,
    authority_attestation=AUTHORITY_ATTESTATION,
    consequence=CONSEQUENCE,
    premise_template=PREMISE_TEMPLATE,
    teach_back_ids={
        "between_group_policy": "remove_arbitrary",
        "may_rely_on_re_exogeneity": "must_not_rely",
    },
    validate_values=validate_values,
)
