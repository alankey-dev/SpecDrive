"""specdrive command-line interface.

Thin wiring over specdrive.state. Commands let any agent (or human) create and
inspect specdrive state from the shell. The methodology itself lives in
playbook.md; `specdrive playbook` prints it so an agent can read and follow it.
"""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

from specdrive import adapters, mutate, state


def _read_playbook() -> str:
    return (files("specdrive") / "playbook.md").read_text(encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        state.init_state(root, force=args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --force to reset existing specdrive state", file=sys.stderr)
        return 1
    print(f"specdrive initialised in {state.specdrive_dir(root)}")
    print("next: run `specdrive playbook` and start Phase 1 (Find the real goal).")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not state.is_managed(root):
        print(f"not specdrive-managed: {root}")
        print("hint: run `specdrive init` to start.")
        return 1
    s = state.load_state(root)
    print(f"specdrive {s['specdrive_version']}  |  phase: {s['phase']}")
    if s["goal"]:
        print(f"goal:          {s['goal']}")
    if s["core_decision"]:
        print(f"core decision: {s['core_decision']}")
    print(f"cross-check:   {s['cross_check']}")
    buckets = s.get("buckets") or []
    if buckets:
        print("buckets:")
        for b in buckets:
            marker = ">" if b["id"] == s.get("current_bucket") else " "
            print(f"  {marker} {b['id']}. {b['name']}  [{b['status']}]")
    else:
        print("buckets:       (none yet)")
    return 0


def cmd_playbook(_args: argparse.Namespace) -> int:
    print(_read_playbook())
    return 0


def cmd_log(args: argparse.Namespace) -> int:
    root = Path(args.path)
    log = state.specdrive_dir(root) / state.DECISION_LOG_FILE
    if not log.is_file():
        print(f"no decision log at {log}", file=sys.stderr)
        return 1
    print(log.read_text(encoding="utf-8").rstrip())
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    try:
        target = adapters.install_adapter(args.agent, args.path, force=args.force)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --force to overwrite the adapter", file=sys.stderr)
        return 1
    print(f"installed {args.agent} adapter at {target}")
    print(adapters.ADAPTERS[args.agent].note)
    return 0


def cmd_xcheck(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not state.is_managed(root):
        print(f"not specdrive-managed: {root}", file=sys.stderr)
        print("hint: run `specdrive init` first.", file=sys.stderr)
        return 1
    s = state.load_state(root)
    s["cross_check"] = args.mode
    state.save_state(root, s)
    line = state.append_decision(root, f"Cross-check mode set to {args.mode}.")
    print(f"cross-check mode: {args.mode}")
    print(line)
    return 0


def _require_managed(root: Path) -> bool:
    if not state.is_managed(root):
        print(f"not specdrive-managed: {root}", file=sys.stderr)
        print("hint: run `specdrive init` first.", file=sys.stderr)
        return False
    return True


def cmd_goal_set(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    mutate.set_goal(root, args.text)
    print(f"goal set: {args.text}")
    return 0


def cmd_decision_set(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    mutate.set_decision(root, args.text)
    print(f"core decision set: {args.text}")
    return 0


def cmd_scope_add(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    mutate.add_scope(root, args.text)
    print(f"out-of-scope added: {args.text}")
    return 0


def cmd_constraint_add(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    mutate.add_constraint(root, args.text)
    print(f"constraint added: {args.text}")
    return 0


def cmd_phase(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    try:
        mutate.set_phase(root, args.phase)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"phase set to {args.phase}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    try:
        state.load_state(root)
    except state.StateError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    print("state is valid")
    return 0


def cmd_bucket_add(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    new_id = mutate.add_bucket(root, args.name)
    print(f"bucket {new_id} added: {args.name}")
    return 0


def cmd_bucket_start(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    try:
        b = mutate.start_bucket(root, args.id)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"bucket {b['id']} building: {b['name']}")
    return 0


def cmd_bucket_approve(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    try:
        b = mutate.approve_bucket(root, args.id)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"bucket {b['id']} approved: {b['name']}")
    return 0


def cmd_next(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    print(mutate.next_step(state.load_state(root)))
    return 0


def cmd_log_add(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not _require_managed(root):
        return 1
    line = state.append_decision(root, args.text)
    print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specdrive",
        description="Take a project from fuzzy idea to finished thing without drifting.",
    )
    parser.add_argument("--version", action="version", version=f"specdrive {state.SCHEMA_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create .specdrive/ state in a project")
    p_init.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_init.add_argument("--force", action="store_true", help="reset existing specdrive state")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="show current phase, goal, and buckets")
    p_status.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_status.set_defaults(func=cmd_status)

    p_next = sub.add_parser("next", help="show what to do next")
    p_next.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_next.set_defaults(func=cmd_next)

    p_validate = sub.add_parser("validate", help="check state.json is structurally valid")
    p_validate.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_validate.set_defaults(func=cmd_validate)

    p_playbook = sub.add_parser("playbook", help="print the specdrive playbook")
    p_playbook.set_defaults(func=cmd_playbook)

    p_install = sub.add_parser("install", help="install an agent adapter into a project")
    p_install.add_argument("agent", choices=sorted(adapters.ADAPTERS), help="target agent")
    p_install.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_install.add_argument("--force", action="store_true", help="overwrite existing adapter")
    p_install.set_defaults(func=cmd_install)

    p_log = sub.add_parser("log", help="print the decision log")
    p_log.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_log.set_defaults(func=cmd_log)

    p_xcheck = sub.add_parser("xcheck", help="record the cross-model check mode")
    p_xcheck.add_argument("mode", choices=state.CROSS_CHECK_MODES, help="cross-check method used")
    p_xcheck.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_xcheck.set_defaults(func=cmd_xcheck)

    def _path(p):
        p.add_argument("path", nargs="?", default=".", help="project root (default: .)")

    # goal set "<text>"
    p_goal = sub.add_parser("goal", help="set the Phase 1 goal")
    goal_sub = p_goal.add_subparsers(dest="goalcmd", required=True)
    p_goal_set = goal_sub.add_parser("set", help="set the goal text")
    p_goal_set.add_argument("text", help="the goal")
    _path(p_goal_set)
    p_goal_set.set_defaults(func=cmd_goal_set)

    # decision set "<text>"
    p_dec = sub.add_parser("decision", help="set the core decision")
    dec_sub = p_dec.add_subparsers(dest="decisioncmd", required=True)
    p_dec_set = dec_sub.add_parser("set", help="set the core decision text")
    p_dec_set.add_argument("text", help="the core decision")
    _path(p_dec_set)
    p_dec_set.set_defaults(func=cmd_decision_set)

    # scope add "<text>"
    p_scope = sub.add_parser("scope", help="manage the out-of-scope list")
    scope_sub = p_scope.add_subparsers(dest="scopecmd", required=True)
    p_scope_add = scope_sub.add_parser("add", help="append an out-of-scope item")
    p_scope_add.add_argument("text", help="the item")
    _path(p_scope_add)
    p_scope_add.set_defaults(func=cmd_scope_add)

    # constraint add "<text>"
    p_con = sub.add_parser("constraint", help="manage the constraints list")
    con_sub = p_con.add_subparsers(dest="constraintcmd", required=True)
    p_con_add = con_sub.add_parser("add", help="append a constraint")
    p_con_add.add_argument("text", help="the constraint")
    _path(p_con_add)
    p_con_add.set_defaults(func=cmd_constraint_add)

    # phase <name>
    p_phase = sub.add_parser("phase", help="set the current phase")
    p_phase.add_argument("phase", choices=(state.PHASE_GOAL, state.PHASE_BUCKETS,
                                           state.PHASE_BUILD, state.PHASE_DONE))
    _path(p_phase)
    p_phase.set_defaults(func=cmd_phase)

    # bucket add/start/approve
    p_bucket = sub.add_parser("bucket", help="manage buckets")
    bucket_sub = p_bucket.add_subparsers(dest="bucketcmd", required=True)
    p_bucket_add = bucket_sub.add_parser("add", help="append a bucket")
    p_bucket_add.add_argument("name", help="bucket name")
    _path(p_bucket_add)
    p_bucket_add.set_defaults(func=cmd_bucket_add)
    p_bucket_start = bucket_sub.add_parser("start", help="mark a bucket building")
    p_bucket_start.add_argument("id", type=int, help="bucket id")
    _path(p_bucket_start)
    p_bucket_start.set_defaults(func=cmd_bucket_start)
    p_bucket_approve = bucket_sub.add_parser("approve", help="mark a bucket approved")
    p_bucket_approve.add_argument("id", type=int, help="bucket id")
    _path(p_bucket_approve)
    p_bucket_approve.set_defaults(func=cmd_bucket_approve)

    # log-add "<text>"  (sibling of `log`; appends a decision line)
    p_logadd = sub.add_parser("log-add", help="append a line to the decision log")
    p_logadd.add_argument("text", help="the decision")
    _path(p_logadd)
    p_logadd.set_defaults(func=cmd_log_add)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except state.StateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: run `specdrive validate` to inspect state.json.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
