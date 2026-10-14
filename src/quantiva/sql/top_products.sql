SELECT s.stock_code, p.display_description, SUM(s.revenue_units)/10000.0 AS revenue_gbp,
 SUM(s.quantity) AS units, COUNT(DISTINCT s.invoice_no) AS orders,
 DENSE_RANK() OVER (ORDER BY SUM(s.revenue_units) DESC) AS revenue_rank,
 100.0*SUM(s.revenue_units)/NULLIF(SUM(SUM(s.revenue_units)) OVER (),0) AS revenue_share_pct
FROM completed_sales s INNER JOIN products p ON s.stock_code=p.stock_code
GROUP BY s.stock_code,p.display_description ORDER BY revenue_gbp DESC,s.stock_code;
