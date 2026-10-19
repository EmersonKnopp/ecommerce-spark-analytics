-- Retenção por coorte: % de clientes da coorte que voltaram a comprar N meses depois
WITH first_purchase AS (
    SELECT customer_id, DATE_TRUNC('month', MIN(order_date)) AS cohort_month
    FROM fact_sales
    GROUP BY customer_id
),
activity AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', order_date) AS activity_month
    FROM fact_sales
),
joined AS (
    SELECT
        f.cohort_month,
        f.customer_id,
        CAST(MONTHS_BETWEEN(a.activity_month, f.cohort_month) AS INT) AS month_index
    FROM first_purchase f
    JOIN activity a ON a.customer_id = f.customer_id
),
sizes AS (
    SELECT cohort_month, COUNT(*) AS cohort_size
    FROM first_purchase
    GROUP BY cohort_month
)
SELECT
    DATE_FORMAT(j.cohort_month, 'yyyy-MM')                          AS cohort,
    j.month_index,
    COUNT(DISTINCT j.customer_id)                                   AS active_customers,
    s.cohort_size,
    ROUND(100 * COUNT(DISTINCT j.customer_id) / s.cohort_size, 1)   AS retention_pct
FROM joined j
JOIN sizes s ON s.cohort_month = j.cohort_month
GROUP BY j.cohort_month, j.month_index, s.cohort_size
ORDER BY j.cohort_month, j.month_index
