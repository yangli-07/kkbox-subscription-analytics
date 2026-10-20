-- KKBOX transaction-branch tables
-- This script only creates tables. It does not load or alter CSV files.

CREATE TABLE IF NOT EXISTS sample_users (
    msno TEXT
);

CREATE TABLE IF NOT EXISTS transactions_v1 (
    source_version TEXT,
    msno TEXT,
    payment_method_id INTEGER,
    payment_plan_days INTEGER,
    plan_list_price NUMERIC(18, 2),
    actual_amount_paid NUMERIC(18, 2),
    is_auto_renew BOOLEAN,
    transaction_date DATE,
    membership_expire_date DATE,
    is_cancel BOOLEAN,
    transaction_month TEXT
);

CREATE TABLE IF NOT EXISTS transactions_v2 (
    source_version TEXT,
    msno TEXT,
    payment_method_id INTEGER,
    payment_plan_days INTEGER,
    plan_list_price NUMERIC(18, 2),
    actual_amount_paid NUMERIC(18, 2),
    is_auto_renew BOOLEAN,
    transaction_date DATE,
    membership_expire_date DATE,
    is_cancel BOOLEAN,
    transaction_month TEXT
);

CREATE TABLE IF NOT EXISTS monthly_reconciliation (
    source_version TEXT,
    transaction_month TEXT,
    transaction_record_amount NUMERIC(18, 2),
    transaction_count INTEGER,
    paying_users INTEGER,
    amount_definition TEXT,
    version_scope TEXT
);
