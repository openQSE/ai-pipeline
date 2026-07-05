# API Documentation

## Public CLI

The public interface is the `ai-pipeline` command. The same CLI can be run
from source with `PYTHONPATH=src python -m ai_pipeline`.

Top-level commands:

- `init` creates a run under `.agent-pipeline/`.
- `status` prints active stage, active phase, completed gates, invalidated
  gates, open requests, open issues, and blocked gates.
- `resume` prints the state needed to continue an interrupted run.
- `report summary` writes or prints a run summary.
- `report trace` writes or prints the activity trace.
- `stage` completes the active pipeline stage when approvals and gates pass.
- `gate` evaluates a deterministic gate and records the result.
- `phase` manages phase start, review, test review, drift, and commit state.
- `validate` runs final validation commands and writes a validation report.
- `docs-review` verifies final documentation and snapshots passing docs.
- `plan` checks or records implementation-plan updates.
- `issues` records append-only review issue lifecycle events.
- `agent` invokes the configured runtime for an agent role.
- `artifacts` creates artifact templates and snapshots artifacts.
- `change` manages change-control requests, approvals, and reopening.

## Stage Commands

Stage commands enforce the ordered pipeline.

```bash
ai-pipeline stage requirements --human-approved --author-confirmed
ai-pipeline stage design --human-approved
ai-pipeline stage design-review
ai-pipeline stage design-acceptance --human-approved
ai-pipeline stage plan --human-approved --author-confirmed
ai-pipeline stage implementation
```

`requirements`, `design`, `design-acceptance`, and `plan` require explicit
approval flags unless the approval records already exist for the run.

## Phase Commands

```bash
ai-pipeline phase start <n>
ai-pipeline phase review <n> --pass
ai-pipeline phase test <n> --pass
ai-pipeline phase drift <n> --reason <text>
ai-pipeline phase commit <n> --sha <commit-sha>
```

Only one implementation phase can be active. Review and test review commands
must target the active phase. `phase commit` verifies that the supplied SHA is
an existing git commit and stores it in phase status.

## Validation Commands

`validate` runs validation commands as argument vectors.

```bash
ai-pipeline validate --command python -m unittest discover -s tests
```

Use `--shell-command` only when shell behavior is required.

```bash
ai-pipeline validate --shell-command "python -m unittest discover -s tests"
```

Validation writes `validation-report.md` under the run artifact directory and
stores failures in `validation-review.jsonl`.

## Change Control Commands

```bash
ai-pipeline change open --baseline requirements --reason <text>
ai-pipeline change classify CR-0001 --baseline requirements
ai-pipeline change approve CR-0001 --human-approved
ai-pipeline change reopen CR-0001
ai-pipeline change status
```

`reopen` requires a classified and human-approved request. It invalidates
downstream gates and records affected artifact snapshot refs.

## Issue Commands

```bash
ai-pipeline issues add <file> --id <id> --source <agent> \
  --severity major --summary <text>
ai-pipeline issues transition <file> <id> --status fixed
ai-pipeline issues resolve <file> <id>
ai-pipeline issues list <file>
```

Review issue files are append-only JSONL logs. Reads collapse lifecycle events
to the latest state for each issue id.

## Runtime Configuration

`agent-pipeline.toml` selects agent runtimes.

```toml
[runtime]
default = "codex"

[runtimes.codex]
adapter = "codex_exec"
command = "codex"
args = ["exec", "--json"]

[roles]
code_review = "codex"
```

Codex review roles run in `read-only` sandbox mode by default. Coding and
documentation-writing roles run in `workspace-write` mode unless the runtime
sets an explicit sandbox option.

## Public Python Modules

- `ai_pipeline.cli` contains the CLI parser and command handlers.
- `ai_pipeline.models` contains versioned state models.
- `ai_pipeline.state_store` reads and writes `.agent-pipeline` state.
- `ai_pipeline.gates` evaluates deterministic gates.
- `ai_pipeline.artifacts` creates templates and snapshots artifacts.
- `ai_pipeline.planning` parses requirement and phase traceability.
- `ai_pipeline.runtime` selects configured agent runtimes.
- `ai_pipeline.adapters.*` implements runtime adapter contracts.
