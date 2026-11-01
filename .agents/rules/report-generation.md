---
trigger: glob
globs: "app/reporting/**/*.py, app/domain/report_data/**/*.py, tests/reporting/**/*.py"
description: "Apply when implementing PDF, Word, Excel report rendering, report-data objects, statement presentation or report templates."
---

# Report Generation Rules

- Read `docs/05_STATEMENT_CATALOGUE_AND_MAPPINGS.md`, `docs/07_REPORT_OUTPUT_SPECIFICATION.md` and `docs/08_VALIDATION_AND_TEST_CATALOGUE.md` before changes.
- PDF, Word and Excel must consume the same immutable report-data object for one calculation run.
- Renderers format and present results; they do not independently recalculate financial figures.
- Default annual statement layout: A = serial, B = note reference, C = particulars, D onward = periods. Seven years occupy D:J.
- Period columns are dynamic; do not assume seven years in the database or hardcode seven result fields.
- Show actual financial-year headings and clearly identify stub/partial periods.
- Wide statements use landscape layout and readable column widths. Excel freezes columns A:C and repeats print headers.
- Do not hide assumptions, material exclusions, warnings or data-source qualifications.
- Do not label project projections as audited or statutory financial statements.
- Reconcile key totals and period labels across PDF, Word and Excel outputs.
