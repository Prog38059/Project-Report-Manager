# Report Output Specification

**Purpose:** Define the output contract for professional project reports and supporting financial models.

## 1. General output principles

1. PDF, Word and Excel must be rendered from the same immutable `calculation_run` and a shared report-data object.
2. Renderers must not independently recalculate financial values. A renderer may format, group, subtotal or pivot approved result lines only according to registered presentation definitions.
3. Every output must record project, entity, scenario, calculation-run ID, report-template code/version, generation timestamp and file hash.
4. The generated report must identify assumptions, exclusions, source references and unresolved warnings that materially affect the projections.
5. Never label projections as audited/statutory financial statements. Use an explicit title such as “Projected Financial Statements” or “Financial Projections for Project Appraisal”.
6. All amounts must use one configured currency and a consistent display convention. Indian number grouping is the default for INR.

## 2. Standard report book structure

The template is configurable. The default project-report sequence is:

1. Cover page and document control.
2. Table of contents.
3. Executive summary and key project parameters.
4. Applicant, entity and promoter profile.
5. Existing business / historical performance section (omit completely unless historical mode is enabled).
6. Project background, objectives and nature.
7. Industry / market / demand information, with source and verification status.
8. Location, site, infrastructure and technical details.
9. Manufacturing / operating process and capacity, as applicable.
10. Implementation schedule and key milestones.
11. Project cost with itemised cost and tax/ITC treatment.
12. Means of finance and funding-gap reconciliation.
13. Revenue assumptions and stream-wise calculations.
14. Operating-cost assumptions and projection methodology.
15. Projected Profit & Loss Account.
16. Projected Balance Sheet.
17. Projected Cash Flow Statement.
18. Fixed-asset and depreciation schedules.
19. Loan-wise repayment schedules and consolidated debt profile.
20. Working-capital assessment and supporting schedules.
21. Financial ratios and lender-configured DSCR.
22. Break-even, payback, NPV, IRR and sensitivity analysis where enabled.
23. Risks, mitigants, assumptions and exclusions.
24. Conclusion / appraisal observations.
25. Annexures and source-document index.

Sections with no relevant data must be omitted or marked “Not applicable” only where the selected bank template requires it. Do not generate empty pages or headings with blank tables.

## 3. Mandatory horizontal financial statement layout

The default annual financial statement layout is horizontal:

| Column | Content |
|---|---|
| A | Sr. No. / blank for section headings |
| B | Note / schedule reference |
| C | Particulars |
| D onward | Project Year 1 through Project Year N |

For the default seven-year model, Project Years 1–7 occupy D:J. For other configured horizons, the number of year columns changes dynamically. Do not hardcode seven result fields in the database.

The same orientation applies to the annual P&L, Balance Sheet, Cash Flow Statement, depreciation schedules, working-capital schedules, ratios and other annual schedules where comparison by year is meaningful. Monthly loan schedules use one row per instalment with columns such as instalment number, due date, opening balance, disbursement, interest, principal, payment and closing balance.

### Period headings

- Show actual financial-year labels (e.g. FY 2027-28) where the period corresponds to a financial year.
- Show explicit date ranges for stub periods and non-standard periods.
- Show whether values represent a full financial year, partial first year, monthly period or annualised amount.
- Do not label a partial period as a full year without clear disclosure.

## 4. Excel output requirements

- One workbook per generated financial model, with an optional separate narrative workbook only if requested.
- Suggested sheets: `Cover & Summary`, `Assumptions`, `Project Cost`, `Means of Finance`, `Revenue`, `Expenses`, `Fixed Assets`, `Depreciation`, `Loan Summary`, `Loan Schedules`, `Working Capital`, `Projected P&L`, `Projected Balance Sheet`, `Projected Cash Flow`, `Ratios & DSCR`, `Break-even & Returns`, `Scenario Comparison`, `Validation`, `Source Register`.
- The user may select a reduced or custom sheet set; essential calculation support should not be deleted from the source workbook by default.
- Financial statements use columns A–C for description and D onward for periods. Freeze panes at D and the first row beneath headings; keep columns A–C visible while scrolling through years.
- Use Excel formulas for transparent presentation subtotals only when useful, but the authoritative calculation remains the engine result. Add a methodology note where the workbook contains formula-driven supplementary calculations.
- Do not use volatile formulas or hidden plug values. Do not hide material assumptions or warnings.
- Set print areas, repeat header rows, page orientation, scaling and margins. Wide annual statements should use landscape orientation.
- Apply consistent number formats: zero as dash where appropriate, negative values in parentheses, percentages with defined decimals, dates in a clear format, and amounts with currency units in headings.
- Avoid merged cells inside data grids. Merged title cells are permitted in presentation headers.
- Add filters to tabular schedules where practical, but do not convert statement grids into Excel Tables if this breaks the required horizontal presentation.

## 5. Word and PDF output requirements

- Use A4 as the default page size, configurable by template.
- Narrative pages normally use portrait orientation; wide year-wise financial statements and schedules use landscape sections/pages.
- Repeat table header rows across pages. Keep section headings with the first paragraph/table row where possible.
- Provide page numbers, report name, project/entity name and confidentiality marking in headers/footers as configured.
- Use a professional restrained visual theme. Avoid excessive colour, decorative cards or oversized headings.
- Provide an automatically generated table of contents and consistent heading hierarchy in Word.
- PDF must preserve table readability and embedded fonts as permitted by the selected libraries/licences.
- Do not split a single financial statement line across pages. Long tables may break between rows with repeated headers.

## 6. Charts and visual analysis

Charts are supporting visuals, not substitutes for tabular statements. Candidate charts:
- Revenue and EBITDA trend.
- PAT trend.
- Project funding mix.
- Debt outstanding and repayment profile.
- DSCR by year.
- Break-even / capacity utilisation.
- Scenario comparison.

Every chart must state units, period basis and source calculation run. Do not use 3D charts or misleading axes. Do not show charts where relevant data is missing or not meaningful.

## 7. Template and branding configuration

A report template may define:
- Template code, name, version and entity / project applicability.
- Section inclusion, order and labels.
- Statement-line presentation mappings.
- Page size, orientation, margins, fonts, theme and header/footer.
- Required disclosures and bank-specific schedules.
- Signature / declaration blocks where requested, but never invent a professional certification or audit opinion.

Firm branding (logo, name, address, contact details) must be optional and user-configurable. Keep branding separate from financial calculations.

## 8. Output reconciliation checks

Before final export:
1. Confirm all output values trace to one selected calculation run.
2. Compare key statement and schedule totals across PDF, Word and Excel data models.
3. Verify P&L, Balance Sheet and Cash Flow headings, period labels and currency.
4. Verify loan balances and total principal/interest tie to loan schedules.
5. Verify every table fits the page or is intentionally split with repeated headers.
6. Check the report template version and report file hash are stored.
7. Display validation warnings and key assumptions in the report where material.
