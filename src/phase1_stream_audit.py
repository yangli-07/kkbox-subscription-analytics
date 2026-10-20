#!/usr/bin/env python3
"""Stream audit for the nested KKBOX 7z files.

The outer ZIP member is written temporarily as a compressed 7z file.  The CSV
itself is streamed through bsdtar and csv.reader; no extracted CSV is written
to the project and no full table is held in memory.
"""
from __future__ import annotations

import csv
import json
import subprocess
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTER = ROOT / "data/raw/kkbox-churn-prediction-challenge.zip"

TARGETS = {
    "members_v3.csv.7z": "members_v3.csv",
    "transactions.csv.7z": "transactions.csv",
    "transactions_v2.csv.7z": "data/churn_comp_refresh/transactions_v2.csv",
    "user_logs.csv.7z": "user_logs.csv",
    "user_logs_v2.csv.7z": "data/churn_comp_refresh/user_logs_v2.csv",
    "train.csv.7z": "train.csv",
    "train_v2.csv.7z": "data/churn_comp_refresh/train_v2.csv",
}

DATE_FIELDS = {
    "registration_init_time",
    "transaction_date",
    "membership_expire_date",
    "date",
}
NUMERIC_FIELDS = {
    "bd",
    "payment_plan_days",
    "plan_list_price",
    "actual_amount_paid",
    "num_25",
    "num_50",
    "num_75",
    "num_985",
    "num_100",
    "num_unq",
    "total_secs",
}


def parse_date(value: str):
    if not value:
        return None, False
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat(), True
    except ValueError:
        return None, False


def audit_one(zf: zipfile.ZipFile, outer_name: str, inner_name: str, tmp: Path):
    compressed_size = zf.getinfo(outer_name).file_size
    with zf.open(outer_name) as src, tmp.open("wb") as dst:
        while True:
            block = src.read(1024 * 1024)
            if not block:
                break
            dst.write(block)

    proc = subprocess.Popen(
        ["bsdtar", "-xOf", str(tmp), inner_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1024 * 1024,
    )
    reader = csv.DictReader(proc.stdout)
    fields = reader.fieldnames or []
    nulls = {f: 0 for f in fields}
    date_stats = {f: {"min": None, "max": None, "invalid": 0} for f in fields if f in DATE_FIELDS}
    numeric_stats = {f: {"min": None, "max": None, "negative": 0, "invalid": 0} for f in fields if f in NUMERIC_FIELDS}
    rows = 0
    duplicate_key_adjacent = 0
    previous_msno = None

    for row in reader:
        rows += 1
        for f in fields:
            value = (row.get(f) or "").strip()
            if not value:
                nulls[f] += 1
            if f in date_stats and value:
                parsed, ok = parse_date(value)
                if not ok:
                    date_stats[f]["invalid"] += 1
                else:
                    if date_stats[f]["min"] is None or parsed < date_stats[f]["min"]:
                        date_stats[f]["min"] = parsed
                    if date_stats[f]["max"] is None or parsed > date_stats[f]["max"]:
                        date_stats[f]["max"] = parsed
            if f in numeric_stats and value:
                try:
                    num = float(value)
                    if numeric_stats[f]["min"] is None or num < numeric_stats[f]["min"]:
                        numeric_stats[f]["min"] = num
                    if numeric_stats[f]["max"] is None or num > numeric_stats[f]["max"]:
                        numeric_stats[f]["max"] = num
                    if num < 0:
                        numeric_stats[f]["negative"] += 1
                except ValueError:
                    numeric_stats[f]["invalid"] += 1
        msno = (row.get("msno") or "").strip()
        if msno and msno == previous_msno:
            duplicate_key_adjacent += 1
        previous_msno = msno

    stderr = proc.stderr.read()
    return {
        "outer_member": outer_name,
        "inner_member": inner_name,
        "compressed_bytes": compressed_size,
        "rows": rows,
        "fields": fields,
        "nulls": nulls,
        "dates": date_stats,
        "numeric": numeric_stats,
        "adjacent_duplicate_msno": duplicate_key_adjacent,
        "bsdtar_stderr": stderr.strip(),
    }


def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="kkbox-phase1-") as td:
        tmp = Path(td) / "member.7z"
        with zipfile.ZipFile(OUTER) as zf:
            for outer_name, inner_name in TARGETS.items():
                print(f"AUDITING {outer_name}", flush=True)
                result = audit_one(zf, outer_name, inner_name, tmp)
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                tmp.unlink(missing_ok=True)
    out = ROOT / "docs/phase1_stream_audit.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print(f"WROTE {out}")


if __name__ == "__main__":
    main()
