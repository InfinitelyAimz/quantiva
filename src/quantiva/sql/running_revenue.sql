WITH daily AS (SELECT DATE(invoice_date) AS date,SUM(revenue_units)/10000.0 AS revenue_gbp
 FROM completed_sales GROUP BY DATE(invoice_date))
SELECT date,revenue_gbp,SUM(revenue_gbp) OVER (
 ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_revenue_gbp
FROM daily ORDER BY date;
