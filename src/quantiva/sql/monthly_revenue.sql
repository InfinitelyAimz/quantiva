SELECT STRFTIME('%Y-%m',invoice_date) AS month, SUM(revenue_units)/10000.0 AS revenue_gbp,
 COUNT(DISTINCT invoice_no) AS orders
FROM completed_sales GROUP BY STRFTIME('%Y-%m',invoice_date) ORDER BY month;
