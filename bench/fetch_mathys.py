"""Download the files inside a Synapse *Dataset* entity.

`synapse get -r` and syncFromSynapse refuse a Dataset ("not a File/Folder/Project/Link"),
so we query the dataset's rows for their member file synIds and fetch each one. This is the
Murphy-et-al reprocessed Mathys-2019 deposit (syn51758062, AD Knowledge Portal).

Auth: reads SYNAPSE_AUTH_TOKEN from the environment (login() picks it up automatically).

    SYNAPSE_AUTH_TOKEN=... .venv/bin/python bench/fetch_mathys.py [syn_id] [dest_dir]
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def _synid(v) -> str:
    s = str(v).strip()
    return s if s.startswith("syn") else f"syn{s}"


def _status_code(exc: Exception) -> int | None:
    response = getattr(exc, "response", None)
    for value in (getattr(response, "status_code", None), getattr(exc, "status_code", None),
                  getattr(exc, "code", None)):
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _is_access_restricted(exc: Exception) -> bool:
    """Recognize only authentication/authorization denial; all other failures are fatal."""
    if _status_code(exc) in {401, 403}:
        return True
    name = type(exc).__name__.lower()
    return name in {
        "synapseauthenticationerror",
        "synapseunmetaccessrestrictions",
        "synapsepermissionerror",
    }


def _login():
    try:
        import synapseclient
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "fetch_mathys requires the data extra: install sc-referee[data]"
        ) from exc
    return synapseclient.login()                       # uses SYNAPSE_AUTH_TOKEN


def main(syn_id: str = "syn51758062", dest: str = "data/mathys_raw", *, client=None) -> dict:
    syn = client if client is not None else _login()
    df = syn.tableQuery(f"SELECT * FROM {syn_id}").asDataFrame()
    print("dataset columns:", list(df.columns))

    id_col = next((c for c in ("id", "ID", "entityId", "file_id") if c in df.columns), None)
    if id_col is None:
        raise SystemExit(f"no id column found in {list(df.columns)} — inspect and adjust")
    name_col = next((c for c in ("name", "Name", "fileName") if c in df.columns), None)

    ids = [_synid(v) for v in df[id_col].tolist()]
    print(f"\n{len(ids)} file(s) in the dataset:")
    for i, row in df.iterrows():
        print("  ", _synid(row[id_col]), "  ", row[name_col] if name_col else "")

    print("\ndownloading ->", dest, "(skipping only access-restricted files)")
    got, restricted = [], []
    destination = Path(dest)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Stage the entire successful subset beside the destination. Unexpected failures leave the
    # pre-existing destination untouched instead of presenting a partial download as success.
    with tempfile.TemporaryDirectory(prefix=".mathys-download-", dir=destination.parent) as stage_raw:
        stage = Path(stage_raw)
        staged = []
        for fid in ids:
            try:
                e = syn.get(fid, downloadLocation=str(stage), ifcollision="keep.local")
                source = Path(getattr(e, "path", stage / getattr(e, "name", fid)))
                if not source.is_file() or source.parent.resolve() != stage.resolve():
                    raise RuntimeError(f"download for {fid} did not produce a regular staged file")
                name = source.name
                if any(existing_name == name for _, existing_name, _ in staged):
                    raise RuntimeError(f"dataset contains duplicate output filename {name!r}")
                staged.append((fid, name, source))
                got.append((fid, name))
                print("  got:", name)
            except Exception as ex:
                if not _is_access_restricted(ex):
                    raise
                first = (str(ex).strip().splitlines() or ["restricted"])[0]
                restricted.append((fid, first))
                print("  SKIP (restricted):", fid, "-", first[:90])

        destination.mkdir(parents=True, exist_ok=True)
        for _, name, source in staged:
            os.replace(source, destination / name)

    print("\n=== summary ===")
    print(f"downloaded {len(got)} file(s):")
    for _, n in got:
        print("   ", n)
    if restricted:
        print(f"\n{len(restricted)} access-restricted file(s) (NOT downloaded):")
        for i, m in restricted:
            print("   ", i, "-", m[:90])
    return {"downloaded": tuple(got), "restricted": tuple(restricted)}


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "syn51758062"
    d = sys.argv[2] if len(sys.argv) > 2 else "data/mathys_raw"
    main(a, d)
