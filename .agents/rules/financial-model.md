---
trigger: glob
globs: "app/domain/financial_model/**/*.py, app/domain/loan_engine/**/*.py, app/domain/depreciation_engine/**/*.py, app/domain/working_capital_engine/**/*.py, app/domain/tax_engine/**/*.py, app/domain/ratio_engine/**/*.py, tests/financial_test_cases/**/*.py"
description: "Apply when implementing or changing financial calculations, loans, depreciation, tax, working capital, ratios or their tests."
---

# Financial Model Rules

- Read `docs/04_FINANCIAL_MODEL_SPECIFICATION.md`, `docs/05_STATEMENT_CATALOGUE_AND_MAPPINGS.md`, `docs/08_VALIDATION_AND_TEST_CATALOGUE.md` and relevant ADRs before editing.
- Use `Decimal` for calculations and integer paise for persisted money. Do not use binary floats for financial values.
- Keep all domain calculations independent of PySide6, ORM entities and document renderers.
- Do not invent accounting/tax/lender treatment. If the method is open, stop and raise an ADR decision with options.
- Do not hardcode current tax rates, GST rates, depreciation percentages or lender thresholds without sourced, effective-dated rules.
- Distinguish revenue, gross customer collection, output tax, eligible ITC, capitalised cost, cash paid and accounting expense.
- Loan principal is not a P&L expense. Keep finance cost separate from principal cash flows.
- Keep book depreciation separate from tax depreciation.
- Preserve exact input, formula method, rounding boundary and calculation trace for every material result.
- Add or update an independently calculated golden fixture for each formula change. Run focused tests and full financial regression tests.
- A Balance Sheet must reconcile through genuine movements. Never add a plug/suspense line to force agreement.
