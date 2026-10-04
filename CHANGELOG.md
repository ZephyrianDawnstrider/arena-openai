# Changelog

Published release notes and unreleased candidate notes are kept separately below.

## Optimization experiment - unreleased, 2026-10-04

This section supersedes the candidate's retry/default guidance for the experiment branch only;
the v0.3.3 snapshot and released history below are preserved.

- New lean runs use one structured result with strict schema, identity, score, and solution checks;
  the local collector extracts derived artifacts only after validation and preserves rejected bytes.
- Keep v0.3.2 run states and their legacy two-file lean contract readable.
- Default to quick2 / 3 planned calls and sequential waves when capacity is unknown; deliberately
  select lean4 for complex work. Larger fields need task-specific evidence and available capacity.
- Shorten repeated prompt guidance without claiming synthetic byte savings improve answer quality.
- Add corruption, malformed-result, extraction-failure, and compatibility regressions. No new live
  smoke or release is implied by the local tests, fixture runs, or package validation.

## v0.3.3 - candidate, not released

- Encode task text as JSON and mark task, baseline, and generated work as untrusted data with an explicit authority boundary.
- Report exact missing judge artifacts and stop unsafe advancement; document a bounded rerun and failure-report path.
- Add a skill VERSION marker and validate every packaged byte against the source payload.
- Document reversible update and uninstall steps without changing installed copies.

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
