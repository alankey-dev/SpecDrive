# specdrive

**Take a project from a fuzzy idea to a finished thing without drifting from the
goal.** A portable, agent-agnostic methodology for LLM coding agents.

specdrive runs a four-phase loop — find the real goal, break it into buckets,
build one bucket at a time, confirm done — and keeps a decision log so the build
never quietly wanders away from what you set out to make. It works inside any
coding agent (Claude Code, opencode, pi-agent, and others): the agent reads the
playbook and follows it, while state lives in plain files any agent can read.

> Distribution name is `specdrive`; the import / command name is `specflow`.

## Install

```sh
pipx install specdrive
# or
uvx specdrive --help
```

## Quickstart

```sh
cd your-project
specflow init                 # create .specflow/ state + fingerprint
specflow install claude-code  # or: specflow install generic
specflow status               # see phase, goal, buckets
```

Then, in your agent, run the playbook (the `/specflow` command if you installed
the claude-code adapter, or point the agent at `SPECFLOW.md` for the generic
adapter). The agent walks you through the phases.

## How it works

Three parts, one source of truth:

- **The playbook** (`specflow playbook`) — the methodology, written as direct
  instructions to the agent. This is the brain.
- **State files** in `.specflow/` — `state.json` (progress), `decision-log.md`
  (append-only log of locked decisions), and `fingerprint` (marks the project as
  specdrive-managed). Any agent reads and writes these, so a guided build can be
  paused and resumed across sessions and even across different agents.
- **Adapters** — `specflow install <agent>` drops a thin wrapper that points the
  agent at the playbook. Adapters embed the playbook at install time; re-run with
  `--force` to refresh after an upgrade.

The agent does the actual code-writing. specdrive orchestrates: it asks the
questions, enforces the checkpoints, and keeps the log.

## The four phases

1. **Find the real goal.** The agent interviews you to surface the actual goal
   and the single core decision the project must drive, then restates it and
   waits for your confirmation.
2. **Break it into buckets.** A breakdown into small, independently reviewable
   pieces, with a suggested order. You approve before any building starts.
3. **Build one bucket at a time.** For each bucket: plan → build → checkpoint →
   drift-check → cross-check → your approval. Nothing starts the next bucket
   until the current one is approved.
4. **Definition of done.** Every bucket approved and the combined result clearly
   drives the core decision from Phase 1.

## Commands

| Command | What it does |
|---------|--------------|
| `specflow init [path]` | Create `.specflow/` state, log, and fingerprint. `--force` resets. |
| `specflow status [path]` | Show phase, goal, core decision, buckets, cross-check mode. |
| `specflow playbook` | Print the methodology playbook. |
| `specflow install <agent> [path]` | Install an agent adapter (`claude-code`, `generic`). `--force` overwrites. |
| `specflow log [path]` | Print the decision log. |
| `specflow xcheck <mode> [path]` | Record the cross-model check mode (`codex-mcp`, `self-critique`, `none`). |

## Cross-model check

After each bucket, specdrive asks the agent to get a second opinion before you
sign off. If a second-model tool such as
[codex-mcp](https://github.com/tuannvm/codex-mcp-server) is available in the
agent, the playbook routes the bucket output through it, surfaces any
disagreement, and records the mode with `specflow xcheck codex-mcp`. If no second
model is available, the agent self-critiques instead and records
`specflow xcheck self-critique`.

## Supported agents

- **claude-code** — installs `.claude/commands/specflow.md` (use `/specflow`).
- **generic** — installs `SPECFLOW.md` at the project root; point any agent at it.

opencode and pi-agent are covered today by the generic adapter; native adapters
for them are planned.

## Development

```sh
pip install -e ".[dev]"
pytest
```
