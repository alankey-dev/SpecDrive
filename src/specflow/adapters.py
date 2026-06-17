"""specflow agent adapters.

An adapter makes specflow invokable inside a specific coding agent. Each adapter
is a thin wrapper: an agent-specific header plus the canonical playbook rendered
in at install time. The playbook (playbook.md, package data) stays the single
source of truth; re-run `install --force` to refresh an adapter after the
playbook changes.

Adding a new agent = add one entry to ADAPTERS. Nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Callable


def _playbook() -> str:
    return (files("specflow") / "playbook.md").read_text(encoding="utf-8")


def _claude_code(playbook: str) -> str:
    return (
        "---\n"
        "description: Run the specflow methodology (idea to finished thing, no drift)\n"
        "---\n\n"
        "Follow the specflow playbook below exactly. Read the project's "
        "`.specflow/state.json` and `decision-log.md` first; if absent, start at "
        "Phase 1.\n\n"
        "---\n\n" + playbook
    )


def _generic(playbook: str) -> str:
    return (
        "# specflow (read me and follow)\n\n"
        "This project uses the specflow methodology. Read the playbook below and "
        "follow it exactly. Check `.specflow/state.json` and `decision-log.md` for "
        "where things stand; if absent, start at Phase 1.\n\n"
        "---\n\n" + playbook
    )


@dataclass(frozen=True)
class Adapter:
    name: str
    relative_path: str  # where the adapter file lands, relative to project root
    render: Callable[[str], str]
    note: str


ADAPTERS: dict[str, Adapter] = {
    "claude-code": Adapter(
        name="claude-code",
        relative_path=".claude/commands/specflow.md",
        render=_claude_code,
        note="Use the /specflow slash command in Claude Code.",
    ),
    "generic": Adapter(
        name="generic",
        relative_path="SPECFLOW.md",
        render=_generic,
        note="Point any agent at SPECFLOW.md (works everywhere).",
    ),
}


def install_adapter(agent: str, root: Path | str, *, force: bool = False) -> Path:
    """Render and write the adapter for `agent` into the project. Returns its path."""
    if agent not in ADAPTERS:
        known = ", ".join(sorted(ADAPTERS))
        raise KeyError(f"unknown agent '{agent}'; known: {known}")
    adapter = ADAPTERS[agent]
    target = Path(root) / adapter.relative_path
    if target.exists() and not force:
        raise FileExistsError(f"{target} exists; pass force=True to overwrite")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(adapter.render(_playbook()), encoding="utf-8")
    return target
