#!/usr/bin/env python3
"""Build a reproducible user-based development sample from nested KKBOX 7z files."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import random
import subprocess
import tempfile
import time
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTER = ROOT / "data/raw/kkbox-churn-prediction-challenge.zip"
PROCESSED = ROOT / "data/processed"
SAMPLE_SIZE = 10_000
SEED = 20261019

SOURCES = [
    ("v1", "transactions.csv.7z", "transactions.csv", "transactions"),
    ("v2", "transactions_v2.csv.7z", "data/churn_comp_refresh/transactions_v2.csv", "transactions"),
    ("v1", "user_logs.csv.7z", "user_logs.csv", "user_logs"),
    ("v2", "user_logs_v2.csv.7z", "data/churn_comp_refresh/user_logs_v2.csv", "user_logs"),
]


def stream_csv(zf: zipfile.ZipFile, outer_name: str, inner_name: str, tmp: Path):
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
    return proc


def reservoir_sample_members(zf: zipfile.ZipFile, tmp: Path):
    start = time.time()
    proc = stream_csv(zf, "members_v3.csv.7z", "members_v3.csv", tmp)
    reader = csv.DictReader(proc.stdout)
    reservoir = []
    total = 0
    rng = random.Random(SEED)
    for row in reader:
        msno = (row.get("msno") or "").strip()
        if not msno:
            continue
        total += 1
        if len(reservoir) < SAMPLE_SIZE:
            reservoir.append(msno)
        else:
            j = rng.randrange(total)
            if j < SAMPLE_SIZE:
                reservoir[j] = msno
    stderr = proc.stderr.read()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"members scan failed: {stderr}")
    users = sorted(set(reservoir))
    (PROCESSED / "sample_users.csv").write_text(
        "msno\n" + "\n".join(users) + "\n", encoding="utf-8"
    )
    return {
        "population_source": "members_v3.csv",
        "population_rows_with_nonempty_msno": total,
        "requested_sample_size": SAMPLE_SIZE,
        "actual_sample_size": len(users),
        "method": "reservoir sampling over the complete members_v3 user population",
        "seed": SEED,
        "elapsed_seconds": round(time.time() - start, 2),
    }, set(users)


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return None


def scan_source(zf, version, outer_name, inner_name, kind, users, tmp):
    start = time.time()
    proc = stream_csv(zf, outer_name, inner_name, tmp)
    reader = csv.DictReader(proc.stdout)
    fields = reader.fieldnames or []
    output_path = PROCESSED / f"{kind}_sample_{version}.csv.gz"
    quality = {
        "source_version": version,
        "outer_member": outer_name,
        "inner_member": inner_name,
        "kind": kind,
        "scanned_rows": 0,
        "matched_rows": 0,
        "matched_users": set(),
        "nulls_scanned": Counter(),
        "invalid_dates_scanned": Counter(),
        "negative_values_scanned": Counter(),
        "date_min_scanned": {},
        "date_max_scanned": {},
        "elapsed_seconds": 0,
    }
    date_fields = [f for f in fields if f in {"date", "transaction_date", "membership_expire_date"}]
    numeric_fields = [f for f in fields if f in {"payment_plan_days", "plan_list_price", "actual_amount_paid", "num_25", "num_50", "num_75", "num_985", "num_100", "num_unq", "total_secs"}]
    with gzip.open(output_path, "wt", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=["source_version"] + fields)
        writer.writeheader()
        for row in reader:
            quality["scanned_rows"] += 1
            for f in fields:
                value = (row.get(f) or "").strip()
                if value == "":
                    quality["nulls_scanned"][f] += 1
                if f in date_fields and value:
                    parsed = parse_date(value)
                    if parsed is None:
                        quality["invalid_dates_scanned"][f] += 1
                    else:
                        quality["date_min_scanned"][f] = min(parsed, quality["date_min_scanned"].get(f, parsed))
                        quality["date_max_scanned"][f] = max(parsed, quality["date_max_scanned"].get(f, parsed))
                if f in numeric_fields and value:
                    try:
                        if float(value) < 0:
                            quality["negative_values_scanned"][f] += 1
                    except ValueError:
                        pass
            if (row.get("msno") or "").strip() in users:
                quality["matched_rows"] += 1
                quality["matched_users"].add(row["msno"])
                row["source_version"] = version
                writer.writerow(row)
    stderr = proc.stderr.read()
    code = proc.wait()
    if code != 0:
        raise RuntimeError(f"{outer_name} scan failed: {stderr}")
    quality["matched_users"] = len(quality["matched_users"])
    quality["nulls_scanned"] = dict(quality["nulls_scanned"])
    quality["invalid_dates_scanned"] = dict(quality["invalid_dates_scanned"])
    quality["negative_values_scanned"] = dict(quality["negative_values_scanned"])
    quality["elapsed_seconds"] = round(time.time() - start, 2)
    return quality


def json_safe(obj):
    if isinstance(obj, set):
        return len(obj)
    if isinstance(obj, Counter):
        return dict(obj)
    raise TypeError(type(obj).__name__)


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with tempfile.TemporaryDirectory(prefix="kkbox-phase2-") as td:
        tmp = Path(td) / "member.7z"
        with zipfile.ZipFile(OUTER) as zf:
            sampling, users = reservoir_sample_members(zf, tmp)
            results = []
            for source in SOURCES:
                version, outer_name, inner_name, kind = source
                print(f"START {outer_name}", flush=True)
                result = scan_source(zf, version, outer_name, inner_name, kind, users, tmp)
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
                tmp.unlink(missing_ok=True)
    report = {
        "sampling": sampling,
        "sources": results,
        "total_elapsed_seconds": round(time.time() - started, 2),
        "notes": [
            "Rows are selected by sampled user, never by transaction row.",
            "v1 and v2 outputs remain separate and carry source_version.",
            "Exact unique-user and v1/v2 overlap statistics are intentionally deferred outside this sample.",
            "train/train_v2 contain no date field; their label months require external competition-window confirmation.",
        ],
    }
    (PROCESSED / "phase2_quality_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (PROCESSED / "sampling_config.json").write_text(json.dumps(sampling, ensure_ascii=False, indent=2) + "\n")
    print(f"WROTE {PROCESSED / 'phase2_quality_report.json'}")


if __name__ == "__main__":
    main()
