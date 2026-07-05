# AI Agent Pipeline

AI Agent Pipeline is a local orchestration tool for disciplined AI-assisted
software development. It turns an informal agent workflow into an ordered,
auditable pipeline:

1. Define requirements with the human operator and design author agent.
2. Create and review the detailed design.
3. Approve an implementation plan with small phases.
4. Implement one phase at a time.
5. Run code review, test review, validation, and documentation review.
6. Preserve all review comments, decisions, commands, and artifacts.

The tool is intentionally not a replacement for human design judgment. It keeps
the creative requirements and design work interactive, then enforces the
engineering discipline around when implementation can start and how review
loops are recorded.

## Why This Exists

AI coding agents are useful, but they can drift when the project lacks a clear
process. This tool provides the process layer around those agents.

It helps by:

- Enforcing requirements before design, and design before implementation.
- Preventing an operator or agent from jumping into the middle of the pipeline.
- Breaking implementation into small reviewed phases instead of one large code
  dump.
- Keeping code review and test review as separate responsibilities.
- Recording an append-only history of agent actions and review comments.
- Supporting controlled iteration when later work exposes a requirement or
  design issue.
- Avoiding waterfall development by making requirement and design refinement a
  first-class change-control path.
- Allowing different agent CLIs to be used behind the same orchestration model.

## Current Status

The current implementation is a local runnable orchestrator prototype.

Implemented:

- Python package and CLI entry point.
- JSON-backed run state under `.agent-pipeline/`.
- Ordered stage gates for requirements, design, planning, implementation,
  validation, and documentation review.
- Explicit human approvals and Design Author confirmations for required
  baseline gates.
- Artifact snapshots, approval records, decisions, review issues, change
  requests, baseline invalidations, and activity events.
- Append-only issue lifecycle transitions.
- Phase start, review, test review, drift, and commit commands.
- Final validation and documentation review gates.
- Change-control classify, approve, and reopen behavior.
- Summary and trace reports.
- Runtime adapter scaffolding for manual, generic CLI, Codex exec, and Codex
  SDK runtimes.
- Unit tests for pipeline state, gates, runtime adapters, phase flow,
  validation, documentation review, change control, and reporting.

Extension points:

- The Codex exec and generic CLI adapters can invoke configured agent CLIs.
- `CodexSdkRuntime` remains a documented extension point.
- Documentation review has deterministic checks and can also consume
  documentation-agent issue records.

## Install For Development

The project currently has no third-party runtime dependencies. Python 3.10 or
newer is required.

Run directly from a checkout:

```bash
PYTHONPATH=src python -m ai_pipeline --help
```

Or install in editable mode:

```bash
python -m pip install -e .
ai-pipeline --help
```

## Basic Usage

Initialize a pipeline run:

```bash
PYTHONPATH=src python -m ai_pipeline init
```

Show the current run state:

```bash
PYTHONPATH=src python -m ai_pipeline status
```

The initial active stage is `requirements`. The pipeline will reject later
stage commands until the required predecessor gates pass.

Create `docs/requirements.md`, then complete the requirements stage:

```bash
mkdir -p docs
printf '# Requirements\n' > docs/requirements.md
PYTHONPATH=src python -m ai_pipeline stage requirements \
  --human-approved \
  --author-confirmed
```

The active stage becomes `design`.

Create `docs/detailed-design.md`, then move through design and design review:

```bash
printf '# Detailed Design\n' > docs/detailed-design.md
PYTHONPATH=src python -m ai_pipeline stage design \
  --human-approved
PYTHONPATH=src python -m ai_pipeline stage design-review
PYTHONPATH=src python -m ai_pipeline stage design-acceptance \
  --human-approved
```

Create `docs/implementation-plan.md`, then approve the plan stage:

```bash
printf '# Implementation Plan\n' > docs/implementation-plan.md
PYTHONPATH=src python -m ai_pipeline stage plan \
  --human-approved \
  --author-confirmed
```

Each implementation-plan phase must include a `Requirements:` line that
references requirement ids from `docs/requirements.md`, such as `REQ-1`.

At this point the run advances to the `implementation` stage. Start one phase,
record code review and test review, then record the verified git commit SHA:

```bash
PYTHONPATH=src python -m ai_pipeline phase start 1
PYTHONPATH=src python -m ai_pipeline phase review 1 --pass
PYTHONPATH=src python -m ai_pipeline phase test 1 --pass
PYTHONPATH=src python -m ai_pipeline phase commit 1 --sha <commit-sha>
```

The phase commit command verifies that the SHA exists in the repository. A
second phase cannot start while another phase is active.

After all planned phases are committed, complete implementation and run
validation:

```bash
PYTHONPATH=src python -m ai_pipeline stage implementation
PYTHONPATH=src python -m ai_pipeline validate
```

Validation commands run as argument vectors. Use `--shell-command` only when
shell behavior is required:

```bash
PYTHONPATH=src python -m ai_pipeline validate \
  --command python -m unittest discover -s tests
PYTHONPATH=src python -m ai_pipeline validate \
  --shell-command "python -m unittest discover -s tests"
```

Complete final documentation review after validation passes:

```bash
PYTHONPATH=src python -m ai_pipeline docs-review
```

## Flow Enforcement

The CLI records one active stage in
`.agent-pipeline/runs/<run-id>/manifest.json`. Mutating commands must match
that active stage and pass predecessor gates.

For example, this fails immediately after `init`:

```bash
PYTHONPATH=src python -m ai_pipeline stage plan
```

The command is blocked because the run is still at `requirements`. This is the
core software engineering rule enforced by the orchestrator: no implementation
planning before requirements and design are approved.

Useful inspection commands:

```bash
PYTHONPATH=src python -m ai_pipeline status
PYTHONPATH=src python -m ai_pipeline resume
PYTHONPATH=src python -m ai_pipeline report summary
PYTHONPATH=src python -m ai_pipeline report trace
PYTHONPATH=src python -m ai_pipeline gate requirements
PYTHONPATH=src python -m ai_pipeline gate implementation
```

## Change Control

Later pipeline stages may reveal a missing requirement, design drift, or an
implementation-plan gap. Those cases must reopen the earliest affected
baseline instead of jumping directly into an arbitrary stage.

Open a change-control request:

```bash
PYTHONPATH=src python -m ai_pipeline change open \
  --baseline requirements \
  --reason "Validation found an undocumented setup workflow."
```

Show open requests:

```bash
PYTHONPATH=src python -m ai_pipeline change status
```

Classify the earliest affected baseline, record human approval, then reopen:

```bash
PYTHONPATH=src python -m ai_pipeline change classify CR-0001 \
  --baseline requirements
PYTHONPATH=src python -m ai_pipeline change approve CR-0001 --human-approved
PYTHONPATH=src python -m ai_pipeline change reopen CR-0001
```

Reopening invalidates downstream gates and matching artifact snapshots. The
pipeline resumes from the reopened baseline stage.

## Agent Runtime Configuration

The design supports configurable agent runtimes. Codex is the default target,
but the pipeline is intended to support any CLI that can satisfy the adapter
contract, including Claude or a local agent command.

A compatible agent CLI must be able to:

- Run non-interactively.
- Receive a role prompt and context bundle.
- Return output that can be parsed into the pipeline's `AgentResult`.
- Make filesystem write behavior clear to the orchestrator.
- Keep credentials outside repository files and durable run state.

Runtime configuration shape:

```toml
[runtime]
default = "codex"

[runtimes.codex]
adapter = "codex_exec"
command = "codex"
args = ["exec", "--json"]
structured_output = "json_schema"

[runtimes.claude]
adapter = "generic_cli"
command = "claude"
args = ["--print"]
structured_output = "prompt_contract"

[roles]
design_review = "codex"
coding = "codex"
code_review = "claude"
test_review = "codex"
documentation = "codex"
```

Codex review roles run with `--sandbox read-only` by default. Coding and
documentation-writing roles run with `--sandbox workspace-write` unless the
runtime configuration supplies an explicit sandbox option.

## State Files

Pipeline state is stored under `.agent-pipeline/`.

Important files:

- `current-run` stores the active run id.
- `runs/<run-id>/manifest.json` stores active stage and completed gates.
- `runs/<run-id>/activity-log.jsonl` stores run events.
- `runs/<run-id>/change-requests.jsonl` stores change-control requests.
- `runs/<run-id>/approvals.jsonl` stores human and agent approvals.
- `runs/<run-id>/baseline-invalidations.jsonl` stores invalidated gates and
  snapshots.
- `runs/<run-id>/*-review.jsonl` stores append-only issue lifecycle records.
- `runs/<run-id>/artifact-snapshots.jsonl` stores approved artifact snapshots.

The `.agent-pipeline/` directory is ignored by git because it contains local
run history.

## Development

Run tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run the CLI smoke check:

```bash
PYTHONPATH=src python -m ai_pipeline --help
```

Run a full smoke check:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m unittest discover -s tests
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -m ai_pipeline --help
```
