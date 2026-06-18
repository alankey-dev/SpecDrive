import json

import pytest

from specdrive import state
from specdrive.cli import main


def test_init_scaffolds_state_and_playbook(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "initialised" in out
    assert state.is_managed(tmp_path)
    sf = state.specdrive_dir(tmp_path)
    assert (sf / state.STATE_FILE).is_file()
    assert (sf / state.PLAYBOOK_FILE).is_file()


def test_init_refuses_without_force(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["init", str(tmp_path)]) == 1
    assert "--force" in capsys.readouterr().err


def test_init_with_agent_installs_adapter(tmp_path, capsys):
    assert main(["init", str(tmp_path), "--agent", "claude-code"]) == 0
    assert (tmp_path / ".claude" / "commands" / "specdrive.md").is_file()


def test_playbook_prints(capsys):
    assert main(["playbook"]) == 0
    assert "# specdrive playbook" in capsys.readouterr().out


def test_install_via_cli(tmp_path, capsys):
    assert main(["install", "generic", str(tmp_path)]) == 0
    assert (tmp_path / "SPECDRIVE.md").is_file()
    assert "installed generic adapter" in capsys.readouterr().out


def test_install_clobber_refused(tmp_path, capsys):
    main(["install", "generic", str(tmp_path)])
    capsys.readouterr()
    assert main(["install", "generic", str(tmp_path)]) == 1
    assert "--force" in capsys.readouterr().err


def test_install_shared_agent_is_idempotent(tmp_path, capsys):
    # AGENTS.md adapters merge a managed block; re-running must not clobber or duplicate.
    (tmp_path / "AGENTS.md").write_text("# project rules\n\nkeep it tidy\n")
    assert main(["install", "codex", str(tmp_path)]) == 0
    assert main(["install", "codex", str(tmp_path)]) == 0  # no --force needed
    text = (tmp_path / "AGENTS.md").read_text()
    assert text.count("specdrive:begin") == 1
    assert "keep it tidy" in text  # existing content preserved


def test_validate_command_clean(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["validate", str(tmp_path)]) == 0
    assert "valid" in capsys.readouterr().out


def test_validate_unmanaged_returns_1(tmp_path, capsys):
    assert main(["validate", str(tmp_path)]) == 1
    assert "not specdrive-managed" in capsys.readouterr().err


def test_corrupt_state_gives_clean_error_not_traceback(tmp_path, capsys):
    main(["init", str(tmp_path)])
    pth = state.specdrive_dir(tmp_path) / state.STATE_FILE
    d = json.loads(pth.read_text())
    d["phase"] = "bogus"
    pth.write_text(json.dumps(d))
    capsys.readouterr()
    assert main(["validate", str(tmp_path)]) == 1
    assert "invalid" in capsys.readouterr().err


def test_unknown_subcommand_rejected():
    with pytest.raises(SystemExit):
        main(["frobnicate"])
