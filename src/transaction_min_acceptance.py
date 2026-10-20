#!/usr/bin/env python3
"""Minimum acceptance checks and Excel inputs for the transaction branch."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
EXCEL_INPUT = ROOT / "excel/input"

EXPECTED = [
    "msno", "payment_method_id", "payment_plan_days", "plan_list_price",
    "actual_amount_paid", "is_auto_renew", "transaction_date",
    "membership_expire_date", "is_cancel",
]


def read_sample(version: str) -> pd.DataFrame:
    path = PROCESSED / f"transactions_sample_{version}.csv.gz"
    df = pd.read_csv(path, dtype={"msno": "string", "payment_method_id": "string", "is_auto_renew": "Int64", "is_cancel": "Int64"})
    missing = [c for c in EXPECTED if c not in df.columns]
    if missing:
        raise ValueError(f"{path} missing fields: {missing}")
    df["source_version"] = version
    df["transaction_date_parsed"] = pd.to_datetime(df["transaction_date"].astype("string"), format="%Y%m%d", errors="coerce")
    df["membership_expire_date_parsed"] = pd.to_datetime(df["membership_expire_date"].astype("string"), format="%Y%m%d", errors="coerce")
    df["transaction_month"] = df["transaction_date_parsed"].dt.to_period("M").astype("string")
    return df


def main():
    users = pd.read_csv(PROCESSED / "sample_users.csv", dtype={"msno": "string"})
    user_set = set(users["msno"].dropna())
    v1 = read_sample("v1")
    v2 = read_sample("v2")
    frames = {"v1": v1, "v2": v2}

    per_version = {}
    for version, df in frames.items():
        tx_users = set(df["msno"].dropna())
        exact_dupes = int(df.duplicated(subset=EXPECTED, keep=False).sum())
        same_day_users = int(df.groupby(["msno", "transaction_date"]).size().gt(1).sum())
        same_day_rows = int(df.groupby(["msno", "transaction_date"]).size().loc[lambda s: s > 1].sum())
        expire_before_tx = int((df["membership_expire_date_parsed"] < df["transaction_date_parsed"]).sum())
        expire_1970 = int((df["membership_expire_date"].astype("string") == "19700101").sum())
        expire_after_2030 = int((df["membership_expire_date_parsed"] > pd.Timestamp("2030-01-01")).sum())
        per_version[version] = {
            "transaction_rows": int(len(df)),
            "transaction_users": len(tx_users),
            "sample_member_count": len(user_set),
            "transaction_user_coverage_of_sample": round(len(tx_users) / len(user_set), 6),
            "all_transaction_users_in_sample": bool(tx_users <= user_set),
            "exact_duplicate_rows": exact_dupes,
            "same_day_user_groups_with_multiple_rows": same_day_users,
            "same_day_transaction_rows_in_those_groups": same_day_rows,
            "expire_before_transaction_rows": expire_before_tx,
            "expire_1970_rows": expire_1970,
            "expire_after_2030_rows": expire_after_2030,
            "transaction_months": sorted(df["transaction_month"].dropna().unique().tolist()),
        }

    users_v1 = set(v1["msno"].dropna())
    users_v2 = set(v2["msno"].dropna())
    union = users_v1 | users_v2
    overlap = users_v1 & users_v2
    summary = {
        "sample_member_count": len(user_set),
        "v1": per_version["v1"],
        "v2": per_version["v2"],
        "union_transaction_users": len(union),
        "union_transaction_user_coverage_of_sample": round(len(union) / len(user_set), 6),
        "v1_v2_transaction_user_overlap": len(overlap),
        "v1_only_transaction_users": len(users_v1 - users_v2),
        "v2_only_transaction_users": len(users_v2 - users_v1),
        "version_rule": "Keep v1 and v2 separate for Excel and reporting; retain source_version. Do not deduplicate across versions or treat v2 as a complete replacement until history/coverage rules are frozen.",
        "amount_label": "transaction_record_amount",
        "amount_note": "actual_amount_paid from transaction records; not net revenue and not MRR. Cancellation rows remain present and are not silently removed.",
    }

    EXCEL_INPUT.mkdir(parents=True, exist_ok=True)
    users.to_csv(EXCEL_INPUT / "sample_users.csv", index=False)
    combined = pd.concat([v1, v2], ignore_index=True)
    export_cols = ["source_version"] + EXPECTED + ["transaction_month"]
    combined[export_cols].to_csv(EXCEL_INPUT / "transactions_sample.csv", index=False)
    monthly = (combined.groupby(["source_version", "transaction_month"], dropna=False)
               .agg(transaction_record_amount=("actual_amount_paid", "sum"), transaction_count=("msno", "size"), paying_users=("msno", "nunique"))
               .reset_index()
               .sort_values(["source_version", "transaction_month"]))
    monthly["amount_definition"] = "transaction_record_amount"
    monthly["version_scope"] = "separate_v1_v2"
    monthly.to_csv(EXCEL_INPUT / "monthly_reconciliation.csv", index=False)
    monthly.to_csv(PROCESSED / "monthly_reconciliation.csv", index=False)

    # Keep version-specific detail available for checks without pretending the files are one history.
    v1[export_cols].to_csv(EXCEL_INPUT / "transactions_sample_v1.csv", index=False)
    v2[export_cols].to_csv(EXCEL_INPUT / "transactions_sample_v2.csv", index=False)
    (PROCESSED / "transaction_min_acceptance.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
