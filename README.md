# specdrive

Take a project from a fuzzy idea to a finished thing without drifting from the
goal. A portable, agent-agnostic methodology for LLM coding agents.

specdrive runs a four-phase loop (find the goal, break it into buckets, build
one bucket at a time, confirm done) and keeps a decision log so the build never
quietly wanders off. It works inside any coding agent: the agent reads the
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

Then run the playbook in your agent: the `/specdrive` command if you installed
the claude-code adapter, or point the agent at `SPECDRIVE.md` for the generic
one.

## How it works

Three parts, one source of truth:

- **The playbook** (`specdrive playbook`). The methodology, written as direct
  instructions to the agent.
- **State files** in `.specdrive/`. `state.json` (progress), `decision-log.md`
  (append-only log of locked decisions), and `fingerprint` (marks the project
  as specdrive-managed). Any agent reads and writes these, so a build can pause
  and resume across sessions and across agents.
- **Adapters**. `specdrive install <agent>` drops a thin wrapper pointing the
  agent at the playbook. Adapters embed the playbook at install time; re-run
  with `--force` after an upgrade.

The agent writes the code. specdrive orchestrates: it asks the questions,
enforces the checkpoints, and keeps the log.

## The four phases

1. **Find the real goal.** The agent interviews you to surface the goal and the
   single core decision the project must drive, then restates it and waits for
   confirmation.
2. **Break it into buckets.** Small, independently reviewable pieces with a
   suggested order. You approve before any building starts.
3. **Build one bucket at a time.** For each: plan, build, checkpoint,
   drift-check, cross-check, your approval. The next bucket waits until the
   current one is approved.
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
| `specdrive bucket start <id>` / `bucket approve <id>` | Move a bucket through building to approved. |
| `specdrive log-add "<text>"` | Append a line to the decision log. |
| `specdrive log [path]` | Print the decision log. |
| `specdrive validate [path]` | Check `state.json` is structurally sound. |
| `specdrive playbook` | Print the methodology playbook. |
| `specdrive install <agent> [path]` | Install an agent adapter (`claude-code`, `generic`). `--force` overwrites. |
| `specdrive uninstall [path]` | Remove `.specdrive/` state and adapters (incl. legacy `specflow` ones). `--yes` skips the prompt; `--state-only` / `--adapters-only` narrow it. |
| `specdrive xcheck <mode> [path]` | Record the cross-model check mode (`codex-mcp`, `self-critique`, `none`). |

Drive a whole session through these commands; no hand-editing of state. The
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

After each bucket, specdrive asks the agent for a second opinion before you sign
off. If a second-model tool such as
[codex-mcp](https://github.com/tuannvm/codex-mcp-server) is available, the
playbook routes the bucket output through it, surfaces any disagreement, and
records the mode with `specdrive xcheck codex-mcp`. Otherwise the agent
self-critiques and records `specdrive xcheck self-critique`.

## Supported agents

- **claude-code**. Installs `.claude/commands/specdrive.md` (use `/specdrive`).
- **generic**. Installs `SPECDRIVE.md` at the project root; point any agent at it.

opencode and pi-agent work today via the generic adapter; native adapters are
planned.

## Development

```sh
pip install -e ".[dev]"
pytest
```
