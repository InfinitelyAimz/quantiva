# Phase 4 UI verification

Verified on Windows with locked Streamlit 1.66.0 and the actual UCI SQLite/model
artifacts. A real Codex in-app browser connected to `http://127.0.0.1:8501`.
Desktop viewport: 1440×950. Smaller viewport: 600×900. Saved PNGs and
`phase_4_browser_checks.json` record the inspected states; these are real screenshots,
not mockups. Temporary viewport overrides were reset afterward.

| Check | Observed result |
| --- | --- |
| Overview, both themes | Six actual full-data KPI cards; monthly/daily trends, country/product revenue and order distribution |
| Sales, both themes | Trends, product/country controls, bounded tables and monthly completeness |
| Customer Intelligence, both themes | Known-customer cards, six descriptive segments, distributions/scatter plots and RFM explanations |
| Predictive Analytics, both themes | 9–15 December 2011 forecast, saved metadata, validation/test comparison and error diagnostics |
| Data Quality, both themes | Original/cleaned/eligible/classification counts, source caveats, lineage and stored verification |
| Country selection | Germany changed revenue to £228,678.40 across 457 eligible orders |
| Product selection | Germany plus POST changed revenue to £21,001.00 across 374 affected invoices |
| Time and metric controls | Weekly aggregation and Units sold were selected and displayed |
| Calendar range | 2–3 December 2010 changed sales to £94,528.05 across 210 orders, AOV £450.13; calendar inspected in both themes |
| Navigation persistence | Light appearance and Germany scope persisted from Sales to Customer; hidden Sales product scope did not apply there |
| Segment selection | Champions restricted RFM charts/table; date/country customer KPI cards retained the labeled scope |
| Evaluation selector | Held-out table showed weekly MAE £11,250.17, forest £12,344.71 and naive £20,978.67; no invented Linear Regression test row |
| Current artifact button | Checksum and deterministic inference passed, origin 2011-12-08, output 2011-12-09–15 |
| Smaller screen | App width matched 600px, document had no horizontal overflow; tables scroll within bounded containers; sidebar drawer opens and navigation works |

Initial inspection exposed cramped two-column charts, unreadable inherited chart
headings and an unthemed date field. The final design stacks smaller layouts,
wraps chart headings outside figures, disables Streamlit's automatic Plotly theme,
and applies the selected colors to date controls and navigation buttons. Native
mobile drawer navigation may leave the drawer open; use its collapse control to
return to the content. It is an overlay rather than a second narrow content column.

Automated AppTest also covers synthetic-data page rendering in both themes, filter
changes, missing database/processed prerequisites, missing model/evaluation evidence,
and setup messages. Corrupt metadata and tampered prediction evidence are rejected
by service tests. No existing UCI artifacts were removed to simulate an error state.
Browser filters and theme toggles were actually used; date-boundary/error/filter
edge cases were exercised through pytest/AppTest in addition to the browser calendar
range check above. Browser loading briefly showed skeleton placeholders while scripts or
frontend components completed; final states were inspected after rendering.

Manual repeat procedure:

1. Install the lock; run preparation, database, analyze and forecast-train commands
   in README. Launch `python -m streamlit run app/Home.py` from the checkout.
2. Open each of the five sidebar pages, switch Light/Dark, inspect labels, axes,
   cards, tables and warnings. Navigate again and verify appearance persists.
3. On Sales select Germany and POST, change time aggregation/metric and check the
   visible scope note. Remove filters to restore full-data results.
4. On Customer select a segment, inspect RFM rules/reference date and confirm that
   segment selection affects charts/tables rather than the upper customer cards.
5. On Predictive choose each evaluation period/model and inspect errors/horizons;
   confirm the weekly baseline win and historical labels. Do not interpret it as live.
6. On Quality distinguish stored evidence from the explicit current integrity button.
7. Resize to 600px, open/collapse sidebar navigation and scroll wide tables within
   their containers. Repeat widget/popover checks before upgrading Streamlit.

The UI is not claimed to have undergone a formal WCAG certification, screen-reader
audit, exhaustive keyboard audit or testing on every browser/device. Styling depends
on the documented Streamlit version; current tests and screenshots are scoped evidence.

## KPI correction and illustrative currency verification — 15 October 2026

The recovery audit identified revenue-card ellipsis at 1280px. The shared metric
value now uses container-relative type bounded between 1.25rem and 2rem, normal
wrapping and no ellipsis. The existing responsive column stacking is unchanged.

A real local browser exercised the following 16 Overview states at height 950px:

| Width | GBP dark | GBP light | ZAR dark | ZAR light |
| --- | --- | --- | --- | --- |
| 600px | Pass | Pass | Pass | Pass |
| 1024px | Pass | Pass | Pass | Pass |
| 1280px | Pass | Pass | Pass | Pass |
| 1440px | Pass | Pass | Pass | Pass |

All six metric values were inspected in the rendered DOM at every state. Revenue
was fully formatted as **£10,642,110.80** or **R 135,240,167.58**; AOV as **£533.17**
or **R 6,775.56**. Orders 19,960, units 5,572,420, customers 4,338 and repeat rate
65.58% stayed unchanged. No metric horizontal overflow or page horizontal overflow
was detected; small screens retain vertical scrolling. Representative actual captures
are `figures/dashboard_currency_*.png`; full measurement records are in
`phase_4_currency_browser_checks.json`. Earlier screenshots above are historical GBP captures,
not evidence of the new ZAR default.

The sidebar selector defaults to ZAR. Both currency settings were exercised on Sales,
Customer Intelligence, Predictive Analytics and Data Quality. Navigation retained the
selection. Monetary headers and plotted values followed the chosen unit; counts,
percentages, RFM scores and the winning baseline remained unchanged. A browser-downloaded
ZAR RFM CSV was independently compared with all 4,338 GBP customer aggregates: monetary
values scaled by the fixed rate, while IDs, recency, frequency, scores and segments
matched. Export source/display currency, rate/date and illustrative status were checked.

The default 2011-12-08 ECB cross-rate and historical-illustration caveat are visible
on each ZAR page. Saved forecast/report data remain GBP. The automated suite is now
96 passing tests, including the original 88 plus eight currency tests. No production
artifacts were rebuilt or retrained for these checks.
