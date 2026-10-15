# QUANTIVA — PHASE 4 IMPLEMENTATION SPECIFICATION
## Interactive Business Intelligence Dashboard

### 1. Role and Project Context

Act as a senior Python engineer, data scientist, analytics engineer, Streamlit developer, UX/UI designer, and technical mentor.

We are continuing development of **Quantiva — Retail Intelligence & Predictive Analytics**, an end-to-end data science portfolio project.

The project demonstrates:

- Data ingestion and cleaning.
- Data engineering and SQL.
- Exploratory and statistical analysis.
- Business intelligence and KPI reporting.
- Machine learning and time-series forecasting.
- Reproducibility and software engineering.
- Interactive analytics application development.

The project uses the UCI Online Retail dataset covering December 2010 through December 2011.

Technology stack:

- Python 3.11.
- pandas and NumPy.
- SQLAlchemy and SQLite.
- scikit-learn and SciPy.
- Matplotlib and Plotly.
- Streamlit.
- pytest and Ruff.
- Git and GitHub.

The application must remain **completely free and locally executable on Windows**.

Repository:

https://github.com/InfinitelyAimz/quantiva

Authoritative project documentation:

- `PROJECT_SPECIFICATION.md`
- `PHASE_2_SPECIFICATION.md`
- `PHASE_3_SPECIFICATION.md`
- `reports/phase_3_progress.md`
- `reports/model_evaluation.md`
- `reports/phase_3_methodology.md`

Inspect the actual repository and implementation before writing code.

Do not assume file paths, functions, or APIs exist without verifying them.

---

### 2. Current Project Status

Phases 1, 2, and 3 are completed, verified, and merged into `main`.

The last reported synchronized `main` commit is:

`7eb1d20d044f17dc8061630419823a0e6fb36c82`

Verify this against the actual repository.

Phase 1 provides:

- Official dataset ingestion.
- Reproducible cleaning.
- Transaction classification.
- Data provenance.
- Parquet outputs.
- Data-quality reporting.

Phase 2 provides:

- Relational SQLite storage.
- SQL analytics.
- Business KPIs.
- Statistical analysis.
- SQL/pandas reconciliation.
- Customer, product, geography, and sales analytics.

Phase 3 provides:

- Daily revenue forecasting.
- Naive and weekly seasonal-naive baselines.
- Linear Regression.
- Random Forest Regression.
- Leakage-safe features.
- Chronological validation.
- Seven-day recursive forecasting.
- Model persistence and inference.
- Forecast evaluation reports.

**Phase 4 must integrate these existing components rather than recreate them.**

Do not modify historical analytical definitions or forecasting results simply to make the dashboard more attractive.

---

### 3. Git Workflow and Development Controls

Before implementation:

1. Inspect Git status and branch history.
2. Confirm local `main` matches `origin/main`.
3. Check for uncommitted or untracked user work.
4. Run the existing test suite.
5. Review the root `AGENTS.md` for repository instructions.
6. Create a new development branch named:

`phase-4`

Use the approved branch convention recorded in `AGENTS.md`.

Create the branch from the verified latest `main`.

Do not overwrite existing branches or discard uncommitted changes.

Save this specification as:

`PHASE_4_SPECIFICATION.md`

#### GitHub workflow

You are authorized to:

- Create `phase-4`.
- Commit Phase 4 implementation work to that branch.
- Push `phase-4` to GitHub.
- Open a draft pull request targeting `main`.
- Update the draft PR as implementation progresses.

You are NOT authorized to:

- Merge the PR.
- Modify `main`.
- Force-push.
- Delete branches.
- Rewrite history.
- Start Phase 5.

Keep the PR in draft status until I explicitly authorize the final review and merge.

If the remote has diverged, a branch already exists unexpectedly, or the working tree contains unrelated changes, stop and explain before proceeding.

---

### 4. Primary Phase 4 Objective

Build a professional, interactive Streamlit dashboard that presents Quantiva's retail intelligence and predictive analytics.

The dashboard must:

1. Provide a clear business overview.
2. Enable interactive sales exploration.
3. Provide customer intelligence and RFM segmentation.
4. Present historical forecasting and model evaluation.
5. Explain data quality, lineage, and analytical limitations.
6. Support dark and light themes.
7. Provide responsive layouts.
8. Use consistent visual components.
9. Handle missing local artifacts gracefully.
10. Reuse existing analytical and forecasting code.
11. Be reproducible from a fresh local setup.
12. Be suitable for portfolio demonstration and screenshots.

The dashboard should feel like a cohesive analytics product, not five unrelated notebooks.

---

### 5. Dashboard Design Direction

Create a modern business intelligence interface.

Visual inspiration:

- Professional SaaS analytics products.
- Financial intelligence platforms.
- Modern data visualization tools.
- Enterprise reporting applications.

Do not copy another company's branding or proprietary interface.

#### Visual identity

Use:

- A distinctive Quantiva wordmark.
- Consistent typography.
- Clear visual hierarchy.
- Refined KPI cards.
- Subtle borders and shadows.
- Consistent chart styling.
- Accessible color contrasts.
- Thoughtful spacing.
- Minimal visual clutter.

The visual identity should be recognizable across all pages.

#### Layout

Use a wide dashboard layout with:

- A sidebar navigation system.
- A top-level page title and contextual description.
- A global filter area where appropriate.
- KPI summaries.
- Interactive charts.
- Supporting tables.
- Contextual explanations.
- Data caveats.

Keep the dashboard functional at common desktop widths and usable on smaller screens.

Avoid unnecessary animations, decorative widgets, and excessive whitespace.

---

### 6. Dark and Light Theme System

**Both dark and light themes are mandatory.**

Provide a visible theme toggle.

#### Dark theme

Suggested design:

- Deep navy or charcoal background.
- Slightly lighter surfaces for cards.
- Blue or cyan accents.
- Soft borders.
- High-contrast text.
- Muted secondary labels.

#### Light theme

Suggested design:

- White or very light gray background.
- Subtle gray card surfaces.
- Blue accents.
- Dark text.
- Clean borders.
- Accessible contrast.

#### Theme requirements

The selected theme must apply consistently to:

- Application background.
- Sidebar.
- Navigation.
- Headers.
- KPI cards.
- Buttons.
- Filters.
- Tables.
- Plotly charts.
- Legends.
- Tooltips.
- Error and warning messages.
- Custom dashboard components.

The toggle must change the actual application appearance, not merely a label.

Persist the theme across page navigation and reruns within the session.

Where Streamlit permits, respect a user's configured theme or system preference on initial load.

Do not claim that the app detects the operating-system theme unless this is genuinely supported.

Prefer supported Streamlit theming and styling APIs.

If runtime theme switching requires controlled CSS overrides, implement them carefully, minimize dependence on unstable DOM selectors, and document any version-specific limitations.

Do not use an unsupported workaround that breaks navigation, accessibility, or standard widgets.

Use a centralized theme configuration rather than duplicating color constants throughout the codebase.

---

### 7. Application Navigation

Implement five main pages:

1. Overview.
2. Sales Analytics.
3. Customer Intelligence.
4. Predictive Analytics.
5. Data Quality.

Use Streamlit's supported multipage navigation capabilities.

Provide a consistent sidebar containing:

- Quantiva branding.
- Page navigation.
- Theme toggle.
- Dataset identification.
- Data coverage information.
- Relevant application status.

Keep navigation clear and intuitive.

Do not overload the sidebar with every possible filter.

---

### 8. Global Data and Filter Architecture

Implement a reusable data access layer for the dashboard.

#### Requirements

- Reuse existing SQLite and analytics functions.
- Do not duplicate complex SQL queries unnecessarily.
- Do not load the raw Excel workbook on every rerun.
- Cache expensive read-only operations appropriately.
- Separate cached data from mutable presentation state.
- Use parameterized SQL where applicable.
- Validate filter inputs.
- Preserve data types and monetary precision.
- Avoid unnecessary full-table loading.
- Handle empty filter results safely.

#### Filters

Where appropriate, support:

- Date range.
- Country.
- Product.
- Customer segment.
- Relevant metric selection.

Use page-specific filters where a global filter would create confusing semantics.

For each KPI and chart, make clear which filters apply.

If a filter cannot be applied meaningfully to a particular metric, explain or disable it rather than silently ignoring it.

#### Caching

Use Streamlit caching correctly.

Avoid stale cached results when the underlying database changes.

Use stable data-version or file-signature invalidation where appropriate.

Do not cache untrusted model artifacts without validation.

---

### 9. Page One — Overview

Build an executive-level retail intelligence dashboard.

#### Primary KPI cards

Display:

- Gross completed-sales revenue.
- Distinct completed orders.
- Average order value.
- Units sold.
- Identifiable customers.
- Repeat purchase rate.

Use the existing Phase 2 KPI definitions.

For reference, the original full-data values include:

| KPI | Historical measured value |
|---|---:|
| Gross completed-sales revenue | £10,642,110.804 |
| Completed orders | 19,960 |
| Average order value | £533.17 |
| Units sold | 5,572,420 |
| Identifiable purchasers | 4,338 |
| Repeat purchase rate | 65.58% |

These are reference values only.

Calculate displayed values from the actual data.

Do not hardcode them.

#### Overview charts

Include:

- Monthly revenue trend.
- Daily revenue trend.
- Revenue by country.
- Top products by revenue.
- Order value distribution or another useful summary.

#### Executive insights

Provide concise, data-derived observations such as:

- Highest full-month revenue.
- Revenue concentration.
- Identifiable versus anonymous revenue.
- Repeat purchasing.
- Unusual revenue patterns.

Do not fabricate insights or claim causal relationships.

#### Coverage limitations

Clearly indicate:

- Dataset period.
- Partial December 2011.
- Unknown customer IDs.
- Gross revenue definition.

The Overview should be immediately understandable to a hiring manager or business stakeholder.

---

### 10. Page Two — Sales Analytics

Build an interactive sales-performance exploration page.

#### Sales trends

Include:

- Daily revenue.
- Weekly revenue.
- Monthly revenue.
- Order counts.
- Average order value.
- Units sold.

Provide appropriate metric selectors and time aggregation options.

#### Product analytics

Include:

- Top products by revenue.
- Top products by units sold.
- Revenue concentration.
- Product search or filtering.
- Product-level detail table.

Preserve original stock codes.

Do not assume that all codes represent physical merchandise.

Use product descriptions as display labels, not unique identifiers.

#### Geographic analytics

Include:

- Revenue by country.
- Order distribution by country.
- Country-level comparison.
- Geographic concentration.

A bar chart is sufficient; a choropleth may be added only if country mapping is accurate and maintainable.

#### Business interpretation

Provide concise explanations of important trends and outliers.

Do not treat exceptional wholesale transactions as automatically invalid.

#### Monthly growth

Do not present partial-month comparisons as complete-month growth.

Preserve the Phase 2 completeness rules.

---

### 11. Page Three — Customer Intelligence

Build a customer analytics page with an explicit RFM segmentation implementation.

This is a new Phase 4 analytical component.

#### Existing customer KPIs

Reuse:

- Identifiable customers.
- Known-customer revenue.
- Revenue per identifiable customer.
- Repeat purchasers.
- Repeat purchase rate.
- Customer spending distribution.
- Customer purchase frequency.

#### RFM analysis

Implement Recency, Frequency, and Monetary analysis.

Definitions:

**Recency:** Days since a customer's most recent eligible purchase relative to a documented reference date.

**Frequency:** Number of distinct eligible completed-sale invoices for that customer.

**Monetary:** Total eligible completed-sales revenue attributed to that customer.

#### RFM eligibility

- Include only identifiable customers.
- Use eligible completed-sale transactions.
- Exclude anonymous customer IDs from RFM scoring.
- Do not net cancellations unless explicitly defined in a separate experiment.
- Do not interpret RFM as verified customer lifetime value.

#### RFM scoring

Use a deterministic, documented scoring approach.

A five-point quantile system is acceptable if ties and small samples are handled correctly.

Explain:

- Score direction.
- Threshold calculation.
- Tie handling.
- Segmentation rules.
- Reference date.
- Filter interactions.

Do not force arbitrary quantile bins if the data cannot support them.

#### Customer segments

Consider business-readable segments such as:

- Champions.
- Loyal Customers.
- Potential Loyalists.
- New Customers.
- At Risk.
- Hibernating.

Ensure segments are mutually exclusive and collectively exhaustive for eligible customers.

Define exact rules rather than relying on vague labels.

#### RFM visualizations

Include:

- Customer segment distribution.
- Revenue by customer segment.
- Recency versus monetary value.
- Frequency versus monetary value.
- RFM score distribution.
- Segment-level summary table.

#### Privacy

Do not expose unnecessary personal information.

Customer IDs may be used as pseudonymous analytical identifiers, but do not present them as verified identities.

#### Important distinction

RFM segmentation is descriptive customer grouping.

Do not call it machine learning clustering unless an actual clustering algorithm is implemented and validated.

---

### 12. Page Four — Predictive Analytics

This page must integrate the verified Phase 3 forecasting pipeline.

Do not create a separate forecasting implementation inside the dashboard.

#### Required sections

**A. Forecasting Overview**

Explain:

- Target: daily gross eligible completed-sales revenue.
- Horizon: seven calendar days.
- Historical modeling period.
- Calendar policy.
- Selected forecasting strategy.
- Model limitations.

**B. Seven-Day Forecast Demonstration**

Display the saved historical forecast for:

9–15 December 2011.

Include:

- Forecast date.
- Predicted revenue in GBP.
- Forecast horizon.
- Model name.
- Training cutoff.
- Model version.

Use the existing Phase 3 inference interface.

The forecast must be clearly labeled:

**Retrospective forecast demonstration — December 2011**

Do not label it as a live or 2026 forecast.

**C. Model Comparison**

Show:

- Naive baseline.
- Weekly seasonal-naive baseline.
- Linear Regression.
- Random Forest.

Distinguish validation and held-out test results.

Do not invent held-out Linear Regression metrics.

Use actual saved evaluation evidence.

**D. Model Performance**

Display:

- MAE.
- RMSE.
- WAPE.
- Forecast bias.
- Error by horizon.
- Significant misses.

For reference:

| Model | Held-out MAE |
|---|---:|
| Weekly seasonal naive | £11,250.17 |
| Random Forest | £12,344.71 |
| Naive | £20,978.67 |

The weekly baseline outperformed the selected Random Forest on the held-out test.

Make this visible.

Do not suggest that Random Forest demonstrated superior generalization.

**E. Forecasting Diagnostics**

Include:

- Actual versus predicted.
- Model comparison chart.
- Error by forecast horizon.
- Residual distribution.
- Significant forecast misses.
- Relevant sensitivity findings.

#### Prediction uncertainty

Phase 3 does not provide calibrated prediction intervals.

Do not invent confidence intervals or uncertainty bands.

#### Model artifact handling

- Validate artifact availability.
- Use the existing trusted model-loading implementation.
- Preserve checksum and metadata validation.
- Do not automatically download model binaries.
- Do not silently retrain on page load.
- Do not load untrusted serialized models.

If model artifacts are missing, show a useful setup message and preserve access to the saved evaluation reports.

---

### 13. Page Five — Data Quality

Build a transparent data-quality and provenance dashboard.

#### Dataset overview

Display:

- Raw transaction count.
- Cleaned transaction count.
- Eligible completed-sales count.
- Excluded duplicate count.
- Missing customer IDs.
- Missing descriptions.
- Cancellation lines.
- Stock-adjustment candidates.
- Zero-value lines.
- Invalid or quarantined records.

Reuse actual Phase 1 reports.

#### Visualizations

Include:

- Transaction classification distribution.
- Missing-value summary.
- Exclusion-reason breakdown.
- Daily observation coverage.
- Calendar gap distribution.
- Revenue sensitivity to duplicates.

#### Data lineage

Explain:

Raw UCI workbook → Cleaning → Parquet → SQLite → Analytics → Forecasting → Dashboard.

Show source provenance and processing metadata where available.

#### Data-quality explanations

Clarify:

- Exact duplicate ambiguity.
- Missing customer IDs.
- Nonstandard product codes.
- Cancellation treatment.
- Negative-price quarantine.
- Missing calendar dates.
- Partial observation boundaries.

#### Reconciliation

Where feasible, surface existing verification evidence:

- Data integrity.
- SQL/pandas reconciliation.
- Forecast artifact verification.

Distinguish stored verification evidence from checks executed during the current dashboard session.

Do not claim that all tests are currently passing merely because a historical report says so.

---

### 14. Charting and Visualization Standards

Use Plotly as the primary interactive charting library.

#### Requirements

- Theme-aware chart backgrounds.
- Consistent color palette.
- Consistent fonts.
- Clear titles.
- Proper axis labels.
- GBP currency formatting.
- Appropriate date formatting.
- Useful hover information.
- Responsive sizing.
- Accessible contrast.

Use a restrained number of colors.

Avoid unnecessary 3D charts, gauges, or decorative visualizations.

Ensure that missing data and partial periods are represented honestly.

#### Chart interactions

Support useful interactions such as:

- Hover details.
- Metric selection.
- Date filtering.
- Country filtering.
- Product selection.
- Segment selection.

Do not implement interactions that appear functional but have no effect.

---

### 15. Dashboard Components and Architecture

Use modular components rather than putting all code in one Streamlit file.

Suggested architecture:

- Application entry point.
- Page modules.
- Theme configuration.
- Shared UI components.
- Data access layer.
- KPI presentation helpers.
- Chart builders.
- Customer RFM analytics.
- Forecast integration.
- Error handling.

Adapt the structure to the existing repository.

Avoid unnecessary frameworks.

Keep business calculations separate from UI rendering.

The application should be testable without requiring every test to launch a browser.

---

### 16. Streamlit State Management

Use Streamlit session state carefully.

Manage:

- Theme selection.
- Navigation-related state.
- Date filters.
- Country selections.
- Product selections.
- Customer segmentation filters.
- Forecast display options.

Avoid inconsistent state between pages.

Ensure filter changes update the appropriate charts and KPI cards.

Provide sensible defaults.

Reset invalid selections when the underlying available options change.

Avoid accidental infinite reruns.

---

### 17. Performance Requirements

The application must run comfortably on a typical personal Windows computer.

#### Performance expectations

- Avoid repeated raw workbook loading.
- Use SQLite for aggregated queries.
- Cache stable analytical results.
- Minimize redundant database access.
- Avoid unnecessary model retraining.
- Load large tables only when needed.
- Use pagination or bounded tables where useful.
- Keep charts responsive.
- Avoid excessive memory usage.

Do not add Redis, paid databases, cloud warehouses, or distributed infrastructure.

Performance improvements must not compromise analytical correctness.

---

### 18. Error Handling and User Experience

Handle missing or invalid prerequisites gracefully.

Examples:

- SQLite database not built.
- Processed dataset missing.
- Forecasting model artifacts missing.
- Forecast evaluation reports unavailable.
- Empty filtered results.
- Invalid date ranges.
- Corrupted metadata.
- Unsupported dependency versions.

Provide actionable messages explaining what the user should do.

Do not expose unnecessary raw stack traces in the user interface.

Do not silently substitute fabricated data.

Avoid automatically rebuilding large datasets or training models without user action.

---

### 19. Local Setup and Execution

Provide a documented command for launching the dashboard.

For example:

`streamlit run ...`

Use the actual application entry point.

Update the existing dependency configuration and lockfile.

Document:

1. Python version.
2. Virtual environment setup.
3. Dependency installation.
4. Data preparation.
5. Database creation.
6. Forecast artifact generation.
7. Dashboard launch.
8. Verification commands.

The application must not require paid services or credentials.

No cloud deployment is required in Phase 4.

---

### 20. Automated Testing

Extend pytest coverage.

#### Required tests

**Theme system**
- Theme switching.
- Session-state persistence.
- Valid theme values.
- Theme-aware chart configuration.

**Data access**
- SQLite loading.
- Query correctness.
- Cache invalidation.
- Missing database handling.
- Invalid filter handling.

**Overview**
- KPI consistency.
- Filtered KPI calculations.
- Date boundaries.
- Empty results.

**Sales analytics**
- Revenue aggregation.
- Order counting.
- Product grouping.
- Geographic grouping.
- Monthly completeness handling.

**Customer intelligence**
- RFM recency.
- Distinct-invoice frequency.
- Monetary aggregation.
- Anonymous customer exclusion.
- Score direction.
- Quantile tie handling.
- Segment assignment.
- Segment completeness and exclusivity.

**Predictive analytics**
- Forecast evidence loading.
- Artifact validation.
- Model metadata display.
- Validation versus held-out separation.
- Missing model handling.
- Historical date labeling.

**Data quality**
- Classification counts.
- Exclusion reasons.
- Missing-value summaries.
- Data lineage metadata.

**Integration**
- Page loading.
- Theme behavior.
- Filter interactions.
- Navigation.
- Missing-artifact states.

Use synthetic fixtures for tests where appropriate.

Do not substitute synthetic data for actual business findings.

---

### 21. Dashboard Verification

Before declaring Phase 4 complete:

1. Run the full pytest suite.
2. Run Ruff lint and formatting checks.
3. Run dependency consistency checks.
4. Verify Phase 1 integrity.
5. Verify Phase 2 database and reconciliation.
6. Verify Phase 3 forecasting evidence and inference.
7. Execute dashboard-specific tests.
8. Launch the Streamlit application.
9. Verify all five pages.
10. Verify both themes.
11. Test interactive filters.
12. Test missing-artifact handling.
13. Inspect charts and tables.
14. Check responsive behavior.
15. Confirm no unsupported analytical claims.

Where a browser or graphical interface is available, perform actual visual inspection and interaction testing.

If browser testing is unavailable, say so explicitly and provide the exact manual verification steps.

Do not claim visual testing occurred unless it actually occurred.

---

### 22. Documentation

Create or update:

- `PHASE_4_SPECIFICATION.md`
- `reports/phase_4_methodology.md`
- `reports/phase_4_progress.md`
- `README.md`
- Appropriate UI verification documentation.

#### Phase 4 methodology

Explain:

- Dashboard architecture.
- Data access.
- Theme system.
- Filtering semantics.
- KPI consistency.
- RFM methodology.
- Forecast integration.
- Caching.
- Performance.
- Error handling.

#### Phase 4 progress report

Include:

- Implemented pages.
- Features.
- Git status.
- Test results.
- Visual verification.
- Known limitations.
- Remaining work.
- Phase 5 readiness.

---

### 23. Portfolio Presentation Requirements

This application will be shown to recruiters, hiring managers, and technical interviewers.

Prioritize:

- Professional appearance.
- Clear navigation.
- Accurate metrics.
- Transparent methodology.
- Useful interactions.
- Reliable execution.
- Reproducible results.
- Readable documentation.

The dashboard should help a reviewer understand what the project accomplishes within a few minutes.

Include concise explanations of business value without overstating findings.

Avoid generic marketing claims such as "AI-powered insights" when the underlying analysis is descriptive.

---

### 24. Learning and Mentorship

I want to understand the implementation.

Explain:

1. How Streamlit applications work.
2. How multipage navigation is structured.
3. How data flows from SQLite to the UI.
4. How filters affect SQL and pandas aggregations.
5. How caching improves performance.
6. How RFM segmentation works.
7. How saved machine learning artifacts are integrated.
8. How theme switching is implemented.
9. How the dashboard is tested.
10. What trade-offs were made.

Provide concise explanations after major milestones.

Do not sacrifice correctness for visual polish.

---

### 25. Implementation Stages

Proceed incrementally.

**Stage 1 — Repository and Architecture**
- Inspect the existing repository.
- Verify main and baseline tests.
- Create `phase-4`.
- Save specification.
- Establish dashboard architecture.

**Stage 2 — Theme and Application Shell**
- Implement Streamlit entry point.
- Build navigation.
- Implement dark/light theme system.
- Build reusable components.

**Stage 3 — Data Access and Overview**
- Implement dashboard data layer.
- Implement global/page filters.
- Build Overview.

**Stage 4 — Sales Analytics**
- Implement trends, products, and geography.
- Validate KPI/filter semantics.

**Stage 5 — Customer Intelligence**
- Implement RFM analytics.
- Build segmentation visualizations.
- Test scoring and segment assignments.

**Stage 6 — Predictive Analytics**
- Integrate Phase 3 model evidence.
- Display historical forecast.
- Build model evaluation visualizations.
- Verify metadata and limitations.

**Stage 7 — Data Quality**
- Integrate Phase 1 reports and Phase 2 reconciliation evidence.
- Build quality and lineage visualizations.

**Stage 8 — Polish and Verification**
- Test both themes.
- Test navigation and filters.
- Verify performance and responsiveness.
- Run all regression tests.
- Update documentation.

You may proceed between these stages without asking permission.

Do not begin Phase 5.

---

### 26. Definition of Done

Phase 4 is complete only when:

- All five pages exist and function.
- Dark and light themes both work.
- Theme selection persists across navigation.
- Shared visual components are consistent.
- KPI values reconcile with existing analytics.
- Interactive filters work correctly.
- Sales and geography charts are accurate.
- RFM segmentation is implemented and tested.
- Predictive Analytics reuses Phase 3 outputs.
- Validation and held-out metrics are distinguished.
- The retrospective forecast is correctly labeled.
- Missing artifacts produce useful errors.
- Data-quality findings are traceable.
- Dashboard performance is acceptable.
- All automated tests pass.
- Existing phases remain functional.
- Both themes are visually reviewed where possible.
- Documentation is complete.
- No fabricated results or misleading claims appear.

---

### 27. Final Git and Delivery Instructions

At the end of implementation:

1. Review all changes.
2. Run the complete verification suite.
3. Commit completed Phase 4 work to `phase-4`.
4. Push `phase-4` to GitHub.
5. Open or update the draft PR targeting `main`.
6. Report the PR URL and latest commit SHA.
7. Leave the PR unmerged.
8. Leave `main` unchanged.
9. Wait for my approval before merging or starting Phase 5.

Do not automatically mark the PR ready for review.

Do not merge even if all checks pass.

---

### 28. Final Progress Report

Create:

`reports/phase_4_progress.md`

Include:

**A. Git Status**
- Current branch.
- Commits.
- Remote synchronization.
- Draft PR status.

**B. Implementation**
- Architecture.
- Pages.
- Theme system.
- Filters.
- RFM.
- Forecast integration.
- Data quality.

**C. Verification**
- Tests passed.
- Regression tests.
- Visual checks.
- Performance checks.
- Outstanding issues.

**D. Analytical Integrity**
- KPI reconciliation.
- RFM definitions.
- Forecasting caveats.
- Data-quality assumptions.

**E. Recommendations**
- Whether Phase 4 is ready for approval.
- Known limitations.
- Recommended Phase 5 work.

Do not fabricate evidence.

---

### 29. Final Execution Instruction

Begin by inspecting the repository and reading `AGENTS.md`.

Confirm the verified Phase 3 baseline.

Create `phase-4` from `main`.

Implement the five-page Streamlit dashboard with both dark and light themes.

Reuse the existing analytics and forecasting pipelines.

Implement and test RFM segmentation.

Maintain accurate business definitions and honest forecasting interpretation.

Commit and push work only to `phase-4`.

Open a draft PR targeting `main`.

Do not merge the PR.

Do not modify `main`.

Do not begin Phase 5.

Provide the completed Phase 4 progress report and wait for my review.

**Begin Phase 4 implementation now.**

## User-approved follow-up — 15 October 2026

Correct the Overview KPI truncation at 1280px through the shared presentation layer.
Keep both themes professional and verify 600px, 1024px, 1280px and 1440px, including
revenue, AOV, orders, units and customers. Preserve business calculations and models.

Add dashboard-wide GBP/ZAR display selection, default ZAR, persistent across pages
and reruns. Keep GBP authoritative for data, SQL, calculations, RFM scoring,
forecasting, model selection/evaluation and stored artifacts. Convert monetary displays
only, using a fixed explicitly dated rate appropriate to the 2010–2011 dataset.
Label ZAR as illustrative rather than actual historical ZAR transactions. Apply the
choice consistently to monetary cards, charts, axes, tooltips, tables, exports, RFM
values, forecasts and narrative amounts. Counts, percentages, scores and model
rankings must not change. Document the rate source, conversion and limitations.

Test conversion, formatting, persistence and dashboard consistency; run the original
88-test suite plus new coverage, lint, formatting and relevant verification. Perform
actual browser checks and update visual evidence. Commit/push only `phase-4` and
update draft PR #2. Do not modify main, merge/close the PR or begin Phase 5. Stop if
the correction introduces significant layout regressions rather than expanding scope.
