# Financial Model Specification and Calculation Contracts

**Purpose:** Define the intended calculation behaviour. This is not a statutory accounting or tax opinion. Where the correct treatment depends on entity, framework, lender, contract or law, expose a selectable/configurable method, record the source and require professional review.

## 1. General calculation rules

1. Use `Decimal` for all financial/rate calculations; use integer paise for persisted money.
2. Maintain full precision internally. Round to paise at defined posting/display boundaries, not after every intermediate operation.
3. A calculation run must use one frozen input snapshot and one engine version.
4. Store unrounded driver values and rounded posted amounts separately where relevant.
5. Every calculated result must be traceable to formula code, inputs and assumptions.
6. Support negative values only where semantically valid; validate quantity, rates, days, percentages and loan balances.
7. No formula may silently substitute zero for missing data unless the field definition explicitly states that zero is a valid default.
8. Distinguish cash timing, accounting recognition, tax treatment and lender appraisal treatment.

## 2. Calculation pipeline

Recommended ordered pipeline:

1. Load project, scenario, period definitions and versioned input snapshot.
2. Validate input completeness, dimensions, effective dates and cross-references.
3. Calculate project costs, eligible ITC, non-creditable taxes and funding gap.
4. Calculate revenue stream drivers, gross billing, indirect tax and net operating revenue.
5. Calculate direct and operating expense forecasts.
6. Calculate fixed-asset roll-forward and book depreciation.
7. Calculate loan disbursements, opening balances, interest, repayments and closing balances.
8. Calculate working-capital investment and release by period.
9. Prepare P&L before tax and entity-specific appropriation schedules.
10. Calculate configured tax estimate / provision; retain tax assumptions and limitations.
11. Prepare P&L after tax, retained earnings/capital movements, Balance Sheet and Cash Flow.
12. Calculate appraisal metrics and ratios using the selected methodology.
13. Run reconciliations and save outputs/validation results.
14. Approve the calculation run before final report generation.

Circular formulas are out of scope for the initial engine. If tax depends on interest, interest on cash sweeps, or repayment depends on cash available, use a documented non-circular modelling approach or flag the feature for a later approved phase.

## 3. Revenue engine

Each revenue stream has a method and period-specific drivers. The calculation service returns at least gross billing, indirect tax amount, net revenue, units and calculation trace.

### 3.1 Supported methods

**Capacity × utilisation × rate**

`Output units = Rated capacity per operating period × Utilisation % × Operating periods`  
`Gross billing = Output units × Selling price per unit`

The exact definition of capacity and operating periods must be specified by the selected industry method (e.g. sessions/day × days/month, production tonnes/year, room nights/year). Prevent multiplying days twice.

**Units × price**

`Gross billing = Quantity sold × Selling price per unit`

**Customers × average bill**

`Gross billing = Number of customers × Average bill per customer`

**Occupancy-based**

`Occupied units = Available unit-days × Occupancy %`  
`Gross billing = Occupied units × Average rate per occupied unit`

**Rental units**

`Gross rent = Rentable units × Occupancy % × Rent per unit per period`

**Headcount / billable utilisation**

`Billable hours = Available hours × Billable utilisation %`  
`Gross billing = Billable hours × Billing rate`

**Turnover growth**

`Gross billing(period n) = Gross billing(period n-1) × (1 + growth rate)`

**Manual**

User enters gross billing or net revenue, with an explicit indication of whether input is GST-inclusive or GST-exclusive. Store override reason and source.

### 3.2 Indirect tax / GST treatment

The selected revenue stream must declare tax treatment: taxable inclusive, taxable exclusive, exempt, nil-rated, zero-rated, out-of-scope, not applicable or review required. Applicable tax rate(s) and effective dates must be sourced and reviewed.

For one taxable rate `t` and a GST-inclusive amount `G`:

`Net revenue = G / (1 + t)`  
`Output tax = G - Net revenue`

For a GST-exclusive price `N`:

`Gross billing = N × (1 + t)`  
`Output tax = Gross billing - N`

These simple formulas are only valid for the stated one-rate situation. Multiple rates, cess, composite/mixed supplies, exempt components, place-of-supply issues or other indirect taxes require a component-wise method or review. Never assume all receipts are taxable at one rate.

Input GST must be separately identified as eligible, ineligible or under review. Recoverable ITC is generally not part of asset cost/expense in the projection model; non-creditable tax may form part of cost according to applicable accounting and tax treatment. Do not infer eligibility solely from an invoice or a user-entered GST rate.

## 4. Expense projection engine

Supported projection methods:
- Fixed amount per period.
- Prior period amount × (1 + escalation %).
- Percentage of revenue.
- Cost per unit × production/sales units.
- Cost per operating day/session/vehicle/bed/room etc.
- Headcount × average cost per employee.
- Capacity step-up or staged cost.
- Manual override.

Expense heads should be grouped for reporting and tagged as direct cost, employee expense, administration, selling/distribution, repair/maintenance, insurance, utilities, rent, platform/commission, finance cost, tax or other. The user can add custom heads.

For every expense, the model records: projection method, basis/driver, escalation, period, tax/GST treatment where relevant, source and notes. Avoid double counting costs already included in another driver (e.g. power expense also included in variable cost per session).

## 5. Project cost and means of finance

### 5.1 Project cost

For each item, distinguish:
- Basic quoted amount.
- GST/other tax amount.
- Eligible recoverable ITC.
- Non-creditable tax.
- Directly attributable installation/freight/commissioning cost.
- Capitalisable amount.
- Deposit / prepayment / other cash requirement.
- Working-capital margin and contingency where applicable.

The project cost total must not automatically equal the sum of every cash outflow. The report should show (a) total project uses and (b) asset-wise capitalisation and expense/deposit classification as separate analyses.

### 5.2 Means of finance

`Total funding = Sum of all funding sources`  
`Funding gap / (surplus) = Total project uses - Total funding`

Funding categories include promoter/member/partner/shareholder contribution, term debt, unsecured debt, grant/subsidy, working-capital facility and other sources. State the basis of debt-equity ratio; for example, term debt divided by promoter contribution is not necessarily the same as total debt/equity.

### 5.3 Contribution / capital movements

Do not model all constitutions using one generic equity line. Use movement schedules:
- Individual/proprietor: opening capital + additional capital + profit - drawings.
- HUF: HUF capital and applicable member/fund movements; collect only relevant details.
- Partnership/LLP: partner-wise opening capital/current account, contribution, drawings, interest/remuneration (where contract/tax treatment permits), share of profit and closing balance.
- Company: share capital movements, securities premium, reserves/surplus, profit appropriation and dividends/distributions where applicable.

All remuneration, partner interest, drawings, dividends, share issue and distribution treatment must be input-driven and reviewed against agreements and applicable law. Do not automatically assume a rate or entitlement.

## 6. Fixed assets and depreciation

Maintain asset-wise gross block, additions, commissioning/put-to-use date, disposal, residual value, useful life, method, depreciation period convention and accumulated depreciation.

### 6.1 Book depreciation methods

**Straight-line method (SLM):**

`Depreciation = (Depreciable amount / Useful life) × Time proportion in use`

where `Depreciable amount = Capitalised cost - Residual value`.

**Written-down value (WDV):**

`Depreciation = Opening carrying amount × Rate × Time proportion`

**Units of production:**

`Depreciation = Depreciable amount × Units produced in period / Estimated total lifetime units`

The method must be selected per asset/class and reporting framework. Time proportion, residual value, useful life changes, impairment and disposal treatment require explicit rules. The initial scope may support SLM/WDV and defer more complex accounting adjustments if clearly disclosed.

### 6.2 Tax depreciation

Keep in a separate tax computation schedule. Tax rates and asset classifications must be versioned by jurisdiction/effective year and sourced. The first release may show a configurable estimate but must not imply that the schedule is a complete income-tax computation.

## 7. Loan engine

Each facility supports staged disbursements, rate changes, repayment frequency, moratorium, interest basis, repayment method and lender overrides.

### 7.1 EMI reducing-balance method

For principal `P`, periodic interest rate `r`, and number of instalments `n`:

`EMI = P × r × (1+r)^n / ((1+r)^n - 1)`

Equivalent form: `P × r / (1 - (1+r)^(-n))`.

For a regular period:
- Opening balance = prior closing balance + applicable disbursements.
- Interest = opening balance × periodic rate (or day-count formula selected for the facility).
- Principal = payment - interest.
- Closing balance = opening balance + disbursements - principal.

Final instalment must be adjusted to clear permitted rounding residue without creating a negative balance. Show any final-payment adjustment. EMI should be calculated using exact Decimal precision and rounded only at payment posting.

### 7.2 Other repayment methods

**Equal principal:** Principal component is set per schedule; interest is calculated on opening outstanding and payment is principal + interest.

**Interest-only / moratorium:** During moratorium, interest may be paid, capitalised or accumulated according to the sanction terms. The chosen treatment must be explicit. Do not assume moratorium means interest-free.

**Custom schedule:** User enters lender-confirmed principal/interest/total payment amounts. Overrides require a reason and source. The schedule must reconcile to facility outstanding.

### 7.3 Irregular periods and interest basis

Support a documented method: periodic rate for regular monthly periods, or daily accrual using a chosen denominator (ACT/365, ACT/360, ACT/ACT or lender-specified). Record the day-count convention. Staged disbursements accrue interest only from the relevant disbursement date. Floating rate resets must apply from their effective dates.

### 7.4 Annual finance cost and debt service

Aggregate interest and principal repayments by financial period using actual due dates. Finance cost in P&L uses the interest component according to the selected accrual/payment method; principal is a financing cash flow and reduces the borrowing balance.

## 8. Working capital

Support component-level calculations for raw materials, WIP, finished goods, receivables, trade payables, expense creditors, statutory dues and cash balance.

**Holding-days method (illustrative generic form):**

`Required component balance = Relevant annual/period cost or sales base × Holding days / Days in period`

The base must match the component (e.g. cost of sales, purchases, sales, operating expenses); do not apply a single denominator to all components. For monthly projections, use period-specific days or an explicitly selected 30-day convention.

`Net working capital = Current operating assets - Current operating liabilities`

The bank's margin/funding assessment is a separate configurable method and must not be confused with accounting net working capital. Any bank method should be named, versioned and source-referenced.

## 9. Projected Profit & Loss

Standard bank-oriented structure (customisable by entity/report template):
1. Revenue from operations (net of applicable indirect tax where presentation requires).
2. Other income.
3. Total income.
4. Direct costs / cost of sales.
5. Gross profit where meaningful.
6. Employee benefits.
7. Administrative and other operating expenses.
8. EBITDA.
9. Depreciation and amortisation.
10. EBIT.
11. Finance costs.
12. Profit before tax.
13. Tax provision (configurable estimate).
14. Profit after tax.
15. Entity-specific appropriation / drawings / distributions below PAT where appropriate to the selected report format.

The exact statement mapping must be configurable. Do not add company-only labels to partnership statements or imply every project report is a statutory Schedule III financial statement.

## 10. Projected Balance Sheet mechanics

Minimum schedules:
- Fixed assets: gross block, accumulated depreciation, net block.
- Capital work in progress where applicable.
- Inventory, receivables, cash/bank and other current assets.
- Capital/partners' accounts/share capital/reserves according to constitution.
- Long-term borrowings and current maturities.
- Short-term borrowings.
- Trade payables, statutory dues and other liabilities.

Fundamental check:

`Total assets - Total equity - Total liabilities = 0`

If not zero, show an error and a trace of affected schedules. Never insert an automatic balancing reserve, suspense or miscellaneous asset/liability.

Opening balances, capital movements, PAT appropriation, drawings/distributions, loan movements, asset additions/disposals and changes in working capital must reconcile.

## 11. Cash Flow Statement

Support an indirect method initially; a direct method may be added after explicit specification.

Operating cash flow should bridge profit to cash by adding back non-cash charges, removing non-operating items where applicable, and adjusting operating working capital movements and cash taxes/interest according to the selected cash-flow policy.

Investing cash flow includes fixed asset acquisition/disposal and investment movements.

Financing cash flow includes capital contribution/share issue, loan disbursement, loan principal repayment, dividend/distributions and other funding movements.

Fundamental check:

`Opening cash + Net cash movement = Closing cash`

Closing cash must agree with the Balance Sheet cash/bank line. Negative cash is not a permitted real bank balance; show an explicit funding deficit/overdraft requirement and validation warning/error.

## 12. Tax provision and entity differences

The tax engine is a projection estimate, not a tax-return computation in the first release. It must support:
- Entity constitution.
- Financial year and applicable regime/profile.
- User-selected calculation method (effective rate, bracket-based estimate, manual input, or not computed).
- Versioned rate inputs, cess/surcharge where relevant, loss brought forward where specifically supported.
- Source, effective date, review status and assumptions.

If statutory details are not verified for the relevant financial year and entity, require user-supplied rate/estimate or mark tax not computed. Do not claim legal correctness. Deferred tax is an open scope item; unless separately specified, disclose that it is not modelled.

## 13. Ratios and appraisal formulas

Every ratio definition stores formula code, numerator, denominator, applicable statement lines, unit, period aggregation rule, limitations and source/method.

### Liquidity
- Current ratio = Current assets / Current liabilities.
- Quick ratio = (Current assets - Inventory - other excluded/non-liquid current assets as configured) / Current liabilities.
- Net working capital = Current assets - Current liabilities.

### Leverage / solvency
- Debt-equity = Defined debt measure / defined equity measure. The selected numerator/denominator mapping must be displayed.
- Total outside liabilities / tangible net worth = configured outside liabilities / tangible net worth; exclusions must be stated.
- Debt to assets = Defined interest-bearing debt / total assets (or lender-specific definition).

### Profitability
- Gross margin = Gross profit / Net revenue.
- EBITDA margin = EBITDA / Net revenue.
- EBIT margin = EBIT / Net revenue.
- Net profit margin = PAT / Net revenue.
- ROCE = EBIT / Average capital employed; the capital-employed definition and averaging basis must be stated.
- ROE = PAT / Average equity, where meaningful for entity type.

### Activity
- Inventory turnover = Cost of goods sold / Average inventory.
- Receivables turnover = Credit sales / Average trade receivables.
- Payables turnover = Credit purchases / Average trade payables.
- Fixed-asset turnover = Net revenue / Average net fixed assets.
- Operating cycle = Inventory days + Receivable days - Payable days, with component definitions disclosed.

### Coverage
- Interest coverage = EBIT / Finance cost (or other selected lender definition).
- EBITDA / debt service = EBITDA / (scheduled principal + interest).
- DSCR = Cash flow available for debt service (CFADS) / scheduled debt service, where CFADS and treatment of cash taxes/interest are explicitly defined in the selected method.
- Average DSCR = lender-configured average of period DSCRs; define whether simple, weighted or cumulative. Do not average ratios without specifying the method.

### Project viability
- Break-even sales (single product/simple contribution model) = Fixed costs / Contribution margin ratio.
- Contribution = Sales - Variable costs.
- Margin of safety = Actual/projected sales - Break-even sales; ratio = margin of safety / sales.
- Simple payback = time until cumulative project cash inflows recover initial project investment; state whether pre-tax/post-tax and whether financing is excluded.
- NPV = Sum of discounted project cash flows, including initial investment at time zero; state cash-flow perspective and discount rate.
- IRR = rate at which NPV of defined project cash flows equals zero. Report non-unique/no-solution limitations.
- Profitability index = Present value of future project cash inflows / initial investment, where method is applicable.

For multi-product, step-fixed cost or capacity-constrained projects, simple break-even is an approximation; label the method and its limitations.

## 14. Scenario and sensitivity engine

Scenario copy must create independent editable assumptions while preserving project-level identity/period definitions as designed. A scenario comparison uses the same period labels and calculation engine version where possible.

Sensitivity inputs can include utilisation, selling price, volume, input cost, power cost, interest rate, project cost, commissioning delay and operating cost escalation. Each sensitivity result must disclose which input was varied and which inputs were held constant.

## 15. Required outputs and calculation trace

For each calculated line, preserve:
- Formula code/version.
- Input references and exact values used.
- Source/assumption identifiers where available.
- Intermediate values where necessary to explain the result.
- Rounding applied.
- Period and scenario.

A user should be able to select a displayed P&L or ratio figure and open a calculation detail panel explaining how it was derived.
