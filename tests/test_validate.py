import json

import pytest

from specdrive import state


def test_default_state_valid():
    assert state.validate(state.default_state()) == []


def test_missing_key():
    s = state.default_state()
    del s["goal"]
    assert any("goal" in e for e in state.validate(s))


def test_bad_type():
    s = state.default_state()
    s["buckets"] = "nope"
    assert any("buckets" in e for e in state.validate(s))


def test_bad_phase():
    s = state.default_state()
    s["phase"] = "bogus"
    assert any("phase" in e for e in state.validate(s))


def test_bad_cross_check():
    s = state.default_state()
    s["cross_check"] = "gpt"
    assert any("cross_check" in e for e in state.validate(s))


def test_bad_bucket_status():
    s = state.default_state()
    s["buckets"] = [{"id": 1, "name": "a", "status": "weird"}]
    assert any("status" in e for e in state.validate(s))


def test_duplicate_ids():
    s = state.default_state()
    s["buckets"] = [{"id": 1, "name": "a", "status": "pending"},
                    {"id": 1, "name": "b", "status": "pending"}]
    assert any("duplicate" in e for e in state.validate(s))


def test_dangling_current_bucket():
    s = state.default_state()
    s["current_bucket"] = 5
    assert any("current_bucket" in e for e in state.validate(s))


def test_extra_keys_tolerated():
    s = state.default_state()
    s["future_field"] = 123  # forward-compat: unknown keys allowed
    assert state.validate(s) == []


def test_load_state_raises_on_corrupt(tmp_path):
    state.init_state(tmp_path)
    p = state.specdrive_dir(tmp_path) / state.STATE_FILE
    d = json.loads(p.read_text())
    d["phase"] = "bogus"
    p.write_text(json.dumps(d))
    with pytest.raises(state.StateError):
        state.load_state(tmp_path)


def test_load_state_raises_on_bad_json(tmp_path):
    state.init_state(tmp_path)
    p = state.specdrive_dir(tmp_path) / state.STATE_FILE
    p.write_text("{not json")
    with pytest.raises(state.StateError):
        state.load_state(tmp_path)
