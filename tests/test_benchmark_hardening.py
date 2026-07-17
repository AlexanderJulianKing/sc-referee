from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from bench import fetch_mathys
from bench.mathys_anchor import _guess_ref_test


ROOT = Path(__file__).resolve().parents[1]


def test_mathys_multilevel_contrast_requires_both_explicit_levels(monkeypatch):
    monkeypatch.delenv("MATHYS_REF", raising=False)
    monkeypatch.delenv("MATHYS_TEST", raising=False)
    with pytest.raises(SystemExit, match="3 levels"):
        _guess_ref_test(["AD", "MCI", "control"])

    monkeypatch.setenv("MATHYS_REF", "control")
    with pytest.raises(SystemExit, match="MATHYS_TEST"):
        _guess_ref_test(["AD", "MCI", "control"])

    monkeypatch.setenv("MATHYS_TEST", "AD")
    assert _guess_ref_test(["MCI", "AD", "control"]) == ("control", "AD")


def test_mathys_two_level_guess_is_order_invariant(monkeypatch):
    monkeypatch.delenv("MATHYS_REF", raising=False)
    monkeypatch.delenv("MATHYS_TEST", raising=False)
    assert _guess_ref_test(["AD", "control"]) == ("control", "AD")
    assert _guess_ref_test(["control", "AD"]) == ("control", "AD")


def _r_has_mathys_packages() -> bool:
    if shutil.which("Rscript") is None:
        return False
    result = subprocess.run(
        ["Rscript", "-e",
         'quit(status=ifelse(requireNamespace("SingleCellExperiment", quietly=TRUE) && '
         'requireNamespace("Matrix", quietly=TRUE), 0, 1))'],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


@pytest.mark.skipif(not _r_has_mathys_packages(), reason="R SingleCellExperiment/Matrix unavailable")
def test_mathys_converter_refuses_transformed_or_noninteger_assays(tmp_path):
    rds = tmp_path / "sce.rds"
    env = {**os.environ, "OUT": str(rds)}
    make = (
        'suppressPackageStartupMessages({library(Matrix); library(SingleCellExperiment)}); '
        'm <- Matrix(matrix(c(0.1, 1.5, 2.0, 3.0), nrow=2), sparse=TRUE); '
        'rownames(m) <- c("g1", "g2"); colnames(m) <- c("c1", "c2"); '
        'sce <- SingleCellExperiment(assays=list(logcounts=m)); saveRDS(sce, Sys.getenv("OUT"))'
    )
    subprocess.run(["Rscript", "-e", make], cwd=ROOT, env=env, check=True,
                   capture_output=True, text=True)

    absent = subprocess.run(
        ["Rscript", "bench/mathys_convert.R", str(rds), str(tmp_path / "absent")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert absent.returncode != 0
    assert "raw-count assay 'counts' is absent" in absent.stderr

    transformed = subprocess.run(
        ["Rscript", "bench/mathys_convert.R", str(rds), str(tmp_path / "transformed"),
         "logcounts"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert transformed.returncode != 0
    assert "non-integer" in transformed.stderr


class _Table:
    def __init__(self, frame):
        self.frame = frame

    def asDataFrame(self):
        return self.frame


class _Denied(Exception):
    status_code = 403


class _Client:
    def __init__(self, failures=()):
        self.failures = dict(failures)

    def tableQuery(self, _query):
        return _Table(pd.DataFrame({"id": ["syn1", "syn2"], "name": ["one.dat", "two.dat"]}))

    def get(self, fid, *, downloadLocation, ifcollision):
        if fid in self.failures:
            raise self.failures[fid]
        path = Path(downloadLocation) / ("one.dat" if fid == "syn1" else "two.dat")
        path.write_text(fid)
        return SimpleNamespace(name=path.name, path=str(path))


def test_mathys_fetch_commits_allowed_subset_and_records_access_denial(tmp_path):
    result = fetch_mathys.main(dest=str(tmp_path / "download"),
                               client=_Client({"syn2": _Denied("access restricted")}))
    assert result["downloaded"] == (("syn1", "one.dat"),)
    assert result["restricted"] == (("syn2", "access restricted"),)
    assert (tmp_path / "download" / "one.dat").read_text() == "syn1"
    assert not (tmp_path / "download" / "two.dat").exists()


def test_mathys_fetch_does_not_hide_or_commit_unexpected_failures(tmp_path):
    destination = tmp_path / "download"
    destination.mkdir()
    (destination / "existing.dat").write_text("preserve")
    with pytest.raises(OSError, match="disk failure"):
        fetch_mathys.main(dest=str(destination),
                          client=_Client({"syn2": OSError("disk failure")}))
    assert sorted(path.name for path in destination.iterdir()) == ["existing.dat"]

