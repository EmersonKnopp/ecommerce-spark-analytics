-- Receita mensal, ticket médio e crescimento mês a mês (LAG)
WITH monthly AS (
    SELECT
        order_month,
        ROUND(SUM(revenue), 2)      AS revenue,
        COUNT(DISTINCT order_id)    AS orders
    FROM fact_sales
    GROUP BY order_month
)
SELECT
    order_month,
    revenue,
    orders,
    ROUND(revenue / orders, 2) AS avg_ticket,
    ROUND(
        100 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
            / LAG(revenue) OVER (ORDER BY order_month),
        2
    ) AS mom_growth_pct
FROM monthly
ORDER BY order_month
