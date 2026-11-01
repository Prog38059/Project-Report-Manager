# Validation, Reconciliation and Test Catalogue

**Purpose:** Define how correctness is proved. A working GUI is not evidence that the financial model is correct.

## 1. Validation severity

- **ERROR:** A material structural or calculation problem prevents a reliable calculation or final report. Example: missing required period, invalid loan schedule, funding mismatch where the chosen template requires full funding, or unreconciled Balance Sheet.
- **WARNING:** The calculation can proceed, but a material assumption is missing, unverified or unusual. Example: rent excluded, civil works not quantified, tax rate not verified, projected utilisation unsupported.
- **INFO:** Disclosure or optional improvement. Example: optional historical statements not supplied.

Every validation result must include code, severity, message, affected record/period, suggested action, source/rule version and whether the user may resolve or override it. Overrides require a reason, user label and timestamp. Errors that compromise arithmetic or data integrity must not be overridable in the initial release.

## 2. Core invariants

1. `total_project_uses = total_funding_sources` when the scenario is marked fully funded. Otherwise the funding gap must be shown explicitly.
2. Loan opening + disbursement - principal repaid = closing principal, per facility and period.
3. Principal repayment must not exceed available outstanding principal, subject to documented lender-specific treatment.
4. Book fixed-asset roll-forward: opening gross block + additions - disposals = closing gross block.
5. Accumulated depreciation and net book value must reconcile to the asset roll-forward.
6. Cash flow opening cash + net movement = closing cash.
7. Balance Sheet: assets = equity + liabilities, within the defined paise tolerance (normally zero paise after posting/rounding rules).
8. Retained earnings / capital roll-forwards must reconcile to PAT, distributions/drawings, contributions and other approved movements.
9. Output GST, net revenue and gross billing must reconcile to the selected tax-inclusive/exclusive method.
10. Eligible input tax credit must not exceed eligible tax recorded for the relevant input transaction/cost item.
11. Every projected statement result must have a period, line code, calculation run and trace metadata.
12. Periods must not overlap unintentionally and must identify stub periods correctly.
13. Report renderers must not change the authoritative numeric values.

## 3. Unit-test catalogue

### 3.1 Money and rounding
- Decimal arithmetic; no binary float inputs to financial domain functions.
- Convert rupees to paise and back without unintended rounding loss.
- Test half-up / selected rounding modes at posting boundaries.
- Test negative values only for semantically permitted lines.

### 3.2 Revenue and indirect tax
- Quantity × rate.
- Capacity × utilisation × unit price.
- Customer count × average bill.
- Occupancy-based revenue.
- Turnover growth over multiple periods.
- Manual override with reason/source.
- GST-inclusive and GST-exclusive single-rate examples.
- Exempt / nil-rated / zero-rated / out-of-scope cases.
- Mixed or multi-rate supplies must return a component-wise result or REVIEW_REQUIRED, not silently use one rate.

### 3.3 Expenses
- Fixed amount.
- Escalation percentage.
- Percentage of revenue.
- Cost per unit.
- Capacity-based expense.
- Headcount-based expense.
- Manual override.
- Detect double counting where the same cost driver is mapped to two expense heads, where configured.

### 3.4 Loan engine
- Reducing-balance EMI.
- Equal-principal schedule.
- Interest-only period.
- Moratorium with interest paid, capitalised or accumulated.
- Multiple disbursements on different dates.
- Rate reset with effective date.
- Monthly, quarterly and annual repayment frequency.
- Day-count convention variations.
- Final instalment adjustment and rounding residue.
- Prepayment and custom schedule override.
- Annual aggregation by financial year and stub period.

### 3.5 Fixed assets and depreciation
- SLM with full year.
- SLM with partial period.
- WDV with partial period.
- Units-of-production where enabled.
- Residual value floor.
- Addition, commissioning and disposal.
- Separate book and tax depreciation.
- Asset under construction not depreciated before the applicable put-to-use/available-for-use rule selected for the accounting framework.

### 3.6 Working capital
- Holding-days calculation by correct cost/sales/purchase base.
- Receivables based on credit sales and collection days.
- Payables based on eligible purchases/expenses and credit days.
- Inventory components with distinct holding periods.
- Opening and closing movements flowing to cash flow.
- Working capital facility and interest where enabled.

### 3.7 Statements and entity movements
- P&L subtotal reconciliation.
- Balance Sheet equation.
- Cash Flow reconciliation.
- Proprietor capital and drawings.
- HUF capital movement.
- Partner-wise capital/current account and profit allocation.
- LLP partner contribution and appropriation based on agreement inputs.
- Company share capital, reserves and distribution movement.
- Tax provision is separately identified from cash tax paid where required.

### 3.8 Ratios and project appraisal
- Current ratio, quick ratio and net working capital.
- Debt-equity variants with clear numerator/denominator definitions.
- Interest coverage.
- EBITDA margin, PAT margin, ROCE and ROE.
- Inventory, receivable, payable and asset turnover.
- DSCR methodology variants.
- Break-even and margin of safety.
- Payback.
- NPV and IRR with rate/period/date conventions.
- Zero denominators and missing inputs produce a clear N/A / validation result, never an unhandled exception or fabricated zero.

## 4. Golden test fixtures

The repository must contain human-readable, independently checkable fixtures in `tests/financial_test_cases/`. Each fixture defines inputs, expected outputs, formula/method, precision and source/assumption note.

Minimum starter fixtures:

### Fixture A — simple quantity × price revenue
- Quantity: 100 units.
- Price: ₹250 per unit, exclusive of indirect tax.
- Expected net revenue: ₹25,000.
- Expected output tax: not calculated unless a rate and tax treatment are explicitly supplied.

### Fixture B — inclusive-tax decomposition
- Gross inclusive amount: ₹10,500.
- Assumed single tax rate solely for this arithmetic test: 5%.
- Expected net amount: ₹10,000.
- Expected tax amount: ₹500.
- This fixture tests arithmetic only; it is not a statement that the rate applies to any real supply.

### Fixture C — SLM depreciation
- Capitalised cost: ₹1,000,000.
- Residual value: ₹100,000.
- Useful life: 9 years.
- Full-year depreciation: ₹100,000.
- No tax depreciation conclusion is implied.

### Fixture D — working capital identity
- Current operating assets: ₹1,200,000.
- Current operating liabilities: ₹450,000.
- Net working capital: ₹750,000.

### Fixture E — simple loan interest period
- Opening loan: ₹1,000,000.
- Annual nominal rate for a one-month periodic-rate test: 12% / 12.
- One-month interest using a 1% periodic rate: ₹10,000.
- Principal/payment details are deliberately omitted; this is an interest calculation fixture, not an EMI fixture.

An EMI golden fixture must be calculated independently and recorded with the precise convention (monthly rate, instalment timing, rounding and payment dates) before the loan-engine implementation is approved. Do not copy an expected value from the function being tested.

## 5. Integration tests

- Create client → entity → project → scenario → seven periods.
- Historical data disabled: no historical input screens/periods in the ordinary workflow.
- Enable historical mode: historical entry/import sections become available without changing projection period IDs.
- Enter project costs and funding; verify reconciliation.
- Enter two revenue streams and multiple expenses; run calculations.
- Add two loan facilities with different repayment methods; verify aggregated finance cost and closing debt.
- Run fixed-asset additions and depreciation.
- Generate statements and assert all core invariants.
- Modify an assumption and create a second calculation run; first run and its reports remain unchanged.
- Render PDF, Word and Excel from the same run and compare all financial totals.
- Backup and restore a project with attachments; verify attachment hashes.

## 6. UI acceptance tests

- Seven-year default creates seven projection columns.
- Horizontal financial grids have A = serial, B = note reference, C = particulars, D onward = period values.
- Freeze panes preserve columns A–C while scrolling horizontally in Excel.
- Keyboard tab navigation, copy/paste, row insert/delete and grid validation behave predictably.
- Historical inputs remain hidden until user enables the feature.
- Save state and unsaved changes are visible.
- Validation messages navigate to the affected input.
- All sample/demo projects are visibly labelled and never mixed with client projects.

## 7. Release gates

A phase cannot be accepted based only on a screenshot or successful application launch. The agent must report:
- Exact test command(s).
- Number of tests passed/failed/skipped.
- Test fixture references.
- Financial reconciliation results.
- Known defects and unresolved warnings.
- Database migration and rollback evidence, if relevant.
- Files changed and screenshots/output samples where useful.
