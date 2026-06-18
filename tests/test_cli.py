import pytest

from specdrive import state
from specdrive.cli import main


def test_init_then_status(tmp_path, capsys):
    assert main(["init", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "initialised" in out

    assert main(["status", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "phase: 1-goal" in out


def test_status_unmanaged_returns_1(tmp_path, capsys):
    assert main(["status", str(tmp_path)]) == 1
    assert "not specdrive-managed" in capsys.readouterr().out


def test_init_refuses_without_force(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["init", str(tmp_path)]) == 1
    err = capsys.readouterr().err
    assert "--force" in err


def test_status_shows_buckets(tmp_path, capsys):
    main(["init", str(tmp_path)])
    s = state.load_state(tmp_path)
    s["buckets"] = [{"id": 1, "name": "alpha", "status": "approved"},
                    {"id": 2, "name": "beta", "status": "building"}]
    s["current_bucket"] = 2
    state.save_state(tmp_path, s)
    capsys.readouterr()

    main(["status", str(tmp_path)])
    out = capsys.readouterr().out
    assert "alpha" in out and "beta" in out
    assert "> 2. beta" in out  # current-bucket marker


def test_playbook_prints(capsys):
    assert main(["playbook"]) == 0
    assert "# specdrive playbook" in capsys.readouterr().out


def test_log_prints(tmp_path, capsys):
    main(["init", str(tmp_path)])
    state.append_decision(tmp_path, "a decision")
    capsys.readouterr()
    assert main(["log", str(tmp_path)]) == 0
    assert "DL-1  a decision" in capsys.readouterr().out


def test_install_via_cli(tmp_path, capsys):
    assert main(["install", "generic", str(tmp_path)]) == 0
    assert (tmp_path / "SPECDRIVE.md").is_file()
    out = capsys.readouterr().out
    assert "installed generic adapter" in out


def test_install_clobber_refused(tmp_path, capsys):
    main(["install", "generic", str(tmp_path)])
    capsys.readouterr()
    assert main(["install", "generic", str(tmp_path)]) == 1
    assert "--force" in capsys.readouterr().err


def test_xcheck_writes_state_and_logs(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["xcheck", "self-critique", str(tmp_path)]) == 0
    out = capsys.readouterr().out
    assert "self-critique" in out

    s = state.load_state(tmp_path)
    assert s["cross_check"] == "self-critique"
    log = (state.specdrive_dir(tmp_path) / state.DECISION_LOG_FILE).read_text()
    assert "Cross-check mode set to self-critique" in log


def test_xcheck_unmanaged_returns_1(tmp_path, capsys):
    assert main(["xcheck", "none", str(tmp_path)]) == 1
    assert "not specdrive-managed" in capsys.readouterr().err


def test_xcheck_bad_mode_rejected(tmp_path):
    main(["init", str(tmp_path)])
    with pytest.raises(SystemExit):  # argparse choices reject
        main(["xcheck", "bogus", str(tmp_path)])


# --- v2 commands ---

def _p(tmp_path):
    return str(tmp_path)


def test_mutation_commands_drive_a_session(tmp_path, capsys):
    p = _p(tmp_path)
    main(["init", p])
    for argv in (["goal", "set", "g", p], ["decision", "set", "d", p],
                 ["scope", "add", "s", p], ["constraint", "add", "c", p],
                 ["phase", "2-buckets", p], ["bucket", "add", "alpha", p],
                 ["phase", "3-build", p], ["bucket", "start", "1", p],
                 ["bucket", "approve", "1", p]):
        assert main(argv) == 0, argv
    capsys.readouterr()
    s = state.load_state(tmp_path)
    assert s["goal"] == "g" and s["core_decision"] == "d"
    assert s["buckets"][0]["status"] == "approved"


def test_next_command(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["next", str(tmp_path)]) == 0
    assert "Phase 1" in capsys.readouterr().out


def test_log_add_command(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["log-add", "a note", str(tmp_path)]) == 0
    assert "DL-1  a note" in capsys.readouterr().out


def test_phase_forward_skip_cli_returns_1(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["phase", "done", str(tmp_path)]) == 1
    assert "cannot skip" in capsys.readouterr().err


def test_bucket_approve_before_start_cli_returns_1(tmp_path, capsys):
    p = _p(tmp_path)
    main(["init", p])
    main(["phase", "2-buckets", p]); main(["bucket", "add", "a", p])
    main(["phase", "3-build", p])
    capsys.readouterr()
    assert main(["bucket", "approve", "1", p]) == 1
    assert "not building" in capsys.readouterr().err


def test_validate_command_clean(tmp_path, capsys):
    main(["init", str(tmp_path)])
    capsys.readouterr()
    assert main(["validate", str(tmp_path)]) == 0
    assert "valid" in capsys.readouterr().out


def test_corrupt_state_gives_clean_error_not_traceback(tmp_path, capsys):
    import json
    main(["init", str(tmp_path)])
    pth = state.specdrive_dir(tmp_path) / state.STATE_FILE
    d = json.loads(pth.read_text()); d["phase"] = "bogus"; pth.write_text(json.dumps(d))
    capsys.readouterr()
    assert main(["status", str(tmp_path)]) == 1  # global StateError handling
    assert "error:" in capsys.readouterr().err


def test_uninstall_removes_state_and_adapters(tmp_path, capsys):
    p = str(tmp_path)
    main(["init", p]); main(["install", "claude-code", p]); main(["install", "generic", p])
    capsys.readouterr()
    assert main(["uninstall", p, "--yes"]) == 0
    assert not state.specdrive_dir(tmp_path).exists()
    assert not (tmp_path / "SPECDRIVE.md").exists()
    assert not (tmp_path / ".claude/commands/specdrive.md").exists()


def test_uninstall_adapters_only_keeps_state(tmp_path, capsys):
    p = str(tmp_path)
    main(["init", p]); main(["install", "generic", p])
    capsys.readouterr()
    assert main(["uninstall", p, "--yes", "--adapters-only"]) == 0
    assert state.is_managed(tmp_path)
    assert not (tmp_path / "SPECDRIVE.md").exists()


def test_uninstall_state_only_keeps_adapters(tmp_path, capsys):
    p = str(tmp_path)
    main(["init", p]); main(["install", "generic", p])
    capsys.readouterr()
    assert main(["uninstall", p, "--yes", "--state-only"]) == 0
    assert not state.specdrive_dir(tmp_path).exists()
    assert (tmp_path / "SPECDRIVE.md").is_file()


def test_uninstall_removes_legacy_specflow_paths(tmp_path, capsys):
    legacy_dir = tmp_path / state.LEGACY_DIR_NAME
    legacy_dir.mkdir(); (legacy_dir / "state.json").write_text("{}")
    (tmp_path / "SPECFLOW.md").write_text("old")
    cmd = tmp_path / ".claude/commands"; cmd.mkdir(parents=True)
    (cmd / "specflow.md").write_text("old")
    capsys.readouterr()
    assert main(["uninstall", str(tmp_path), "--yes"]) == 0
    assert not legacy_dir.exists()
    assert not (tmp_path / "SPECFLOW.md").exists()
    assert not (cmd / "specflow.md").exists()


def test_uninstall_nothing_to_do(tmp_path, capsys):
    assert main(["uninstall", str(tmp_path), "--yes"]) == 0
    assert "nothing to uninstall" in capsys.readouterr().out


def test_uninstall_abort_on_no(tmp_path, capsys, monkeypatch):
    p = str(tmp_path)
    main(["init", p])
    capsys.readouterr()
    monkeypatch.setattr("builtins.input", lambda _="": "n")
    assert main(["uninstall", p]) == 1
    assert state.is_managed(tmp_path)
    assert "aborted" in capsys.readouterr().err
