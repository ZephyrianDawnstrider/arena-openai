# Arena for ChatGPT and Codex

Arena runs a bounded tournament of candidate answers to one task. Each candidate receives a distinct reasoning, workflow, and strategy card; candidates meet in a bracket, and a judge selects and improves the answer that advances.

This repository contains an Agent Plugin package and a standalone Codex skill. The plugin manifests are at [`plugin.json`](plugin.json) and [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json). The skill and its local Python engine are in [`skills/arena/`](skills/arena/).

The manifests identify released version **0.3.1**. See [the changelog](CHANGELOG.md) for its release notes.

## Install the skill by copying it

Requirements: Python 3.10 or newer and the Python standard library. Python 3.10 is the repository's CI test version; earlier versions have not been verified for this release. No package installation or API key is needed for local bracket bookkeeping. A live tournament also needs a host that can run the Arena skill and delegate independent candidate/judge jobs; if it cannot, Arena's instructions require an explicit sequential fallback.

Run the commands from a directory where `arena-openai` does not already exist. They check out the `v0.3.1` release tag and copy the `arena` skill folder into your user skill directory. The examples honor `CODEX_HOME` when set and otherwise use the default `~/.codex` directory. OpenAI's [Codex skill guide](https://developers.openai.com/blog/eval-skills) shows user-scoped skills under `~/.codex/skills`. These commands stop if an `arena` skill already exists, so an existing skill is not silently overwritten. Start a new Codex session after copying so it can discover the skill.

PowerShell:

```powershell
git clone --branch v0.3.1 https://github.com/ZephyrianDawnstrider/arena-openai.git
Set-Location arena-openai
$source = Join-Path (Get-Location) 'skills\arena'
$codexHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE '.codex' }
$destination = Join-Path (Join-Path $codexHome 'skills') 'arena'
if (Test-Path $destination) { throw "Arena skill already exists at $destination. Review it before updating." }
New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
Copy-Item -Path $source -Destination $destination -Recurse
```

macOS or Linux shell:

```sh
git clone --branch v0.3.1 https://github.com/ZephyrianDawnstrider/arena-openai.git
cd arena-openai
codex_home="${CODEX_HOME:-$HOME/.codex}"
destination="$codex_home/skills/arena"
if [ -e "$destination" ]; then
  printf 'Arena skill already exists at %s. Review it before updating.\n' "$destination" >&2
  exit 1
fi
mkdir -p "$codex_home/skills"
cp -R skills/arena "$destination"
```

Download `arena-skill-v0.3.1.zip` from the GitHub Release assets and extract its `arena/` folder. Copy that folder to the same `skills/arena` destination shown above; set `$source` in PowerShell or the source path in the shell command to the extracted folder. The release workflow also uploads a copy in the GitHub Actions artifact named `arena-skill-v0.3.1`; that artifact is separate from the ZIP attached to the release. The ZIP contains the installable skill payload only; it is not a Python package and is not installed with `pip`.

OpenAI's current plugin documentation also describes packaging skills in a plugin and using a local marketplace in Codex. This repository's two manifests identify that package, but this release workflow provides a downloadable skill ZIP; it does not publish or install a marketplace entry. See [Package your plugin](https://developers.openai.com/plugins/build/plugins) for the official plugin and marketplace workflow.

## Use Arena

Ask Codex to use the skill and state the task. Flags are optional:

```text
$arena --quick Compare these two approaches and recommend one: ...
```

For a difficult task, omit `--quick` to use the default four-candidate tournament:

```text
$arena Find the root cause of this failure and propose a fix: ...
```

These are live-use examples: a real request can launch model or agent work under the host's normal access, quota, and cost rules. The examples here are not executed as part of documentation checks. Ask Arena to plan before running when you want to inspect the count and budget first.

## Modes and call budget

- Default lean mode: 4 candidates and 7 planned sub-agent calls (4 candidate drafts, then 3 judge-and-improve matches).
- `--quick`: 2 candidates and 3 planned calls.
- `--classic`: the original attack, defend, judge flow, with 5 calls per match. Four candidates require 19 total calls including their four initial drafts.
- `--agents N`: choose the field size.
- `--seed S`: make the strategy cards and bracket reproducible.
- `--wave W`: cap the number of jobs launched together; the host still controls its actual worker capacity.
- `--max-calls C`: set the hard planned-call ceiling. It defaults to 32. Arena refuses a plan above that ceiling unless the user explicitly raises it.

The counts include initial candidate drafts and, when requested, the final comparison against a rejected baseline. They are planned agent calls, not a guarantee of elapsed time or billed tokens. The 100-candidate classic plan needs 595 calls and exceeds the default cap.

Lean mode uses one judge-and-improve call per match. Classic mode preserves separate attack, defend, and judge phases for work that benefits from that extra scrutiny. The smaller call count does not guarantee a better answer: assess the result against the task and rubric.

## Reproducible local examples

Run the fixture harness from the repository root. It writes two deterministic simulations to the chosen output folder and makes no model/API calls:

```powershell
python examples/run_fixture.py --output-dir "$env:TEMP\arena-fixtures"
```

```sh
python3 examples/run_fixture.py --output-dir "${TMPDIR:-/tmp}/arena-fixtures"
```

Use a new or empty output directory for each run. The fixtures cover a two-candidate lean quick run (3 synthetic planned calls) and a two-candidate classic run (7 synthetic planned calls). Each result includes its Arena state and a `winner.txt` file with the champion ID and solution. These deterministic simulations verify bracket bookkeeping; they do not run independent agents or evaluate answer quality. See the [observed fixture output](docs/demo.md).

## Historical benchmark and model guidance

The v0.3.0 README recorded one controlled two-candidate comparison: the classic flow used 7 calls and lean used 3, a 57% reduction; a separate blind evaluator preferred the lean answer 46/50 to 42/50. This is one task-specific result, not a general quality guarantee. The v0.3.0 model guidance preferred Sol-class candidates and an Astra-class judge when the host supported worker-specific model selection; model names and availability can change. See [`docs/history.md`](docs/history.md) for the preserved historical wording and scope.

## Compatibility and safety

The bracket engine runs locally. Independent competitors require a host with separate agents or equivalent delegation. When unavailable, follow the skill's sequential fallback and disclose that the candidates were not independent. `--wave` limits work within the host's real concurrency capacity; it does not create workers.

Tournament state is stored under `.arena/` in the current project. Competitors must return proposed code changes for the user to review; they must not edit the user's project during the tournament.

## Project history and license

This is an OpenAI orchestration and packaging adaptation of [Jake Schincariol's Arena project](https://github.com/Jakeschincariol/arena-skill). The inherited engine, strategy cards, rubric, and tests retain the original MIT attribution. See [`CREDITS.md`](CREDITS.md), [`LICENSE`](LICENSE), and [`CHANGELOG.md`](CHANGELOG.md).
