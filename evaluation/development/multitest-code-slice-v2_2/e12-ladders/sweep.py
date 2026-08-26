"""Full impact sweep: baseline vs a delta set, over every opened case and the open corpus."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import h  # noqa: E402
import patched  # noqa: E402

ENVELOPES = {"E10": h.E10, "E11": h.E11, "E12": h.E12}


def envelope_rows(fn):
    rows = {}
    for tag, root in ENVELOPES.items():
        for item in h.roles(root):
            key = f"{tag}-{item['role']}"
            rows[key] = h.classify(h.analyze_envelope(root / item["case_id"], fn=fn))
    return rows


def corpus_rows(fn):
    labels = json.loads((h.CORPUS / "specs" / "labels.json").read_text())
    rows = {}
    for spec in sorted(labels):
        rows[spec] = h.classify(h.analyze_corpus(spec, fn=fn))
    return rows, labels


def main(deltas: str) -> None:
    base = patched.analyzer("")
    new = patched.analyzer(deltas)

    eb, en = envelope_rows(base), envelope_rows(new)
    cb, labels = corpus_rows(base)
    cn, _ = corpus_rows(new)

    print(f"=== deltas {deltas} : opened envelope cases (E10/E11/E12) ===")
    moved = 0
    for key in eb:
        if eb[key] != en[key]:
            moved += 1
            print(f"  MOVED {key:<9} {eb[key]} -> {en[key]}")
    print(f"  moved: {moved} of {len(eb)}")
    neg_cand_base = [k for k, v in eb.items() if "-N" in k and v[0] == "candidate"]
    neg_cand_new = [k for k, v in en.items() if "-N" in k and v[0] == "candidate"]
    print(f"  negative candidates baseline={neg_cand_base} delta={neg_cand_new}")
    pos_base = sorted(k for k, v in eb.items() if "-P" in k and v[0] == "candidate")
    pos_new = sorted(k for k, v in en.items() if "-P" in k and v[0] == "candidate")
    print(f"  positive candidates baseline={pos_base}")
    print(f"  positive candidates delta   ={pos_new}")

    print(f"=== deltas {deltas} : open corpus (25 correct / 25 misstep) ===")
    cmoved = 0
    for spec in sorted(cb):
        if cb[spec] != cn[spec]:
            cmoved += 1
            print(f"  MOVED {spec:<8} [{labels[spec]['label']:<7}] {cb[spec]} -> {cn[spec]}")
    correct_base = sorted(
        s for s in cb if labels[s]["label"] == "correct" and cb[s][0] == "candidate"
    )
    correct_new = sorted(
        s for s in cn if labels[s]["label"] == "correct" and cn[s][0] == "candidate"
    )
    mis_base = sorted(s for s in cb if labels[s]["label"] == "misstep" and cb[s][0] == "candidate")
    mis_new = sorted(s for s in cn if labels[s]["label"] == "misstep" and cn[s][0] == "candidate")
    print(f"  moved: {cmoved} of 50")
    print(f"  labeled-CORRECT candidates baseline={len(correct_base)} {correct_base}")
    print(f"  labeled-CORRECT candidates delta   ={len(correct_new)} {correct_new}")
    print(f"  labeled-misstep candidates baseline={len(mis_base)}")
    print(f"  labeled-misstep candidates delta   ={len(mis_new)}")
    print(f"  misstep gained: {sorted(set(mis_new) - set(mis_base))}")
    print(f"  misstep lost  : {sorted(set(mis_base) - set(mis_new))}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "12345")
