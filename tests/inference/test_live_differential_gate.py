from __future__ import annotations

import json

import yaml


def _signature(result):
    return [(finding.check_id, finding.status) for finding in result.findings]


def _old_and_new(folder, monkeypatch, *, engine="simple"):
    import sc_referee.audit as audit
    from sc_referee.checks.double_dipping import DoubleDippingCheck

    current = audit.build_checks
    def legacy_only(selected):
        checks = []
        for check in current(selected):
            if check.id.startswith("inference."):
                continue
            if check.id == "double_dipping" and type(check).__module__ == "sc_referee.inference.live":
                checks.append(DoubleDippingCheck())
            else:
                checks.append(check)
        return checks
    monkeypatch.setattr(
        audit, "build_checks",
        legacy_only,
    )
    old = audit.run_audit(folder, engine=engine)
    monkeypatch.setattr(audit, "build_checks", current)
    new = audit.run_audit(folder, engine=engine)
    return old, new


def _retype(folder, analysis_type, *, unit=None):
    path = folder / "sc-referee.yaml"
    config = yaml.safe_load(path.read_text())
    config["analysis_type"] = analysis_type
    if unit is not None:
        config.setdefault("reported_results", {})["unit_of_test"] = unit
    path.write_text(yaml.safe_dump(config, sort_keys=False))


def test_frozen_live_audit_migration_table_matches_actual_differences(tmp_path, monkeypatch):
    from fixtures.confounding_alias.make_fixture import build
    from tests.test_audit import _write_eqtl_audit_fixture

    frozen_path = __import__("pathlib").Path(__file__).parents[1] / "frozen_oracles" / "live_audit_oracles.json"
    frozen = json.loads(frozen_path.read_text())

    condition = tmp_path / "condition"
    build(condition)
    old, new = _old_and_new(condition, monkeypatch)
    assert _signature(old) == _signature(new)

    marker = tmp_path / "pbmc_dex"
    build(marker)
    _retype(marker, "marker_detection", unit="cell")
    (marker / "analysis.py").write_text(
        "from sklearn.mixture import GaussianMixture\n"
        "import scanpy as sc\n"
        "adata = sc.read_h5ad('confounding_alias.h5ad')\n"
        "labels = GaussianMixture(10).fit_predict(adata.X)\n"
        "adata.obs['gmm'] = labels\n"
        "sc.tl.rank_genes_groups(adata, groupby='gmm', method='wilcoxon')\n"
        "markers = sc.get.rank_genes_groups_df(adata, group=None)\n"
        "markers.to_csv('results/de.csv', index=False)\n"
    )
    old, new = _old_and_new(marker, monkeypatch)
    assert frozen["pbmc_dex_guardrail"]["previous_engine_status"] == "blocker"
    assert next(item.status for item in old.findings if item.check_id == "double_dipping") == (
        frozen["pbmc_dex_guardrail"]["old_status"]
    )
    assert next(item.status for item in new.findings if item.check_id == "double_dipping") == (
        frozen["pbmc_dex_guardrail"]["new_status"]
    )

    eqtl = tmp_path / "eqtl"
    eqtl.mkdir()
    _write_eqtl_audit_fixture(eqtl)
    old, new = _old_and_new(eqtl, monkeypatch)
    assert _signature(old) == [tuple(item) for item in frozen["eqtl_missing_joint_contract"]["old"]]
    assert _signature(new) == [tuple(item) for item in frozen["eqtl_missing_joint_contract"]["new"]]

    for analysis_type, key in (
        ("trajectory", "trajectory_missing_contract"),
        ("differential_abundance", "enrichment_missing_contract"),
        ("other", "coordinate_missing_contract"),
    ):
        folder = tmp_path / analysis_type
        build(folder)
        _retype(folder, analysis_type)
        old, new = _old_and_new(folder, monkeypatch)
        assert _signature(old) == [tuple(item) for item in frozen[key]["old"]]
        assert _signature(new) == [tuple(item) for item in frozen[key]["new"]]


def test_overlap_migration_is_deferred_and_legacy_public_outputs_remain_frozen():
    from sc_referee.registry import build_checks
    from tests.frozen_oracles.cases import confounding_cases
    from tests.inference._serialization import normalized_public_bytes, normalized_public_json
    from sc_referee.checks.confounding import evaluate_confounding

    frozen = json.loads(
        (__import__("pathlib").Path(__file__).parents[1] / "frozen_oracles" /
         "legacy_oracles.json").read_text()
    )
    for name, observations, design in confounding_cases():
        assert normalized_public_bytes(evaluate_confounding(observations, design)).decode() == (
            normalized_public_json(frozen["confounding"][name])
        )

    by_id = {check.id: check for check in build_checks("simple")}
    assert type(by_id["double_dipping"]).__module__ == "sc_referee.inference.live"
    assert type(by_id["confounding"]).__module__ == "sc_referee.checks.confounding"
    assert type(by_id["experimental_unit"]).__module__ == "sc_referee.checks.experimental_unit"
