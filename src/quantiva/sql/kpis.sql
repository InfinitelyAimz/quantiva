-- Revenue is gross completed sales. Customer revenue excludes anonymous sales.
SELECT COALESCE(SUM(revenue_units),0)/10000.0 AS gross_revenue_gbp,
 COUNT(DISTINCT invoice_no) AS completed_orders,
 COALESCE(SUM(revenue_units),0)/10000.0/NULLIF(COUNT(DISTINCT invoice_no),0) AS aov_gbp,
 COALESCE(SUM(quantity),0) AS units_sold,
 COUNT(DISTINCT customer_id) AS identifiable_customers,
 COALESCE(SUM(CASE WHEN customer_id IS NOT NULL THEN revenue_units ELSE 0 END),0)/10000.0
 AS identifiable_revenue_gbp,
 COALESCE(SUM(CASE WHEN customer_id IS NOT NULL THEN revenue_units ELSE 0 END),0)/10000.0
 /NULLIF(COUNT(DISTINCT customer_id),0) AS revenue_per_identifiable_customer_gbp
FROM completed_sales;
