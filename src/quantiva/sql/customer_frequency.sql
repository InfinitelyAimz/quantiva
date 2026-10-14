SELECT c.customer_id,COUNT(DISTINCT s.invoice_no) AS frequency,
 SUM(s.revenue_units)/10000.0 AS spending_gbp,
 MIN(DATE(s.invoice_date)) AS first_purchase,MAX(DATE(s.invoice_date)) AS last_purchase
FROM customers c INNER JOIN completed_sales s ON c.customer_id=s.customer_id
GROUP BY c.customer_id ORDER BY spending_gbp DESC,c.customer_id;
