"""Growth-13 paired authority and pair-position proof contracts."""

from __future__ import annotations

import json
import os
import runpy
import subprocess
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from sc_referee_evaluation.lean_pipeline import (
    _description_v2_authority_lock,
    _registered_dependence_callable_set_v2,
)

from sc_referee.core.ids import semantic_digest, sha256_digest
from sc_referee.dependence_recognition_v2.adapter import DependenceRecognitionV2ShadowAdapter
from sc_referee.dependence_recognition_v2.authority_lock import (
    DependenceV2AuthorizationLockError,
    build_dependence_v2_authorization_lock,
)
from sc_referee.dependence_recognition_v2.certificate import (
    verify_paired_dependence_certificate,
)
from sc_referee.dependence_recognition_v2.ir import PairedDependenceCertificate
from sc_referee.dependence_recognition_v2.paired_domain import (
    prove_paired_value_sequence_with_reason,
)
from sc_referee.dependence_recognition_v2.python_analyzer import (
    _trusted_v2_authorizations,
    _trusted_v2_procedure_sets,
    analyze_dependence_growth_python,
    discharge_dependence_growth_analysis,
)
from sc_referee.scientific_checks.core import (
    FrozenBaseRecord,
    FrozenMaterialInput,
    RecordRef,
    ScientificCheckContractError,
)

_BASE = runpy.run_path(str(Path(__file__).with_name("test_dependence_recognition_v2.py")))
_context = _BASE["_context"]
_source = _BASE["_source"]
_RUNTIME = Path(
    os.environ.get(
        "SC_REFEREE_DEPENDENCE_V2_SANDBOX_PYTHON",
        "/Users/alexanderking/Desktop/random_stuff/sc-referee-pilot-runtime/"
        "scipy114-venv/bin/python",
    )
)


def _paired_source(*, arguments: str = "before, after", callable_name: str = "ttest_rel") -> str:
    return f"""import csv
from pathlib import Path
from scipy import stats

INPUT = Path("inputs/data.csv")
REPORT = Path("results/report.md")

def main():
    before = []
    after = []
    with INPUT.open(newline="", encoding="ascii") as handle:
        for row in csv.DictReader(handle):
            before.append(float(row["before"]))
            after.append(float(row["after"]))
    result = stats.{callable_name}({arguments})
    REPORT.write_text(str(result), encoding="utf-8")

main()
"""


def _paired_context(source: str, data: bytes, *, procedure: str = "scipy.stats.ttest_rel"):
    context = _context(source, data)
    analysis_ref = RecordRef("analysis", "analysis:v2")
    procedure_ref = RecordRef("procedure", "procedure-v2:test")
    authority_ref = RecordRef("human_method_authorization", "authorization-v2:test")
    retained = tuple(
        item
        for item in context.base_records
        if item.ref.record_type not in {"procedure", "human_method_authorization"}
    )
    procedure_record = FrozenBaseRecord.from_record(
        procedure_ref,
        {
            "record_type": "procedure",
            "record_id": procedure_ref.record_id,
            "resolved_callable": procedure,
        },
    )
    authority_record = FrozenBaseRecord.from_record(
        authority_ref,
        {
            "record_type": "human_method_authorization",
            "record_id": authority_ref.record_id,
            "actor_id": "human:method-owner",
            "authority_state": "authorized",
            "analysis_target_ref": analysis_ref.to_dict(),
            "procedure_ref": procedure_ref.to_dict(),
            "independent_unit_definition_id": "unit-definition:v2",
            "authorized_key_columns": ["unit_id"],
            "input_path": "inputs/data.csv",
            "input_content_digest": sha256_digest(data),
        },
    )
    return replace(
        context,
        base_records=tuple(
            sorted((*retained, procedure_record, authority_record), key=lambda x: x.ref)
        ),
    )


_UNIQUE = b"unit_id,before,after\nu1,1,2\nu2,3,4\n"
_REPEATED = b"unit_id,before,after\nu1,1,2\nu1,3,4\n"


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\n",
            (("scipy.stats.ttest_rel",), "lock-minted"),
        ),
        (
            "from scipy import stats\n(stats.ttest_rel)(a, b)\n",
            (("scipy.stats.ttest_rel",), "lock-minted"),
        ),
        (
            "from scipy import stats\nstats.wilcoxon(a, b)\n",
            (("scipy.stats.wilcoxon",), "lock-minted"),
        ),
        (
            "from scipy import stats\nf = stats.ttest_rel\nf(a, b)\n",
            (None, "procedure-unresolved-by-lock-schema-resolver"),
        ),
        (
            "from scipy import stats\nstats.ttest_rel = replacement\nstats.ttest_rel(a, b)\n",
            (None, "procedure-binding-not-closed"),
        ),
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\nstats.ttest_rel(c, d)\n",
            (None, "procedure-ambiguous-multiple-statistical-calls"),
        ),
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\nstats.ttest_ind(c, d)\n",
            (None, "procedure-ambiguous-multiple-statistical-calls"),
        ),
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\nstats.binomtest(1, 2)\n",
            (None, "procedure-set-count-member-unsupported"),
        ),
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\nstats.unknown(c)\n",
            (None, "procedure-unavailable-to-closed-lock-schema"),
        ),
        (
            "from scipy import stats\nx = stats.t.ppf(.9, 2)\nstats.ttest_rel(a, b)\n",
            (("scipy.stats.ttest_rel",), "lock-minted"),
        ),
    ],
)
def test_transport_raw_call_precedence(source: str, expected: tuple[Any, str]) -> None:
    assert _registered_dependence_callable_set_v2(source) == expected


@pytest.mark.parametrize(
    "binding",
    [
        "stats = replacement",
        "stats: object = replacement",
        "stats += replacement",
        "stats, other = replacement, None",
        "(stats := replacement)",
        "for stats in values:\n    pass",
        "with manager() as stats:\n    pass",
        "del stats",
        "def stats():\n    pass",
        "class stats:\n    pass",
        "import math as stats",
    ],
)
def test_transport_direct_binding_invalidators(binding: str) -> None:
    source = f"from scipy import stats\n{binding}\nstats.ttest_rel(a, b)\n"
    assert _registered_dependence_callable_set_v2(source) == (
        None,
        "procedure-binding-not-closed",
    )


@pytest.mark.parametrize(
    "source",
    [
        "from scipy import stats\ndef f(stats):\n    return stats.ttest_rel(a, b)\n",
        "from scipy import stats\ntry:\n    pass\nexcept Exception as stats:\n    pass\nstats.ttest_rel(a, b)\n",
        "from scipy import stats\ndef f():\n    global stats\n    return stats.ttest_rel(a, b)\n",
        "from scipy import stats\ndef outer():\n    stats = None\n    def inner():\n        nonlocal stats\n        return stats\n    return inner\nstats.ttest_rel(a, b)\n",
        "from scipy import stats\ndel stats.ttest_rel\nstats.ttest_rel(a, b)\n",
        "from scipy import stats\nmatch value:\n    case stats:\n        pass\nstats.ttest_rel(a, b)\n",
    ],
)
def test_transport_scope_and_deletion_invalidators(source: str) -> None:
    assert _registered_dependence_callable_set_v2(source) == (
        None,
        "procedure-binding-not-closed",
    )


def test_comprehension_binding_uses_its_python_local_scope() -> None:
    source = "from scipy import stats\n[stats.ttest_rel(a, b) for stats in values]\n"
    assert _registered_dependence_callable_set_v2(source) == (
        None,
        "procedure-unresolved-by-lock-schema-resolver",
    )


def test_exact_frozen_paired_opportunity_census(project_root: Path) -> None:
    sources = sorted(
        path
        for path in (project_root / "evaluation/development/dependence-growth-loop").glob(
            "batch-*/authoring/cases/*/workflow/analysis.py"
        )
        if "ttest_rel" in path.read_text(encoding="utf-8")
        or "wilcoxon" in path.read_text(encoding="utf-8")
    )
    assert len(sources) == 9
    text = "\n".join(path.read_text(encoding="utf-8") for path in sources)
    assert text.count("ttest_rel(") == 7
    assert text.count("wilcoxon(") == 4
    results = [_registered_dependence_callable_set_v2(path.read_text()) for path in sources]
    assert sum(value is not None for value, _reason in results) == 7
    assert (
        sum(
            value is None and reason == "procedure-ambiguous-multiple-statistical-calls"
            for value, reason in results
        )
        == 2
    )


def test_lock_builder_rejects_paired_plural_records() -> None:
    with pytest.raises(DependenceV2AuthorizationLockError):
        build_dependence_v2_authorization_lock(
            case_id="case:test",
            snapshot_digest="sha256:" + "0" * 64,
            intake_recorded_at="2026-08-16T00:00:00Z",
            procedure=("scipy.stats.ttest_rel", "scipy.stats.wilcoxon"),
            unit_column="unit_id",
            input_path="inputs/data.csv",
            input_content_digest="sha256:" + "1" * 64,
        )


@pytest.mark.parametrize(
    ("procedure_source", "reason"),
    [
        (
            "from scipy import stats\nstats = replacement\nstats.ttest_rel(a, b)\n",
            "procedure-binding-not-closed",
        ),
        (
            "from scipy import stats\nstats.ttest_rel(a, b)\nstats.ttest_rel(c, d)\n",
            "procedure-ambiguous-multiple-statistical-calls",
        ),
        (
            "from scipy import stats\nfor stats.ttest_rel in [replacement]:\n    pass\nstats.ttest_rel(a, b)\n",
            "procedure-binding-not-closed",
        ),
        (
            "from scipy import stats\nwith manager() as stats.ttest_rel:\n    pass\nstats.ttest_rel(a, b)\n",
            "procedure-binding-not-closed",
        ),
        (
            "from scipy import stats\n[None for stats.ttest_rel in [replacement]]\nstats.ttest_rel(a, b)\n",
            "procedure-binding-not-closed",
        ),
        (
            "def establish():\n    from scipy import stats\nstats.ttest_rel(a, b)\n",
            "procedure-binding-not-closed",
        ),
        (
            "from scipy import stats\nf: object = stats.ttest_rel\nf(a, b)\nstats.ttest_rel(a, b)\n",
            "procedure-unresolved-by-lock-schema-resolver",
        ),
        (
            "from scipy import stats\n(f,) = (stats.ttest_rel,)\nf(a, b)\nstats.ttest_rel(a, b)\n",
            "procedure-unresolved-by-lock-schema-resolver",
        ),
        (
            "from scipy import stats\n(f := stats.ttest_rel)\nf(a, b)\nstats.ttest_rel(a, b)\n",
            "procedure-unresolved-by-lock-schema-resolver",
        ),
        (
            "from scipy import stats\nother = stats\nother.ttest_rel(a, b)\nstats.ttest_rel(a, b)\n",
            "procedure-unresolved-by-lock-schema-resolver",
        ),
    ],
)
def test_no_lock_translation_has_no_file_and_zero_authority_records(
    procedure_source: str, reason: str, tmp_path: Path
) -> None:
    case = tmp_path / "case"
    (case / "workflow").mkdir(parents=True)
    (case / "data").mkdir()
    (case / "workflow/analysis.py").write_text(procedure_source, encoding="ascii")
    (case / "data/input.csv").write_bytes(_UNIQUE)
    (case / "data-description.md").write_text(
        "Independent unit column: unit_id\nOne row is: one paired measurement\n",
        encoding="utf-8",
    )
    lock, observed, unit = _description_v2_authority_lock(
        case_id="case:test",
        case_root=case,
        intake_row={
            "expected_audit_snapshot_digest": "sha256:" + "0" * 64,
            "file_digests": {"data/input.csv": sha256_digest(_UNIQUE)},
        },
        intake_recorded_at="2026-08-16T00:00:00Z",
        description_path="data-description.md",
        input_path="data/input.csv",
    )
    assert lock is None
    assert observed == reason
    assert unit == "unit_id"
    assert not (case / "authorization-lock.json").exists()
    assert (
        sum(
            item.get("record_type") == "human_method_authorization"
            for item in (() if lock is None else lock["records"])
        )
        == 0
    )


@pytest.mark.parametrize(
    ("data", "outcome", "reason"),
    [
        (_UNIQUE, "covered_negative", "one-paired-observation-per-independent-unit"),
        (
            _REPEATED,
            "evaluation_candidate",
            "repeated-unit-pairs-counted-as-independent-ttest-rel-observations",
        ),
    ],
)
def test_pair_position_legitimacy_and_adversity(data: bytes, outcome: str, reason: str) -> None:
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _paired_context(_paired_source(), data)
    )
    assert payload["outcome"] == outcome
    assert payload["reason_code"] == reason
    assert payload["production_finding_permitted"] is False
    assert payload["abstention_reasons"] == []


def test_argument_reversal_preserves_pair_positions() -> None:
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _paired_context(_paired_source(arguments="after, before"), _UNIQUE)
    )
    assert payload["outcome"] == "covered_negative"
    assert payload["payload"]["left_value_column"] == "after"
    assert payload["payload"]["right_value_column"] == "before"


@pytest.mark.parametrize(
    ("source", "reason"),
    [
        (_paired_source(arguments="before"), "paired-operand-arity-mismatch"),
        (_paired_source(arguments="before, after, axis=0"), "paired-procedure-form-unmodeled"),
        (_paired_source(callable_name="wilcoxon"), "paired-procedure-form-unmodeled"),
        (
            _paired_source().replace("after.append", "before.append"),
            "paired-vector-construction-unproven",
        ),
        (
            _paired_source().replace('            after.append(float(row["after"]))\n', ""),
            "paired-vector-construction-unproven",
        ),
        (
            _paired_source().replace("    result =", "    before.clear()\n    result ="),
            "sink-mutates-operand-name",
        ),
        (
            _paired_source().replace("    result =", "    alias = before\n    result ="),
            "sink-aliases-operand-object",
        ),
        (
            _paired_source().replace("    result =", "    before = before[:-1]\n    result ="),
            "operand-name-rebound",
        ),
        (
            _paired_source().replace("    result =", "    (before := before[:-1])\n    result ="),
            "operand-name-rebound",
        ),
        (
            _paired_source().replace("    result =", "    (marker := 1)\n    result ="),
            "named-expression-not-modeled",
        ),
    ],
)
def test_exact_paired_structural_reasons(source: str, reason: str) -> None:
    procedure = "scipy.stats.wilcoxon" if "stats.wilcoxon" in source else "scipy.stats.ttest_rel"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _paired_context(source, _UNIQUE, procedure=procedure)
    )
    assert payload["outcome"] == "unsupported"
    assert payload["abstention_reasons"] == [reason]
    assert payload["production_finding_permitted"] is False


def test_group_crossover_changed_to_paired_refuses_without_reinterpretation() -> None:
    source = _source().replace("stats.ttest_ind", "stats.ttest_rel")
    data = b"unit_id,arm,value\nu1,A,1\nu1,B,2\nu2,A,3\nu2,B,4\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_paired_context(source, data))
    assert payload["abstention_reasons"] == ["paired-position-unit-binding-unproven"]


def test_unsupported_reader_materialization_has_its_exact_stage_reason() -> None:
    source = _paired_source().replace(
        "        for row in csv.DictReader(handle):\n"
        '            before.append(float(row["before"]))\n'
        '            after.append(float(row["after"]))',
        "        rows = list(csv.DictReader(handle))\n"
        "    for row in rows:\n"
        '        before.append(float(row["before"]))\n'
        '        after.append(float(row["after"]))',
    )
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_paired_context(source, _UNIQUE))
    assert payload["abstention_reasons"] == ["paired-reader-form-unsupported"]


@pytest.mark.parametrize(
    ("data", "reason"),
    [
        (b"unit_id,before,before\nu1,1,2\n", "duplicate-header"),
        (b"unit_id,before,after\n,1,2\n", "paired-unit-cell-empty"),
        (b"unit_id,before,after\nu1,,2\n", "paired-value-cast-unproven"),
        (b"unit_id,before,after\nu1,nope,2\n", "paired-value-cast-unproven"),
        (b"unit_id,before,after\nu1,nan,2\n", "paired-value-not-finite"),
        (b"unit_id,before,after\nu1,inf,2\n", "paired-value-not-finite"),
        (b"unit_id,before,after\nu1,1\n", "ragged-row"),
        (b"unit_id,before,after\n", "paired-domain-unproven"),
        (b"\xef\xbb\xbfunit_id,before,after\nu1,1,2\n", "bom-unsupported"),
        ("unit_id,before,after\nu1,é,2\n".encode(), "reader-bytes-not-ascii"),
    ],
)
def test_exact_paired_domain_reasons(data: bytes, reason: str) -> None:
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _paired_context(_paired_source(), data)
    )
    assert payload["abstention_reasons"] == [reason]


def test_direct_prover_binding_mismatch_is_phase_specific() -> None:
    context = _paired_context(_paired_source(), _UNIQUE)
    analysis = analyze_dependence_growth_python(context)
    assert analysis.obligation is not None
    fact, reason = prove_paired_value_sequence_with_reason(
        context.material_inputs[0],
        obligation=replace(analysis.obligation, path="other.csv"),
    )
    assert fact is None
    assert reason == "paired-domain-binding-mismatch"


def test_material_selection_and_paired_discharge_are_distinct_phases() -> None:
    context = _paired_context(_paired_source(), _UNIQUE)
    authority = next(
        item
        for item in context.base_records
        if item.ref.record_type == "human_method_authorization"
    )
    authority_value = json.loads(authority.canonical_payload)
    authority_value["input_path"] = "missing.csv"
    missing = replace(
        context,
        base_records=tuple(
            FrozenBaseRecord.from_record(item.ref, authority_value) if item is authority else item
            for item in context.base_records
        ),
    )
    payload = DependenceRecognitionV2ShadowAdapter().inspect(missing)
    assert payload["abstention_reasons"] == ["authority-material-binding-mismatch"]

    analysis = analyze_dependence_growth_python(context)
    assert isinstance(analysis.certificate, PairedDependenceCertificate)
    assert analysis.obligation is not None
    changed = replace(analysis.obligation, path="other.csv")
    forged = replace(
        analysis, obligation=changed, certificate=replace(analysis.certificate, obligation=changed)
    )
    discharged = discharge_dependence_growth_analysis(forged, context)
    assert discharged.abstention_reasons == ("paired-domain-binding-mismatch",)


def test_invalid_frozen_material_digest_is_a_constructor_contract_error() -> None:
    material = _paired_context(_paired_source(), _UNIQUE).material_inputs[0]
    with pytest.raises(ScientificCheckContractError):
        FrozenMaterialInput(
            path=material.path,
            file_ref=material.file_ref,
            asset_identity_ref=material.asset_identity_ref,
            content=material.content,
            content_digest="sha256:" + "0" * 64,
        )


def test_direct_prover_unsupported_encoding_is_not_a_reader_shape_reason() -> None:
    context = _paired_context(_paired_source(), _UNIQUE)
    analysis = analyze_dependence_growth_python(context)
    assert analysis.obligation is not None
    fact, reason = prove_paired_value_sequence_with_reason(
        context.material_inputs[0], obligation=replace(analysis.obligation, encoding="latin-1")
    )
    assert fact is None
    assert reason == "unsupported-reader-encoding"


def test_paired_kernel_bypass_obligations_are_independent() -> None:
    context = _paired_context(_paired_source(), _REPEATED)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    verified = discharged.verified_certificate
    assert verified is not None
    certificate = analysis.certificate
    assert isinstance(certificate, PairedDependenceCertificate)
    certificate = replace(
        certificate,
        certificate_id=verified.certificate_id,
        conclusion=verified.conclusion,
    )
    common = {
        "trusted_paired_facts": (verified.fact,),
        "trusted_material_inputs": (context.material_inputs[0],),
        "trusted_authorizations": _trusted_v2_authorizations(context),
        "trusted_procedure_sets": _trusted_v2_procedure_sets(context),
        "source_bytes": context.documents[0].content,
    }
    assert verify_paired_dependence_certificate(certificate, **common) is not None
    cases = [
        (replace(certificate, source_extent=(0, 1)), "paired-envelope-binding"),
        (replace(certificate, authority_record_id="other"), "paired-authority-binding"),
        (replace(certificate, procedure_call_token="other"), "paired-procedure-class"),
        (replace(certificate, left_vector_name="other"), "paired-procedure-class"),
        (
            replace(certificate, conclusion="one_pair_position_per_unit"),
            "paired-conclusion-equation",
        ),
        (replace(certificate, certificate_id="other"), "paired-certificate-identity"),
        (replace(certificate, operand_slice_statement_tokens=()), "paired-sink-partition"),
    ]
    for forged, expected in cases:
        failures: list[str] = []
        assert (
            verify_paired_dependence_certificate(forged, **common, _failure_reasons=failures)
            is None
        )
        assert failures == [expected]

    malformed = b"not valid python ("
    failures = []
    assert (
        verify_paired_dependence_certificate(
            replace(
                certificate,
                source_digest=sha256_digest(malformed),
                source_extent=(0, len(malformed)),
            ),
            **{**common, "source_bytes": malformed},
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-source-parse"]

    oversized = b"#" * (1024 * 1024 + 1)
    failures = []
    assert (
        verify_paired_dependence_certificate(
            replace(
                certificate,
                source_digest=sha256_digest(oversized),
                source_extent=(0, len(oversized)),
            ),
            **{**common, "source_bytes": oversized},
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-source-size"]

    failures = []
    forged_fact = replace(verified.fact, header=("unit_id", "before"))
    assert (
        verify_paired_dependence_certificate(
            certificate,
            **{**common, "trusted_paired_facts": (forged_fact,)},
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-fact-closure"]

    incomplete = context.documents[0].content.replace(
        b'            after.append(float(row["after"]))', b"            pass"
    )
    failures = []
    assert (
        verify_paired_dependence_certificate(
            replace(
                certificate,
                source_digest=sha256_digest(incomplete),
                source_extent=(0, len(incomplete)),
            ),
            **{**common, "source_bytes": incomplete},
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-vector-completeness"]

    wrong_column = context.documents[0].content.replace(b'row["after"]', b'row["other"]')
    failures = []
    assert (
        verify_paired_dependence_certificate(
            replace(
                certificate,
                source_digest=sha256_digest(wrong_column),
                source_extent=(0, len(wrong_column)),
            ),
            **{**common, "source_bytes": wrong_column},
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-position-equation"]

    assert certificate.alpha_renames
    failures = []
    bad_rename = replace(certificate.alpha_renames[0], fresh_name="__dependence_v2_wrong")
    assert (
        verify_paired_dependence_certificate(
            replace(certificate, alpha_renames=(bad_rename, *certificate.alpha_renames[1:])),
            **common,
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-alpha-renaming"]


def test_paired_kernel_replays_complete_fact_from_selected_material() -> None:
    context = _paired_context(_paired_source(), _REPEATED)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    verified = discharged.verified_certificate
    assert verified is not None
    certificate = analysis.certificate
    assert isinstance(certificate, PairedDependenceCertificate)
    certificate = replace(
        certificate,
        certificate_id=verified.certificate_id,
        conclusion=verified.conclusion,
    )
    common = {
        "trusted_material_inputs": (context.material_inputs[0],),
        "trusted_authorizations": _trusted_v2_authorizations(context),
        "trusted_procedure_sets": _trusted_v2_procedure_sets(context),
        "source_bytes": context.documents[0].content,
    }
    observations = verified.fact.observations
    first, second = observations
    wrong_unit = "unit-key:sha256:" + "b" * 64
    wrong_unit_observations = tuple(
        replace(item, authorized_unit_id=wrong_unit) for item in observations
    )
    reordered_values = (
        replace(
            first,
            left_source_value=second.left_source_value,
            right_source_value=second.right_source_value,
            left_cast_value_repr=second.left_cast_value_repr,
            right_cast_value_repr=second.right_cast_value_repr,
        ),
        replace(
            second,
            left_source_value=first.left_source_value,
            right_source_value=first.right_source_value,
            left_cast_value_repr=first.left_cast_value_repr,
            right_cast_value_repr=first.right_cast_value_repr,
        ),
    )
    fact_cases = (
        replace(
            verified.fact,
            observations=(
                replace(first, observation_id="paired-observation:sha256:" + "a" * 64),
                second,
            ),
        ),
        replace(
            verified.fact,
            observations=(replace(first, left_cast_value_repr="999.0"), second),
        ),
        replace(verified.fact, observations=wrong_unit_observations),
        replace(
            verified.fact,
            observations=(replace(first, left_source_value="01.0"), second),
        ),
        replace(verified.fact, header=tuple(reversed(verified.fact.header))),
        replace(verified.fact, observations=reordered_values),
        replace(verified.fact, file_ref=RecordRef("file_record", "file:wrong")),
        replace(
            verified.fact,
            asset_identity_ref=RecordRef("asset_identity", "asset:wrong"),
        ),
    )
    for forged_fact in fact_cases:
        failures: list[str] = []
        assert (
            verify_paired_dependence_certificate(
                certificate,
                trusted_paired_facts=(forged_fact,),
                **common,
                _failure_reasons=failures,
            )
            is None
        )
        assert failures == ["paired-fact-closure"]

    distinct_fact = replace(
        verified.fact,
        observations=(
            first,
            replace(second, authorized_unit_id="unit-key:sha256:" + "c" * 64),
        ),
    )
    distinct_certificate = replace(certificate, conclusion="one_pair_position_per_unit")
    distinct_certificate = replace(
        distinct_certificate,
        certificate_id=f"dependence-growth-paired-certificate:{semantic_digest({'source_digest': distinct_certificate.source_digest, 'fact': distinct_fact.evidence_id, 'left': distinct_certificate.left_vector_name, 'right': distinct_certificate.right_vector_name, 'conclusion': distinct_certificate.conclusion})}",
    )
    failures = []
    assert (
        verify_paired_dependence_certificate(
            distinct_certificate,
            trusted_paired_facts=(distinct_fact,),
            **common,
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-fact-closure"]


def test_paired_kernel_dead_construct_bypass_has_its_own_obligation() -> None:
    source = _paired_source().replace(
        "def main():", 'def unused():\n    return "dead"\n\ndef main():'
    )
    context = _paired_context(source, _UNIQUE)
    analysis = analyze_dependence_growth_python(context)
    discharged = discharge_dependence_growth_analysis(analysis, context)
    verified = discharged.verified_certificate
    assert verified is not None
    certificate = analysis.certificate
    assert isinstance(certificate, PairedDependenceCertificate)
    certificate = replace(
        certificate,
        certificate_id=verified.certificate_id,
        conclusion=verified.conclusion,
        dead_syntactic_construct_tokens=(),
    )
    failures: list[str] = []
    assert (
        verify_paired_dependence_certificate(
            certificate,
            trusted_paired_facts=(verified.fact,),
            trusted_material_inputs=(context.material_inputs[0],),
            trusted_authorizations=_trusted_v2_authorizations(context),
            trusted_procedure_sets=_trusted_v2_procedure_sets(context),
            source_bytes=context.documents[0].content,
            _failure_reasons=failures,
        )
        is None
    )
    assert failures == ["paired-dead-construct-completeness"]


def test_pinned_runtime_operands_match_certificate_order(tmp_path: Path) -> None:
    if not _RUNTIME.is_file():
        pytest.fail(f"required pinned SciPy runtime is absent: {_RUNTIME}")
    source = _paired_source().replace(
        "from scipy import stats",
        "from scipy import stats\n"
        "_real = stats.ttest_rel\n"
        "def capture(a, b):\n"
        '    Path("results/operands.json").write_text(json.dumps([a, b]))\n'
        "    return _real(a, b)\n"
        "import json\n"
        "stats.ttest_rel = capture",
    )
    root = tmp_path / "case"
    (root / "inputs").mkdir(parents=True)
    (root / "workflow").mkdir()
    (root / "results").mkdir()
    (root / "inputs/data.csv").write_bytes(_REPEATED)
    (root / "workflow/analysis.py").write_text(source, encoding="ascii")
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "workflow/analysis.py"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert json.loads((root / "results/operands.json").read_text()) == [[1.0, 3.0], [2.0, 4.0]]


@pytest.mark.parametrize(
    "source",
    [
        """from scipy import stats
class ReplacementStats:
    @staticmethod
    def ttest_rel(a, b):
        print("REPLACEMENT")
stats = ReplacementStats()
stats.ttest_rel([1.0], [2.0])
""",
        """from scipy import stats
def replacement(a, b):
    print("REPLACEMENT")
stats.ttest_rel = replacement
stats.ttest_rel([1.0], [2.0])
""",
        """from scipy import stats
def replacement(a, b):
    print("REPLACEMENT")
for stats.ttest_rel in [replacement]:
    pass
stats.ttest_rel([1.0], [2.0])
""",
    ],
)
def test_pinned_runtime_binding_replacements_never_mint_authority(
    source: str, tmp_path: Path
) -> None:
    if not _RUNTIME.is_file():
        pytest.fail(f"required pinned SciPy runtime is absent: {_RUNTIME}")
    completed = subprocess.run(
        [str(_RUNTIME), "-I", "-c", source],
        cwd=tmp_path,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    assert completed.stdout.decode().strip() == "REPLACEMENT"
    assert _registered_dependence_callable_set_v2(source) == (
        None,
        "procedure-binding-not-closed",
    )


def test_authority_free_payload_uses_reason_code_not_abstention_member() -> None:
    payload = DependenceRecognitionV2ShadowAdapter().inspect(
        _context(_paired_source(), _UNIQUE, authority=False)
    )
    assert payload["outcome"] == "question"
    assert payload["reason_code"] == "independent-unit-definition-unresolved"
    assert payload["abstention_reasons"] == []


def test_row_independent_crossover_path_is_unchanged() -> None:
    data = b"unit_id,arm,value\nu1,A,1\nu1,B,2\nu2,A,3\nu2,B,4\n"
    payload = DependenceRecognitionV2ShadowAdapter().inspect(_context(_source(), data))
    assert payload["abstention_reasons"] == ["unit-spans-multiple-operands"]
