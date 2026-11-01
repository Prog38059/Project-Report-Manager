# Start Here — Google Antigravity

This handoff package is optimised for Google Antigravity.

## How Antigravity should load this workspace

1. Extract the ZIP to a local working folder.
2. Open the extracted `Project_Report_Manager_Antigravity_Handoff_v1.0` folder as the Antigravity workspace.
3. Keep the root `AGENTS.md` in the workspace root. Antigravity discovers root `AGENTS.md` as persistent workspace instructions.
4. Keep `.agents/rules/*.md` and `.agents/skills/*/SKILL.md` in their exact folders. Rule files contain required YAML trigger frontmatter; skills are reusable procedural playbooks.
5. Do not move the `.agents` directory or rename the root instruction file unless the customization discovery configuration is updated.
6. Read `README.md` and the full `docs/` folder before starting.

## First task — planning only

Open `prompts/ANTIGRAVITY_PHASE_0_REVIEW.md` and give its contents to Antigravity. It instructs the agent to review the design, identify gaps and prepare a Phase 1 plan without writing code or creating a database.

## After the review

Discuss the review and resolve any open ADRs. Only after explicitly approving Phase 1, use `prompts/ANTIGRAVITY_PHASE_1_START.md` and the `phase-implementation` skill.

## Antigravity rules and skills included

- `.agents/rules/financial-model.md`
- `.agents/rules/database-and-migrations.md`
- `.agents/rules/report-generation.md`
- `.agents/rules/desktop-ui.md`
- `.agents/skills/phase-implementation/SKILL.md`
- `.agents/skills/financial-calculation-change/SKILL.md`
- `.agents/skills/report-output-verification/SKILL.md`

The root `AGENTS.md` is the always-active project instruction set. Modular rules activate only according to their declared triggers. Skills are procedural references that the agent can load when the relevant work is requested.

## Important

The pack is a specification, not source code. Do not ask Antigravity to implement the entire application in one pass. Begin with Phase 0 review, then obtain approval for each phase.

## Why the folder layout matters

Antigravity's current documentation recognises workspace-root `AGENTS.md` / `GEMINI.md`, immediate `.agents/rules/*.md` rule files, and `.agents/skills/<name>/SKILL.md` skills. Rule files require valid YAML trigger frontmatter; the supplied rule files use `glob` triggers. Skills are used for repeatable multi-step procedures. See the official [Rules documentation](https://antigravity.google/docs/rules/) and [Learn command documentation](https://antigravity.google/docs/commands/learn).

Do not move rule files into deeper nested folders under `.agents/rules/` unless discovery is explicitly configured. Keep each rule file below Antigravity's documented per-file size limit.
