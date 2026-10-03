# Deterministic fixture demo

Run the fixture harness from the repository root with a new or empty output directory:

```text
python examples/run_fixture.py --output-dir <temporary-directory>
```

Observed output:

```text
lean-quick: complete champion=a002 synthetic_planned_calls=3
classic-two: complete champion=a001 synthetic_planned_calls=7
```

The harness creates `lean-quick/` and `classic-two/` under the output directory. Each includes `arena.json` and `winner.txt`; the latter identifies the champion and includes its synthetic solution. Both outputs mark their planned-call values as synthetic, not API usage.

These runs use deterministic fixture solutions and verdicts. They exercise the local bracket bookkeeping only: they make no model or agent calls and do not evaluate answer quality or demonstrate independent live agents.
