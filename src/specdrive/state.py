"""specdrive state: read/write the .specdrive/ directory.

This module is the single place that touches on-disk state. The CLI and any
agent adapter go through these functions so the state contract in playbook.md
stays authoritative and consistent.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "0.1.0"

# Directory layout (see "State contract" in playbook.md).
DIR_NAME = ".specdrive"
STATE_FILE = "state.json"
DECISION_LOG_FILE = "decision-log.md"
FINGERPRINT_FILE = "fingerprint"

CROSS_CHECK_MODES = ("codex-mcp", "self-critique", "none")

PHASE_GOAL = "1-goal"
PHASE_BUCKETS = "2-buckets"
PHASE_BUILD = "3-build"
PHASE_DONE = "done"

_DL_LINE = re.compile(r"^DL-(\d+)\b")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def specdrive_dir(root: Path | str) -> Path:
    return Path(root) / DIR_NAME


def _state_path(root: Path | str) -> Path:
    return specdrive_dir(root) / STATE_FILE


def _log_path(root: Path | str) -> Path:
    return specdrive_dir(root) / DECISION_LOG_FILE


def _fingerprint_path(root: Path | str) -> Path:
    return specdrive_dir(root) / FINGERPRINT_FILE


def default_state() -> dict[str, Any]:
    """Fresh state matching the frozen schema in playbook.md."""
    return {
        "specdrive_version": SCHEMA_VERSION,
        "phase": PHASE_GOAL,
        "goal": "",
        "core_decision": "",
        "out_of_scope": [],
        "constraints": [],
        "buckets": [],
        "current_bucket": None,
        "cross_check": "none",
    }


def is_managed(root: Path | str) -> bool:
    """True if this project carries the specdrive fingerprint."""
    return _fingerprint_path(root).is_file()


def init_state(root: Path | str, *, force: bool = False) -> dict[str, Any]:
    """Create .specdrive/ with fresh state, empty log, and fingerprint.

    Refuses to clobber an existing project unless force=True.
    """
    root = Path(root)
    sf = specdrive_dir(root)
    if is_managed(root) and not force:
        raise FileExistsError(f"{sf} already specdrive-managed; pass force=True to reset")

    sf.mkdir(parents=True, exist_ok=True)

    state = default_state()
    save_state(root, state)

    if not _log_path(root).exists() or force:
        _log_path(root).write_text(
            "# specdrive decision log\n\n"
            "Append-only. One locked decision per line as `DL-N  <decision>`.\n\n",
            encoding="utf-8",
        )

    fingerprint = {
        "tool": "specdrive",
        "version": SCHEMA_VERSION,
        "created": _now(),
    }
    _fingerprint_path(root).write_text(
        json.dumps(fingerprint, indent=2) + "\n", encoding="utf-8"
    )

    return state


def load_state(root: Path | str) -> dict[str, Any]:
    """Load state.json. Raises FileNotFoundError if not managed."""
    path = _state_path(root)
    if not path.is_file():
        raise FileNotFoundError(f"no specdrive state at {path}; run init first")
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_state(root: Path | str, data: dict[str, Any]) -> None:
    """Write state.json atomically."""
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def _next_dl_number(log_text: str) -> int:
    nums = [int(m.group(1)) for line in log_text.splitlines() if (m := _DL_LINE.match(line))]
    return max(nums, default=0) + 1


def append_decision(root: Path | str, text: str) -> str:
    """Append an auto-numbered DL-N line to decision-log.md. Returns the line."""
    path = _log_path(root)
    existing = path.read_text(encoding="utf-8") if path.is_file() else ""
    n = _next_dl_number(existing)
    line = f"DL-{n}  {text.strip()}"
    if existing and not existing.endswith("\n"):
        existing += "\n"
    path.write_text(existing + line + "\n", encoding="utf-8")
    return line
