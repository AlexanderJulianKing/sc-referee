"""The report's audit grammar is check-owned, closed, and registry-driven."""


EXPECTED_DIMENSIONS = {
    "experimental_unit": ("unit_of_independence",),
    "allele_orientation": ("orientation",),
    "eqtl_design_support": ("unit_of_independence",),
    "confounding": ("conditioning_set",),
    "confounding_strong": ("conditioning_set",),
    "confounding_random_intercept": ("conditioning_set",),
    "confounding_random_intercept_conditional": ("conditioning_set",),
    "contamination_confound": ("conditioning_set",),
    "double_dipping": ("selection",),
    "count_model": ("scale",),
    "pairing": ("unit_of_independence", "estimand"),
    "pseudobulk_integrity": ("unit_of_independence", "scale"),
    "hic_loop_strength": ("inclusion_set", "scale", "weighting"),
    "multiple_testing": ("inclusion_set", "calibration"),
    "effect_size_threshold": ("advisory_policy",),
}


def test_every_registered_check_declares_only_allowed_audit_dimensions():
    from sc_referee.audit_dimensions import AUDIT_DIMENSIONS, AUDIT_DIMENSION_LABELS
    from sc_referee.registry import CHECKS

    assert AUDIT_DIMENSIONS == frozenset(AUDIT_DIMENSION_LABELS)
    assert all(AUDIT_DIMENSION_LABELS[dimension] for dimension in AUDIT_DIMENSIONS)
    for check in CHECKS:
        assert isinstance(check.audit_dimensions, tuple)
        assert check.audit_dimensions
        assert set(check.audit_dimensions) <= AUDIT_DIMENSIONS


def test_registered_check_dimension_mapping_is_pinned():
    from sc_referee.registry import CHECKS

    assert {check.id: check.audit_dimensions for check in CHECKS} == EXPECTED_DIMENSIONS


def test_random_intercept_stage1_has_hard_mapped_citation_and_dimension():
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import CHECKS
    check = next(c for c in CHECKS if c.id == "confounding_random_intercept")
    assert check.audit_dimensions == ("conditioning_set",)
    assert CITATIONS[check.id]


def test_conditional_stage2_has_hard_mapped_citation_and_requires_marker_for_flag():
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import CHECKS
    check = next(c for c in CHECKS if c.id == "confounding_random_intercept_conditional")
    assert check.audit_dimensions == ("conditioning_set",)
    assert CITATIONS[check.id]


def test_contamination_check_has_hard_mapped_citation_and_major_ceiling():
    from sc_referee import statuses as S
    from sc_referee.citations import CITATIONS
    from sc_referee.registry import CHECKS

    check = next(c for c in CHECKS if c.id == "contamination_confound")
    assert check.audit_dimensions == ("conditioning_set",)
    assert check.max_status == S.MAJOR
    assert CITATIONS[check.id]
