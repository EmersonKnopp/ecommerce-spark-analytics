-- Segmentação RFM (Recência, Frequência, Valor) com NTILE
WITH ref AS (
    SELECT MAX(order_date) AS ref_date FROM fact_sales
),
base AS (
    SELECT
        f.customer_id,
        DATEDIFF(r.ref_date, MAX(f.order_date)) AS recency_days,
        COUNT(DISTINCT f.order_id)              AS frequency,
        ROUND(SUM(f.revenue), 2)                AS monetary
    FROM fact_sales f
    CROSS JOIN ref r
    GROUP BY f.customer_id, r.ref_date
),
scored AS (
    SELECT
        *,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,  -- menos dias = nota maior
        NTILE(5) OVER (ORDER BY frequency)         AS f_score,
        NTILE(5) OVER (ORDER BY monetary)          AS m_score
    FROM base
)
SELECT
    customer_id, recency_days, frequency, monetary, r_score, f_score, m_score,
    CASE
        WHEN r_score >= 4 AND f_score >= 4 THEN 'Campeões'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Leais'
        WHEN r_score >= 4                  THEN 'Novos'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'Em risco'
        ELSE 'Hibernando'
    END AS segment
FROM scored
ORDER BY monetary DESC
