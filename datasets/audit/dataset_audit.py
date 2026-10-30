from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path
import pandas as pd

def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def norm(value: object) -> str:
    return re.sub(r"\s+", " ", str(value).strip().lower())

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    args=ap.parse_args()
    root=args.repo_root.resolve()
    out=root/"datasets"/"audit"
    out.mkdir(parents=True, exist_ok=True)

    paths={
        "JailbreakBench": root/"datasets/jailbreak/processed/jailbreakbench_master.csv",
        "HarmBench": root/"datasets/benchmark/harmbench/processed/harmbench_behaviors_master.csv",
        "IndiBias": root/"datasets/bias/indibias/processed/indibias_master.csv",
        "DefAn": root/"datasets/hallucination/defan/processed/defan_aicas_master.csv",
    }
    report={}
    for name,path in paths.items():
        if not path.exists():
            raise FileNotFoundError(path)
        df=pd.read_csv(path)
        report[name]={
            "rows": int(len(df)),
            "columns": list(df.columns),
            "null_cells": int(df.isna().sum().sum()),
            "duplicate_rows": int(df.duplicated().sum()),
            "sha256": sha256(path),
        }
    agent=root/"datasets/benchmark/agentdojo/raw/agentdojo_v1_2_2_injection_tasks.json"
    if agent.exists():
        data=json.loads(agent.read_text(encoding="utf-8"))
        report["AgentDojo"]={"scenarios":len(data),"sha256":sha256(agent)}
    j=pd.read_csv(paths["JailbreakBench"])
    h=pd.read_csv(paths["HarmBench"])
    j_harm={norm(x) for x in j.loc[j["behavior_class"]=="harmful","goal"]}
    h_beh={norm(x) for x in h["behavior"]}
    report["cross_dataset"]={"JailbreakBench_harmful_vs_HarmBench_behavior_exact_normalized_overlap":len(j_harm & h_beh)}
    output=out/"DATASET_AUDIT_RUNTIME.json"
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
