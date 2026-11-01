# User Interface and Interaction Specification

## 1. Design principles

- Professional CA-practice desktop software; restrained, consistent visual design.
- High information density without clutter. Financial data grids should be more prominent than decorative cards.
- Persistent project context: client, entity, project, scenario and selected calculation run should be visible.
- Keyboard-first data entry with tab navigation, copy/paste, Excel-style grid editing, undo for safe draft edits and clear save state.
- Hide optional sections until needed (historical mode, advanced tax, detailed sensitivity etc.).
- Use consistent units, currency formatting and negative number treatment.
- Do not use colour alone to communicate validation status.

## 2. Main application shell

### Global frame
- Left navigation rail with Dashboard, Clients, Entities, Projects, Knowledge Base and Settings.
- Main content workspace with page title, breadcrumbs and contextual actions.
- Top context strip: selected client/entity/project/scenario/period.
- Status area: saved/unsaved, validation count, latest calculation run and application version.

### Dashboard
- Search projects and clients.
- Recent projects, drafts, reports generated and pending review.
- Actions: New Project, Open Project, Import Project, Browse Knowledge.
- Sample/demo projects clearly labelled and kept separate from client records.

## 3. Project workspace navigation

Recommended project navigation:
1. Overview
2. Applicant & Promoters
3. Project Details
4. Project Cost
5. Means of Finance
6. Revenue
7. Operating Expenses
8. Fixed Assets & Depreciation
9. Loans
10. Working Capital
11. Historical Data (only when enabled)
12. Financial Statements
13. Schedules
14. Ratios & Appraisal
15. Scenarios
16. Validation & Review
17. Reports & Annexures

Navigation should show completion/validation indicators but must not imply that a completed form is necessarily professionally verified.

## 4. Screen-level requirements

### Client and entity screens
- Searchable list, create/edit/archive actions.
- Entity constitution selector controls visible extension fields.
- Entity members grid supports multiple persons, roles and effective dates.
- Identifier values masked in list view; reveal/edit requires deliberate interaction.
- Validation prompts for missing required identity fields but do not require unrelated personal information.

### Project creation wizard
Step 1: client and entity.  
Step 2: project name, industry, project nature and location.  
Step 3: dates, financial-year start and commercial operation date.  
Step 4: projection horizon (default 7 years).  
Step 5: historical data toggle (off by default).  
Step 6: scenario creation (Base Case default).  
Step 7: review and create.

Historical mode off: do not show historical years, historical import buttons or historical navigation. Historical mode on: reveal historical period count and historical statement entry/import.

### Project cost grid
Columns: Sr. No.; Cost Head; Description; Quantity; Unit; Rate; Basic Amount; GST Rate; GST Amount; Eligible ITC; Non-creditable Tax; Capitalised Amount; Cash Requirement; Source; Notes.

Actions: Add item, edit, duplicate, delete draft item, add custom head, import Excel, attach source, export grid. Provide live totals by category and project cost summary. Do not silently overwrite typed values when changing a head or tax treatment.

### Means of finance grid
Columns: Sr. No.; Source; Category; Proposed/Committed/Received; Amount; Expected Date; Linked Loan; Supporting Source; Notes. Show total sources, total project uses, funding gap/surplus, promoter margin and debt/equity calculation basis.

### Revenue screens
- Revenue stream list and add/edit wizard.
- Select forecast method; show only relevant driver fields.
- Period grid with years across columns or one selected stream's period rows, while preserving the standard horizontal financial statement style in reports.
- Show calculation preview and GST-exclusive/inclusive bridge.
- Every manual override requires confirmation, reason and source/assumption note.

### Expense screens
- Expense head, behaviour and method selector.
- Dynamic fields based on method.
- Year-wise grid with escalation/driver preview.
- Duplicate previous year, apply annual increase, apply percentage of revenue and manual override actions.
- Detect duplicate expense allocation and potentially double-counted drivers.

### Fixed asset screen
- Asset register with category, quantity, vendor, source, cost, ITC, capitalised amount, expected put-to-use date, book depreciation method, useful life, residual value and optional tax block reference.
- Separate tabs for book and tax schedules.
- Display asset roll-forward by year.

### Loan screen
- Facility summary cards/list and detailed editable facility form.
- Loan inputs include lender, sanctioned amount, disbursement(s), interest type/rate/effective dates, day-count basis, repayment frequency/method, tenure, moratorium and fees.
- Preview EMI and repayment schedule before saving.
- Full schedule grid: instalment, due date, opening balance, disbursement, payment, interest, principal, closing balance.
- Overrides require reason/source and show difference from calculated schedule.

### Working-capital screen
- Component-wise inventory/receivable/payable/other current asset/liability assumptions.
- Select holding days, turnover percentage, direct amount or approved bank method.
- Display selected base, formula, amount and source.

### Financial statements
- Tabular horizontal layout. A = Sr. No.; B = Note/Schedule Ref.; C = Particulars; D onwards = annual periods.
- Default D:J = Project Year 1–7.
- Freeze leading descriptive columns in grids; freeze header row.
- Support subtotals, totals, expandable detailed schedules and drill-down to calculation trace.
- Display source/assumption trace and formula explanation on row selection.
- Never allow direct editing of calculated results. Provide a controlled input override through the owning input module.

### Ratios and appraisal
- Year-wise ratio grid, with columns by projected year.
- Selecting a ratio shows formula, numerator, denominator, definitions, method and limitations.
- DSCR shows lender method and debt service components.
- Include charts only where useful; table remains the authoritative result.

### Validation and review
- Separate Errors, Warnings and Information.
- Filter by module and severity; select issue navigates to the relevant input.
- Overrides require reason and actor/time; only permitted warning rules may be overridden.
- Material errors block report approval by default.

### Report generation
- Choose report template, output type, calculation run and sections.
- Preview section list and period columns before generation.
- Include/exclude historical sections only when history enabled.
- Choose firm logo/branding and output folder.
- Generated files must be linked to the selected calculation run.

## 5. Grid behaviour

- Numeric editors use locale-aware display while storing exact Decimal values.
- Negative values display consistently in parentheses or a configurable accounting style.
- Blank is distinct from zero.
- Paste multiple cells from Excel with validation feedback.
- Sorting/filtering must not alter row identity or formula mapping.
- Do not rely on row number as a persistent identifier.
- Row additions and deletions must update validation and dependent calculations only after save/recalculate.

## 6. Error and confirmation design

Use clear messages that state: what is wrong, where, why it matters, and how to fix it. Destructive actions (delete source, remove a loan linked to funding, change projection horizon, disable historical mode) require a preview and confirmation if data will be hidden or affected. No destructive action should silently delete historical calculation runs or generated reports.
