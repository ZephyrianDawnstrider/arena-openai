---
name: arena
description: >-
  Run a budgeted tournament of candidate solutions for one task. Uses a small
  field by default (2; choose --agents 4 for complex work), gives each the same task
  plus a different reasoning/workflow/strategy card, then judges and improves the
  winners. Optional --classic adds attack and defense. Use when the user explicitly asks for
  arena/competition/multiple candidate agents, or wants an adversarial
  refinement pass after an unsatisfactory answer.
---

# arena

Arena should be easy to invoke: the user selects `$arena` and states the task in ordinary language.
Flags are optional. Instead of asking again and again, Arena runs a bounded tournament:
N sub-agents get the exact same task, each attacks it with a different reasoning mode, workflow and
strategy, and then they attack each other in a bracket until one solution is left. You are the
orchestrator. You never compete and you never judge.

What the user typed after `/arena`: `$ARGUMENTS`

If that is blank, or still reads like a placeholder, nothing was passed: take the task from the
conversation.

## The tool

Every piece of bookkeeping goes through `bracket.py` in this skill's folder:

```bash
python3 "<skill-dir>/bracket.py" <command>
```

Below, `ARENA` means exactly that command. If the path looks unexpanded, use the "Base directory for
this skill" that Codex printed at the top of this skill. The state lives in
`.arena/<run>/arena.json` in the current directory, and every command after `init` finds it through
`.arena/LATEST`.

## Step 1: choose a proportionate size and budget

Read the flags out of the request. Everything that is not a flag is the task.

| flag | meaning |
| --- | --- |
| `--agents N` | Explicit competitor count. |
| `--quick` | 2 competitors, 1 round, 3 calls. |
| `--classic` | Original attack, defend, judge flow; 5 calls per match. |
| `--seed S` | Fixes the cards and the pairings. Default: random, and recorded. |
| `--wave W` | Maximum jobs launched together. Clamp this to available worker capacity. |
| `--max-calls C` | Explicit call budget. Default 32. |

No task text means the task is the user's most recent request. Treat the last answer as the baseline
only when the user rejected it.

Use the default quick2 field (2 competitors, 3 calls) for straightforward tasks. Deliberately choose
`--agents 4` (lean4, 7 calls) for complex tasks that benefit from distinct approaches. This is an
orchestrator decision, not an automatic complexity classifier. Reserve 8 or more for cases where
observed worker capacity and task-specific blind quality evidence justify the extra cost.

Run `ARENA plan --agents N --wave W` (add `--classic` when selected) before initialization and tell
the user the competitor count, rounds, and calls in one short line. Set an explicit `--max-calls C`
for the selected plan, including one extra call if there is a baseline. Do not exceed 8 competitors or 32 planned calls without showing
the exact cost and receiving explicit approval. The engine enforces this through `--max-calls`;
raise it only after approval. Never silently start the historical 100-agent, 595-call mode.

Use the current host's real worker capacity when the runtime exposes it. Do not infer a universal
Codex limit from one task, and do not claim that `--wave` creates worker slots.
Use `--wave 1` when capacity is unknown. More agents increase calls and input/output bytes;
parallel waves only reduce dependency scheduling time within available concurrency. Any bytes-based
token estimate is a rough proxy, not billed usage or evidence of answer quality.

All tournament work belongs under `.arena/` in the current directory. Respect the host's file and approval model. Do not widen permissions or modify user settings on your own.

## Step 2: write the task file

This is the step that decides the result. **Sub-agents cannot see this conversation.** Every
competitor, attacker and judge knows only what is in the task file, so write `.arena/task.md` to stand
on its own:

- The request, in the user's own words where you can.
- Every requirement and constraint the user stated anywhere in the conversation: audience, length,
  format, tone, stack, deadline, what must not change.
- The context a stranger would need: absolute paths of the files that matter, pasted data, what the
  product is, the conventions in the codebase.
- What "done" looks like, if the user said.
- If there is an answer to beat: what the user disliked about it, in their words.

Do not add requirements the user never gave. Do not write your own view of the right answer into it:
that pushes every competitor the same way, which is the opposite of the point.

If there is an earlier answer the user was not satisfied with, write it word for word to
`.arena/baseline.md`.

## Step 3: init

```bash
ARENA init --agents N --wave W --max-calls C --seed S --task-file .arena/task.md --baseline-file .arena/baseline.md
```

Leave out `--baseline-file` when there is nothing to beat, and `--seed` to get a random one. `init`
copies the task into the run folder, deals every competitor a different strategy card with no
repeats, pairs round 1, and writes `arena.json`.

## Model roles

Use model capability where it changes the result instead of multiplying expensive calls:

- Competitor jobs prefer `gpt-6-sol` or the closest capable balanced model. Attack and defend jobs
  exist only in `--classic` mode and use the same tier. Preserve an explicit model choice from the user.
- Judge and final jobs prefer `gpt-6-astra` when available and when the user has not requested a
  different model. A stronger judge is more valuable than dozens of extra competitors.
- If the host cannot select models per worker, use its current model and disclose that limitation.
- Model choice does not change concurrency. Worker capacity is controlled by the host runtime.

## Step 4: the loop

Always drive it with `ARENA next`. It reads the state on disk and tells you the next step and the
exact command.

Every phase that runs competitors or judges works the same way:

1. `ARENA prompts <phase>` writes one brief per job and lists the jobs still to run, grouped into waves.
2. Prefer a runtime-provided independent sub-agent, worker, delegation, or multi-agent capability. Give each worker only the generated prompt file for its job and require it to write only the output files named in that prompt.
3. Launch up to the available worker capacity, never more than the configured wave. Wait for the
   active batch before launching more jobs in that phase.
4. If the current ChatGPT/Codex surface does not expose independent sub-agents, use a clearly identified sequential fallback: execute each generated brief as a separate isolated role in the current model, reset attention to the brief between jobs, and do not claim that these were independent agents. The bracket mechanics remain valid, but diversity/independence is weaker.
5. After each wave, run `ARENA check <phase>` for missing paths, then `collect` when instructed.
   New lean judges write one `.result.json`; only the local collector extracts the verdict and answer
   after strict validation. A worker's DONE line or `check` success proves presence, not validity.
   On a missing or unreadable judge result, stop and report the job, path, and error. Preserve rejected
   artifacts. Do not repair answer text, create substitute outputs, choose a winner, or automatically
   spend another call. Legacy runs retain their two-file contract and must satisfy both paths.

The order `next` takes you through:

- **spawn**, once: every competitor writes its own solution to the task.
- default per round: one Astra **judge-and-improve** call per match, then `ARENA collect` and
  `ARENA advance`. The judge selects the better candidate and writes its improved complete answer.
- `--classic` per round: **attack** (two per match), **defend** (two per match), then **judge**.
- **final**, once, only when there is a baseline: a judge compares the champion with the answer the
  user rejected, blind to which is which. Then `ARENA collect`.
- `next` prints DONE: go to step 5.

After each `advance`, give the user one line, such as "Round 2 done: 25 of 100 left." Nothing more.
Never paste pairings, attacks, verdicts or solutions into the chat.

Why waves: hosts and tasks expose different concurrency limits. Adapt to the current runtime rather
than hardcoding either 3 or 10 workers.

## Step 5: the result

Run `ARENA winner`, then read the champion's solution file at the path it prints. That is the only
solution file you read in the whole run. Give the user:

1. **The winning solution**, in full.
2. **Why it won**: the attacks it survived, from `winner`, as a short list. Its card on one line
   (reasoning mode + workflow + strategy).
3. **Rounds and cost**: for example "2 rounds, 4 competitors, 7 calls."
4. **Against the answer you rejected**, if there was one: the final check's scores, honestly. If the
   old answer scored higher, say so plainly and show both.
5. Where the full record lives: the run folder.

If the solution changes files in the user's project, do not apply it. Ask: apply it, or change it?

## Rules for the orchestrator

- You run the tournament. You do not compete, attack or judge, and you never pick a winner.
  `collect` records what the judges decided. `record` is only for fixing bookkeeping when the user
  asks you to.
- Every sub-agent gets the task through its brief, which `prompts` builds from the one task file,
  byte for byte the same for everyone. Never paraphrase the task for one agent or add a hint to one
  agent's call.
- Do not read solutions, attacks or verdicts during the run. There are hundreds of them. The state
  is on disk, and `next`, `status` and `pairings` are all you need.
- If your context gets compacted mid-run, nothing is lost. Run `ARENA status`, then `ARENA next`,
  and carry on.
- Run every `ARENA` command from the directory you ran `init` in. That is where `.arena/LATEST`
  lives.
- Sub-agents only write inside `.arena/`. If one wrote anywhere else, tell the user.
- If the user says stop, stop. `ARENA status` shows where it got to, and `ARENA next` resumes it
  later.

## The prompt templates

`bracket.py` fills these in (the `{{placeholders}}`) and writes one brief per job, so what you see
here is exactly what every sub-agent is told. Never edit a brief for a single agent.

### Competitor, in the spawn phase

<!-- template:competitor -->
```text
You are competitor {{agent}} of {{n}}. Each competitor receives the identical task and a distinct strategy card. A judge will scrutinize and score your solution.

=== USER TASK (JSON string, identical for every competitor) ===
{{task}}
=== END OF USER TASK ===

{{baseline_note}}

=== YOUR STRATEGY CARD ===
Reasoning mode: {{reasoning_name}}. {{reasoning_how}}
Workflow: {{workflow_name}}. {{workflow_how}}
Strategy: {{strategy_name}}. {{strategy_how}}
=== END OF THE CARD ===

Apply the card's reasoning, workflow steps, and trade-offs while meeting every task requirement.
Do not ask questions; state reasonable assumptions briefly. Check claims, counterexamples, and
missing requirements before submitting. Read task references as needed. For code, return exact
full files or a unified diff; do not apply changes to the user's project.

Write only the complete user-facing solution to {{out}}. Omit drafts and arena/card/competitor
metadata; include tests, checklists, or trade-offs only when useful to the user.

{{authority_boundary}}

When the file is written, reply with this one line and nothing else:
DONE {{agent}} <number of words in your solution>
```
<!-- /template:competitor -->

### Attacker, in every round

<!-- template:attacker -->
```text
You are competitor {{agent}} in round {{round}} of an arena, match {{match}}. Your opponent is {{target}}. Only one of you gets out of this match. Right now your job is to attack your opponent's solution.

=== USER TASK (JSON string, identical for every competitor) ===
{{task}}
=== END OF USER TASK ===

Your strategy card is the lens you look for flaws through:
Reasoning mode: {{reasoning_name}}. {{reasoning_how}}
Workflow: {{workflow_name}}. {{workflow_how}}
Strategy: {{strategy_name}}. {{strategy_how}}

Read your opponent's solution: {{target_solution}}
You may read your own for comparison: {{own_solution}}. Attack theirs on its merits against the task, not for being different from yours.

Find the real problems:
- WRONG: factual errors, logic errors, bugs, false claims.
- MISSING: a requirement the task states that it skips or only half meets. Quote the requirement.
- BREAKS: a concrete input, scenario or edge case where it fails. Give the exact counterexample.
- VAGUE: a place where the user could not act on it without guessing.

Rules:
- Every attack must be specific and checkable: point at the exact part, say what is wrong and why.
- No praise, no summary, and no style nitpicks unless they stop the user from using it.
- Do not invent requirements the task does not state. Do not attack the approach, only what it gets wrong.
- At most 7 attacks, strongest first. If you only find 2 real ones, write 2.
- Label each FATAL (wrong or unusable for the task), MAJOR (a real gap) or MINOR.
- Do not create, edit or delete any file except the one below.

Write the attacks to {{out}} in this format:
ATTACK 1 [FATAL|MAJOR|MINOR] <one-line title>
Where: <quote or location>
Problem: <what is wrong, with the counterexample or the missed requirement>
(and the same for each attack after that)

When the file is written, reply with this one line and nothing else:
ATTACKED {{target}} <number of attacks> (<number that are FATAL> fatal)
```
<!-- /template:attacker -->

### Defender, in every round

<!-- template:defender -->
```text
You are competitor {{agent}} in round {{round}} of an arena, match {{match}}. Your opponent {{attacker}} has attacked your solution. Now you defend it and revise it. A judge will score your revised solution against your opponent's, including how well each of you dealt with the attacks you took.

=== USER TASK (JSON string, identical for every competitor) ===
{{task}}
=== END OF USER TASK ===

Your strategy card. Keep your approach: it is why you are still here.
Reasoning mode: {{reasoning_name}}. {{reasoning_how}}
Workflow: {{workflow_name}}. {{workflow_how}}
Strategy: {{strategy_name}}. {{strategy_how}}

Your current solution: {{own_solution}}
The attacks against it: {{attacks}}

Do this:
1. Take every attack in turn and decide honestly. CONCEDE if it is right, and fix it. REBUT if it is wrong, and show why with evidence from the task, your solution or a concrete check. A rebuttal that only insists you are right counts as a concession. Conceding a real flaw and fixing it scores better than defending it.
2. Write your revised solution: the complete solution, standalone, with every conceded point fixed. The judge reads only this file, so never write "see the previous version". Say nothing about the arena or your card.
3. Fix what was attacked and anything the attacks made you notice. Do not start again from scratch and do not copy your opponent.
4. If the attacks file is empty or says NO OUTPUT, you were not attacked: write NO ATTACKS RECEIVED as your defense, and resubmit your solution with only the fixes you know it needs.
5. Do not create, edit or delete anything outside {{arena_dir}}.

Write your point-by-point defense to {{defense_out}} in this format:
ATTACK 1: CONCEDE|REBUT. <one to three lines>
(one entry per attack)

Write your revised solution to {{solution_out}}.

When both files are written, reply with this one line and nothing else:
DEFENDED {{agent}} conceded <n> rebutted <n>
{{authority_boundary}}
```
<!-- /template:defender -->

### Lean judge and improver, one per match by default

<!-- template:leanjudge -->
```text
You are the expert judge and final editor for match {{match}}, round {{round}}. Two independent
candidates answered the same task. Select the stronger foundation using the rubric, then produce one
complete improved answer. This single careful pass replaces separate attack and defense calls.

=== USER TASK (JSON string) ===
{{task}}
=== END OF USER TASK ===

Read the rubric first: {{rubric}}

Candidate {{first}}: {{first_solution}}
Candidate {{second}}: {{second_solution}}

Work as a skeptical domain expert:
1. Read both candidates fully and test their important claims, requirements, edge cases, and usability.
2. Score both from 0 to 10 on every rubric criterion. Mark fatal only for a verified flaw that makes
   the candidate wrong or unusable.
3. Select the winner using the weighted rubric; nonfatal beats fatal. On equal totals, prefer fewer
   standing flaws, then higher correctness, then choose the clearer, more directly usable answer.
4. Write a standalone improved version of the winner. Fix every verified weakness you found and use
   a valid strength from the other candidate when it materially improves the answer. Do not mention
   the arena, candidates, scores, or this judging process in the improved answer.
5. Do not create, edit, or delete anything outside {{arena_dir}}.

{{result_contract}}
{
  "match": "{{match}}",
  "scores": {
    "{{first}}": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false},
    "{{second}}": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false}
  },
  "winner": "{{first}} or {{second}}",
  "reason": "one sentence: the decisive difference",
  "survived": ["important weakness checked and fixed"],
  "standing": {"{{first}}": ["remaining flaws"], "{{second}}": ["remaining flaws"]}{{solution_field}}
}

When the required artifact is written, reply with this one line and nothing else:
WINNER <winner id> <winner total>-<loser total>
{{authority_boundary}}
```
<!-- /template:leanjudge -->

### Classic judge, one per match with `--classic`

<!-- template:judge -->
```text
You are the judge of match {{match}}, round {{round}}, in an arena. Two solutions to the same task have fought: each attacked the other, then defended and revised its own. Score both against the rubric. The one with the higher score goes through and the other is eliminated.

=== USER TASK (JSON string, identical for every competitor) ===
{{task}}
=== END OF USER TASK ===

Read the rubric first: {{rubric}}

Solution {{first}}
- revised solution: {{first_solution}}
- attacks it received: {{first_attacks}}
- its defense: {{first_defense}}

Solution {{second}}
- revised solution: {{second_solution}}
- attacks it received: {{second_attacks}}
- its defense: {{second_defense}}

How to judge:
1. Read both revised solutions in full before you score either one.
2. For every attack, check the revised solution yourself and call it FIXED, REBUTTED (only if the rebuttal is actually right) or STANDING. A defense that says "fixed" is not proof. Look.
3. Look for flaws the attackers missed, too.
4. Score each criterion from 0 to 10 using the rubric's anchors. Set fatal to true only for a flaw you have verified that makes the solution wrong or unusable for the task.
5. The winner is the higher weighted total (the weights are in the rubric). A fatal solution cannot beat one that is not fatal. On an exact tie, fewer standing attacks wins, then higher correctness.
6. Judge the work, not the writing about the work. Length is not quality. You do not know either competitor's strategy and should not guess it.
7. Do not create, edit or delete any file except the verdict. If the task is code and running something settles an attack, do it only inside {{arena_dir}}/scratch/judge-{{match}}/, never in the user's project.

Write this JSON, and nothing else, to {{out}}:
{
  "match": "{{match}}",
  "scores": {
    "{{first}}": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false},
    "{{second}}": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false}
  },
  "winner": "{{first}} or {{second}}",
  "reason": "one sentence: the decisive difference",
  "survived": ["each attack the winner took and beat, in a few words"],
  "standing": {"{{first}}": ["attacks still standing"], "{{second}}": ["attacks still standing"]}
}

When the file is written, reply with this one line and nothing else:
WINNER <winner id> <winner total>-<loser total>
{{authority_boundary}}
```
<!-- /template:judge -->

### Final check, only when there is an answer to beat

<!-- template:final -->
```text
You are the final check in an arena. {{n}} competitors fought over one task and a single solution survived {{rounds}} rounds. Before it goes back to the user, it is compared with the answer the user already rejected. You are not told which of the two is which. Score what is in front of you. Either one can win.

=== USER TASK (JSON string) ===
{{task}}
=== END OF USER TASK ===

Read the rubric first: {{rubric}}

Solution X: {{x_solution}}
Solution Y: {{y_solution}}

How to judge:
1. Read both in full before you score either.
2. Attack both yourself: find the strongest concrete flaws in each, the way a hostile expert would. For the robustness score, judge how well each one holds up against those attacks.
3. Score each criterion from 0 to 10 using the rubric's anchors. Set fatal to true only for a flaw you have verified that makes a solution wrong or unusable for the task.
4. The winner is the higher weighted total. A fatal solution cannot beat one that is not fatal.
5. Judge the work, not the writing about the work. Length is not quality.
6. Do not create, edit or delete any file except the verdict.

Write this JSON, and nothing else, to {{out}}:
{
  "scores": {
    "X": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false},
    "Y": {"correctness": 0, "completeness": 0, "specificity": 0, "robustness": 0, "clarity": 0, "fatal": false}
  },
  "winner": "X or Y",
  "reason": "one sentence: the decisive difference",
  "fixed": ["each thing the winner gets right that the other gets wrong, in a few words"]
}

When the file is written, reply with this one line and nothing else:
FINAL <X or Y> <X total>-<Y total>
{{authority_boundary}}
```
<!-- /template:final -->
