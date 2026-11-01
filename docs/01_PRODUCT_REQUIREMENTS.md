# Product Requirements Specification (PRS)

**Document version:** 1.0  
**Product:** Project Report Manager  
**Status:** Handoff specification; subject to design review before Phase 1.

## 1. Product summary

Project Report Manager is a Windows desktop tool for creating bank-oriented project reports and integrated financial projections. It combines client/entity records, project assumptions, costing, funding, operating forecasts, loan schedules, projected statements, appraisal ratios, validation and professional report generation.

It is not a spreadsheet wrapper. The core product is a reusable financial model whose calculations are independent of the interface and renderers.

## 2. Legal constitutions

Core constitutions:
- `INDIVIDUAL`: individual borrower/applicant not represented as a distinct business constitution.
- `PROPRIETORSHIP`: business carried on by an individual proprietor. The proprietor and business profile must be linked, but the system must not imply that a sole proprietorship is a separate incorporated legal person.
- `HUF`: HUF profile, Karta and relevant members.
- `PARTNERSHIP`: partnership deed, partners, profit-sharing ratio, capital/current accounts and deed-dependent appropriation inputs.
- `LLP`: LLPIN, designated partners, contribution, partner accounts and LLP agreement-dependent inputs.
- `PRIVATE_LIMITED`: CIN, directors, shareholders, authorised/paid-up share capital, reserves and company-specific funding accounts.

The data model must support additional constitutions later. Entity-specific fields should be conditional; do not collect information that is not needed for the selected entity or report.

## 3. Project types and industries

The engine is industry-neutral. Initial starter templates / acceptance cases:
1. Manufacturing — production capacity, capacity utilisation, yield, wastage, selling price, raw material and conversion costs.
2. Trading — quantity/turnover, purchase cost, gross margin, inventory, receivables and payables.
3. Hospital/clinic — beds, occupancy, procedures, average billing, departments and staff.
4. Hotel — rooms, occupancy, average daily rate, food/ancillary streams and seasonality.
5. Restaurant — covers/customers, average bill, operating days, food cost, delivery commissions and staffing.
6. EV charging — sessions, kWh/session, tariff, power cost, platform fee, charger uptime and other streams.
7. Transport/logistics — vehicles, trips, utilisation, distance, freight rate, fuel and maintenance.
8. Education — students, fee categories, collection rates, capacity, staffing and academic calendar.
9. Rental property — units, occupancy, rent per unit, escalation, deposits and maintenance.
10. Professional/IT services — staff/consultants, billable utilisation, billing rates, projects and collection cycle.

A template supplies input fields, suggested methods and help text only. It does not impose unreviewed assumptions or hardcode financial accounting.

## 4. Standard user workflow

1. Create/select client.
2. Create/select legal entity and maintain entity members/identifiers.
3. Create project and choose project nature, industry and business model.
4. Confirm commencement date, financial-year convention, currency and projection horizon (default seven years).
5. Optionally enable historical data; disabled by default.
6. Add promoter/management details, project location, implementation details and source documents.
7. Prepare project cost and means of finance.
8. Define revenue streams and projection methods.
9. Define expenses and cost behaviour.
10. Define fixed assets, depreciation policies and dates put to use.
11. Define one or more loan facilities and repayment terms.
12. Define working-capital assumptions.
13. Review assumptions and run validations.
14. Calculate scenario; review statements, schedules and appraisal.
15. Resolve material errors or document authorised overrides.
16. Approve calculation run and generate PDF, Word and Excel.

## 5. Projection and historical modes

### Default mode
- Seven annual projection years.
- Historical data entry, import, navigation and report sections hidden.
- The user may select 3, 5, 7, 10 or a custom number of years within a product-configured maximum.
- The year columns are generated dynamically; the default is Project Year 1–7.

### Optional historical mode
- Explicit project-level toggle.
- When enabled, show historical period configuration and historical P&L, Balance Sheet and Cash Flow input/import workflows.
- Historical period count can vary based on available data and lender requirements.
- Historical data must be clearly labelled as user-entered/imported and must not be silently treated as audited or verified.
- Historical data is stored separately from projected-period inputs and is included in reports only when selected.

## 6. Financial statement presentation

The default project-report layout is horizontal and year-wise:
- Column A: Sr. No.
- Column B: Note / Schedule Reference.
- Column C: Particulars.
- Columns D:J: Project Years 1–7.
- Header row: actual financial-year labels where known, otherwise Project Year 1, etc.

For other horizons, the number of period columns changes dynamically. The first three descriptive columns remain fixed. Excel should freeze the top heading row and columns A:C. PDF and Word should use landscape pages for wide statements and repeat table headers on subsequent pages.

## 7. Core modules and functional requirements

### Client/entity
- Create, edit, search, archive and reopen client/entity records.
- Support multiple entities per client and multiple projects per entity.
- Maintain multiple members with roles and effective dates.
- Capture identifiers only when needed. Sensitive identifiers must be protected.

### Project setup
- Project code/name, nature, industry, location, implementation timeline, commercial operation date, financial year start, currency and projection horizon.
- Project source register and document attachments.
- Project status and notes.

### Project cost
- Dynamic cost heads and user-defined subheads.
- Item-level quantity, unit, rate, base value, GST rate/amount, eligibility of ITC, non-creditable tax, capitalisable amount, payment timing, supplier and source.
- Separate capital expenditure, pre-operative costs, deposits, contingencies and initial working-capital margin.
- Reconcile total project uses and total funding sources.

### Means of finance
- Promoter/owner/partner/shareholder contribution, term loans, unsecured loans, subsidy/grant, working capital facilities and other configured sources.
- Link loan funding lines to loan facilities.
- Identify proposed, committed and received sources.
- Show funding gap/surplus and debt-equity calculation basis.

### Revenue
- Multiple revenue streams.
- Methods: capacity × utilisation × output × selling price; units × price; customer/occupancy-based; rental; growth rate; manual entry; other registered methods.
- GST inclusive/exclusive price setting with tax treatment and effective date.
- Annual escalation, ramp-up, operating days, seasonal factors and explicit manual override.
- Display calculation bridge: drivers → gross billing → GST → net revenue.

### Expenses
- Fixed, variable and semi-variable behaviour.
- Methods: fixed amount; growth; percentage of revenue; cost per unit; capacity-based; headcount-based; manual input.
- Direct costs, employee costs, administration, sales/distribution, repairs, insurance, rent, utilities, professional fees, platform/commission and other heads.
- Expense assumptions can be varied by year and scenario.

### Fixed assets and depreciation
- Asset-wise additions, dates, supplier/source, ITC treatment, capitalised cost, useful life, depreciation method, residual value and disposal.
- Separate book depreciation and tax-depreciation reference schedules.
- No statutory depreciation defaults without applicable source/version.

### Loans
- Multiple facilities and staged disbursements.
- Fixed/floating rates, effective dates and reset history.
- EMI, equal-principal, interest-only/moratorium and lender-confirmed custom schedules.
- Monthly/quarterly/annual frequencies where permitted.
- Day-count and interest calculation basis recorded.
- Prepayment/foreclosure and schedule overrides with reason/source.
- Interest and principal feed linked statements appropriately.

### Working capital
- Inventory/raw materials/WIP/finished goods, receivables, payables, expense creditors, statutory balances and cash assumptions.
- Holding days, turnover percentages, direct amount overrides and selected method.
- Optional bank-specific working-capital methods; methodology and source disclosed.

### Statements and ratios
- Projected P&L, Balance Sheet and Cash Flow.
- Fixed asset, depreciation, loan, interest, working-capital, funding and capital schedules.
- Liquidity, solvency, profitability, activity/efficiency, debt-service and project-viability metrics.
- Every ratio exposes formula, numerator, denominator, period, interpretation and limitations.

### Scenarios
- Base, conservative, optimistic and custom scenarios.
- Copy scenario and selectively override drivers.
- Compare revenue, EBITDA, PAT, cash balance, debt outstanding, DSCR, break-even, payback, NPV and IRR.

### Output
- PDF, editable Word and Excel financial model.
- Firm branding and reusable report templates.
- Bank-specific section/order and appraisal formula configurations.
- Annexure register and source-document listing.

## 8. Non-functional requirements

- Offline core functionality.
- Responsive UI; long-running calculations and exports must not freeze the interface.
- Keyboard navigation, paste from Excel, column resizing, sorting and filtering in financial grids.
- Save indicators, autosave or recoverable drafts, clear error messages and safe shutdown.
- No external transfer of client data unless explicitly enabled.
- Logs must omit sensitive personal and financial identifiers.
- Backup/restore must include database and managed attachments.
- Reproducible calculation and report history.
- Installer must support a clean Windows installation and documented data location.

## 9. Out-of-scope in first release

- Automated income-tax return filing or GST return filing.
- Statutory audit sign-off or assurance.
- Automatic legal opinion or unreviewed AI-generated compliance advice.
- Mandatory cloud accounts, external APIs or telemetry.
- Concurrent LAN users (future version only).

## 10. Requirements still needing product decisions

- Exact financial-year handling for projects starting mid-year, including stub/partial first period.
- Whether the initial output includes a standardised cash flow format, bank-specific format or both.
- Whether Excel outputs should be formula-driven or values-driven with traceable formulas; recommended: formulas for transparent schedules where stable, but calculation engine outputs remain authoritative.
- Exact statutory / accounting framework defaults by entity and project purpose.
- The user-editable report template configuration experience.
