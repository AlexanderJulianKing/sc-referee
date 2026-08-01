#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
import yaml
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from referencing import Registry, Resource

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_DIR=ROOT/"schemas"/"v0.5.0"
CATALOG=json.loads((ROOT/"schema-catalog.json").read_text())

def registry_and_schemas():
    reg=Registry(); schemas={}; aliases={}
    for item in CATALOG["schemas"]:
        data=json.loads((SCHEMA_DIR/item["file"]).read_text())
        validator_for(data).check_schema(data)
        reg=reg.with_resource(data["$id"],Resource.from_contents(data))
        schemas[data["$id"]]=data; aliases[item["name"]]=data["$id"]
    return reg,schemas,aliases

def load(path):
    if path.suffix.lower() in {".yaml",".yml"}: return yaml.safe_load(path.read_text())
    return json.loads(path.read_text())

def infer_alias(obj):
    return obj.get("record_type","").replace("-","_")

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("paths",nargs="+"); ap.add_argument("--schema"); args=ap.parse_args()
    reg,schemas,aliases=registry_and_schemas(); failures=0; count=0
    files=[]
    for raw in args.paths:
        p=Path(raw)
        if p.is_dir(): files += sorted([x for x in p.rglob("*") if x.suffix.lower() in {".json",".yaml",".yml"}])
        else: files.append(p)
    for p in files:
        obj=load(p); alias=args.schema or infer_alias(obj)
        if alias not in aliases:
            print(f"FAIL {p}: unknown schema alias {alias}"); failures+=1; continue
        sch=schemas[aliases[alias]]; v=validator_for(sch)(sch,registry=reg,format_checker=FormatChecker())
        errs=sorted(v.iter_errors(obj),key=lambda e:list(e.path)); count+=1
        if errs:
            print(f"FAIL {p}")
            for e in errs[:20]: print("  "+"/".join(map(str,e.path))+": "+e.message)
            failures+=1
        else: print(f"OK   {p}")
    print(f"\nValidated {count} record(s).")
    raise SystemExit(1 if failures else 0)
if __name__=="__main__": main()
