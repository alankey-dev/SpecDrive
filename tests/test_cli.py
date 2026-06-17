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
