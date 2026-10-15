# QUANTIVA — PHASE 4 UI/UX REFINEMENT & PROFESSIONAL POLISH

## 1. Objective

Refine the existing Quantiva Streamlit dashboard into a polished, modern, professional business intelligence application suitable for:

- A data science and analytics portfolio.
- Demonstrations to recruiters and prospective employers.
- Business stakeholders exploring retail performance.
- Technical reviewers evaluating analytical quality and reproducibility.

**This is a refinement of the existing Phase 4 implementation, not a redesign from scratch.**

The current dashboard is functional, analytically verified, and supports both dark and light themes, with ZAR as the default illustrative display currency and GBP as the authoritative source currency.

Preserve those capabilities.

The desired design direction is:

**Clean, modern, minimal, professional, readable, consistent, and data-focused.**

Think of a well-designed SaaS analytics product rather than a technical notebook converted into a dashboard.

Do not imitate a particular commercial product or introduce unnecessary visual complexity.

## 2. Repository and Git constraints

Repository: `InfinitelyAimz/quantiva`

Current development branch: `phase-4`

Existing draft PR: #2, targeting `main`.

Before implementation:

1. Read `AGENTS.md` and all relevant Phase 4 specifications.
2. Inspect the current dashboard architecture and reusable components.
3. Verify the active branch and working-tree status.
4. Review existing screenshots and UI verification reports.
5. Confirm the current test baseline and relevant dependencies.

All changes must remain on `phase-4`.

You may commit and push verified UI refinements to that branch and update the existing draft PR.

Do not:

- Modify or merge `main`.
- Mark PR #2 ready for review.
- Close or merge PR #2.
- Force-push or delete branches.
- Start Phase 5.
- Rebuild the application from scratch.
- Replace Streamlit with another framework.
- Introduce paid services or cloud dependencies.

If the working tree contains unexpected changes, stop and report them before editing.

## 3. Preserve existing functionality

The dashboard currently includes:

1. Overview
2. Sales Analytics
3. Customer Intelligence
4. Predictive Analytics
5. Data Quality

Preserve all five pages.

Also preserve:

- Existing SQLite and Parquet data access.
- Source provenance and verification.
- Business metric definitions.
- Date, country, product, and customer filters.
- RFM segmentation rules and counts.
- Phase 3 forecasting models and saved evidence.
- Validation and held-out evaluation separation.
- Dashboard caching and invalidation.
- CSV exports.
- Dark/light appearance selection.
- GBP/ZAR currency selection and session persistence.
- The documented fixed historical exchange rate.
- Current test coverage and analytical reproducibility.

All underlying monetary calculations must remain in GBP.

ZAR conversion must remain a presentation-layer transformation.

Do not alter forecasting results, RFM classifications, or stored source data for aesthetic reasons.

## 4. Design system refinement

Establish or improve a centralized, reusable design system.

Use consistent design tokens for:

- Page backgrounds.
- Sidebar backgrounds.
- Cards and surfaces.
- Borders and dividers.
- Text hierarchy.
- Accent colors.
- Chart colors.
- Hover and selected states.
- Spacing.
- Border radii.
- Typography.
- Focus indicators.

### Color direction

Keep the existing Quantiva blue/navy identity.

**Dark theme**

- Deep navy application background.
- Slightly lighter navy card surfaces.
- Clear, restrained borders.
- Bright but controlled blue accents.
- High-contrast primary text.
- Muted secondary text that remains readable.

**Light theme**

- Soft neutral or blue-grey page background.
- White or near-white cards.
- Dark navy headings.
- Subtle borders.
- The same recognizable blue accents.

Avoid excessive gradients, neon colors, heavy shadows, and decorative effects.

Use color primarily to communicate hierarchy, selection, comparison, and meaning.

Both themes must feel like the same product.

## 5. Typography and information hierarchy

Improve the visual hierarchy across all pages.

Each page should have:

1. A clear page title.
2. A concise, business-friendly description.
3. Relevant filters in a consistent location.
4. Primary KPIs where appropriate.
5. The most important visualizations.
6. Supporting tables, diagnostics, and methodology details.

Use consistent heading sizes, font weights, and spacing.

Prioritize readability over fitting excessive information above the fold.

Avoid unnecessarily small labels and overly dense explanatory paragraphs.

Technical terms should remain accurate, but the main interface should be understandable to someone who is not a data scientist.

For example:

- Display "Random Forest" instead of `random_forest`.
- Display "Seasonal Naive" instead of `seasonal_naive`.
- Display "Mean Absolute Error (MAE)" where context requires it.
- Use clear descriptions for validation and held-out testing.

Keep raw identifiers in machine-readable exports or technical evidence where necessary.

## 6. Page headers and layout

The existing screenshots show that some pages can benefit from clearer title and section hierarchy.

Refine the layout so users can immediately identify:

- Which page they are viewing.
- What business question the page answers.
- Which filters are active.
- Which currency is selected.
- Whether monetary values are illustrative conversions.

Keep controls aligned and consistent across pages.

Avoid excessive empty space, inconsistent margins, or charts beginning abruptly without contextual headings.

Do not unnecessarily reduce the available chart area.

## 7. KPI card improvements

The existing KPI cards are functional and the earlier truncation issue has been corrected.

Preserve the full-value display behavior.

Refine KPI cards with:

- Consistent dimensions and padding.
- Clear metric labels.
- Prominent, readable values.
- Optional subtle icons only where they improve comprehension.
- Consistent number formatting.
- Appropriate visual hierarchy.

Do not add decorative elements that distract from the data.

Avoid truncation at supported viewport widths.

Where useful, provide short explanations through accessible captions or tooltips.

For example:

**Gross completed sales**

R 135,240,167.58

Illustrative ZAR conversion of eligible GBP sales.

Do not imply that historical transactions originally occurred in ZAR.

## 8. Overview page

Make the Overview page feel like the executive summary of Quantiva.

The page should quickly answer:

- How much revenue was recorded?
- How many orders were completed?
- What was the average order value?
- How many units were sold?
- How many identifiable customers purchased?
- How much repeat purchasing occurred?
- How did recorded sales change over time?
- Which countries contributed most to recorded revenue?

### Required improvements

**A. Monthly revenue chart**

The current chart uses a legend similar to:

`Full month — True / False`

Replace that presentation with business-friendly labels such as:

- Complete month
- Partial month

Preserve the underlying month-completeness rules.

Ensure partial months remain visually distinguishable and are not presented as directly comparable full-month performance.

**B. Country revenue chart**

Improve readability of country labels.

Consider adding values or percentages where they remain legible.

Avoid unnecessary chart clutter.

Preserve correct ranking and the meaning of filtered results.

**C. Daily revenue chart**

Ensure the title and surrounding explanation make clear that the chart represents recorded eligible sales, not a complete measure of underlying demand.

## 9. Sales Analytics page

Review the page for consistency with the refined Overview.

Improve:

- Filter layout and grouping.
- Revenue trend presentation.
- Product ranking readability.
- Geographic analysis.
- Date-axis formatting.
- Chart titles and legends.
- Table formatting.

Prioritize actionable business questions over displaying as many charts as possible.

Preserve all existing analytical functionality.

Ensure users can understand when they are looking at a partial month or a filtered subset.

## 10. Customer Intelligence page

This page is a major portfolio feature and should receive particular attention.

The existing RFM segmentation is analytically verified and must remain unchanged.

### A. Segment distribution

Improve the customer-segment chart so that differences between the six segments are immediately understandable.

A horizontal bar chart, donut chart, or improved existing bar chart may be appropriate.

Choose based on readability and the information conveyed, not decoration.

Use a consistent segment color mapping across all customer visualizations.

### B. Revenue by segment

Improve comparison of segment revenue.

Consider ordering segments by revenue, where appropriate, and using clearly formatted monetary labels.

Avoid implying that descriptive segment labels represent validated churn predictions or lifetime value.

### C. Recency and monetary scatterplot

The current scatterplot has substantial compression near zero because a small number of customers have much higher recorded monetary values.

Improve its readability.

Evaluate suitable approaches such as:

- A clearly labelled logarithmic monetary axis.
- A `log1p`-based visual transformation with correctly formatted original-value hover data.
- An optional scale selector.
- A supplementary distribution chart.

Choose the simplest analytically defensible solution.

Do not silently remove outliers or change source values.

If logarithmic scaling is used, handle zero and non-positive values correctly and document the method.

### D. Frequency and monetary scatterplot

Apply the same principles.

Preserve the relationship between recorded invoice frequency and monetary value.

Make dense customer clusters easier to inspect.

### E. RFM score and monetary distributions

Improve histogram labels and visual clarity.

Replace technical labels such as `Rfm Score` with `RFM Score`.

Explain that RFM scores are relative to the selected customer scope.

### F. Customer tables

Keep detailed customer and segment tables.

Improve:

- Header readability.
- Column names.
- Numeric formatting.
- Alignment.
- Responsive behavior.
- Scrolling experience.

Use concise labels in the UI while preserving precise technical field names where needed for exports or reproducibility.

## 11. Predictive Analytics page

Make the forecasting page accessible to both technical and business audiences.

Preserve all Phase 3 experimental results and limitations.

### A. Forecast overview

Present the historical forecasting demonstration with a clear title and explanation.

For example:

**Seven-day historical sales forecast**

Random Forest predictions generated from a December 2011 training cutoff.

Make it immediately apparent that this is a retrospective demonstration, not a live 2026 forecast.

### B. Forecast chart

Improve date labels, hover information, legends, and line styling.

Ensure that zero predictions are displayed honestly.

Do not interpret a zero prediction as proof of zero underlying demand.

### C. Model evaluation

Use reader-friendly model names.

Clearly distinguish:

- Validation performance.
- Held-out test performance.

Highlight the best model for the selected evaluation period using a restrained visual treatment.

Do not change the validation-selected model based on held-out results.

**Critical analytical finding:**

Random Forest was selected using validation MAE, but Weekly Seasonal Naive achieved the better held-out MAE.

This must remain clearly visible.

Do not invent held-out Linear Regression results.

### D. Diagnostic charts

Refine:

- Actual versus predicted.
- Error by forecast horizon.
- Residual distribution.
- Largest forecast misses.

Improve chart titles, legends, axis labels, and tooltips.

Where possible, place technical interpretation in concise expandable methodology sections rather than large paragraphs that interrupt the visual flow.

Do not remove important caveats.

## 12. Data Quality page

Refine the Data Quality page into a clear explanation of data reliability and analytical boundaries.

Organize the information into understandable sections:

- Source data.
- Cleaning and exclusions.
- Eligible sales.
- Missing customer identifiers.
- Cancellations and adjustments.
- Calendar coverage.
- Verification and provenance.

Use clear labels and restrained visual indicators.

Do not describe a data-quality condition as a successful check unless it has actually been verified.

Preserve the distinction between stored verification evidence and checks executed during the current session.

## 13. Sidebar and navigation

Preserve the existing sidebar navigation and Quantiva branding.

Improve:

- Active-page highlighting.
- Inactive icon contrast.
- Navigation spacing.
- Sidebar section separation.
- Theme control presentation.
- Currency control presentation.
- Dataset/source information.

The sidebar should feel organized, not crowded.

Keep theme and currency controls easy to find.

Maintain their persistence across navigation and reruns.

Ensure text remains readable in both themes.

## 14. Chart design consistency

Centralize Plotly presentation settings wherever practical.

Standardize:

- Chart background colors.
- Font colors.
- Gridline intensity.
- Axis labels.
- Legend positioning.
- Hover templates.
- Color palettes.
- Plot margins.
- Number formatting.
- Date formatting.
- Responsive sizing.

Charts should look like parts of one application rather than independent notebook outputs.

Use a consistent semantic palette for customer segments and model comparisons.

Do not rely on color alone to communicate important distinctions.

Avoid excessive gridlines or unnecessarily large legends.

Maintain sufficient contrast in both themes.

## 15. Reduce visual clutter

Review explanatory text across the application.

Separate information into three levels:

**Primary:** Business insight and headline metrics.

**Secondary:** Concise context needed to interpret the data.

**Technical:** Detailed methodology, provenance, assumptions, and verification.

Where appropriate, move technical detail into accessible Streamlit expanders or methodology sections.

However:

- Do not hide critical warnings.
- Do not remove material analytical limitations.
- Do not conceal the illustrative nature of ZAR.
- Do not make forecasting performance appear stronger than it is.
- Do not weaken data-quality disclosures.

The goal is progressive disclosure, not omission.

## 16. Responsive behavior

Test the dashboard at:

- 600px
- 1024px
- 1280px
- 1440px

Check:

- Sidebar usability.
- KPI wrapping.
- Full-value visibility.
- Chart scaling.
- Table overflow.
- Filter alignment.
- Long labels.
- Legends.
- Theme controls.
- Currency controls.

Avoid horizontal page overflow.

Allow appropriate internal scrolling for wide tables.

Use supported Streamlit layout APIs and restrained CSS.

Do not introduce fragile browser-specific styling without justification.

## 17. Accessibility and usability

Improve practical accessibility:

- Adequate contrast.
- Visible focus states.
- Clear control labels.
- Readable font sizes.
- Understandable chart titles.
- Non-color-dependent information.
- Keyboard-accessible controls where supported.

Do not claim formal accessibility certification without conducting an appropriate audit.

Avoid animations or effects that reduce usability.

## 18. Performance and dependencies

Keep the dashboard lightweight.

Do not add a new UI framework.

Do not introduce paid libraries, external APIs, or cloud services.

Avoid unnecessary database queries, model loading, or expensive recomputation during page rendering.

Preserve existing caching behavior.

Do not introduce performance regressions merely for styling.

## 19. Implementation approach

Use a controlled, incremental workflow.

**Stage 1 — Inspect and plan**

Review existing implementation and screenshots.

Identify the highest-value changes.

Produce a concise implementation plan before editing.

**Stage 2 — Design system**

Refine shared tokens, components, typography, and layout.

**Stage 3 — Overview and Sales**

Improve KPI presentation, labels, charts, and hierarchy.

**Stage 4 — Customer Intelligence**

Improve segment charts, monetary visualizations, tables, and legends.

**Stage 5 — Predictive Analytics**

Improve forecasting presentation and diagnostic readability.

**Stage 6 — Data Quality and navigation**

Refine documentation presentation, sidebar, and shared controls.

**Stage 7 — Verification**

Run automated checks and browser tests.

**Stage 8 — Documentation and delivery**

Update relevant Phase 4 documentation and existing draft PR.

Do not expand the task into unrelated feature development.

## 20. Verification requirements

Run the complete existing test suite.

The most recent reported baseline is:

**96 passing tests.**

Also run:

- Ruff lint.
- Ruff formatting checks.
- Dependency consistency checks.
- Phase 1 integrity verification.
- Phase 2 analytics verification.
- Phase 3 forecasting verification.
- Phase 4 dashboard verification.

Add or update tests where component behavior changes.

Verify that:

- Currency conversions remain correct.
- GBP values remain authoritative.
- Theme and currency selections persist.
- All five pages render.
- Filtering remains correct.
- RFM segment counts remain unchanged for the full dataset.
- Forecast evaluation metrics remain unchanged.
- CSV exports remain correct.
- No important KPI values are truncated.

Do not overwrite tracked verification reports unintentionally.

## 21. Browser-based visual verification

Perform actual browser inspection where supported.

Verify both themes at the required viewport widths.

Review at least:

- Overview.
- Sales Analytics.
- Customer Intelligence.
- Predictive Analytics.
- Data Quality.

Capture representative screenshots.

Inspect actual rendered output for:

- Layout problems.
- Clipped text.
- Overlapping elements.
- Unreadable legends.
- Excessive empty space.
- Broken controls.
- Unexpected horizontal scrolling.
- Poor chart contrast.

Do not claim visual verification if browser inspection was unavailable.

## 22. Documentation

Update relevant documentation to reflect meaningful UI changes.

Preserve existing methodology and provenance.

Record:

- Design improvements made.
- Files changed.
- Tests executed.
- Browser widths checked.
- Any known limitations.
- Before/after observations.
- Screenshots captured.

Avoid unnecessary documentation duplication.

## 23. Git delivery

After successful verification:

1. Review the diff for unrelated changes.
2. Commit the verified refinement to `phase-4`.
3. Push `phase-4`.
4. Update existing draft PR #2.
5. Confirm `main` remains unchanged.
6. Confirm the PR remains draft and unmerged.
7. Check GitHub CI status.

Do not merge or start Phase 5.

## 24. Final completion report

Provide:

### A. Summary of visual improvements
### B. Files changed
### C. Before/after design comparison
### D. Analytical integrity confirmation
### E. Automated test results
### F. Browser verification and screenshots
### G. Performance observations
### H. Known limitations
### I. Git commit and PR status
### J. Recommended next step

Clearly distinguish completed work from suggestions.

## Final instruction

Prioritize **professional visual quality, analytical clarity, and usability**.

Make meaningful refinements, not superficial changes for the sake of changing things.

Preserve Quantiva's existing identity, architecture, business logic, reproducibility, and local-first operation.

The desired result is a cohesive business intelligence dashboard that could be confidently demonstrated in a professional portfolio review.

**Begin with repository inspection and a concise refinement plan, then implement and verify the approved Phase 4 UI improvements.**