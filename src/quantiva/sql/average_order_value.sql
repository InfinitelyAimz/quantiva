WITH orders AS (SELECT invoice_no,SUM(revenue_units)/10000.0 AS order_revenue
 FROM completed_sales GROUP BY invoice_no)
SELECT COUNT(*) AS completed_orders, AVG(order_revenue) AS aov_gbp FROM orders;
