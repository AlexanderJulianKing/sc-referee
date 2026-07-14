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

import synapseclient


def _synid(v) -> str:
    s = str(v).strip()
    return s if s.startswith("syn") else f"syn{s}"


def main(syn_id: str = "syn51758062", dest: str = "data/mathys_raw") -> None:
    os.makedirs(dest, exist_ok=True)
    syn = synapseclient.login()                       # uses SYNAPSE_AUTH_TOKEN
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

    print("\ndownloading ->", dest, "(skipping any access-restricted files)")
    got, restricted = [], []
    for fid in ids:
        try:
            e = syn.get(fid, downloadLocation=dest, ifcollision="keep.local")
            got.append((fid, getattr(e, "name", fid)))
            print("  got:", got[-1][1])
        except Exception as ex:                       # controlled-access / unmet-AR / 403 etc.
            first = (str(ex).strip().splitlines() or ["restricted"])[0]
            restricted.append((fid, first))
            print("  SKIP (restricted):", fid, "-", first[:90])

    print("\n=== summary ===")
    print(f"downloaded {len(got)} file(s):")
    for _, n in got:
        print("   ", n)
    if restricted:
        print(f"\n{len(restricted)} access-restricted file(s) (NOT downloaded):")
        for i, m in restricted:
            print("   ", i, "-", m[:90])


if __name__ == "__main__":
    a = sys.argv[1] if len(sys.argv) > 1 else "syn51758062"
    d = sys.argv[2] if len(sys.argv) > 2 else "data/mathys_raw"
    main(a, d)
