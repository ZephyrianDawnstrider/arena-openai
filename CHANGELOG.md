# Changelog

This file records published release notes for the project.

## v0.3.2 - released, 2026-10-03

- Reject malformed score values and verdicts that identify a different match or unrelated participants; preserve each quarantined verdict.
- Require synthesized winner solutions throughout lean collection and advancement.
- Validate saved state before use and report malformed or mismatched state without rewriting it.
- Add regression coverage for validation, recovery evidence, and unchanged call-budget contracts.
- Align both plugin manifests and the skill archive test with version 0.3.2.

## v0.3.1 - released, 2026-10-03

- Clarify the default lean, quick, classic, and maximum planned-call budgets.
- Document manual Windows PowerShell and macOS/Linux skill-copy installation, prerequisites, and the skill-only ZIP artifact.
- Add deterministic local fixture examples and distinguish simulated planned calls from live agent work.
- Align both plugin manifests with version 0.3.1.

## v0.3.0 - historical

- Added the lean judge-and-improve tournament flow as the default, with the classic attack/defend/judge flow retained as an option.
- Added a 32-call default guard and the `--max-calls` override.
- Added plugin manifests for portable Agent Plugins packaging and Codex compatibility.
- Preserved the inherited engine and its MIT attribution.
