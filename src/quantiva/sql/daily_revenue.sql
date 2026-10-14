SELECT DATE(invoice_date) AS date, SUM(revenue_units)/10000.0 AS revenue_gbp,
 COUNT(DISTINCT invoice_no) AS orders, SUM(quantity) AS units
FROM completed_sales GROUP BY DATE(invoice_date) ORDER BY date;
