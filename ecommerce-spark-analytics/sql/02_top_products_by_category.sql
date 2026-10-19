-- Top 3 produtos por receita em cada categoria (RANK + PARTITION BY)
WITH product_sales AS (
    SELECT
        category,
        product_id,
        product_name,
        ROUND(SUM(revenue), 2) AS revenue,
        SUM(quantity)          AS units_sold
    FROM fact_sales
    GROUP BY category, product_id, product_name
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY category ORDER BY revenue DESC) AS rnk
    FROM product_sales
)
SELECT category, rnk, product_name, revenue, units_sold
FROM ranked
WHERE rnk <= 3
ORDER BY category, rnk
