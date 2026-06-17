# specdrive

Take a project from a fuzzy idea to a finished thing without drifting from the
goal. A portable, agent-agnostic methodology for LLM coding agents.

specdrive runs a four-phase loop (find the goal, break it into buckets, build
one bucket at a time, confirm done) and keeps a decision log so the build never
quietly wanders off. It works inside any coding agent: the agent reads the
playbook and follows it, and the state lives in plain files the agent reads and
writes directly.

**No CLI in the loop.** Like [spec-kit](https://github.com/github/spec-kit),
specdrive ships a tiny bootstrap CLI whose only job is to scaffold a project. The
methodology itself runs entirely on committed Markdown + JSON files, so the agent
never needs a `specdrive` binary on its PATH. That is what makes it work cleanly
in web / cloud agents.

## Install (the bootstrap CLI)

```sh
pipx install specdrive
# or run it without installing:
uvx specdrive --help
```

You only need this on the machine where you scaffold a project. The agent that
later runs the methodology does **not** need specdrive installed.

## Quickstart

```sh
cd your-project
specdrive init --agent claude-code   # scaffold .specdrive/ + the agent adapter
git add .specdrive AGENTS.md SPECDRIVE.md .claude && git commit -m "add specdrive"
```

`init` creates a `.specdrive/` directory (state, decision log, a committed copy of
the playbook, and a fingerprint) and installs the adapter for your agent. Then,
in your agent, run the `/specdrive` command (Claude Code) or just tell it to
"follow specdrive" — it reads `.specdrive/playbook.md` and drives the rest.

Pick your agent with `--agent` (or run `specdrive install <agent>` later):

| `--agent` | What it installs | How you invoke it |
|-----------|------------------|-------------------|
| `claude-code` | `.claude/commands/specdrive.md` | the `/specdrive` slash command |
| `codex` | a managed block in `AGENTS.md` | tell Codex to "run specdrive" |
| `pi-agent` | a managed block in `AGENTS.md` | tell pi-agent to "run specdrive" |
| `generic` | `SPECDRIVE.md` at the repo root | point any agent at `SPECDRIVE.md` |

The `AGENTS.md` adapters merge an idempotent block, so they never clobber your
existing instructions, and Codex + pi-agent can share one file.

## Using it with web / cloud agents

This is the whole point of the bootstrap-only design: the agent runs specdrive
from files in the repo, with nothing to install in the cloud environment.

1. **Once, locally** (or in any environment with the CLI): scaffold and commit.

   ```sh
   specdrive init --agent claude-code   # or codex / pi-agent / generic
   git add .specdrive .claude AGENTS.md SPECDRIVE.md
   git commit -m "add specdrive" && git push
   ```

2. **In the web / cloud agent**: open the repo and run `/specdrive` (Claude Code
   on the web) or tell the agent to "follow specdrive". It reads the committed
   `.specdrive/playbook.md`, sees where things stand in `.specdrive/state.json`,
   and continues — pausing at every checkpoint for your approval.

Because all state is committed plain files, a build can pause in one session and
resume in another, even across different agents.

> No CLI at all? You can skip the bootstrap entirely: copy `SPECDRIVE.md` (run
> `specdrive playbook` to print the methodology, or grab it from this repo) into
> your project and tell the agent to follow it. It will create `.specdrive/`
> itself on first run, exactly as the playbook describes.

## How it works

Two parts, committed to your repo:

- **The playbook** (`.specdrive/playbook.md`). The methodology, written as direct
  instructions to the agent. `init` drops it into the project so it always
  travels with the repo; `specdrive playbook` prints the canonical copy.
- **State files** in `.specdrive/`: `state.json` (progress), `decision-log.md`
  (append-only log of locked decisions), and `fingerprint` (marks the project as
  specdrive-managed). The agent reads and writes these directly per the rules in
  the playbook — no CLI, no daemon.

The agent writes the code *and* keeps the state. specdrive is the discipline: it
asks the questions, enforces the checkpoints, and keeps the log honest.

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

## Cross-model check

After each bucket, specdrive asks for a second opinion before you sign off. If a
second-model tool such as
[codex-mcp](https://github.com/tuannvm/codex-mcp-server) is available, the
playbook routes the bucket output through it and surfaces any disagreement.
Otherwise the agent self-critiques. The method used is recorded in `state.json`
under `cross_check`.

## CLI reference

The CLI only scaffolds and inspects; it never drives the workflow.

| Command | What it does |
|---------|--------------|
| `specdrive init [path] [--agent <agent>] [--force]` | Create `.specdrive/` state, log, playbook, and fingerprint; optionally install an adapter. |
| `specdrive install <agent> [path] [--force]` | Install an agent adapter (`claude-code`, `codex`, `pi-agent`, `generic`). |
| `specdrive playbook` | Print the canonical methodology playbook. |
| `specdrive validate [path]` | Check `.specdrive/state.json` is structurally sound. |

## Development

```sh
pip install -e ".[dev]"
pytest
```
