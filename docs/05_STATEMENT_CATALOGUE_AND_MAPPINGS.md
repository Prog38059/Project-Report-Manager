# Financial Statement Line Catalogue and Entity Presentation Mapping

## 1. Purpose

Define stable line codes separately from their displayed labels, order and entity-specific presentation. The calculation engine works with stable line codes; report templates decide labels, ordering, grouping and inclusion.

## 2. Horizontal layout contract

Default annual output:

| Column | Role | Content |
|---|---|---|
| A | SERIAL | Sr. No. / blank on headings and subtotals |
| B | NOTE_REF | Schedule/note reference |
| C | PARTICULARS | Account / schedule / ratio description |
| D | PERIOD_1 | Project Year 1 / actual FY label |
| E | PERIOD_2 | Project Year 2 |
| F | PERIOD_3 | Project Year 3 |
| G | PERIOD_4 | Project Year 4 |
| H | PERIOD_5 | Project Year 5 |
| I | PERIOD_6 | Project Year 6 |
| J | PERIOD_7 | Project Year 7 |

The period column count is dynamic. For a five-year project, columns D:H are used; for ten years, D:M. The database does not store a separate field for each year. It stores line code + period ID + amount and the renderer pivots to columns.

## 3. Profit & Loss line catalogue

Initial line codes (the exact mapping may vary by chosen report format):

| Line code | Default display label | Kind | Notes |
|---|---|---|---|
| `PL_REV_OPERATIONS` | Revenue from operations | INPUT/SUBTOTAL | Net of GST where applicable to report presentation |
| `PL_OTHER_INCOME` | Other income | INPUT | Include only supported income streams |
| `PL_TOTAL_INCOME` | Total income | TOTAL | Sum of revenue and other income |
| `PL_DIRECT_MATERIAL` | Cost of materials / direct costs | INPUT | Industry-specific sublines permitted |
| `PL_PURCHASES` | Purchases / cost of goods sold | INPUT | Trading / manufacturing mapping |
| `PL_GROSS_PROFIT` | Gross profit | SUBTOTAL | Include only where meaningful |
| `PL_EMPLOYEE_COST` | Employee benefit expenses | INPUT | Salaries, wages and staff costs |
| `PL_POWER_FUEL` | Power and fuel | INPUT | Can be split by expense subhead |
| `PL_REPAIRS` | Repairs and maintenance | INPUT | Include CAMC where applicable |
| `PL_RENT` | Rent and lease expense | INPUT | Accounting treatment may differ by framework |
| `PL_SELLING` | Selling and distribution | INPUT | Commission, freight, marketing etc. |
| `PL_ADMIN` | Administrative and other operating expenses | INPUT | Expand into detailed schedule |
| `PL_PLATFORM_FEES` | Platform / service fees | INPUT | E.g. EV charging platform fee |
| `PL_OTHER_OPERATING` | Other operating expenses | INPUT | Must avoid double count |
| `PL_EBITDA` | EBITDA | SUBTOTAL | Operating result before depreciation/amortisation, interest and tax; definition configurable |
| `PL_DEPRECIATION` | Depreciation and amortisation | INPUT/CALCULATED | From asset schedule |
| `PL_EBIT` | EBIT | SUBTOTAL | EBITDA less depreciation/amortisation |
| `PL_FINANCE_COST` | Finance costs | INPUT/CALCULATED | From loan schedule / other finance sources |
| `PL_PBT` | Profit before tax | SUBTOTAL | Before tax provision |
| `PL_CURRENT_TAX` | Current tax / estimated tax provision | INPUT/CALCULATED | Projection estimate, not return computation |
| `PL_DEFERRED_TAX` | Deferred tax | INPUT/CALCULATED | Excluded unless separately implemented and supported |
| `PL_PAT` | Profit after tax | TOTAL | PBT less tax expense |

Do not force every industry to show all lines. A statement template selects appropriate lines and labels.

## 4. Balance Sheet line catalogue

### Equity / capital and liabilities
- `BS_OWNER_CAPITAL` — Proprietor / owner capital.
- `BS_HUF_CAPITAL` — HUF capital.
- `BS_PARTNER_CAPITAL` — Partners' capital accounts.
- `BS_PARTNER_CURRENT` — Partners' current accounts.
- `BS_SHARE_CAPITAL` — Share capital.
- `BS_SECURITIES_PREMIUM` — Securities premium.
- `BS_RESERVES` — Reserves and surplus.
- `BS_RETAINED_EARNINGS` — Retained earnings / accumulated profit or loss.
- `BS_LONG_TERM_BORROWINGS` — Long-term borrowings.
- `BS_CURRENT_MATURITIES` — Current maturities of long-term debt.
- `BS_SHORT_TERM_BORROWINGS` — Short-term borrowings / working-capital facilities.
- `BS_TRADE_PAYABLES` — Trade payables.
- `BS_STATUTORY_DUES` — Statutory liabilities.
- `BS_OTHER_CURRENT_LIABILITIES` — Other current liabilities.
- `BS_PROVISIONS` — Provisions.
- `BS_TOTAL_EQUITY_LIABILITIES` — Total equity and liabilities.

### Assets
- `BS_GROSS_FIXED_ASSETS` — Gross fixed assets.
- `BS_ACCUM_DEPRECIATION` — Accumulated depreciation / amortisation.
- `BS_NET_FIXED_ASSETS` — Net fixed assets.
- `BS_CWIP` — Capital work-in-progress.
- `BS_NON_CURRENT_INVESTMENTS` — Non-current investments.
- `BS_INVENTORY` — Inventory.
- `BS_TRADE_RECEIVABLES` — Trade receivables.
- `BS_CASH_BANK` — Cash and bank balances.
- `BS_LOANS_ADVANCES` — Loans and advances.
- `BS_GST_ITC_RECEIVABLE` — GST/indirect tax credit receivable, where applicable and supported.
- `BS_OTHER_CURRENT_ASSETS` — Other current assets.
- `BS_TOTAL_ASSETS` — Total assets.
- `BS_BALANCE_CHECK` — Assets less equity and liabilities; must equal zero or display a validation error.

Line mapping rules must specify whether assets/contra-assets use positive or negative stored signs and how they display. Prefer a consistent signed amount convention and explicit normal-balance metadata.

## 5. Cash Flow line catalogue

### Operating activities (indirect method initial scope)
- `CF_PL_BEFORE_TAX`
- `CF_DEPRECIATION_ADD_BACK`
- `CF_FINANCE_COST_ADJUSTMENT`
- `CF_OTHER_NON_CASH_ADJUSTMENTS`
- `CF_CHANGE_IN_INVENTORY`
- `CF_CHANGE_IN_RECEIVABLES`
- `CF_CHANGE_IN_PAYABLES`
- `CF_CHANGE_IN_OTHER_OPERATING_BALANCES`
- `CF_TAX_PAID`
- `CF_NET_OPERATING`

### Investing activities
- `CF_FIXED_ASSET_PURCHASES`
- `CF_FIXED_ASSET_DISPOSALS`
- `CF_INVESTMENT_PURCHASES`
- `CF_INVESTMENT_SALES`
- `CF_NET_INVESTING`

### Financing activities
- `CF_CAPITAL_CONTRIBUTION`
- `CF_SHARE_ISSUE`
- `CF_LOAN_DRAWDOWN`
- `CF_LOAN_PRINCIPAL_REPAID`
- `CF_DIVIDENDS_DISTRIBUTIONS`
- `CF_OTHER_FINANCING`
- `CF_NET_FINANCING`

### Cash reconciliation
- `CF_NET_CHANGE_CASH`
- `CF_OPENING_CASH`
- `CF_CLOSING_CASH`

Interest and tax classification in cash flow must be selected according to the applicable presentation framework/template and disclosed. The model must not silently use different classifications between outputs.

## 6. Schedule catalogue

- Project cost and means of finance.
- Revenue by stream and driver.
- Expense by head and projection method.
- Fixed asset gross block and accumulated depreciation.
- Book depreciation by asset.
- Tax depreciation reference schedule (separate).
- Loan facility summary and complete repayment schedule.
- Interest schedule by lender/facility.
- Working-capital component schedule.
- Promoter/partner capital and current accounts.
- Company equity movement schedule where relevant.
- Tax assumptions and estimated tax schedule.
- DSCR and ratio schedules.
- Break-even / payback / NPV / IRR schedules.

## 7. Entity-specific mapping principles

| Entity | Equity/capital presentation | Entity-specific logic to support |
|---|---|---|
| Individual | Individual capital / funds introduced | Personal applicant vs business-project profile; do not collect irrelevant personal information |
| Proprietorship | Proprietor's capital/current account | Capital introduced, drawings and current-year profit |
| HUF | HUF capital | Karta/member information as applicable; do not treat member capital as company share capital |
| Partnership | Partner-wise capital/current accounts | Contributions, drawings, remuneration/interest if agreement and tax assumptions support, profit allocation |
| LLP | Partner-wise contribution/current accounts | LLP agreement inputs and profit allocation |
| Private Limited Company | Share capital, premium, reserves/surplus | Share issues, reserves, retained earnings and distributions |

Entity constitution alone does not determine the full accounting framework or statutory presentation. The project must select a reporting basis/template; the application can warn if a combination appears inconsistent, but must not claim statutory compliance automatically.

## 8. Mapping table behaviour

The implementation should seed stable line codes and default mappings. Users may customise report labels, note references, line visibility and order in a report template without changing the underlying line code or engine formula. Custom line items must be assigned a stable custom code and explicitly mapped to a statement category.
