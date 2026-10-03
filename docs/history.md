# Historical release guidance

## v0.3.0 README snapshot - superseded 2026-10-03

This section preserves the v0.3.0 benchmark and model/concurrency guidance when the main README was revised for v0.3.1. The benchmark is task-specific evidence; model names and host capabilities can change.

### Benchmark wording and scope

The v0.3.0 README recorded this controlled comparison:

> We ran both flows on the same two independently generated answers to a production PostgreSQL migration task, with the same task, candidates, rubric, and Astra-class judging tier. The original attack, defend, judge flow used 7 calls; the default judge-and-improve flow used 3, a 57% reduction. A separate blind evaluator preferred the optimized answer (46/50 versus 42/50), citing better completeness, specificity, and rollback safety. This is one controlled benchmark, not a universal quality guarantee; `--classic` remains available for unusually adversarial work.

These figures describe that one benchmark only. They do not establish a general quality improvement or current model availability.

### Model and concurrency guidance from v0.3.0

The v0.3.0 README stated:

> Arena adapts to the current runtime rather than assuming every Codex task has the same worker limit. Balanced Sol-class models are appropriate for candidates. When worker-specific model selection is available, the judge-and-improve and final comparison should prefer `gpt-6-astra` unless the user chose another model. This is the quality, cost, and latency sweet spot: capable diverse drafts plus a strong decision-maker, without five model calls per match. Model selection does not create additional concurrent worker slots.

Current Arena operation should follow the installed host's available models and worker capacity. The skill's rules remain authoritative for an individual run.
