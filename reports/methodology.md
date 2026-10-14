# Phase 1 methodology

## Purpose and boundary

Build a traceable transaction dataset before computing business metrics. This phase
validates the source and establishes analytical eligibility; it does not produce
EDA, forecasting, customer segments, SQL tables, or a dashboard.

## Data lineage

The source is the official UCI Online Retail workbook. Keep raw bytes immutable.
Download provenance records source URLs, UTC retrieval time, SHA-256, and byte size.
Inspection and cleaning reports record the actual workbook hash even for manual
imports. `source_row` is the Excel row number (first data row is 2); it links outputs
back to their raw observations. A policy version identifies the cleaning rules.

Parquet retains nullable identifiers, timestamps, and boolean eligibility flags
without CSV type inference. The output manifest hashes every derived file. Repeated
runs replace outputs; they never append records. Each individual write is atomic;
the set of output files is not one transaction. Run one preparation process at a
time and wait for completion before reading the files.

## Cleaning policy 1.0.0

1. Detect exact duplicates across all eight original columns **before** normalization.
   Keep the first occurrence and put every subsequent occurrence in the exclusion
   audit. There is no unique source line key, so this is an explicit assumption.
   Repeating an invoice or product alone is not grounds for removing a row.
2. Trim surrounding whitespace in text fields; keep invoice and product codes as
   strings. A customer identifier is valid if it is positive, finite, and integral;
   represent it as a nullable string. Never invent a customer or fill missing IDs
   with a shared pseudo-customer.
3. Quarantine rows with missing invoice/product codes, invalid timestamps, nonfinite
   or nonintegral quantities, zero quantities, negative/nonfinite prices, or
   C-prefixed invoices with nonnegative quantities. Preserve original values as
   text in `exclusions.parquet` with all applicable reasons.
4. Keep zero-price rows and missing descriptions in the ledger with explicit flags.
   Missing descriptions do not invalidate a transaction amount. Missing countries
   remain missing and flagged; later analytics must make unknown-country totals visible.
5. Classify each valid line by the following precedence:

| Type | Rule | Eligible for completed-sales revenue? |
| --- | --- | --- |
| cancellation | Invoice begins with C (case-insensitive), quantity negative | No |
| stock_adjustment_candidate | Other negative quantity with zero price | No |
| unlinked_negative | Other negative quantity with positive price | No |
| zero_value | Noncancelled positive quantity with zero price | No |
| completed_sale | Noncancelled positive quantity with positive price | Yes |

C-prefixed lines follow UCI's cancellation convention. The source does not establish
whether an item physically returned, or link every adjustment to its original sale.
Do not present inferred adjustments as confirmed returns. Signed amounts are
retained so a later net-revenue analysis can define its own scope transparently.
Completed sales are an operational eligibility definition, not evidence of payment
settlement, fulfillment, or accounting recognition. Product codes may also describe
postage, fees, or adjustments; no item catalogue has yet verified merchandise scope.

6. Calculate `line_revenue_gbp = Quantity × UnitPrice`, rounded to four decimal places
   to retain sub-penny source pricing. Values are float64 for analysis, not an
   accounting ledger; reconcile aggregations with a stated numerical tolerance.
   Do not trim extreme but structurally valid amounts without investigation.
7. Retain customers without IDs for aggregate sales; exclude them from future RFM
   and customer metrics. Customer analyses therefore describe an identifiable subset.
8. Preserve timestamps as timezone-naive source wall times. No timezone is supplied
   by the workbook. Do not silently localize or shift calendar dates.

## Statistical concepts

Missingness can create **selection bias**: known-ID customers may have different
spending behavior from anonymous purchases. Counting missing IDs is not enough to
prove their values are missing at random. Later EDA should compare both populations.

The median and quartiles describe typical values and spread without relying on a
normal distribution. Large gaps between the median and upper percentiles suggest a
heavy right tail. Wholesale orders and cancellation pairs may explain extreme
quantities; an outlier is not automatically an error.

Duplicated rows can inflate aggregates. Deduplication trades that risk against the
possibility of removing valid identical line items; Phase 2 should compare metrics
with and without deduplication as a sensitivity analysis.

Condition counts overlap: a cancellation can also be duplicated. Only the disjoint
final partition can be summed: **raw rows = cleaned ledger + duplicate exclusions +
quarantined nonduplicate rows**. The ledger itself partitions into five transaction types.

## Validation and next phase

Tests cover ingestion failure, schema validation, download preservation, category
precedence, invalid-record quarantine, anonymous sales, source immutability, and
idempotent output hashes. Small test fixtures are synthetic solely to exercise
code; all published quality findings come from the downloaded workbook.

The full-data validation script checks row reconciliation, unique source-row
coverage, eligibility rules, source hash consistency, and manifest integrity.
The source ends at midday on 9 December 2011, making that December incomplete.
December 2010 lies within the observation span but contains a Christmas gap;
later time-series analysis must avoid treating that final day as a full day or
claiming December-to-December growth from unequal periods. Calendar gaps require
investigation before equating them with zero demand.
