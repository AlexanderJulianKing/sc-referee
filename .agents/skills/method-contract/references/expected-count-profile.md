# Expected-count profile v1

Accept only a complete JSON object with exactly these fields and closed values:

```json
{
  "profile_id": "expected_count_background_v1",
  "profile_version": "1.0.0",
  "estimator_family": "negative_binomial_glm | same_stratum_arithmetic_mean",
  "likelihood_family": "negative_binomial | not_applicable",
  "link_function": "log | not_applicable",
  "background_scope": "model_predicted_expected_count | other_same_stratum_observations",
  "grouping_structure": "replicate_intercepts | replicate_specific_background",
  "covariate_terms": [],
  "group_specific_terms": [],
  "training_exclusions": ["target_observation"],
  "target_excluded": true,
  "analysis_resolution_bp": 20000
}
```

Allowed `covariate_terms` are `distance`, `exposure`, `gc`, `mappability`, and
`restriction_site_count`. Allowed `group_specific_terms` are `distance` and `gc`. Allowed
`training_exclusions` are `case_specific_structural_variant`, `low_mappability`, and
`target_observation`. Arrays are duplicate-free and canonicalized in sorted order.

The arithmetic-mean estimator requires `not_applicable` likelihood/link and
`other_same_stratum_observations`. The negative-binomial estimator requires
`negative_binomial`, `log`, and `model_predicted_expected_count`. Both require
`target_excluded: true` and `target_observation` in the exclusions.

Do not select among these values for the scientist. If the scientist supplies an unsupported,
partial, or internally inconsistent object, preserve the unresolved contract and explain the exact
validation error.
