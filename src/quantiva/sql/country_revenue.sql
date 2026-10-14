-- LEFT JOIN preserves an unknown geography; order counts need not be additive
-- if one invoice contains lines attributed to multiple countries.
SELECT c.country, SUM(s.revenue_units)/10000.0 AS revenue_gbp,
 COUNT(DISTINCT s.invoice_no) AS orders, COUNT(*) AS sale_lines,
 100.0*SUM(s.revenue_units)/NULLIF(SUM(SUM(s.revenue_units)) OVER (),0) AS revenue_share_pct
FROM completed_sales s LEFT JOIN countries c ON s.country=c.country
GROUP BY c.country ORDER BY revenue_gbp DESC, c.country;
