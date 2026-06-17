import json

import pytest

from specdrive import state


def test_init_creates_files_and_fingerprint(tmp_path):
    assert state.is_managed(tmp_path) is False
    state.init_state(tmp_path)
    assert state.is_managed(tmp_path) is True

    sf = state.specdrive_dir(tmp_path)
    assert (sf / state.STATE_FILE).is_file()
    assert (sf / state.DECISION_LOG_FILE).is_file()
    # The playbook is committed into the project so it travels with the repo.
    playbook = (sf / state.PLAYBOOK_FILE).read_text()
    assert playbook == state.packaged_playbook()
    assert "# specdrive playbook" in playbook
    fp = json.loads((sf / state.FINGERPRINT_FILE).read_text())
    assert fp["tool"] == "specdrive"
    assert fp["version"] == state.SCHEMA_VERSION
    assert "created" in fp


def test_default_state_shape(tmp_path):
    state.init_state(tmp_path)
    s = state.load_state(tmp_path)
    assert s["phase"] == state.PHASE_GOAL
    assert s["specdrive_version"] == state.SCHEMA_VERSION
    for key in ("goal", "core_decision", "out_of_scope", "constraints",
                "buckets", "current_bucket", "cross_check"):
        assert key in s


def test_reinit_refused_without_force(tmp_path):
    state.init_state(tmp_path)
    with pytest.raises(FileExistsError):
        state.init_state(tmp_path)
    # force resets cleanly
    state.init_state(tmp_path, force=True)


def test_save_load_round_trip(tmp_path):
    state.init_state(tmp_path)
    s = state.load_state(tmp_path)
    s["goal"] = "ship it"
    s["phase"] = state.PHASE_BUILD
    s["buckets"] = [{"id": 1, "name": "x", "status": "approved"}]
    state.save_state(tmp_path, s)

    reloaded = state.load_state(tmp_path)
    assert reloaded["goal"] == "ship it"
    assert reloaded["phase"] == state.PHASE_BUILD
    assert reloaded["buckets"][0]["name"] == "x"


def test_load_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        state.load_state(tmp_path)
