SELECT stock_code, SUM(quantity) AS units,
 DENSE_RANK() OVER (ORDER BY SUM(quantity) DESC) AS units_rank
FROM completed_sales GROUP BY stock_code ORDER BY units DESC,stock_code;
