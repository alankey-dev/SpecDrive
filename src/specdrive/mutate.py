"""specdrive state mutations.

The state-transition layer: small functions that load state, change one thing,
save, and (for meaningful changes) append a decision-log line. The CLI wires
these to commands so an agent or human can drive a whole session without ever
hand-editing state.json.

state.py stays pure I/O; this module owns the "what is a legal change" intent.
Transition *guards* (rejecting illegal moves) are layered on in the hardening
bucket; here the happy path is implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from specdrive import state


def next_step(s: dict[str, Any]) -> str:
    """Pure: given a state dict, return guidance on what to do next.

    Read-only. Suggests the command to run; never runs it.
    """
    phase = s.get("phase")

    if phase == state.PHASE_GOAL:
        if not s.get("goal"):
            return ('Phase 1: set the goal — `specdrive goal set "<text>"` and '
                    '`specdrive decision set "<text>"`.')
        if not s.get("core_decision"):
            return 'Phase 1: set the core decision — `specdrive decision set "<text>"`.'
        return ("Phase 1: goal and core decision are set. Confirm them, then "
                "`specdrive phase 2-buckets`.")

    if phase == state.PHASE_BUCKETS:
        buckets = s.get("buckets") or []
        if not buckets:
            return ('Phase 2: add buckets — `specdrive bucket add "<name>"`, '
                    "then `specdrive phase 3-build`.")
        return (f"Phase 2: {len(buckets)} bucket(s) defined. Confirm the breakdown, "
                "then `specdrive phase 3-build`.")

    if phase == state.PHASE_BUILD:
        buckets = s.get("buckets") or []
        cur = s.get("current_bucket")
        b = next((x for x in buckets if x["id"] == cur), None)
        if b is None:
            if buckets and all(x["status"] == "approved" for x in buckets):
                return "All buckets approved. Set `specdrive phase done`."
            nxt = next((x for x in buckets if x["status"] == "pending"), None)
            if nxt:
                return f"Phase 3: start bucket {nxt['id']} — `specdrive bucket start {nxt['id']}`."
            return "Phase 3: no current bucket. Add or start one."
        if b["status"] == "pending":
            return f'Phase 3: start bucket {b["id"]} ({b["name"]}) — `specdrive bucket start {b["id"]}`.'
        if b["status"] == "building":
            return (f'Phase 3: build bucket {b["id"]} ({b["name"]}). Then checkpoint, '
                    f"drift-check, cross-check, and `specdrive bucket approve {b['id']}`.")
        if b["status"] == "approved":
            return "Bucket approved. Set `specdrive phase done` if all are approved."
        return f"Phase 3: bucket {b['id']} status is {b['status']}."

    if phase == state.PHASE_DONE:
        return ("Done. Summarise what was built and confirm it drives the core "
                "decision from Phase 1.")

    return f"Unknown phase '{phase}'. Set one with `specdrive phase <name>`."


def _find_bucket(s: dict[str, Any], bucket_id: int) -> dict[str, Any]:
    for b in s.get("buckets", []):
        if b["id"] == bucket_id:
            return b
    raise ValueError(f"no bucket with id {bucket_id}")


def set_goal(root: Path | str, text: str) -> None:
    s = state.load_state(root)
    s["goal"] = text
    state.save_state(root, s)
    state.append_decision(root, f"Goal set: {text}")


def set_decision(root: Path | str, text: str) -> None:
    s = state.load_state(root)
    s["core_decision"] = text
    state.save_state(root, s)
    state.append_decision(root, f"Core decision set: {text}")


def add_scope(root: Path | str, text: str) -> None:
    s = state.load_state(root)
    s.setdefault("out_of_scope", []).append(text)
    state.save_state(root, s)


def add_constraint(root: Path | str, text: str) -> None:
    s = state.load_state(root)
    s.setdefault("constraints", []).append(text)
    state.save_state(root, s)


def set_phase(root: Path | str, phase: str) -> None:
    s = state.load_state(root)
    cur_idx = state.PHASES.index(s["phase"])
    new_idx = state.PHASES.index(phase)
    if new_idx > cur_idx + 1:
        raise ValueError(
            f"cannot skip from {s['phase']} to {phase}; "
            f"move to {state.PHASES[cur_idx + 1]} first"
        )
    s["phase"] = phase
    state.save_state(root, s)
    state.append_decision(root, f"Phase set to {phase}.")


def add_bucket(root: Path | str, name: str) -> int:
    s = state.load_state(root)
    buckets = s.setdefault("buckets", [])
    new_id = max((b["id"] for b in buckets), default=0) + 1
    buckets.append({"id": new_id, "name": name, "status": "pending"})
    state.save_state(root, s)
    state.append_decision(root, f"Bucket {new_id} added: {name}")
    return new_id


def start_bucket(root: Path | str, bucket_id: int) -> dict[str, Any]:
    s = state.load_state(root)
    if s["phase"] != state.PHASE_BUILD:
        raise ValueError(f"buckets are built in phase {state.PHASE_BUILD}; current is {s['phase']}")
    b = _find_bucket(s, bucket_id)
    if b["status"] != "pending":
        raise ValueError(f"bucket {bucket_id} is {b['status']}, not pending; cannot start")
    b["status"] = "building"
    s["current_bucket"] = bucket_id
    state.save_state(root, s)
    state.append_decision(root, f"Bucket {bucket_id} started ({b['name']}).")
    return b


def approve_bucket(root: Path | str, bucket_id: int) -> dict[str, Any]:
    s = state.load_state(root)
    if s["phase"] != state.PHASE_BUILD:
        raise ValueError(f"buckets are approved in phase {state.PHASE_BUILD}; current is {s['phase']}")
    b = _find_bucket(s, bucket_id)
    if b["status"] != "building":
        raise ValueError(f"bucket {bucket_id} is {b['status']}, not building; run `bucket start {bucket_id}` first")
    b["status"] = "approved"
    # advance current_bucket to the next pending bucket, if any
    nxt = next((x["id"] for x in s["buckets"] if x["status"] == "pending"), None)
    s["current_bucket"] = nxt
    state.save_state(root, s)
    state.append_decision(root, f"Bucket {bucket_id} approved ({b['name']}).")
    return b
