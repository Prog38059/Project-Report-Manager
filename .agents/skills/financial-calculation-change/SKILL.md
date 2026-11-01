---
name: financial-calculation-change
description: Use when adding, correcting or refactoring a financial formula, loan schedule, depreciation method, tax estimate, working-capital calculation, financial statement or ratio.
---

# Financial Calculation Change Procedure

1. Identify the documented formula/method and relevant open ADR. Do not proceed on an unresolved material methodology.
2. Define inputs, units, period basis, timing convention, precision, rounding boundary and missing-data behaviour.
3. Write a small independently checkable numerical example before implementing.
4. Implement the pure domain function using `Decimal` and typed inputs/outputs.
5. Add unit tests for normal, boundary, zero/missing, negative-if-valid, rounding and invalid cases.
6. Add an independently calculated golden fixture. Do not derive expected values by calling the function under test.
7. Integrate the result into the calculation pipeline and statement line mappings.
8. Verify P&L, Balance Sheet, Cash Flow, loan/asset schedules and ratios affected by the change.
9. Run the full financial regression suite and report exact results.
10. Update formula documentation, engine version policy and change log where appropriate.
