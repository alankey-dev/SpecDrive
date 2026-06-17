"""specdrive agent adapters.

An adapter makes specdrive discoverable inside a specific coding agent. Each
adapter is a thin pointer: a small file (or a managed block in a shared file)
that tells the agent to read `.specdrive/playbook.md` and follow it. The playbook
itself is the single source of truth and is committed into the project by
`specdrive init`; adapters never embed a copy, so they never go stale.

There is no runtime CLI in the loop: once installed, the agent runs the whole
methodology by reading and writing the plain `.specdrive/` files directly.

Adding a new agent = add one entry to ADAPTERS. Nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

BLOCK_BEGIN = "<!-- specdrive:begin -->"
BLOCK_END = "<!-- specdrive:end -->"

# What the agent is told to do. Kept identical across adapters so behaviour does
# not depend on which agent picked it up.
_POINTER_BODY = (
    "This project uses the **specdrive** methodology (idea to finished thing, no "
    "drift). Read `.specdrive/playbook.md` and follow it exactly. First read "
    "`.specdrive/state.json` and `.specdrive/decision-log.md` to see where things "
    "stand; if `.specdrive/` does not exist yet, create it as the playbook "
    "describes and start at Phase 1. You read and write those state files "
    "directly — there is no CLI to call."
)


def _claude_code() -> str:
    return (
        "---\n"
        "description: Run the specdrive methodology (idea to finished thing, no drift)\n"
        "---\n\n" + _POINTER_BODY + "\n"
    )


def _generic() -> str:
    return "# specdrive (read me and follow)\n\n" + _POINTER_BODY + "\n"


def _agents_block() -> str:
    return "## specdrive\n\n" + _POINTER_BODY + "\n"


@dataclass(frozen=True)
class Adapter:
    name: str
    relative_path: str  # where the adapter lands, relative to project root
    render: "object"  # callable returning the adapter text
    note: str
    shared: bool = False  # True => merge a managed block into an existing file


ADAPTERS: dict[str, Adapter] = {
    "claude-code": Adapter(
        name="claude-code",
        relative_path=".claude/commands/specdrive.md",
        render=_claude_code,
        note="Use the /specdrive slash command in Claude Code.",
    ),
    "generic": Adapter(
        name="generic",
        relative_path="SPECDRIVE.md",
        render=_generic,
        note="Point any agent at SPECDRIVE.md (works everywhere).",
    ),
    "codex": Adapter(
        name="codex",
        relative_path="AGENTS.md",
        render=_agents_block,
        note="Codex reads AGENTS.md; a specdrive block was added to it.",
        shared=True,
    ),
    "pi-agent": Adapter(
        name="pi-agent",
        relative_path="AGENTS.md",
        render=_agents_block,
        note="pi-agent reads AGENTS.md; a specdrive block was added to it.",
        shared=True,
    ),
}


def _merge_block(existing: str, block: str) -> str:
    """Insert or replace the specdrive managed block within `existing`."""
    wrapped = f"{BLOCK_BEGIN}\n{block.rstrip()}\n{BLOCK_END}\n"
    start = existing.find(BLOCK_BEGIN)
    end = existing.find(BLOCK_END)
    if start != -1 and end != -1 and end > start:
        end += len(BLOCK_END)
        # consume a trailing newline so we do not accumulate blank lines
        if end < len(existing) and existing[end] == "\n":
            end += 1
        return existing[:start] + wrapped + existing[end:]
    if existing and not existing.endswith("\n"):
        existing += "\n"
    sep = "\n" if existing else ""
    return existing + sep + wrapped


def install_adapter(agent: str, root: Path | str, *, force: bool = False) -> Path:
    """Render and write the adapter for `agent` into the project. Returns its path.

    Dedicated-file adapters refuse to clobber without `force`. Shared-file
    adapters (e.g. AGENTS.md) merge an idempotent managed block instead, leaving
    any surrounding content untouched, so `force` is not needed for them.
    """
    if agent not in ADAPTERS:
        known = ", ".join(sorted(ADAPTERS))
        raise KeyError(f"unknown agent '{agent}'; known: {known}")
    adapter = ADAPTERS[agent]
    target = Path(root) / adapter.relative_path
    target.parent.mkdir(parents=True, exist_ok=True)

    if adapter.shared:
        existing = target.read_text(encoding="utf-8") if target.exists() else ""
        target.write_text(_merge_block(existing, adapter.render()), encoding="utf-8")
        return target

    if target.exists() and not force:
        raise FileExistsError(f"{target} exists; pass force=True to overwrite")
    target.write_text(adapter.render(), encoding="utf-8")
    return target
