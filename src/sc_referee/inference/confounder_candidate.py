"""Confounder-candidate diagnostic — the three legs assembled into one evidence record.

This is the top-level entry point for spec v2. It composes the pieces built in this session:

* leg 1   -> `materialization.dual_materialize` (calibrated, pre/post gate)
* leg 2a  -> `legs.leg2a` (residual test, when a ModelSpec is available)
* leg 2b  -> `replay.refit_with_term` (per human-declared term, when declared)

It renders NO verdict. It produces a record a scientist reads: candidates, their calibrated
associations across both populations, optional residual and refit evidence, and the standing
statement that the confounder-vs-mediator call is theirs. Nothing here is a routed `Finding`.
"""
from __future__ import annotations

from dataclasses import dataclass

from sc_referee.inference import bind as _bind
from sc_referee.inference import model_recovery as _mr
from sc_referee.inference import replay as _replay
from sc_referee.inference.legs import leg2a
from sc_referee.inference.materialization import dual_materialize, materialize

STANDING_STATEMENT = (
    "This diagnostic surfaces quantities associated with the exposure and prices how their treatment "
    "would move the reported effect. It does not decide whether any of them is a technical confounder "
    "to adjust for or a mediator of the exposure to leave alone -- that question is undecidable from "
    "the data and is the scientist's to answer."
)


@dataclass(frozen=True)
class DiagnosticRecord:
    unit: str
    exposure: str
    leg1: dict                  # from dual_materialize (or single materialize)
    leg2a: dict | None
    leg2b: tuple                # one entry per human-declared term
    standing_statement: str
    model_recovery: dict = None  # how the ModelSpec was obtained: recovered from code, or supplied

    def to_json(self) -> str:
        import json
        return json.dumps({
            "unit": self.unit, "exposure": self.exposure,
            "leg1": self.leg1, "leg2a": self.leg2a, "leg2b": list(self.leg2b),
            "model_recovery": self.model_recovery,
            "standing_statement": self.standing_statement,
        }, indent=2, sort_keys=True, default=str)

    def to_md(self) -> str:
        """Human-readable evidence. Renders no verdict; this is deliberately NOT a routed finding.

        Symmetric language only: associations and effect shifts, never "confounder" or "error".
        """
        import json as _json
        out = ["## Confounder-candidate diagnostic (evidence, not a verdict)", "",
               f"Exposure `{self.exposure}`, summarised at `{self.unit}` level.", ""]

        # leg 1
        rec = _json.loads(self.leg1["record"])
        summaries = rec["post_gate"]["summaries"] if self.leg1["kind"] == "dual" else rec["summaries"]
        unread = rec["post_gate"]["unread_columns"] if self.leg1["kind"] == "dual" else rec["unread_columns"]
        out.append("**Leg 1 — quantities associated with the exposure** "
                   "(family-wise calibrated; a low scan-wide p survives the whole candidate set):")
        out.append("")
        out.append("| candidate | r with exposure | scan-wide p |")
        out.append("|---|---|---|")
        for item in list(summaries) + list(unread):
            cal = item["association"].get("calibration")
            if not cal:
                continue
            out.append(f"| `{item['name']}` | {cal['statistic']:+.3f} | {cal['scanwide_p']} |")
        out.append("")

        if self.leg2a and "candidates" in self.leg2a:
            out.append("**Leg 2a — does the candidate predict the fitted model's residuals?** "
                       "(finds *omitted* terms; blind to terms the model already absorbs)")
            out.append("")
            out.append("| candidate | r with residuals | per-test p | scan-wide p |")
            out.append("|---|---|---|---|")
            for c in self.leg2a["candidates"]:
                out.append(f"| `{c['name']}` | {c['statistic']:+.3f} | {c['permutation_p']} | {c['scanwide_p']} |")
            out.append("")
            out.append(f"> {self.leg2a['caveat']}")
            out.append("")

        if self.leg2b:
            out.append("**Leg 2b — effect shift when a scientist-declared term is added** "
                       "(the tool computes; the scientist chose the term and basis):")
            out.append("")
            for b in self.leg2b:
                if b.get("abstained"):
                    out.append(f"- term `{b.get('term', {}).get('name', '?')}`: abstained — {b['abstained']}")
                else:
                    t = b["term"]
                    out.append(f"- `{t['name']}` ({t['basis']}): "
                               f"effect {b['target_effect_without_term']} → "
                               f"**{b['target_effect_with_term']}** (shift {b['shift']})")
            out.append("")

        out.append(f"> {self.standing_statement}")
        return "\n".join(out)


def diagnose(source: str, tables: dict, unit: str, exposure: str, *,
             fitted_mask=None, model_spec: "_replay.ModelSpec | None" = None,
             fit_data: dict | None = None, reported_effect: float | None = None,
             obs_unit=None, residual_candidates: dict | None = None,
             declared_terms: tuple = (), data_paths: tuple = (),
             outcome: str | None = None, all_counts=None) -> DiagnosticRecord:
    """Run whichever legs the available inputs permit. Each leg is optional and abstains cleanly.

    - leg 1 always runs (dual if `fitted_mask` given, else single).
    - leg 2a runs only if a `model_spec` + `fit_data` + `obs_unit` + `residual_candidates` are given
      and the replay is faithful; otherwise it is None with a reason.
    - leg 2b runs one entry per `declared_terms` (each a `replay.AddedTerm`), when a model is
      available.

    If `model_spec` is None, the spec is RECOVERED from `source` (model_recovery.recover). The record
    reports whether the model was recovered or hand-supplied, and the recovery's own reasons -- so a
    reader can see the tool reconstructed the structure rather than being told it.
    """
    recovery = None
    bind_note = None
    if model_spec is None:
        recovery = _mr.recover(source, exposure, outcome)
        if recovery.recognised:
            model_spec = recovery.to_model_spec()
            if recovery.proxy and reported_effect is None:
                # An approximate replay (DESeq2/edgeR/pydeseq2 size factors not reproduced) may not
                # match the analyst's fit. Without a reported effect to check it against, the model
                # legs cannot be trusted, so they are not run. Leg 1 still runs.
                model_spec = None
                bind_note = {"abstained": "recognised an approximate (proxy) fit but no reported "
                             "effect was available to gate its faithfulness; model legs skipped, "
                             "leg 1 still ran"}
            # auto-bind the fit variables from the analyst's own definitions, if not supplied
            if model_spec is not None and fit_data is None:
                names = [model_spec.response]
                names += [n for n in (model_spec.exposure_offset, model_spec.additive_reference)
                          if n]
                names += list(model_spec.predictors)
                try:
                    fit_data = _bind.bind_fit_data(source, names, tables, fitted_mask=fitted_mask)
                    if model_spec.family == "limma_voom" and all_counts is not None:
                        fit_data["__all_counts__"] = all_counts   # full matrix for the voom trend
                    bind_note = {"bound": sorted(k for k in fit_data if not k.startswith("__")),
                                 "source": "auto (analyst definitions)"}
                except _bind.Abstain as exc:
                    bind_note = {"abstained": f"could not auto-bind fit variables: {exc}"}

    if fitted_mask is not None:
        leg1 = dual_materialize(source, tables, unit, exposure, fitted_mask,
                                data_paths=data_paths)
        leg1_out = {"kind": "dual", **{"record": leg1.to_json()}}
    else:
        rec = materialize(source, tables, unit, exposure, data_paths=data_paths)
        leg1_out = {"kind": "single", "record": rec.to_json()}

    leg2a_out = None
    fit = None
    if model_spec is not None and fit_data is not None:
        try:
            fit = _replay.replay(model_spec, fit_data, reported_effect=reported_effect)
        except _replay.Abstain as exc:
            leg2a_out = {"abstained": f"replay not faithful: {exc}"}
    if fit is not None and obs_unit is not None and residual_candidates:
        leg2a_out = leg2a(fit, obs_unit, residual_candidates).as_dict()

    leg2b_out = []
    if model_spec is not None and fit_data is not None:
        for term in declared_terms:
            try:
                leg2b_out.append(_replay.refit_with_term(model_spec, fit_data, term))
            except _replay.Abstain as exc:
                leg2b_out.append({"leg": "2b", "term": {"name": term.name, "basis": term.basis},
                                  "abstained": str(exc)})
    elif declared_terms:
        leg2b_out.append({"abstained": "leg 2b needs a model_spec and fit_data"})

    return DiagnosticRecord(
        unit=unit, exposure=exposure, leg1=leg1_out, leg2a=leg2a_out,
        leg2b=tuple(leg2b_out), standing_statement=STANDING_STATEMENT,
        model_recovery=({**recovery.as_dict(), "binding": bind_note} if recovery is not None else
                        {"source": "hand-supplied model_spec"} if model_spec is not None else
                        {"source": "none: no model available"}),
    )
