"""Historical and D14-specific false-accusation fixtures for executed sweeps."""

from __future__ import annotations

import runpy
from pathlib import Path

from h import ENVELOPE_ROOTS
from ladders import p3_rungs

E12 = ENVELOPE_ROOTS["E12"]
E13 = ENVELOPE_ROOTS["E13"]


def _e12_fixtures() -> list[tuple[str, Path, str]]:
    payload = runpy.run_path("evaluation/development/multitest-code-slice-v2_2/e12-ladders/fa.py")
    return list(payload["FIXTURES"])


def _d13_a_fixtures() -> list[tuple[str, Path, str]]:
    base_case = E13 / "80091f37c722eba28e18"
    base = (base_case / "project/analysis.py").read_text(encoding="utf-8")
    variants: list[tuple[str, str]] = []
    variants.append(
        (
            "mutated",
            base.replace(
                "    frame = pd.read_csv(path)", "    path += ''\n    frame = pd.read_csv(path)"
            ),
        )
    )
    variants.append(
        (
            "conditional",
            base.replace(
                "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
                "    if True:\n        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
            ),
        )
    )
    variants.append(
        (
            "aliased",
            base.replace(
                "    frame = pd.read_csv(path)",
                "    reader_path = path\n    frame = pd.read_csv(reader_path)",
            ),
        )
    )
    variants.append(
        (
            "nonconstant",
            base.replace(
                "os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
                "os.path.join(os.path.dirname(os.path.abspath(__file__)), choose_file())",
            ),
        )
    )
    variants.append(
        (
            "reassigned",
            base.replace(
                "    frame = pd.read_csv(path)",
                "    frame = pd.read_csv(path)\n    path = DATA_FILE",
            ),
        )
    )
    variants.append(
        (
            "cross-function",
            base.replace(
                "def load_data():",
                "def reader_path():\n    return os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)\n\n\ndef load_data():",
            ).replace(
                "    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), DATA_FILE)",
                "    path = reader_path()",
            ),
        )
    )
    variants.append(
        (
            "second-reader",
            base.replace(
                "    frame = pd.read_csv(path)",
                "    pd.read_csv('other.csv')\n    frame = pd.read_csv(path)",
            ),
        )
    )
    variants.append(
        (
            "escaped",
            base.replace(
                "    frame = pd.read_csv(path)", "    print(path)\n    frame = pd.read_csv(path)"
            ),
        )
    )

    _label, complete_case, complete = _e12_fixtures()[1]
    complete = complete.replace(
        'DATA_FILE = Path(__file__).resolve().parent / "allergy_spray_trial.csv"',
        'CSV_NAME = "allergy_spray_trial.csv"',
    ).replace(
        "    df = pd.read_csv(DATA_FILE)",
        "    data_path = Path(__file__).resolve().parent / CSV_NAME\n"
        "    df = pd.read_csv(data_path)",
    )
    result = [(f"D13-A-{name}", base_case, source) for name, source in variants]
    result.append(("D13-A-complete-correction", complete_case, complete))
    return result


def _terminal_helper(source: str, *, corrected: bool) -> str:
    source = source.replace(
        "\ndef main():",
        "\ndef verdict(p):\n"
        "    return 'significant' if p < ALPHA else 'not significant'\n\n\n"
        "def main():",
    )
    if not corrected:
        source = source.replace("ALPHA = 0.05", "ALPHA = 0.01")
        source = source.replace(
            "p_used = min(1.0, float(result.pvalue) * n_comparisons)",
            "p_used = float(result.pvalue)",
        )
    return source.replace(
        'verdict = "significant" if p_used < ALPHA else "not significant"\n'
        '        print(f"{label}: corrected p = {p_used:.4f} -> {verdict}")',
        'print("%s: p = %.4f -> %s" % (label, p_used, verdict(p_used)))',
    )


def _d13_b_fixtures() -> list[tuple[str, Path, str]]:
    _label, complete_case, complete = _e12_fixtures()[1]
    rows = [
        ("D13-B-complete", complete_case, _terminal_helper(complete, corrected=True)),
        ("D13-B-preregistered-001", complete_case, _terminal_helper(complete, corrected=False)),
    ]
    case = E13 / "80091f37c722eba28e18"
    base = (case / "project/analysis.py").read_text(encoding="utf-8")
    hidden = base.replace(
        "def verdict(p_value):",
        "def adjust(p):\n    return hidden_adjust(p)\n\n\ndef verdict(p_value):",
    ).replace(
        'return "SIGNIFICANT" if p_value < ALPHA else "not significant"',
        'return "SIGNIFICANT" if adjust(p_value) < ALPHA else "not significant"',
    )
    duplicate = base.replace(
        'print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, verdict(result["p_value"])))',
        'decision = verdict(result["p_value"])\n'
        '        print("  verdict at alpha=%.2f  : %s (unadjusted p)" % (ALPHA, decision))\n'
        '        print("  repeated verdict: %s" % decision)',
    )
    computed = base.replace("p_value < ALPHA", "p_value < (1 - (1 - ALPHA) ** (1 / 7))")
    exported = base.replace(
        "    print()\n\n\ndef main():",
        '    pd.DataFrame({"p": [result["p_value"]]}).to_csv("p.csv")\n    print()\n\n\ndef main():',
    )
    rows.extend(
        [
            ("D13-B-hidden-correction", case, hidden),
            ("D13-B-two-sinks", case, duplicate),
            ("D13-B-family-position-collision", case, duplicate),
            ("D13-B-computed-threshold", case, computed),
            ("D13-B-export-sibling", case, exported),
        ]
    )
    return rows


def historical_fixtures() -> list[tuple[str, Path, str]]:
    """Six 2.2 fixtures plus all 15 normative and one extra 2.3 guard fixture."""

    return [*_e12_fixtures(), *_d13_a_fixtures(), *_d13_b_fixtures()]


def d14_fixtures() -> list[tuple[str, Path, str]]:
    """One admitted complete-correction control and five exact refusal neighbors."""

    case = ENVELOPE_ROOTS["E14"] / "502687d9137dab93ff99"
    base = p3_rungs()[3][2]
    old = """        "mean_uncoated": uncoated[outcome].mean(),
        "mean_hydrophilic": hydrophilic[outcome].mean(),
        "difference": hydrophilic[outcome].mean() - uncoated[outcome].mean(),
        "p_value": ttest_ind(
            uncoated[outcome], hydrophilic[outcome], equal_var=False
        ).pvalue,
    }
    for outcome in OUTCOMES
}"""
    exact = """        "mean_uncoated": u.mean(),
        "mean_hydrophilic": h.mean(),
        "difference": h.mean() - u.mean(),
        "p_value": min(1.0, ttest_ind(u, h, equal_var=False).pvalue * 4),
    }
    for outcome in OUTCOMES
    for u, h in [(uncoated[outcome], hydrophilic[outcome])]
}"""
    eligible = base.replace(old, exact)
    if eligible == base or old in eligible:
        raise ValueError("D14 fixture anchor was not found")
    call_value = eligible.replace(
        "[(uncoated[outcome], hydrophilic[outcome])]",
        "[(identity(uncoated[outcome]), hydrophilic[outcome])]",
    ).replace(
        "coupons = pd.read_csv(CSV_PATH)",
        "def identity(value):\n    return value\n\n\ncoupons = pd.read_csv(CSV_PATH)",
    )
    two_rows = eligible.replace(
        "[(uncoated[outcome], hydrophilic[outcome])]",
        "[(uncoated[outcome], hydrophilic[outcome]), (uncoated[outcome], hydrophilic[outcome])]",
    )
    filtered = eligible.replace(
        "for u, h in [(uncoated[outcome], hydrophilic[outcome])]",
        "for u, h in [(uncoated[outcome], hydrophilic[outcome])] if outcome",
    )
    mismatched = eligible.replace(
        "for u, h in [(uncoated[outcome], hydrophilic[outcome])]",
        "for [u, h] in [(uncoated[outcome], hydrophilic[outcome])]",
    )
    arithmetic = eligible.replace(
        "uncoated[outcome], hydrophilic[outcome]",
        "uncoated[outcome] + 0, hydrophilic[outcome]",
    )
    return [
        ("D14-A-complete-correction", case, eligible),
        ("D14-A-call-component-refused", case, call_value),
        ("D14-A-two-row-generator-refused", case, two_rows),
        ("D14-A-filtered-generator-refused", case, filtered),
        ("D14-A-container-kind-mismatch-refused", case, mismatched),
        ("D14-A-arithmetic-component-refused", case, arithmetic),
    ]
