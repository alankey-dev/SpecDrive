"""specdrive command-line interface.

A thin bootstrap. The CLI's only job is to scaffold specdrive into a project:
create the `.specdrive/` state files (including a committed copy of the playbook)
and drop an agent adapter that points at them. After that, the methodology runs
with no CLI in the loop — the agent reads and writes the plain `.specdrive/`
files directly, following `.specdrive/playbook.md`. So the CLI never needs to be
installed on the machine running the agent (handy for web / cloud agents).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from specdrive import adapters, state


def cmd_init(args: argparse.Namespace) -> int:
    root = Path(args.path)
    try:
        state.init_state(root, force=args.force)
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --force to reset existing specdrive state", file=sys.stderr)
        return 1
    print(f"specdrive initialised in {state.specdrive_dir(root)}")
    if args.agent:
        rc = _install(args.agent, root, force=args.force)
        if rc != 0:
            return rc
    print("next: open the playbook (.specdrive/playbook.md) in your agent and start Phase 1.")
    return 0


def cmd_playbook(_args: argparse.Namespace) -> int:
    print(state.packaged_playbook())
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    return _install(args.agent, Path(args.path), force=args.force)


def _install(agent: str, root: Path, *, force: bool) -> int:
    try:
        target = adapters.install_adapter(agent, root, force=force)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except FileExistsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        print("hint: pass --force to overwrite the adapter", file=sys.stderr)
        return 1
    print(f"installed {agent} adapter at {target}")
    print(adapters.ADAPTERS[agent].note)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    root = Path(args.path)
    if not state.is_managed(root):
        print(f"not specdrive-managed: {root}", file=sys.stderr)
        print("hint: run `specdrive init` first.", file=sys.stderr)
        return 1
    try:
        state.load_state(root)
    except state.StateError as exc:
        print(f"invalid: {exc}", file=sys.stderr)
        return 1
    print("state is valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="specdrive",
        description=(
            "Scaffold the specdrive methodology into a project. After setup the "
            "agent drives everything by editing .specdrive/ directly — no CLI needed."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"specdrive {state.SCHEMA_VERSION}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="create .specdrive/ state and playbook in a project")
    p_init.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_init.add_argument(
        "--agent",
        choices=sorted(adapters.ADAPTERS),
        help="also install this agent adapter",
    )
    p_init.add_argument("--force", action="store_true", help="reset existing specdrive state")
    p_init.set_defaults(func=cmd_init)

    p_install = sub.add_parser("install", help="install an agent adapter into a project")
    p_install.add_argument("agent", choices=sorted(adapters.ADAPTERS), help="target agent")
    p_install.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_install.add_argument("--force", action="store_true", help="overwrite existing adapter")
    p_install.set_defaults(func=cmd_install)

    p_playbook = sub.add_parser("playbook", help="print the specdrive playbook")
    p_playbook.set_defaults(func=cmd_playbook)

    p_validate = sub.add_parser("validate", help="check .specdrive/state.json is structurally valid")
    p_validate.add_argument("path", nargs="?", default=".", help="project root (default: .)")
    p_validate.set_defaults(func=cmd_validate)

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
