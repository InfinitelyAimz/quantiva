WITH spending AS (SELECT customer_id,SUM(revenue_units)/10000.0 AS spending_gbp
 FROM completed_sales WHERE customer_id IS NOT NULL GROUP BY customer_id)
SELECT customer_id,spending_gbp,DENSE_RANK() OVER (ORDER BY spending_gbp DESC) AS spending_rank,
 100.0*spending_gbp/NULLIF(SUM(spending_gbp) OVER (),0) AS identifiable_revenue_share_pct
FROM spending ORDER BY spending_gbp DESC,customer_id;
