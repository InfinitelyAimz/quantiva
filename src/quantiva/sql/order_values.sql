SELECT invoice_no, SUM(revenue_units)/10000.0 AS revenue_gbp,
 SUM(quantity) AS units, COUNT(*) AS lines, MIN(invoice_date) AS first_line_time
FROM completed_sales GROUP BY invoice_no ORDER BY invoice_no;
