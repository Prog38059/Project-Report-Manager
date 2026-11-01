---
trigger: glob
globs: "app/ui/**/*.py, app/presentation/**/*.py"
description: "Apply when building or changing the PySide6 desktop user interface and interaction workflows."
---

# Desktop UI Rules

- Follow `docs/06_UI_UX_SPECIFICATION.md`.
- Maintain a professional, dense-but-readable financial application interface; prioritise accurate grids and keyboard workflow over decorative widgets.
- Keep business and financial calculations out of widget classes. Call application services and display typed results.
- Preserve project, entity, scenario and calculation-run context across navigation.
- Seven-year projections are the default. Historical sections remain hidden until explicitly enabled for the project.
- Horizontal financial grids display particulars in column C and period values from column D onward; adapt to configured horizon.
- Provide visible save state, input validation, error navigation and confirmation for destructive actions.
- Ensure copy/paste, tab navigation, row operations and accessible labels work for financial data entry.
- Do not display sample data as real client information.
