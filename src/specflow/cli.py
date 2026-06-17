"""specflow command-line interface.

Thin wiring over specflow.state. Commands let any agent (or human) create and
inspect specflow state from the shell. The methodology itself lives in
playbook.md; `specflow playbook` prints it so an agent can read and follow it.
"""

from __future__ import annotations

import argparse
import sys
from importlib.resources import files
from pathlib import Path

from specflow import adapters, state


def _read_playbook() -> str:
    return (files("specflow") / "playbook.md").read_text(encoding="utf-8")


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        state.init_state(root, force=args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --force to reset existing specflow state", file=sys.stderr)
        return 1
    print(f"specflow initialised in {state.specflow_dir(root)}")
    print("next: run `specflow playbook` and start Phase 1 (Find the real goal).")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not state.is_managed(root):
        print(f"not specflow-managed: {root}")
        print("hint: run `specflow init` to start.")
        return 1
    s = state.load_state(root)
    print(f"specflow {s['specflow_version']}  |  phase: {s['phase']}")
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
    log = state.specflow_dir(root) / state.DECISION_LOG_FILE
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
        print(f"not specflow-managed: {root}", file=sys.stderr)
        print("hint: run `specflow init` first.", file=sys.stderr)
        return 1
    s = state.load_state(root)
    s["cross_check"] = args.mode
    state.save_state(root, s)
    line = state.append_decision(root, f"Cross-check mode set to {args.mode}.")
    print(f"cross-check mode: {args.mode}")
    print(line)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specflow",
        description="Take a project from fuzzy idea to finished thing without drifting.",
    )
    parser.add_argument("--version", action="version", version=f"specflow {state.SCHEMA_VERSION}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create .specflow/ state in a project")
    p_init.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_init.add_argument("--force", action="store_true", help="reset existing specflow state")
    p_init.set_defaults(func=cmd_init)

    p_status = sub.add_parser("status", help="show current phase, goal, and buckets")
    p_status.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_status.set_defaults(func=cmd_status)

    p_playbook = sub.add_parser("playbook", help="print the specflow playbook")
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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
