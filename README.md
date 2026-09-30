# Arena for ChatGPT + Codex

An OpenAI adaptation of [Jakeschincariol/arena-skill](https://github.com/Jakeschincariol/arena-skill).

Arena turns one task into a structured tournament. Multiple candidate solutions receive different reasoning/workflow/strategy cards, attack each other, defend and revise, and are judged against a written rubric until one solution survives.

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
  "version": "0.1.0",
  "description": "Tournament-style answer refinement for ChatGPT and Codex.",
  "skills": "./skills/"
}
```

Then ask Codex to use the Arena skill, for example:

```
Use arena --quick to solve this task: ...
```

or:

```
Run an arena with 32 competitors for this debugging problem: ...
```

## Modes

- default: 100 competitors
- `--quick`: 16 competitors
- `--agents N`: choose the competitor count
- `--seed S`: reproducible cards and bracket
- `--wave W`: jobs grouped per orchestration wave

The original engine estimates 595 sub-agent calls for a 100-competitor tournament and 91 for the 16-competitor quick mode.

## Safety / project isolation

Arena's generated tournament state lives under `.arena/`. Competitors should not directly modify the user's project during the tournament. Code changes should be returned as patches/full files in the candidate answer and only applied after the user chooses to do so.

## Attribution

Original Arena project by Jake Schincariol:
https://github.com/Jakeschincariol/arena-skill

The original project is MIT licensed. This adaptation preserves that license and attribution.

## Status

This is an adaptation for OpenAI's current skills/plugin model. The Python tournament engine is inherited from the original project; the OpenAI-specific orchestration layer is maintained here.
