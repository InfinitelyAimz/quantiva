-- Signed movements, not matched returns or defensible accounting net revenue.
SELECT transaction_type,COUNT(*) AS lines,SUM(revenue_units)/10000.0 AS signed_amount_gbp
FROM transactions GROUP BY transaction_type ORDER BY transaction_type;
