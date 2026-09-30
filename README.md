# Arena for ChatGPT + Codex

An OpenAI adaptation of [Jakeschincariol/arena-skill](https://github.com/Jakeschincariol/arena-skill).

Arena turns one task into a budgeted tournament. A small set of candidate solutions receive different reasoning/workflow/strategy cards, attack each other, defend and revise, and are judged against a written rubric until one solution survives.

This repository keeps the original portable tournament engine and adapts the orchestration layer for OpenAI skills/plugins and Codex.

## What is included

- `skills/arena/SKILL.md` - OpenAI/Codex orchestration instructions
- `skills/arena/bracket.py` - deterministic tournament state machine
- `skills/arena/strategies.json` - 2,160 possible strategy cards
- `skills/arena/rubric.md` - judging rubric
- `tests/test_bracket.py` - engine tests
- `plugin.json` - portable Agent Plugins manifest
- `.codex-plugin/plugin.json` - Codex compatibility manifest

## Important compatibility note

The bracket engine is fully local and portable. True parallel competitors require a host/runtime that exposes independent sub-agents or equivalent delegation. In environments without that capability, the skill must use an explicit sequential fallback and must not pretend those runs were independent agents.

## Install / use with Codex

Clone the repository, then register the repository as a plugin/skill source according to your Codex environment.

The portable plugin is rooted at this repository. The compatibility manifest also declares:

```json
{
  "name": "arena-openai",
  "version": "0.2.0",
  "description": "Tournament-style answer refinement for ChatGPT and Codex.",
  "skills": "./skills/"
}
```

Then ask Codex to use the Arena skill, for example:

```
Use arena to solve this task: ...
```

or:

```
Run an arena with 8 competitors for this difficult debugging problem: ...
```

## Modes

- default: 4 competitors, 19 calls
- `--quick`: 2 competitors, 7 calls
- `--agents N`: choose the competitor count
- `--seed S`: reproducible cards and bracket
- `--wave W`: jobs grouped per orchestration wave; set it to current host capacity
- `--max-calls C`: hard call budget; default 44

The engine refuses runs above 44 calls unless the caller explicitly raises `--max-calls`. That keeps
plain-language Arena requests within 8 competitors, including one optional final check. The historical 100-competitor mode requires 595
calls and should be used only after explicit cost approval.

## Codex model and concurrency policy

Arena adapts to the current runtime rather than assuming every Codex task has the same worker limit.
Fast, economical models are appropriate for candidate, attack, and defense jobs. When worker-specific
model selection is available, the judge and final comparison should prefer `gpt-6-astra` unless the
user chose another model. Model selection does not create additional concurrent worker slots.

## Safety / project isolation

Arena's generated tournament state lives under `.arena/`. Competitors should not directly modify the user's project during the tournament. Code changes should be returned as patches/full files in the candidate answer and only applied after the user chooses to do so.

## Attribution

Original Arena project by Jake Schincariol:
https://github.com/Jakeschincariol/arena-skill

The original project is MIT licensed. This adaptation preserves that license and attribution.

## Status

This is an adaptation for OpenAI's current skills/plugin model. The Python tournament engine is inherited from the original project; the OpenAI-specific orchestration layer is maintained here.
