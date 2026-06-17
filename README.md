# specdrive

**Take a project from a fuzzy idea to a finished thing without drifting from the
goal.** A portable, agent-agnostic methodology for LLM coding agents.

specdrive runs a four-phase loop — find the real goal, break it into buckets,
build one bucket at a time, confirm done — and keeps a decision log so the build
never quietly wanders away from what you set out to make. It works inside any
coding agent (Claude Code, opencode, pi-agent, and others): the agent reads the
playbook and follows it, while state lives in plain files any agent can read.

## Install

```sh
pipx install specdrive
# or
uvx specdrive --help
```

## Quickstart

```sh
cd your-project
specdrive init                 # create .specdrive/ state + fingerprint
specdrive install claude-code  # or: specdrive install generic
specdrive status               # see phase, goal, buckets
```

Then, in your agent, run the playbook (the `/specdrive` command if you installed
the claude-code adapter, or point the agent at `SPECDRIVE.md` for the generic
adapter). The agent walks you through the phases.

## How it works

Three parts, one source of truth:

- **The playbook** (`specdrive playbook`) — the methodology, written as direct
  instructions to the agent. This is the brain.
- **State files** in `.specdrive/` — `state.json` (progress), `decision-log.md`
  (append-only log of locked decisions), and `fingerprint` (marks the project as
  specdrive-managed). Any agent reads and writes these, so a guided build can be
  paused and resumed across sessions and even across different agents.
- **Adapters** — `specdrive install <agent>` drops a thin wrapper that points the
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
| `specdrive init [path]` | Create `.specdrive/` state, log, and fingerprint. `--force` resets. |
| `specdrive status [path]` | Show phase, goal, core decision, buckets, cross-check mode. |
| `specdrive next [path]` | Show what to do next (and the command to run). |
| `specdrive goal set "<text>"` | Set the Phase 1 goal. |
| `specdrive decision set "<text>"` | Set the core decision. |
| `specdrive scope add "<text>"` / `constraint add "<text>"` | Append to the out-of-scope / constraints list. |
| `specdrive phase <name>` | Advance the phase (forward-skips are blocked). |
| `specdrive bucket add "<name>"` | Append a bucket. |
| `specdrive bucket start <id>` / `bucket approve <id>` | Move a bucket through building → approved. |
| `specdrive log-add "<text>"` | Append a line to the decision log. |
| `specdrive log [path]` | Print the decision log. |
| `specdrive validate [path]` | Check `state.json` is structurally sound. |
| `specdrive playbook` | Print the methodology playbook. |
| `specdrive install <agent> [path]` | Install an agent adapter (`claude-code`, `generic`). `--force` overwrites. |
| `specdrive xcheck <mode> [path]` | Record the cross-model check mode (`codex-mcp`, `self-critique`, `none`). |

You drive a whole session through these commands — no hand-editing of state. The
agent runs `specdrive next` to see what is due, then the suggested command:

```sh
specdrive goal set "a CLI that does X for Y"
specdrive decision set "can a user do X in one command?"
specdrive phase 2-buckets
specdrive bucket add "parser"
specdrive bucket add "output formatter"
specdrive phase 3-build
specdrive bucket start 1   # build it...
specdrive bucket approve 1
```

## Cross-model check

After each bucket, specdrive asks the agent to get a second opinion before you
sign off. If a second-model tool such as
[codex-mcp](https://github.com/tuannvm/codex-mcp-server) is available in the
agent, the playbook routes the bucket output through it, surfaces any
disagreement, and records the mode with `specdrive xcheck codex-mcp`. If no second
model is available, the agent self-critiques instead and records
`specdrive xcheck self-critique`.

## Supported agents

- **claude-code** — installs `.claude/commands/specdrive.md` (use `/specdrive`).
- **generic** — installs `SPECDRIVE.md` at the project root; point any agent at it.

opencode and pi-agent are covered today by the generic adapter; native adapters
for them are planned.

## Development

```sh
pip install -e ".[dev]"
pytest
```
