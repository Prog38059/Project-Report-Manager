# Open Decisions Register

**Rule:** These topics must not be silently decided by the coding agent. The agent should identify when a decision blocks implementation and present recommended options with impact.

| ID | Decision | Proposed default / options | Status |
|---|---|---|---|
| ADR-001 | Financial year convention | India April–March by default; configurable start month | Proposed, confirm before period engine finalisation |
| ADR-002 | Projection horizon | 7 annual years by default; configurable 3/5/7/10/custom | Approved by user |
| ADR-003 | Historical data | Hidden/disabled by default; explicit per-project activation | Approved by user |
| ADR-004 | Horizontal statement columns | A serial, B note ref, C particulars, D onward periods; default 7 years D:J | Approved by user |
| ADR-005 | Entity coverage | Individual, proprietorship, HUF, partnership, LLP, private limited | Approved scope |
| ADR-006 | Initial tax computation depth | Indicative entity-specific tax estimate vs fuller tax engine | Open; must be scoped before tax module |
| ADR-007 | Deferred tax | Exclude from initial release or support as separate schedule | Open |
| ADR-008 | Book depreciation frameworks | Select methods and framework-specific policy; exact default lives/rates not hardcoded | Open; method policy to be approved |
| ADR-009 | Tax depreciation | Indicative configurable schedule vs comprehensive tax depreciation schedule | Open |
| ADR-010 | Partner remuneration/interest | User-entered agreement-based terms and verified tax treatment | Calculation policy open |
| ADR-011 | Company financial-statement format | Bank-oriented statement vs Schedule III-style mapping or both | Open; proposed selectable templates |
| ADR-012 | Individual/HUF/firm statement layouts | Entity-aware bank project-report mapping | Open; mapping review required |
| ADR-013 | Working capital assessment methods | Operating cycle, turnover method, lender-specific method | Open; propose configurable methods |
| ADR-014 | DSCR variants | Configurable lender formula with formula and source selected per report | Approved architectural principle; exact variants open |
| ADR-015 | Cash flow method | Indirect method default; direct method later/optional | Open |
| ADR-016 | Loan interest convention | Monthly periodic vs ACT/365, ACT/360, ACT/ACT or lender custom | Per facility; default convention open |
| ADR-017 | NPV/IRR assumptions | Cash flow timing, discount rate source, terminal value and project life | Open |
| ADR-018 | Negative cash / overdraft | Present as funding deficit or model an approved cash-credit facility | Open; never silently leave negative bank cash as an ordinary asset |
| ADR-019 | GST treatment | Stream/item-specific sourced rates, ITC eligibility and effective dates | Open per project; no universal defaults |
| ADR-020 | Report branding | Firm logo/name/address, configurable templates | Open UI detail |
| ADR-021 | Report sign-off blocks | Optional wording, never imply audit/certification | Open |
| ADR-022 | Local encryption | Evaluate Windows DPAPI or approved OS secret store | Open technical review |
| ADR-023 | Future LAN API stack | FastAPI or another reviewed service framework; PostgreSQL/MS SQL | Deferred to separate phase |
| ADR-024 | AI-assisted research/narrative | Disabled initially; explicit approval, sourcing, privacy and review workflow | Deferred |

When a decision is approved, record date, approver, selected option, rationale, affected documents and whether a migration or calculation-engine version change is required. Do not delete superseded decisions.
