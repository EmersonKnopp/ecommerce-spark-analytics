-- Receita acumulada e média móvel de 3 meses por categoria (window frames)
WITH monthly_category AS (
    SELECT category, order_month, SUM(revenue) AS revenue
    FROM fact_sales
    GROUP BY category, order_month
)
SELECT
    category,
    order_month,
    ROUND(revenue, 2) AS revenue,
    ROUND(SUM(revenue) OVER (
        PARTITION BY category ORDER BY order_month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 2) AS running_revenue,
    ROUND(AVG(revenue) OVER (
        PARTITION BY category ORDER BY order_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)         AS moving_avg_3m
FROM monthly_category
ORDER BY category, order_month
