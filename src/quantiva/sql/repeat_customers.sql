WITH frequency AS (SELECT customer_id,COUNT(DISTINCT invoice_no) AS purchases
 FROM completed_sales WHERE customer_id IS NOT NULL GROUP BY customer_id),
repeaters AS (SELECT customer_id FROM frequency GROUP BY customer_id HAVING MAX(purchases)>=2)
SELECT (SELECT COUNT(*) FROM frequency) AS identifiable_customers,
 (SELECT COUNT(*) FROM repeaters) AS repeat_customers,
 1.0*(SELECT COUNT(*) FROM repeaters)/NULLIF((SELECT COUNT(*) FROM frequency),0) AS repeat_purchase_rate;
