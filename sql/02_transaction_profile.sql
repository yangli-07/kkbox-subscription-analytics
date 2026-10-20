-- Read-only transaction profile queries.
-- v1 and v2 are intentionally queried separately; do not union them here.

-- 1. Version-level profile: counts, shares, and transaction-record amount.
SELECT
    'v1' AS source_version,
    COUNT(*) AS transaction_record_count,
    COUNT(DISTINCT msno) AS distinct_user_count,
    COUNT(*) FILTER (WHERE is_auto_renew IS TRUE) AS auto_renew_record_count,
    ROUND(
        COUNT(*) FILTER (WHERE is_auto_renew IS TRUE)::numeric / NULLIF(COUNT(*), 0),
        6
    ) AS auto_renew_record_share,
    COUNT(*) FILTER (WHERE is_cancel IS TRUE) AS cancel_flag_record_count,
    ROUND(
        COUNT(*) FILTER (WHERE is_cancel IS TRUE)::numeric / NULLIF(COUNT(*), 0),
        6
    ) AS cancel_flag_record_share,
    SUM(actual_amount_paid) AS transaction_record_amount_total
FROM transactions_v1;

SELECT
    'v2' AS source_version,
    COUNT(*) AS transaction_record_count,
    COUNT(DISTINCT msno) AS distinct_user_count,
    COUNT(*) FILTER (WHERE is_auto_renew IS TRUE) AS auto_renew_record_count,
    ROUND(
        COUNT(*) FILTER (WHERE is_auto_renew IS TRUE)::numeric / NULLIF(COUNT(*), 0),
        6
    ) AS auto_renew_record_share,
    COUNT(*) FILTER (WHERE is_cancel IS TRUE) AS cancel_flag_record_count,
    ROUND(
        COUNT(*) FILTER (WHERE is_cancel IS TRUE)::numeric / NULLIF(COUNT(*), 0),
        6
    ) AS cancel_flag_record_share,
    SUM(actual_amount_paid) AS transaction_record_amount_total
FROM transactions_v2;

-- 2. Payment method and plan duration profile for v1.
SELECT
    'v1' AS source_version,
    payment_method_id,
    payment_plan_days,
    COUNT(*) AS transaction_record_count,
    SUM(actual_amount_paid) AS transaction_record_amount_total
FROM transactions_v1
GROUP BY payment_method_id, payment_plan_days
ORDER BY payment_method_id, payment_plan_days;

-- 3. Payment method and plan duration profile for v2.
SELECT
    'v2' AS source_version,
    payment_method_id,
    payment_plan_days,
    COUNT(*) AS transaction_record_count,
    SUM(actual_amount_paid) AS transaction_record_amount_total
FROM transactions_v2
GROUP BY payment_method_id, payment_plan_days
ORDER BY payment_method_id, payment_plan_days;
