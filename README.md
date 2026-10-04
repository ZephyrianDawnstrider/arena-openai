# Arena for ChatGPT and Codex

Arena runs a bounded tournament of candidate answers to one task. Each candidate receives a distinct reasoning, workflow, and strategy card; candidates meet in a bracket, and a judge selects and improves the answer that advances.

This repository contains an Agent Plugin package and a standalone Codex skill. The plugin manifests are at [`plugin.json`](plugin.json) and [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json). The skill and its local Python engine are in [`skills/arena/`](skills/arena/).

The latest published version remains **0.3.2**. The repository may contain a newer unreleased candidate; check both plugin manifests and `skills/arena/VERSION` before copying a working tree. See [the changelog](CHANGELOG.md) for release and candidate notes.

## Install the skill by copying it

Requirements: Python 3.10 or newer and the Python standard library. Python 3.10 is the repository's CI test version; earlier versions have not been verified for this release. No package installation or API key is needed for local bracket bookkeeping. A live tournament also needs a host that can run the Arena skill and delegate independent candidate/judge jobs; if it cannot, Arena's instructions require an explicit sequential fallback.

Run the commands from a directory where `arena-openai` does not already exist. They check out the `v0.3.2` release tag and copy the `arena` skill folder into your user skill directory. The examples honor `CODEX_HOME` when set and otherwise use the default `~/.codex` directory. OpenAI's [Codex skill guide](https://developers.openai.com/blog/eval-skills) shows user-scoped skills under `~/.codex/skills`. These commands stop if an `arena` skill already exists, so an existing skill is not silently overwritten. Start a new Codex session after copying so it can discover the skill.

PowerShell:

```powershell
git clone --branch v0.3.2 https://github.com/ZephyrianDawnstrider/arena-openai.git
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
git clone --branch v0.3.2 https://github.com/ZephyrianDawnstrider/arena-openai.git
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

Download `arena-skill-v0.3.2.zip` from the GitHub Release assets and extract its `arena/` folder. Copy that folder to the same `skills/arena` destination shown above; set `$source` in PowerShell or the source path in the shell command to the extracted folder. The release workflow also uploads a copy in the GitHub Actions artifact named `arena-skill-v0.3.2`; that artifact is separate from the ZIP attached to the release. The ZIP contains the installable skill payload only; it is not a Python package and is not installed with `pip`.

## Update or uninstall a copied skill

The copied `skills/arena/VERSION` file identifies the installed skill version. Confirm the source is a published release and inspect its version before updating. Keep the old folder as a reversible backup; do not merge files across versions.

PowerShell update (set `$source` to the new release's `skills\arena` folder and `$version` to its VERSION text):

```powershell
$version = (Get-Content (Join-Path $source 'VERSION') -Raw).Trim()
$currentVersion = (Get-Content (Join-Path $destination 'VERSION') -Raw).Trim()
if (-not $version -or $version -eq $currentVersion) { throw "Choose a different source version; installed version is $currentVersion." }
$backup = "$destination.backup-$currentVersion"
if (Test-Path $backup) { throw "Backup already exists: $backup" }
Move-Item -LiteralPath $destination -Destination $backup
try { Copy-Item -LiteralPath $source -Destination $destination -Recurse }
catch { Move-Item -LiteralPath $backup -Destination $destination; throw }
if ((Get-Content (Join-Path $destination 'VERSION') -Raw).Trim() -ne $version) {
  Remove-Item -LiteralPath $destination -Recurse
  Move-Item -LiteralPath $backup -Destination $destination
  throw 'Installed version check failed; previous skill restored.'
}
```

After verifying Arena works in a new session, remove the backup manually if you no longer need rollback. To uninstall, rename `skills/arena` to a backup name first, start a new session to confirm the skill is no longer discovered, then remove that backup if desired. These steps only affect the selected user skill folder; they do not uninstall a marketplace plugin.

macOS or Linux: compare `cat "$source/VERSION"` with `cat "$destination/VERSION"`, choose a unique backup path, move the old directory there, copy the new `skills/arena` directory into place, and verify `cat "$destination/VERSION"`. If copying or verification fails, remove only the new destination and move the backup back. For uninstall, move the destination aside, verify discovery in a new session, then remove it if desired.

OpenAI's current plugin documentation also describes packaging skills in a plugin and using a local marketplace in Codex. This repository's two manifests identify that package, but this release workflow provides a downloadable skill ZIP; it does not publish or install a marketplace entry. See [Package your plugin](https://developers.openai.com/plugins/build/plugins) for the official plugin and marketplace workflow.

## Use Arena

Ask Codex to use the skill and state the task. Flags are optional:

```text
$arena --quick Compare these two approaches and recommend one: ...
```

For a complex task, deliberately choose the four-candidate lean tournament:

```text
$arena --agents 4 Find the root cause of this failure and propose a fix: ...
```

These are live-use examples: a real request can launch model or agent work under the host's normal access, quota, and cost rules. The examples here are not executed as part of documentation checks. Ask Arena to plan before running when you want to inspect the count and budget first.

## Modes and call budget

- Default lean mode / `--quick`: 2 candidates and 3 planned calls for straightforward tasks.
- `--agents 4`: deliberate complex-task lean mode, 7 calls (4 drafts and 3 judge-and-improve matches).
- `--classic`: the original attack, defend, judge flow, with 5 calls per match. Four candidates require 19 total calls including their four initial drafts.
- `--agents N`: choose the field size.
- `--seed S`: make the strategy cards and bracket reproducible.
- `--wave W`: cap jobs launched together at observed available worker capacity; unknown capacity defaults to 1.
- `--max-calls C`: set the hard planned-call ceiling. It defaults to 32. Arena refuses a plan above that ceiling unless the user explicitly raises it.

The listed counts include initial drafts; comparing against a rejected baseline adds one final call.
Pass an explicit planned-call ceiling and per-wave limit for each run. More agents increase calls
and input/output bytes. Parallelism can reduce dependency waves only within actual worker capacity;
neither planned waves nor synthetic local timing measure model wall time. Byte-based token estimates
are rough proxies, not billed usage. Reserve 8 or more agents for cases where runtime capacity and
task-specific blind quality evidence justify the cost. There is no automatic complexity classifier.
The 100-candidate classic plan needs 595 calls and exceeds the default cap.

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

New lean runs require one atomic `.result.json` from the judge, containing strict verdict fields and
a nonempty `solution` string. The collector rejects trailing text, duplicate/extra/missing fields,
wrong identities, incomplete or invalid scores, a winner inconsistent with scoring, invalid UTF-8,
and recognizable leaked artifact commands or embedded verdicts. It never sanitizes an answer into success.
Rejected bytes are preserved as `.unreadable` with numbered suffixes. Presence checks do not validate
content; `collect` must succeed before advancement. Stop on invalid results and report the error;
no automatic model retry is authorized by the skill.

Only after validation does the collector stage both derived files and atomically replace each,
solution first and verdict last. Two separate files are not one filesystem transaction. A write
failure leaves the match unrecorded and retains the source result for deterministic local retry;
no additional judge call is needed for an extraction failure. Schema checks cannot prove answer quality.

Existing v0.3.2 states remain readable. Lean states without `lean_result_format` retain the legacy
two-file contract; classic and final verdicts also keep their previous validation behavior, including
the incomplete-score fallback. They do not gain the new strict-result guarantee retroactively.
Invalid saved state stops unchanged for inspection.

## Project history and license

This is an OpenAI orchestration and packaging adaptation of [Jake Schincariol's Arena project](https://github.com/Jakeschincariol/arena-skill). The inherited engine, strategy cards, rubric, and tests retain the original MIT attribution. See [`CREDITS.md`](CREDITS.md), [`LICENSE`](LICENSE), and [`CHANGELOG.md`](CHANGELOG.md).
