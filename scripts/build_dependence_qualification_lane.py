"""Build the two-block dependence qualification lane without opening it.

This one-shot builder is intentionally absent from repository generation.  It
freezes a seven-case threshold-pilot dress rehearsal and a separate seven-case
qualification-heldout block.  Tests may write the artifacts only below a
temporary directory; the real lane remains unbuilt pending maintainer action.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from sc_referee_evaluation.direct_qualification_lane import (
    freeze_authoring_brief_manifest,
    freeze_direct_qualification_lane,
    freeze_participant_enrollment,
)
from sc_referee_evaluation.prospective_qualification import REQUIRED_CELL_TYPES

from sc_referee.core.ids import semantic_digest, sha256_digest, stable_id
from sc_referee.detectors.bounded_analysis_method_conflict import (
    BoundedAnalysisMethodConflictDetector,
)
from sc_referee.scientific_checks.profiles import scientific_check_release_registry
from scripts.lean_pipeline import default_dependence_config

LANE_RELATIVE = Path(
    "evaluation/qualification/"
    "authorized-independent-unit-entry-into-row-independent-procedure-"
    "v1.1.0-direct-lane"
)
REGISTRY_RELATIVE = Path("src/sc_referee/resources/scientific-check-manifests-v1/registry.json")
CHECK_ID = "check:authorized-independent-unit-entry-into-row-independent-procedure"
CANDIDATE_ID = "one-analyzed-row-per-authorized-independent-unit"
ENVELOPE_ID = "relation-envelope:authorized-independent-unit-entry-into-row-independent-procedure"
CANONICAL_ISSUE_CLASS = (
    "issue-class:repeated-authorized-independent-unit-entry-into-row-independent-procedure"
)
DETECTOR_ID = "detector:bounded-analysis-method-conflict"
LANE_ID = "lane:authorized-independent-unit-entry-v1"
PILOT_BLOCK_ID = "block:" + semantic_digest({"lane_id": LANE_ID, "role": "threshold_pilot"})[7:23]
HELDOUT_BLOCK_ID = (
    "block:" + semantic_digest({"lane_id": LANE_ID, "role": "qualification_heldout"})[7:23]
)
FROZEN_AT = "2026-08-10T23:02:00Z"
ASSIGNED_AT = "2026-08-10T23:01:00Z"
DETECTOR_FROZEN_AT = "2026-08-10T23:00:00Z"

PILOT_AUTHOR_1 = "actor:dependence-pilot-e-sealed-author-01"
PILOT_AUTHOR_2 = "actor:dependence-pilot-e-sealed-author-02"
HELDOUT_AUTHOR_1 = "actor:dependence-heldout-sealed-author-01"
HELDOUT_AUTHOR_2 = "actor:dependence-heldout-sealed-author-02"
STAGE1_IDS = (
    "actor:dependence-stage1-claude-01",
    "actor:dependence-stage1-claude-02",
    "actor:dependence-stage1-codex-01",
    "actor:dependence-stage1-codex-02",
)
STAGE2_IDS = (
    "actor:dependence-stage2-claude-01",
    "actor:dependence-stage2-codex-01",
)
ROLES = (
    "error_bearing",
    "corrected_twin",
    "valid_alternative",
    "hard_negative",
    "ambiguous",
    "unsupported",
    "renamed_implementation",
)
AUTHOR_BY_BLOCK_AND_ROLE = {
    "threshold_pilot": {
        "error_bearing": PILOT_AUTHOR_1,
        "corrected_twin": PILOT_AUTHOR_1,
        "valid_alternative": PILOT_AUTHOR_2,
        "hard_negative": PILOT_AUTHOR_2,
        "ambiguous": PILOT_AUTHOR_2,
        "unsupported": PILOT_AUTHOR_2,
        "renamed_implementation": PILOT_AUTHOR_2,
    },
    "qualification_heldout": {
        "error_bearing": HELDOUT_AUTHOR_1,
        "corrected_twin": HELDOUT_AUTHOR_1,
        "valid_alternative": HELDOUT_AUTHOR_2,
        "hard_negative": HELDOUT_AUTHOR_2,
        "ambiguous": HELDOUT_AUTHOR_2,
        "unsupported": HELDOUT_AUTHOR_2,
        "renamed_implementation": HELDOUT_AUTHOR_2,
    },
}
ADDITIONAL_HIDDEN_TERMS = [
    "pseudoreplication",
    "repeated measurement",
    "independent unit",
    CANONICAL_ISSUE_CLASS,
    CANDIDATE_ID,
]

HELDOUT_ERROR_TRIPLES = (
    ("ea01", "eb07", "et01"),
    ("ea01", "eb08", "et02"),
    ("ea02", "eb09", "et03"),
    ("ea02", "eb10", "et04"),
    ("ea03", "eb11", "et05"),
    ("ea03", "eb12", "et06"),
    ("ea04", "eb13", "et07"),
    ("ea04", "eb14", "et08"),
    ("ea05", "eb15", "et09"),
    ("ea05", "eb16", "et10"),
    ("ea06", "eb17", "et11"),
    ("ea06", "eb18", "et12"),
    ("ea07", "eb19", "et13"),
    ("ea07", "eb20", "et14"),
    ("ea08", "eb21", "et15"),
    ("ea08", "eb22", "et16"),
    ("ea09", "eb23", "et17"),
    ("ea09", "eb24", "et18"),
    ("ea10", "eb01", "et19"),
    ("ea10", "eb02", "et20"),
    ("ea11", "eb03", "et21"),
    ("ea11", "eb04", "et22"),
    ("ea12", "eb05", "et23"),
    ("ea12", "eb06", "et24"),
)
HELDOUT_ERROR_LEFT = (
    101.0,
    101.5,
    102.0,
    102.5,
    103.0,
    103.5,
    104.0,
    104.5,
    105.0,
    105.5,
    106.0,
    106.5,
    107.0,
    107.5,
    108.0,
    108.5,
    109.0,
    109.5,
    110.0,
    110.5,
    111.0,
    111.5,
    112.0,
    112.5,
)
HELDOUT_ERROR_RIGHT = (
    102.0,
    102.25,
    104.0,
    104.25,
    103.0,
    103.25,
    105.0,
    105.25,
    107.0,
    107.25,
    106.0,
    106.25,
    109.0,
    109.25,
    108.0,
    108.25,
    111.0,
    111.25,
    110.0,
    110.25,
    113.0,
    113.25,
    112.0,
    112.25,
)
HELDOUT_ERROR_RESULT = (
    "TtestResult(statistic=np.float64(-0.8581613266497022), "
    "pvalue=np.float64(0.3952529117073811), df=np.float64(46.0))"
)

HELDOUT_TWIN_TRIPLES = (
    ("ca01", "cb07", "ct01"),
    ("ca02", "cb09", "ct02"),
    ("ca03", "cb11", "ct03"),
    ("ca04", "cb13", "ct04"),
    ("ca05", "cb15", "ct05"),
    ("ca06", "cb17", "ct06"),
    ("ca07", "cb19", "ct07"),
    ("ca08", "cb21", "ct08"),
    ("ca09", "cb23", "ct09"),
    ("ca10", "cb01", "ct10"),
    ("ca11", "cb03", "ct11"),
    ("ca12", "cb05", "ct12"),
)
HELDOUT_TWIN_LEFT = (
    201.0,
    202.0,
    203.0,
    204.0,
    205.0,
    206.0,
    207.0,
    208.0,
    209.0,
    210.0,
    211.0,
    212.0,
)
HELDOUT_TWIN_RIGHT = (
    202.0,
    204.0,
    203.0,
    205.0,
    207.0,
    206.0,
    209.0,
    208.0,
    211.0,
    210.0,
    213.0,
    212.0,
)
HELDOUT_TWIN_RESULT = (
    "TtestResult(statistic=np.float64(-0.6793662204867575), "
    "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
)

HELDOUT_VALID_TRIPLES = (
    ("va01", "vb04", "vt01"),
    ("va02", "vb06", "vt02"),
    ("va03", "vb08", "vt03"),
    ("va04", "vb10", "vt04"),
    ("va05", "vb12", "vt05"),
    ("va06", "vb14", "vt06"),
    ("va07", "vb16", "vt07"),
    ("va08", "vb18", "vt08"),
    ("va09", "vb20", "vt09"),
    ("va10", "vb22", "vt10"),
    ("va11", "vb24", "vt11"),
    ("va12", "vb02", "vt12"),
)
HELDOUT_VALID_LEFT = (
    301.0,
    302.0,
    303.0,
    304.0,
    305.0,
    306.0,
    307.0,
    308.0,
    309.0,
    310.0,
    311.0,
    312.0,
)
HELDOUT_VALID_RIGHT = (
    303.0,
    305.0,
    304.0,
    306.0,
    308.0,
    307.0,
    310.0,
    309.0,
    312.0,
    311.0,
    314.0,
    313.0,
)
HELDOUT_VALID_RESULT = (
    "MannwhitneyuResult(statistic=np.float64(50.0), pvalue=np.float64(0.21349573711632197))"
)

HELDOUT_HARD_TRIPLES = (
    ("ha01", "hb13", "ht01"),
    ("ha02", "hb14", "ht02"),
    ("ha03", "hb15", "ht03"),
    ("ha04", "hb16", "ht04"),
    ("ha05", "hb17", "ht05"),
    ("ha06", "hb18", "ht06"),
    ("ha07", "hb19", "ht07"),
    ("ha08", "hb20", "ht08"),
    ("ha09", "hb21", "ht09"),
    ("ha10", "hb22", "ht10"),
    ("ha11", "hb23", "ht11"),
    ("ha12", "hb24", "ht12"),
    ("ha13", "hb01", "ht13"),
    ("ha14", "hb02", "ht14"),
    ("ha15", "hb03", "ht15"),
    ("ha16", "hb04", "ht16"),
    ("ha17", "hb05", "ht17"),
    ("ha18", "hb06", "ht18"),
    ("ha19", "hb07", "ht19"),
    ("ha20", "hb08", "ht20"),
    ("ha21", "hb09", "ht21"),
    ("ha22", "hb10", "ht22"),
    ("ha23", "hb11", "ht23"),
    ("ha24", "hb12", "ht24"),
)
HELDOUT_HARD_LEFT = (
    401.0,
    401.5,
    402.0,
    402.5,
    403.0,
    403.5,
    404.0,
    404.5,
    405.0,
    405.5,
    406.0,
    406.5,
    407.0,
    407.5,
    408.0,
    408.5,
    409.0,
    409.5,
    410.0,
    410.5,
    411.0,
    411.5,
    412.0,
    412.5,
)
HELDOUT_HARD_RIGHT = (
    402.0,
    402.25,
    404.0,
    404.25,
    403.0,
    403.25,
    405.0,
    405.25,
    407.0,
    407.25,
    406.0,
    406.25,
    409.0,
    409.25,
    408.0,
    408.25,
    411.0,
    411.25,
    410.0,
    410.25,
    413.0,
    413.25,
    412.0,
    412.25,
)
HELDOUT_HARD_RESULT = (
    "TtestResult(statistic=np.float64(-0.8581613266497022), "
    "pvalue=np.float64(0.3952529117073811), df=np.float64(46.0))"
)

HELDOUT_AMBIGUOUS_TRIPLES = (
    ("ma01", "mb07", "mt01"),
    ("ma01", "mb11", "mt02"),
    ("ma02", "mb06", "mt03"),
    ("ma02", "mb09", "mt04"),
    ("ma03", "mb01", "mt05"),
    ("ma03", "mb12", "mt06"),
    ("ma04", "mb05", "mt07"),
    ("ma04", "mb03", "mt08"),
    ("ma05", "mb10", "mt09"),
    ("ma05", "mb04", "mt10"),
    ("ma06", "mb08", "mt11"),
    ("ma06", "mb02", "mt12"),
)
HELDOUT_AMBIGUOUS_LEFT = (
    501.0,
    502.0,
    503.0,
    504.0,
    505.0,
    506.0,
    507.0,
    508.0,
    509.0,
    510.0,
    511.0,
    512.0,
)
HELDOUT_AMBIGUOUS_RIGHT = (
    502.0,
    504.0,
    503.0,
    505.0,
    507.0,
    506.0,
    509.0,
    508.0,
    511.0,
    510.0,
    513.0,
    512.0,
)
HELDOUT_AMBIGUOUS_RESULT = (
    "TtestResult(statistic=np.float64(-0.6793662204867575), "
    "pvalue=np.float64(0.5039915691282064), df=np.float64(22.0))"
)

HELDOUT_UNSUPPORTED_TRIPLES = (
    ("pa01", "pb05", "pt01"),
    ("pa02", "pb07", "pt02"),
    ("pa03", "pb09", "pt03"),
    ("pa04", "pb11", "pt04"),
    ("pa05", "pb13", "pt05"),
    ("pa06", "pb15", "pt06"),
    ("pa07", "pb17", "pt07"),
    ("pa08", "pb19", "pt08"),
    ("pa09", "pb21", "pt09"),
    ("pa10", "pb23", "pt10"),
    ("pa11", "pb01", "pt11"),
    ("pa12", "pb03", "pt12"),
)
HELDOUT_UNSUPPORTED_LEFT = (
    601.0,
    602.0,
    603.0,
    604.0,
    605.0,
    606.0,
    607.0,
    608.0,
    609.0,
    610.0,
    611.0,
    612.0,
)
HELDOUT_UNSUPPORTED_RIGHT = (
    603.0,
    605.0,
    604.0,
    606.0,
    608.0,
    607.0,
    610.0,
    609.0,
    612.0,
    611.0,
    614.0,
    613.0,
)
HELDOUT_UNSUPPORTED_RESULT = (
    "TtestResult(statistic=np.float64(-7.26636084983398), "
    "pvalue=np.float64(1.610229916816512e-05), df=np.int64(11))"
)

PILOT_RENAMED_TRIPLES = (
    ("x01", "y09", "s01"),
    ("x01", "y10", "s02"),
    ("x01", "y11", "s03"),
    ("x02", "y12", "s04"),
    ("x02", "y13", "s05"),
    ("x02", "y14", "s06"),
    ("x03", "y15", "s07"),
    ("x03", "y16", "s08"),
    ("x03", "y17", "s09"),
    ("x04", "y18", "s10"),
    ("x04", "y19", "s11"),
    ("x04", "y20", "s12"),
    ("x05", "y21", "s13"),
    ("x05", "y22", "s14"),
    ("x05", "y23", "s15"),
    ("x06", "y24", "s16"),
    ("x06", "y08", "s17"),
    ("x06", "y02", "s18"),
    ("x07", "y03", "s19"),
    ("x07", "y04", "s20"),
    ("x07", "y05", "s21"),
    ("x08", "y06", "s22"),
    ("x08", "y07", "s23"),
    ("x08", "y01", "s24"),
)
PILOT_RENAMED_LEFT = (
    10.0,
    10.5,
    11.0,
    20.0,
    20.5,
    21.0,
    30.0,
    30.5,
    31.0,
    40.0,
    40.5,
    41.0,
    50.0,
    50.5,
    51.0,
    60.0,
    60.5,
    61.0,
    70.0,
    70.5,
    71.0,
    80.0,
    80.5,
    81.0,
)
PILOT_RENAMED_RIGHT = (
    12.0,
    22.0,
    32.0,
    42.0,
    52.0,
    62.0,
    72.0,
    82.0,
    14.0,
    24.0,
    34.0,
    44.0,
    54.0,
    64.0,
    74.0,
    84.0,
    16.0,
    26.0,
    36.0,
    46.0,
    56.0,
    66.0,
    76.0,
    86.0,
)
PILOT_RENAMED_RESULT = (
    "MannwhitneyuResult(statistic=np.float64(252.0), pvalue=np.float64(0.4641699943597949))"
)

HELDOUT_RENAMED_TRIPLES = (
    ("r01", "z09", "q01"),
    ("r01", "z10", "q02"),
    ("r01", "z11", "q03"),
    ("r02", "z12", "q04"),
    ("r02", "z13", "q05"),
    ("r02", "z14", "q06"),
    ("r03", "z15", "q07"),
    ("r03", "z16", "q08"),
    ("r03", "z17", "q09"),
    ("r04", "z18", "q10"),
    ("r04", "z19", "q11"),
    ("r04", "z20", "q12"),
    ("r05", "z21", "q13"),
    ("r05", "z22", "q14"),
    ("r05", "z23", "q15"),
    ("r06", "z24", "q16"),
    ("r06", "z08", "q17"),
    ("r06", "z02", "q18"),
    ("r07", "z03", "q19"),
    ("r07", "z04", "q20"),
    ("r07", "z05", "q21"),
    ("r08", "z06", "q22"),
    ("r08", "z07", "q23"),
    ("r08", "z01", "q24"),
)
HELDOUT_RENAMED_LEFT = (
    701.0,
    701.25,
    701.75,
    702.0,
    702.25,
    702.75,
    703.0,
    703.25,
    703.75,
    704.0,
    704.25,
    704.75,
    705.0,
    705.25,
    705.75,
    706.0,
    706.25,
    706.75,
    707.0,
    707.25,
    707.75,
    708.0,
    708.25,
    708.75,
)
HELDOUT_RENAMED_RIGHT = (
    699.125,
    699.625,
    700.125,
    700.625,
    701.125,
    701.625,
    702.125,
    702.625,
    703.125,
    703.625,
    704.125,
    704.625,
    705.125,
    705.625,
    706.125,
    706.625,
    707.125,
    707.625,
    708.125,
    708.625,
    709.125,
    709.625,
    710.125,
    710.625,
)
HELDOUT_RENAMED_RESULT = "MannwhitneyuResult(statistic=np.float64(288.0), pvalue=np.float64(1.0))"

HELDOUT_TRIPLES_BY_ROLE = {
    "error_bearing": HELDOUT_ERROR_TRIPLES,
    "corrected_twin": HELDOUT_TWIN_TRIPLES,
    "valid_alternative": HELDOUT_VALID_TRIPLES,
    "hard_negative": HELDOUT_HARD_TRIPLES,
    "ambiguous": HELDOUT_AMBIGUOUS_TRIPLES,
    "unsupported": HELDOUT_UNSUPPORTED_TRIPLES,
    "renamed_implementation": HELDOUT_RENAMED_TRIPLES,
}
HELDOUT_LEFT_BY_ROLE = {
    "error_bearing": HELDOUT_ERROR_LEFT,
    "corrected_twin": HELDOUT_TWIN_LEFT,
    "valid_alternative": HELDOUT_VALID_LEFT,
    "hard_negative": HELDOUT_HARD_LEFT,
    "ambiguous": HELDOUT_AMBIGUOUS_LEFT,
    "unsupported": HELDOUT_UNSUPPORTED_LEFT,
    "renamed_implementation": HELDOUT_RENAMED_LEFT,
}
HELDOUT_RIGHT_BY_ROLE = {
    "error_bearing": HELDOUT_ERROR_RIGHT,
    "corrected_twin": HELDOUT_TWIN_RIGHT,
    "valid_alternative": HELDOUT_VALID_RIGHT,
    "hard_negative": HELDOUT_HARD_RIGHT,
    "ambiguous": HELDOUT_AMBIGUOUS_RIGHT,
    "unsupported": HELDOUT_UNSUPPORTED_RIGHT,
    "renamed_implementation": HELDOUT_RENAMED_RIGHT,
}
HELDOUT_PROCEDURE_BY_ROLE = {
    "error_bearing": "ttest_ind",
    "corrected_twin": "ttest_ind",
    "valid_alternative": "mannwhitneyu",
    "hard_negative": "ttest_ind",
    "ambiguous": "ttest_ind",
    "unsupported": "ttest_rel",
    "renamed_implementation": "mannwhitneyu",
}
HELDOUT_RESULT_BY_ROLE = {
    "error_bearing": HELDOUT_ERROR_RESULT,
    "corrected_twin": HELDOUT_TWIN_RESULT,
    "valid_alternative": HELDOUT_VALID_RESULT,
    "hard_negative": HELDOUT_HARD_RESULT,
    "ambiguous": HELDOUT_AMBIGUOUS_RESULT,
    "unsupported": HELDOUT_UNSUPPORTED_RESULT,
    "renamed_implementation": HELDOUT_RENAMED_RESULT,
}


class DependenceQualificationScaffoldError(ValueError):
    """The live tuple or requested sealed-lane shape cannot be frozen."""


def _visible_brief(
    case_id: str,
    task: str,
    constraints: list[str],
) -> dict[str, Any]:
    return {
        "brief_version": "1.0.0",
        "case_id": case_id,
        "scientific_task": task,
        "available_inputs": [
            "The controller supplies the governing task and pinned requirements material."
        ],
        "required_artifacts": [
            "One ASCII inputs/data.csv table with exact header k1,k2,tag,a,b.",
            "One UTF-8 workflow/analysis.py file using the supplied byte-exact template.",
            "One ASCII results/report.md file containing exactly the selected result line.",
        ],
        "construction_constraints": constraints,
    }


def _renamed_constraints(block_role: str) -> list[str]:
    if block_role == "threshold_pilot":
        triples_source = PILOT_RENAMED_TRIPLES
        left_source = PILOT_RENAMED_LEFT
        right_source = PILOT_RENAMED_RIGHT
        result = PILOT_RENAMED_RESULT
        key_prefix, companion_prefix, tag_prefix = "x", "y", "s"
    elif block_role == "qualification_heldout":
        triples_source = HELDOUT_RENAMED_TRIPLES
        left_source = HELDOUT_RENAMED_LEFT
        right_source = HELDOUT_RENAMED_RIGHT
        result = HELDOUT_RENAMED_RESULT
        key_prefix, companion_prefix, tag_prefix = "r", "z", "q"
    else:
        raise DependenceQualificationScaffoldError(
            f"Unsupported renamed-construction block role: {block_role!r}."
        )
    triples = "; ".join(f"`{','.join(item)}`" for item in triples_source)
    left = ", ".join(str(value) for value in left_source)
    right = ", ".join(str(value) for value in right_source)
    return [
        f"Use exactly these 24 k1,k2,tag triples in row order: {triples}.",
        f"Use a values in row order `{left}` and corresponding b values `{right}`.",
        (
            f"Each {key_prefix}01 through {key_prefix}08 code occurs on exactly three rows "
            f"with three different a values; every {companion_prefix}01 through "
            f"{companion_prefix}24 code and every {tag_prefix}01 through {tag_prefix}24 tag "
            "occurs once."
        ),
        "No row has matching numeric suffixes for `k1` and `k2`.",
        "Call `scipy.stats.mannwhitneyu`.",
        (
            "The exact SciPy 1.14.0 result text is `"
            + result
            + "`; the report must be `[selected-result] ` followed by exactly that text."
        ),
        (
            f"Use only the prescribed {key_prefix}/{companion_prefix}/{tag_prefix} namespaces "
            "and numeric values, which differ from every other supplied construction; do not "
            "substitute identifiers or values from another case."
        ),
    ]


def _heldout_constraints(role: str) -> list[str]:
    triples_source = HELDOUT_TRIPLES_BY_ROLE[role]
    left_source = HELDOUT_LEFT_BY_ROLE[role]
    right_source = HELDOUT_RIGHT_BY_ROLE[role]
    procedure = HELDOUT_PROCEDURE_BY_ROLE[role]
    result = HELDOUT_RESULT_BY_ROLE[role]
    key_prefix = triples_source[0][0].rstrip("0123456789")
    companion_prefix = triples_source[0][1].rstrip("0123456789")
    tag_prefix = triples_source[0][2].rstrip("0123456789")
    triples = "; ".join(f"`{','.join(item)}`" for item in triples_source)
    left = ", ".join(str(value) for value in left_source)
    right = ", ".join(str(value) for value in right_source)
    if role in {"error_bearing", "ambiguous"}:
        multiplicity = (
            f"Each prescribed {key_prefix} code occurs on exactly two rows with different a "
            f"values; every {companion_prefix} code and every {tag_prefix} tag occurs once."
        )
    else:
        multiplicity = (
            f"Every prescribed {key_prefix} code, {companion_prefix} code, and "
            f"{tag_prefix} tag occurs exactly once."
        )
    return [
        f"Use exactly these {len(triples_source)} k1,k2,tag triples in row order: {triples}.",
        f"Use a values in row order `{left}` and corresponding b values `{right}`.",
        multiplicity,
        "No row has matching numeric suffixes for `k1` and `k2`.",
        f"Call `scipy.stats.{procedure}`.",
        (
            "The exact SciPy 1.14.0 result text is `"
            + result
            + "`; the report must be `[selected-result] ` followed by exactly that text."
        ),
        (
            f"Use only the prescribed {key_prefix}/{companion_prefix}/{tag_prefix} namespaces "
            "and numeric values, which differ from every other supplied construction; do not "
            "substitute identifiers or values from another case."
        ),
    ]


def _case_specs() -> list[dict[str, Any]]:
    base = default_dependence_config()
    specs: list[dict[str, Any]] = []
    for block_role, block_id in (
        ("threshold_pilot", PILOT_BLOCK_ID),
        ("qualification_heldout", HELDOUT_BLOCK_ID),
    ):
        for role in ROLES:
            case_id = stable_id("case", LANE_ID, block_role, role)
            task_role = "error_bearing" if role == "renamed_implementation" else role
            if role == "renamed_implementation":
                constraints = _renamed_constraints(block_role)
            elif block_role == "qualification_heldout":
                constraints = _heldout_constraints(role)
            else:
                constraints = list(base.role_constraints[role])
            specs.append(
                {
                    "case_id": case_id,
                    "brief_id": stable_id("brief", LANE_ID, block_role, role),
                    "block_id": block_id,
                    "block_role": block_role,
                    "cell_type": role,
                    "reference_role": (
                        "error_bearing"
                        if role in {"corrected_twin", "renamed_implementation"}
                        else None
                    ),
                    "author_id": AUTHOR_BY_BLOCK_AND_ROLE[block_role][role],
                    "design_status": (
                        "hostile_brief_review_cleared_for_freeze"
                        if role == "renamed_implementation"
                        else (
                            "pilot_d_structure_fresh_literals"
                            if block_role == "qualification_heldout"
                            else "pilot_d_construction_reused"
                        )
                    ),
                    "visible": _visible_brief(case_id, base.task_by_role[task_role], constraints),
                }
            )
    return specs


def _participant(identifier: str, role: str, provider: str) -> dict[str, str]:
    model = "claude-opus-5" if provider == "Anthropic" else "gpt-5.6-sol"
    if provider == "Local deterministic software":
        model = "software:dependence-evidence-validator-v1"
    return {
        "participant_id": identifier,
        "role": role,
        "provider": provider,
        "agent_surface": "sealed dependence qualification scaffold",
        "agent_version": "1.0.0",
        "model_name": model,
        "model_id": model,
        "reasoning_configuration": (
            "deterministic_no_model" if provider == "Local deterministic software" else "high"
        ),
        "execution_context_id": f"context:{identifier.removeprefix('actor:')}-sealed-v1",
        "system_prompt_digest": sha256_digest(f"dependence:{role}:system:v1"),
        "tool_policy_digest": semantic_digest({"role": role, "sealed": True}),
        "environment_digest": semantic_digest(
            {"python": "3.11.15", "scipy": "1.14.0", "numpy": "2.2.6"}
        ),
        "calibration_suite_digest": semantic_digest("dependence-heldout-calibration-v1"),
        "calibration_status": (
            "required_before_participation"
            if role in {"stage1_reviewer", "stage2_reviewer"}
            else "not_applicable"
        ),
    }


def _participants() -> list[dict[str, str]]:
    rows = [
        _participant(PILOT_AUTHOR_1, "author", "Anthropic"),
        _participant(PILOT_AUTHOR_2, "author", "Anthropic"),
        _participant(HELDOUT_AUTHOR_1, "author", "Anthropic"),
        _participant(HELDOUT_AUTHOR_2, "author", "Anthropic"),
        *[
            _participant(identifier, "stage1_reviewer", provider)
            for identifier, provider in zip(
                STAGE1_IDS,
                ("Anthropic", "Anthropic", "OpenAI", "OpenAI"),
                strict=True,
            )
        ],
        *[
            _participant(identifier, "stage2_reviewer", provider)
            for identifier, provider in zip(
                STAGE2_IDS,
                ("Anthropic", "OpenAI"),
                strict=True,
            )
        ],
        _participant(
            "actor:dependence-evidence-validator-01",
            "evidence_validator",
            "Local deterministic software",
        ),
        _participant(
            "actor:dependence-detector-implementer-codex-01",
            "detector_implementer",
            "OpenAI",
        ),
    ]
    return rows


def _live_precase_freeze(project_root: Path) -> dict[str, Any]:
    registry = scientific_check_release_registry()
    modules = [module for module in registry.modules if module.manifest.check_id == CHECK_ID]
    bindings = [
        binding for binding in registry.method_conflict_bindings if binding.check_id == CHECK_ID
    ]
    if len(modules) != 1 or len(bindings) != 1:
        raise DependenceQualificationScaffoldError(
            "The live registry does not expose exactly one dependence module and binding."
        )
    module = modules[0]
    binding = bindings[0]
    adapters = list(module.adapter_manifests)
    if len(adapters) != 1:
        raise DependenceQualificationScaffoldError(
            "The live dependence module does not expose exactly one adapter."
        )
    adapter = adapters[0]
    candidates = {item.candidate_id for item in module.manifest.requirement_candidates}
    if CANDIDATE_ID not in candidates:
        raise DependenceQualificationScaffoldError(
            "The live dependence check does not publish the sealed candidate."
        )
    if binding.detector_id != DETECTOR_ID:
        raise DependenceQualificationScaffoldError(
            "The live dependence binding names a different detector."
        )
    registry_path = project_root / REGISTRY_RELATIVE
    detector_path = Path("src/sc_referee/detectors/bounded_analysis_method_conflict.py")
    adapter_path = Path("src/sc_referee/scientific_checks/dependence_recognition_adapter.py")
    envelope_projection = {
        "envelope_id": ENVELOPE_ID,
        "canonical_issue_class": CANONICAL_ISSUE_CLASS,
        "check_id": CHECK_ID,
        "candidate_id": CANDIDATE_ID,
        "binding_digest": binding.binding_digest,
        "case_evidence_contract_version": "3.0.0",
    }
    record: dict[str, Any] = {
        "artifact_kind": "direct_envelope_precase_freeze",
        "freeze_version": "1.0.0",
        "freeze_id": "freeze:authorized-independent-unit-entry-v1-precase",
        "frozen_at": DETECTOR_FROZEN_AT,
        "qualification_authority": "none_precase_freeze_only",
        "metric_case_count": 0,
        "scientific_label_count": 0,
        "detector_outcome_count": 0,
        "registry": {
            "path": REGISTRY_RELATIVE.as_posix(),
            "content_digest": sha256_digest(registry_path.read_bytes()),
            "semantic_digest": registry.registry_digest,
        },
        "envelope": {
            **envelope_projection,
            "envelope_digest": semantic_digest(envelope_projection),
        },
        "scientific_check": {
            "check_id": CHECK_ID,
            "check_version": module.manifest.check_version,
            "check_manifest_digest": module.declared_manifest_digest,
        },
        "adapter": {
            "adapter_id": adapter.adapter_id,
            "adapter_version": adapter.adapter_version,
            "adapter_manifest_digest": adapter.manifest_digest,
            "implementation_path": adapter_path.as_posix(),
            "implementation_digest": adapter.implementation_digest,
            "implementation_source_digest": sha256_digest(
                (project_root / adapter_path).read_bytes()
            ),
            "recognition_grammar_digest": adapter.recognition_grammar_digest,
        },
        "binding": {
            **binding.to_dict(),
            "binding_digest": binding.binding_digest,
        },
        "detector": {
            "detector_id": binding.detector_id,
            "detector_version": binding.detector_version,
            "detector_manifest_digest": binding.detector_manifest_digest,
            "implementation_path": detector_path.as_posix(),
            "implementation_digest": BoundedAnalysisMethodConflictDetector.implementation_digest(),
            "maturity": "experimental",
            "production_finding_permitted": False,
        },
        "limitations": [
            "This scaffold has no threshold, label, detector outcome, promotion, or Finding authority.",
            "Hostile brief review cleared both renamed constructions for freeze only.",
        ],
    }
    if (
        sha256_digest((project_root / detector_path).read_bytes())
        != record["detector"]["implementation_digest"]
    ):
        raise DependenceQualificationScaffoldError(
            "The live detector implementation bytes drift from the detector class."
        )
    record["freeze_digest"] = semantic_digest(record)
    return record


def _protocol_participants(enrollment: dict[str, Any]) -> list[dict[str, Any]]:
    rows = [
        {
            "participant_id": item["participant_id"],
            "role": item["role"],
            "provider": item["provider"],
            "execution_context_id": item["execution_context_id"],
            "identity_evidence_digest": item["configuration_digest"],
        }
        for item in enrollment["participants"]
        if item["role"] != "evidence_validator"
    ]
    return sorted(rows, key=lambda item: str(item["participant_id"]))


def assemble_dependence_qualification_inputs(project_root: Path) -> dict[str, Any]:
    """Assemble replayable inputs for the two-block, fourteen-case lane."""

    if tuple(REQUIRED_CELL_TYPES) != ROLES:
        raise DependenceQualificationScaffoldError(
            "The prospective allocator's seven-cell vocabulary has drifted."
        )
    precase = _live_precase_freeze(project_root)
    enrollment = freeze_participant_enrollment(
        {
            "enrollment_id": "enrollment:authorized-independent-unit-entry-v1",
            "precase_freeze_digest": precase["freeze_digest"],
            "participants": _participants(),
        },
        frozen_at=FROZEN_AT,
    )
    cases = _case_specs()
    brief_manifest = freeze_authoring_brief_manifest(
        {
            "manifest_id": "brief-manifest:authorized-independent-unit-entry-v1",
            "lane_id": LANE_ID,
            "precase_freeze_digest": precase["freeze_digest"],
            "expected_case_count": 14,
            "additional_hidden_terms": list(ADDITIONAL_HIDDEN_TERMS),
            "briefs": [
                {
                    "brief_id": item["brief_id"],
                    "case_id": item["case_id"],
                    "author_visible_brief": item["visible"],
                }
                for item in cases
            ],
        },
        frozen_at=FROZEN_AT,
    )
    brief_by_case = {str(item["case_id"]): item for item in brief_manifest["briefs"]}
    case_by_block_and_role = {
        (str(item["block_id"]), str(item["cell_type"])): str(item["case_id"]) for item in cases
    }
    assignments = [
        {
            "case_id": item["case_id"],
            "envelope_id": ENVELOPE_ID,
            "block_id": item["block_id"],
            "cell_type": item["cell_type"],
            "source_kind": "independent_prospective",
            "reference_case_id": (
                case_by_block_and_role[(str(item["block_id"]), str(item["reference_role"]))]
                if item["reference_role"] is not None
                else None
            ),
            "author_id": item["author_id"],
            "stage1_reviewer_ids": list(STAGE1_IDS),
            "stage2_reviewer_ids": list(STAGE2_IDS),
            "authoring_brief_digest": brief_by_case[str(item["case_id"])]["brief_digest"],
            "assigned_at": ASSIGNED_AT,
        }
        for item in cases
    ]
    lane_spec = {
        "lane_id": LANE_ID,
        "heldout_access_policy": "withhold_author_access_until_approved_threshold",
        "prospective_protocol": {
            "protocol_id": "prospective-protocol:authorized-independent-unit-entry-v1",
            "expected_envelope_count": 1,
            "detector_lock": {
                "detector_id": precase["detector"]["detector_id"],
                "detector_version": precase["detector"]["detector_version"],
                "detector_manifest_digest": precase["detector"]["detector_manifest_digest"],
                "implementation_digest": precase["detector"]["implementation_digest"],
                "frozen_at": precase["frozen_at"],
            },
            "participants": _protocol_participants(enrollment),
            "envelopes": [
                {
                    "envelope_id": ENVELOPE_ID,
                    "check_id": CHECK_ID,
                    "candidate_id": CANDIDATE_ID,
                    "binding_digest": precase["binding"]["binding_digest"],
                }
            ],
            "blocks": [
                {"block_id": PILOT_BLOCK_ID, "evidence_role": "threshold_pilot"},
                {
                    "block_id": HELDOUT_BLOCK_ID,
                    "evidence_role": "qualification_heldout",
                },
            ],
            "assignments": assignments,
            "governance": {
                "all_outcomes_retained": True,
                "no_replacement": True,
                "public_benchmark_qualification_excluded": True,
                "development_case_qualification_excluded": True,
                "detector_implementers_label_blind": True,
                "review_detector_output_hidden": True,
                "independent_review_contexts_required": True,
            },
        },
    }
    return {
        "FREEZE_MANIFEST.json": precase,
        "PARTICIPANT_ENROLLMENT.json": enrollment,
        "AUTHORING_BRIEF_MANIFEST.json": brief_manifest,
        "lane_spec": lane_spec,
        "case_specs": cases,
    }


def build_dependence_qualification_lane(
    project_root: Path, output_dir: Path
) -> dict[str, dict[str, Any]]:
    """Freeze and write the four two-block lane artifacts without opening either block."""

    assembled = assemble_dependence_qualification_inputs(project_root)
    precase = assembled["FREEZE_MANIFEST.json"]
    enrollment = assembled["PARTICIPANT_ENROLLMENT.json"]
    briefs = assembled["AUTHORING_BRIEF_MANIFEST.json"]
    lane = freeze_direct_qualification_lane(
        assembled["lane_spec"],
        precase_freeze=precase,
        participant_enrollment=enrollment,
        brief_manifest=briefs,
        frozen_at=FROZEN_AT,
    )
    artifacts = {
        "FREEZE_MANIFEST.json": precase,
        "PARTICIPANT_ENROLLMENT.json": enrollment,
        "AUTHORING_BRIEF_MANIFEST.json": briefs,
        "LANE_FREEZE.json": lane,
    }
    if output_dir.exists() or output_dir.is_symlink():
        raise FileExistsError(f"Refusing to overwrite dependence lane: {output_dir}")
    output_dir.mkdir(parents=True)
    for name, value in artifacts.items():
        (output_dir / name).write_text(
            json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    project_root = args.project_root.resolve()
    output = args.output.resolve() if args.output else project_root / LANE_RELATIVE
    build_dependence_qualification_lane(project_root, output)


if __name__ == "__main__":
    main()
