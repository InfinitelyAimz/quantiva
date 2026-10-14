# QUANTIVA — PHASE 2 IMPLEMENTATION SPECIFICATION

## 1. Your Role and Project Context

Act as a senior data scientist, data engineer, Python developer, SQL specialist, and technical mentor.

We are continuing development of **Quantiva — Retail Intelligence & Predictive Analytics**, an end-to-end data science portfolio project.

The purpose of Quantiva is to demonstrate practical data science, data analytics, data engineering, statistical analysis, and machine learning skills suitable for Junior Data Scientist, Data Analyst, and Junior Data Engineer positions.

The project is being developed locally on Windows using Python, Git, GitHub, and Codex.

The GitHub repository is:

https://github.com/InfinitelyAimz/quantiva

The master requirements document is:

`PROJECT_SPECIFICATION.md`

Treat this document as the authoritative source of project requirements.

**Phase 1 — Foundation has been completed and provisionally approved based on its implementation and verification report.**

We are now beginning:

**Phase 2 — Data Analytics & Business Intelligence**

Do not implement Phase 3, Phase 4, or Phase 5 during this task.

---

## 2. Git Repository and Branch Management

Before beginning Phase 2, inspect the repository.

### Existing branch

Phase 1 was implemented on:

`codex/phase-1-foundation`

I would like to stop using `codex/` as a branch prefix wherever the execution environment allows custom branch names.

Use the following branch naming convention:

- `main` — Stable project branch
- `phase/01-foundation` — Phase 1
- `phase/02-analytics` — Phase 2
- `phase/03-machine-learning` — Phase 3
- `phase/04-dashboard` — Phase 4
- `phase/05-portfolio` — Phase 5

### Required Git actions

1. Inspect the current Git status, branch structure, and commit history.
2. Confirm whether all Phase 1 changes are committed.
3. Verify that the Phase 1 test suite passes.
4. If safe and supported, rename the local Phase 1 branch to `phase/01-foundation`.
5. Preserve all existing commits, files, and Git history.
6. Identify whether Phase 1 has been merged into `main`.
7. Explain any outstanding merge or synchronization requirements.
8. Do not automatically merge Phase 1 into `main`.
9. Do not push any branches or commits to GitHub without my explicit approval.

### Phase 2 branch

Phase 2 should be developed on:

`phase/02-analytics`

Create this branch from the verified Phase 1 state so all required Phase 1 functionality is available.

If Codex requires a `codex/` prefix, explain the restriction and use the safest supported alternative.

Do not discard changes or rewrite Git history to achieve a naming preference.

**Important:** Branch renaming and Phase 2 development must not overwrite or compromise the completed Phase 1 implementation.

---

## 3. Phase 1 Baseline

The following results were reported during Phase 1.

### Dataset

Source: UCI Online Retail dataset.

Dataset DOI: `10.24432/C5BW33`

Original transaction lines: **541,909**

Dataset period: 1 December 2010 to 9 December 2011.

### Reported data-quality results

| Measure | Count |
|---|---:|
| Original transaction lines | 541,909 |
| Missing customer identifiers | 135,080 |
| Missing descriptions | 1,454 |
| Exact duplicate exclusions | 5,268 |
| C-prefixed cancellation rows | 9,288 |
| Negative quantity rows | 10,624 |
| Zero-price rows | 2,515 |
| Negative-price rows | 2 |

### Reported cleaned results

| Classification | Count |
|---|---:|
| Cleaned ledger rows | 536,639 |
| Eligible completed-sale lines | 524,878 |
| Cancellation lines | 9,251 |
| Stock-adjustment candidates | 1,336 |
| Positive-quantity zero-value lines | 1,174 |

### Existing processed outputs

The Phase 1 pipeline produces:

- `transactions.parquet`
- `exclusions.parquet`
- `initial_inspection.json`
- `cleaning_report.json`
- `manifest.json`

These are stored under `data/processed` and excluded from Git.

Phase 1 reportedly passed 23 automated tests and full-data integrity verification.

**Do not assume these results are correct without inspecting the actual repository and generated outputs.**

Preserve the Phase 1 cleaning logic unless a genuine defect is identified.

Any proposed correction must be explained and supported by tests.

---

## 4. Phase 2 Objectives

The primary objective is to transform the cleaned retail transaction data into trustworthy business intelligence and statistical findings.

By the end of Phase 2, Quantiva must be able to:

1. Store cleaned transaction data in a relational database.
2. Execute reproducible analytical SQL queries.
3. Calculate meaningful retail business KPIs.
4. Independently reconcile SQL results with pandas calculations.
5. Analyze sales, products, customers, and geography.
6. Perform appropriate descriptive statistical analysis.
7. Identify patterns, anomalies, and limitations.
8. Produce meaningful visualizations.
9. Document analytical findings in executable notebooks.
10. Provide a reliable analytical foundation for the future machine learning and dashboard phases.

The emphasis must be on **analytical correctness, reproducibility, and interpretability**, not simply generating charts.

---

## 5. Relational Database Implementation

Use SQLite with SQLAlchemy.

The database must be created locally without any paid service or cloud dependency.

### Database requirements

Design a suitable relational schema representing:

- Transaction lines
- Invoices
- Products
- Customers
- Relevant geographic attributes

Use appropriate primary keys, foreign keys, constraints, and indexes.

Avoid unnecessary complexity or excessive normalization.

### Data integrity

The implementation must:

1. Preserve the relationship between transaction lines and invoices.
2. Preserve original source-row traceability where available.
3. Correctly handle transactions with missing customer identifiers.
4. Preserve cancellations and stock-adjustment classifications.
5. Prevent accidental duplicate imports.
6. Support deterministic database rebuilding.
7. Support efficient date, invoice, customer, and product queries.
8. Avoid treating line items as distinct orders.
9. Validate database record counts against the processed dataset.
10. Document any schema assumptions.

Product descriptions may not be unique or stable identifiers. Investigate product-code behavior before establishing uniqueness rules.

Do not assume every invoice has an identifiable customer.

### Database workflow

Implement a repeatable command that:

- Loads the validated Phase 1 processed dataset.
- Creates the required database schema.
- Imports the data.
- Validates referential integrity.
- Confirms imported row counts.
- Reports any import or reconciliation failures.

Repeated execution must not silently duplicate data.

Prefer an atomic rebuild or appropriately transactional import strategy.

---

## 6. Business KPI Definitions

Before calculating KPIs, define them precisely.

Create a documented KPI specification describing the numerator, denominator, filtering rules, aggregation grain, and interpretation of each metric.

### Required KPIs

- Gross completed-sales revenue
- Completed order count
- Average order value
- Units sold
- Distinct identifiable customers
- Revenue per identifiable customer
- Monthly revenue
- Daily revenue
- Revenue growth
- Product revenue contribution
- Geographic revenue contribution
- Repeat purchase rate

Where appropriate, include cancellation and return-related measures separately.

### Revenue definitions

Clearly distinguish between:

1. Gross completed-sales revenue.
2. Cancellation-related monetary values.
3. Net revenue, only where defensible from the available data.

Do not assume every cancellation can be matched to an original completed sale.

Do not label a measure as net revenue unless the treatment of cancellations, adjustments, and unmatched records is clearly documented.

### Orders and customers

An invoice may contain multiple transaction lines.

Order counts must use appropriately defined distinct invoices, not row counts.

Missing customer identifiers must not cause otherwise eligible completed sales to disappear from revenue analysis.

Customer-specific metrics must exclude unidentified customers where identity is required.

Use an explicit, documented definition of repeat purchasing.

---

## 7. SQL Analytics

Implement professional analytical SQL queries using SQLite-compatible syntax.

### Required SQL techniques

Demonstrate:

- INNER JOIN
- LEFT JOIN
- GROUP BY
- HAVING
- Common Table Expressions (CTEs)
- Window functions
- Date-based aggregations
- Ranking
- Running totals
- Percentage contribution calculations

### Required analyses

Develop SQL queries for:

1. Daily sales revenue.
2. Monthly sales revenue.
3. Revenue by country.
4. Top products by revenue.
5. Top products by units sold.
6. Average order value.
7. Customer purchase frequency.
8. Top customers by spending.
9. Monthly revenue growth.
10. Product revenue contribution.
11. Revenue running totals.
12. Customer repeat purchasing behavior.

Queries must use the correct transaction eligibility rules.

Store important SQL queries in clearly organized `.sql` files where appropriate.

Provide examples showing how to execute the queries.

Avoid unnecessary database-specific extensions that would prevent the project from running on standard SQLite.

---

## 8. SQL and pandas Reconciliation

This is a critical Phase 2 requirement.

Business metrics calculated using SQL must be independently verified against pandas implementations.

### Required reconciliation

Compare at least:

- Total completed-sales revenue
- Completed order count
- Average order value
- Distinct identifiable customers
- Monthly revenue
- Revenue by country
- Top product revenue

Use documented numerical tolerances for monetary comparisons.

Do not simply call the same underlying calculation twice and describe that as independent verification.

Report any discrepancies and investigate their causes.

Create automated tests that fail when SQL and pandas calculations diverge beyond accepted tolerances.

Generate a reconciliation report showing:

- Metric name
- SQL result
- pandas result
- Absolute difference
- Relative difference where meaningful
- Pass/fail status

All values must come from actual executed calculations.

---

## 9. Exploratory Data Analysis

Create or extend the project's Jupyter notebooks.

The notebooks must be executable and clearly explain the analysis.

### A. Revenue analysis

Investigate:

- Total completed-sales revenue
- Daily revenue
- Monthly revenue
- Revenue growth
- Average order value
- Sales volatility
- Calendar-related patterns
- Revenue concentration

Account for partial calendar periods.

Avoid comparing incomplete months directly with full months without qualification.

### B. Product analysis

Investigate:

- Highest-revenue products
- Highest-volume products
- Product revenue concentration
- Slow-moving products
- Unusual product codes
- Product descriptions and naming inconsistencies
- Extreme transaction quantities
- Extreme unit prices

Distinguish ordinary retail products from charges, adjustments, and other nonstandard records where possible.

Do not silently exclude unusual products without documenting the decision.

### C. Customer analysis

Investigate:

- Number of identifiable customers
- Purchase frequency
- Spending distribution
- Repeat purchasing behavior
- Customer revenue concentration
- High-value customers
- Missing customer ID limitations

Do not implement full RFM segmentation during Phase 2 unless it is needed for a clearly justified analytical dependency.

RFM segmentation remains part of the broader project specification and can be implemented in a later phase.

### D. Geographic analysis

Investigate:

- Revenue by country
- Order distribution by country
- Geographic revenue concentration
- Differences between the United Kingdom and international sales

Use descriptive analysis rather than unsupported causal claims.

---

## 10. Statistical Analysis

Create a dedicated statistical analysis notebook.

### Required statistics

Calculate and explain:

- Mean
- Median
- Standard deviation
- Variance where useful
- Quartiles
- Percentiles
- Interquartile range
- Distribution skewness
- Correlation where meaningful

### Statistical interpretation

Explain what each statistic reveals about the retail business.

For example:

- What does the difference between mean and median order values suggest?
- How concentrated is revenue among products or customers?
- How much does daily revenue fluctuate?
- Are transaction amounts heavily skewed?
- How do extreme observations affect averages?

### Methodological requirements

- Use suitable units of analysis.
- Avoid mixing transaction-line, invoice, customer, and daily observations.
- Distinguish descriptive relationships from causal conclusions.
- Investigate outliers rather than automatically deleting them.
- Explain limitations introduced by missing customer identifiers.
- Avoid inappropriate statistical tests performed merely to make the project appear more sophisticated.

Statistical conclusions must be supported by actual observed results.

---

## 11. Data Quality and Sensitivity Analysis

Build on the Phase 1 quality report.

### Duplicate sensitivity

Investigate the impact of removing the 5,268 exact duplicate rows.

Quantify how relevant metrics change when those records are retained versus excluded.

At minimum, compare:

- Completed-sales revenue
- Completed order count
- Average order value
- Units sold

Explain the ambiguity of exact duplicate transaction rows when no unique transaction-line identifier exists.

### Cancellation and adjustment sensitivity

Investigate:

- C-prefixed cancellations
- Noncancelled negative quantities
- Zero-price transactions
- Negative-price quarantined rows
- Unusual stock codes
- Extremely high quantities and prices

Preserve the audit trail.

Do not reinterpret ambiguous inventory adjustments as customer returns without evidence.

### Calendar coverage

Investigate:

- Incomplete final observation day
- Partial December periods
- Missing transaction dates
- Calendar effects relevant to future forecasting

Document recommendations for handling these issues in Phase 3.

---

## 12. Visualizations

Use Plotly and Matplotlib as appropriate.

Create clear, professional visualizations demonstrating meaningful analysis.

### Required charts

- Daily revenue time series
- Monthly revenue trend
- Top products by revenue
- Revenue by country
- Order value distribution
- Customer spending distribution
- Product revenue concentration
- Revenue variability or calendar pattern chart

Additional charts may be included where justified.

### Visualization requirements

1. Use meaningful titles and axis labels.
2. Clearly identify currencies and units.
3. Avoid misleading axis scaling.
4. Handle skewed distributions appropriately.
5. Explain significant outliers.
6. Document relevant data exclusions.
7. Include written interpretations.
8. Keep plots reproducible from the processed dataset.

The visual design should be consistent with Quantiva's professional dark navy and restrained blue visual identity where practical.

Do not prioritize visual styling over statistical correctness.

---

## 13. Project Architecture

Build on the existing Phase 1 structure.

Expected areas of development include:

- Database models and schema
- Database import and rebuild logic
- SQL query files
- KPI definitions
- Analytics functions
- Reconciliation utilities
- EDA notebooks
- Statistical analysis notebooks
- Technical reports
- Automated tests

Use modular Python code with type hints and meaningful documentation.

Keep business metric definitions centralized.

Avoid duplicating complex eligibility logic across SQL, pandas, and notebooks.

However, ensure SQL/pandas reconciliation still provides an independent implementation check.

Adapt the existing architecture when justified, and explain significant changes.

Do not unnecessarily restructure working Phase 1 components.

---

## 14. Testing and Verification

Extend the Phase 1 automated test suite.

### Required tests

Test:

1. Database schema creation.
2. Foreign-key integrity.
3. Missing customer ID handling.
4. Repeatable database imports.
5. Correct invoice-level order counting.
6. Correct revenue filtering.
7. KPI calculations.
8. SQL/pandas reconciliation.
9. Calendar aggregations.
10. Duplicate sensitivity calculations.
11. Empty or invalid input handling.
12. Representative edge cases involving cancellations and zero-price records.

### Verification requirements

Run:

- All existing Phase 1 tests.
- All new Phase 2 tests.
- Ruff lint checks.
- Ruff formatting checks.
- Dependency consistency checks.
- Data integrity verification.
- Database reconciliation checks.

Execute the analytical notebooks and confirm they run successfully from a clean environment.

Do not report a test as passing unless it was actually executed.

Document any checks that could not be completed and explain why.

---

## 15. Documentation

Update the project documentation.

### README

Document:

- Phase 2 architecture
- Database setup
- Data preparation commands
- Database rebuild commands
- Analytical query execution
- Notebook execution
- Business KPI definitions
- Reconciliation procedure
- Known limitations

### Analytical findings

Create or update:

`reports/findings.md`

Include:

- Actual business KPIs
- Significant sales trends
- Product findings
- Customer findings
- Geographic findings
- Statistical observations
- Data-quality sensitivity results
- Important limitations

### Technical methodology

Document:

- Relational schema decisions
- KPI formulas
- Revenue treatment
- SQL/pandas reconciliation
- Statistical methodology
- Assumptions
- Reproducibility instructions

Use actual measured results only.

Do not fabricate metrics or analytical conclusions.

---

## 16. Learning and Mentorship Requirements

I want to understand the data science behind the project.

Do not simply generate code and move on.

For each major implementation area:

1. Explain what was built.
2. Explain why it matters.
3. Explain the underlying analytical or statistical concepts.
4. Identify important engineering decisions.
5. Explain how the implementation was verified.
6. Discuss limitations and alternatives.

Keep explanations technically accurate but accessible to someone with a BSc IT background and existing Python/SQL experience.

Where useful, provide short examples of SQL queries, statistical calculations, or Python implementations.

The objective is to build both a strong portfolio project and practical data science knowledge.

---

## 17. Engineering Constraints

All previous engineering requirements remain in effect.

Specifically:

- Python 3.11 or another explicitly justified supported version.
- SQLite with SQLAlchemy.
- pandas and NumPy.
- Plotly and Matplotlib.
- SciPy/statsmodels where appropriate.
- pytest.
- Ruff.
- Git and GitHub.
- Local Windows development.
- Completely free tooling.
- No mandatory cloud services.
- No paid APIs.
- No fabricated data.
- No fabricated model results.
- No hardcoded personal file paths.
- No credentials in Git.
- No large raw datasets committed to Git.
- Reproducible processing.
- Clear documentation.
- Maintainable code.

Preserve compatibility with the existing Phase 1 environment wherever practical.

---

## 18. Phase 2 Definition of Done

Phase 2 is complete only when:

- The verified Phase 1 outputs can be imported into SQLite.
- The database schema is documented.
- Database imports are reproducible and rebuild-safe.
- Foreign-key integrity checks pass.
- Required analytical SQL queries execute correctly.
- KPI definitions are documented.
- SQL and pandas calculations reconcile.
- Revenue and order metrics use the correct aggregation grain.
- Duplicate sensitivity is quantified.
- Significant data-quality limitations are investigated.
- EDA notebooks execute successfully.
- Statistical analysis notebooks execute successfully.
- Major visualizations include written interpretations.
- All automated tests pass.
- Documentation is updated.
- Actual analytical findings are recorded.
- No fabricated results appear in the repository.

Do not declare Phase 2 complete until these criteria have been verified.

---

## 19. Execution Strategy

Implement Phase 2 incrementally.

### Stage 1 — Repository Verification

- Inspect Git status.
- Verify Phase 1 commits.
- Run baseline tests.
- Review branch naming.
- Establish a safe Phase 2 development branch.

### Stage 2 — Database Foundation

- Design the relational schema.
- Implement database initialization.
- Import validated records.
- Verify data integrity and repeatability.

### Stage 3 — Business Analytics

- Define KPIs.
- Implement SQL queries.
- Implement independent pandas calculations.
- Reconcile results.

### Stage 4 — Exploratory and Statistical Analysis

- Investigate sales, products, customers, and geography.
- Perform descriptive statistics.
- Produce charts and written interpretations.
- Quantify data-quality sensitivity.

### Stage 5 — Verification and Documentation

- Execute all tests.
- Execute notebooks.
- Update reports.
- Update README.
- Review Phase 2 completion criteria.

You may implement these stages sequentially without requesting approval between each stage.

However, do not proceed to Phase 3 without my explicit approval.

---

## 20. Final Deliverables and Progress Report

When Phase 2 is complete, provide a detailed report containing:

### A. Git Status

- Current branch
- Branch naming changes
- Commit history summary
- Uncommitted changes
- Merge status
- GitHub push status

### B. Implementation

- Files created
- Files modified
- Database architecture
- SQL queries
- Analytics modules
- Notebooks
- Tests

### C. Actual Business Findings

Report calculated values for:

- Completed-sales revenue
- Completed order count
- Average order value
- Identifiable customers
- Top products
- Top countries
- Significant trends
- Statistical findings

### D. Data Validation

- Database record counts
- SQL/pandas reconciliation results
- Duplicate sensitivity findings
- Data-quality limitations

### E. Verification

- Tests executed
- Tests passed and failed
- Lint and formatting results
- Notebook execution results
- Outstanding defects

### F. Recommendations

- Remaining technical debt
- Data limitations affecting forecasting
- Recommended Phase 3 architecture
- Any decisions requiring my approval

Do not push to GitHub or merge branches without my explicit approval.

Do not begin Phase 3.

---

## 21. Begin Phase 2

Start by inspecting the existing repository and verifying the Phase 1 implementation.

Handle branch naming safely.

Establish the Phase 2 development branch.

Then implement the database foundation, business analytics, statistical analysis, and verification requirements described above.

Make sensible engineering decisions independently.

Explain significant findings and trade-offs.

**Begin Phase 2 now.**