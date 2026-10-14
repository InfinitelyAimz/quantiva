# Business KPI definitions — Phase 2

All sales metrics use **Phase 1 eligible completed-sale lines**: noncancelled,
positive quantity, positive price. This includes anonymous sales and nonstandard
product codes such as charges. It is gross observed transaction activity, not
settled payments, profit, or merchandise-only revenue. No new cleaning exclusions
are introduced. SQL exposes this scope through the `completed_sales` view; pandas
uses the validated `is_completed_sale` flag. No currency conversion is needed:
source prices are GBP.

| Metric | Numerator / denominator | Grain and interpretation |
| --- | --- | --- |
| Gross completed-sales revenue | Sum of eligible Quantity × UnitPrice | Line amounts summed to the requested scope, GBP |
| Completed order count | Distinct eligible InvoiceNo | Invoice, not transaction line; an invoice with at least one eligible line counts |
| Average order value | Gross completed-sales revenue / completed orders | GBP per eligible invoice; undefined for no orders |
| Units sold | Sum of eligible Quantity | Source units, including nonstandard item codes; not strictly merchandise units |
| Identifiable customers | Distinct nonmissing eligible CustomerID | Purchasers in the selected observation period, not all customers in the ledger |
| Revenue per identifiable customer | Eligible revenue with valid CustomerID / identifiable customers | GBP; numerator excludes anonymous sales to match denominator |
| Daily revenue | Sum of eligible line amounts grouped by source timestamp date | Daily observed activity; absent dates are marked, not assumed zero demand |
| Monthly revenue | Sum of eligible line amounts grouped by YYYY-MM | Calendar month; coverage accompanies totals |
| Monthly growth | (current revenue / previous revenue − 1) × 100 | Only adjacent fully covered calendar months and a positive previous denominator |
| Product revenue contribution | Product eligible revenue / gross eligible revenue × 100 | StockCode grain; description is a label, not a key |
| Geographic revenue contribution | Country eligible revenue / gross eligible revenue × 100 | Line-level country; missing countries remain a separate group |
| Repeat purchase rate | Identifiable customers with ≥2 distinct eligible invoices / identifiable customers | Observation-period repeat behavior; not cohort retention or lifetime loyalty |
| Customer revenue concentration | Top N identifiable customer spending / all identifiable spending | Excludes anonymous revenue from both parts |
| Cancellation-related amount | Signed sum of cancellation line amounts | Separate negative movement, not matched physical returns |

For zero denominators, ratios return null, not a fabricated zero. Counts/sums return
zero on empty input. Frequency counts distinct invoices per known customer. Customer
metrics exclude customers appearing only in cancellations or other ineligible lines.

Invoice totals combine all eligible lines; multiple timestamps within an invoice
are preserved. Daily orders count invoices represented on each date, so daily order
counts need not sum to overall distinct orders. The same nonadditivity applies if
an invoice spans geographic groups. Revenue remains additive across disjoint lines.

**No accounting net revenue is published.** Gross sales plus signed cancellations
is shown only as an unmatched signed movement sensitivity measure. Cancellations
may refer to purchases before the observation window; stock corrections are not
proven returns. The two quarantined negative prices labelled “Adjust bad debt” are
reported separately and are not reinstated into sales or cancellation KPIs.

December 2011 ends on 9 December at 12:50 and is incomplete. December 2010 covers all
calendar dates, although the first observation day is a boundary. Coverage flags
describe the dataset date span; they cannot prove complete capture on every trading
day. Growth is descriptive and does not establish seasonality or causality.

SQL sums integer units of £0.0001 before division. pandas independently sums the
Parquet float amounts. Counts require exact equality; monetary and ratio comparisons
use an absolute tolerance of **£0.000001** (or 0.000001 for dimensionless ratios),
with no relative tolerance. This permits floating summation noise but is stricter
than the source's stored price precision. Group-key presence must also match.
