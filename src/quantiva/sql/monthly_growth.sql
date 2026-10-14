-- Include zero-sale months; protect comparisons involving truncated calendar months.
WITH RECURSIVE bounds AS (
 SELECT DATE(MIN(invoice_date)) AS first_date,DATE(MAX(invoice_date)) AS last_date FROM transactions
), calendar(month) AS (
 SELECT DATE(first_date,'start of month') FROM bounds WHERE first_date IS NOT NULL
 UNION ALL SELECT DATE(month,'+1 month') FROM calendar,bounds
 WHERE DATE(month,'+1 month')<=DATE(last_date,'start of month')
), totals AS (
 SELECT STRFTIME('%Y-%m',invoice_date) AS month,SUM(revenue_units)/10000.0 AS revenue_gbp
 FROM completed_sales GROUP BY STRFTIME('%Y-%m',invoice_date)
), coverage AS (
 SELECT STRFTIME('%Y-%m',c.month) AS month,COALESCE(t.revenue_gbp,0) AS revenue_gbp,
 b.first_date<=c.month AND b.last_date>=DATE(c.month,'+1 month','-1 day') AS complete_month
 FROM calendar c CROSS JOIN bounds b LEFT JOIN totals t ON t.month=STRFTIME('%Y-%m',c.month)
), previous AS (
 SELECT *,LAG(revenue_gbp) OVER (ORDER BY month) AS previous_revenue,
 LAG(complete_month) OVER (ORDER BY month) AS previous_complete FROM coverage
)
SELECT month,revenue_gbp,complete_month,
 CASE WHEN complete_month AND previous_complete AND previous_revenue>0
 THEN 100.0*(revenue_gbp/previous_revenue-1) END AS growth_pct
FROM previous ORDER BY month;
