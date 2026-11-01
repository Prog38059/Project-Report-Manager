---
name: report-output-verification
description: Use when creating, changing or validating PDF, Word or Excel project-report outputs and their financial statement layouts.
---

# Report Output Verification Procedure

1. Select one immutable calculation run and one report template/version.
2. Build/validate the common report-data object before invoking renderers.
3. Confirm statement period labels and horizontal layout: A serial, B note reference, C particulars, D onward periods.
4. Render PDF, Word and Excel from the same report-data object. Do not recalculate in renderers.
5. Compare key totals, line values, period order, units and signs across all three outputs.
6. Inspect page breaks, table splits, repeated headers, print areas, freeze panes and landscape sections.
7. Confirm warnings, assumptions, exclusions and sources are disclosed.
8. Record output template version, calculation-run ID, generation timestamp and hashes.
9. Attach representative outputs or screenshots to the phase completion report.
