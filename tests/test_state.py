import json

import pytest

from specflow import state


def test_init_creates_files_and_fingerprint(tmp_path):
    assert state.is_managed(tmp_path) is False
    state.init_state(tmp_path)
    assert state.is_managed(tmp_path) is True

    sf = state.specflow_dir(tmp_path)
    assert (sf / state.STATE_FILE).is_file()
    assert (sf / state.DECISION_LOG_FILE).is_file()
    fp = json.loads((sf / state.FINGERPRINT_FILE).read_text())
    assert fp["tool"] == "specflow"
    assert fp["version"] == state.SCHEMA_VERSION
    assert "created" in fp


def test_default_state_shape(tmp_path):
    state.init_state(tmp_path)
    s = state.load_state(tmp_path)
    assert s["phase"] == state.PHASE_GOAL
    assert s["specflow_version"] == state.SCHEMA_VERSION
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


def test_append_decision_autonumbers_and_appends(tmp_path):
    state.init_state(tmp_path)
    assert state.append_decision(tmp_path, "first") == "DL-1  first"
    assert state.append_decision(tmp_path, "second") == "DL-2  second"

    log = (state.specflow_dir(tmp_path) / state.DECISION_LOG_FILE).read_text()
    assert "DL-1  first" in log
    assert "DL-2  second" in log
    # append-only: header preserved
    assert "decision log" in log


def test_append_decision_continues_numbering_across_calls(tmp_path):
    state.init_state(tmp_path)
    for i in range(5):
        state.append_decision(tmp_path, f"d{i}")
    assert state.append_decision(tmp_path, "next") == "DL-6  next"
