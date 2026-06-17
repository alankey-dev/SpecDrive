import pytest

from specdrive import mutate, state


@pytest.fixture
def proj(tmp_path):
    state.init_state(tmp_path)
    return tmp_path


def _statuses(root):
    return [b["status"] for b in state.load_state(root)["buckets"]]


def test_set_goal_and_decision(proj):
    mutate.set_goal(proj, "the goal")
    mutate.set_decision(proj, "the decision")
    s = state.load_state(proj)
    assert s["goal"] == "the goal"
    assert s["core_decision"] == "the decision"


def test_scope_and_constraint_append(proj):
    mutate.add_scope(proj, "no auth")
    mutate.add_constraint(proj, "python only")
    s = state.load_state(proj)
    assert s["out_of_scope"] == ["no auth"]
    assert s["constraints"] == ["python only"]


def test_add_bucket_autoids(proj):
    assert mutate.add_bucket(proj, "a") == 1
    assert mutate.add_bucket(proj, "b") == 2
    assert [b["name"] for b in state.load_state(proj)["buckets"]] == ["a", "b"]


def test_start_and_approve_advances_current(proj):
    mutate.add_bucket(proj, "a")
    mutate.add_bucket(proj, "b")
    mutate.set_phase(proj, state.PHASE_BUCKETS)
    mutate.set_phase(proj, state.PHASE_BUILD)
    mutate.start_bucket(proj, 1)
    assert state.load_state(proj)["current_bucket"] == 1
    mutate.approve_bucket(proj, 1)
    s = state.load_state(proj)
    assert s["buckets"][0]["status"] == "approved"
    assert s["current_bucket"] == 2  # advanced to next pending


def test_selective_logging(proj):
    mutate.set_goal(proj, "g")
    mutate.add_scope(proj, "s")          # not logged
    mutate.add_constraint(proj, "c")     # not logged
    mutate.set_phase(proj, state.PHASE_BUCKETS)
    mutate.add_bucket(proj, "a")
    log = (state.specdrive_dir(proj) / state.DECISION_LOG_FILE).read_text()
    assert "Goal set" in log
    assert "Phase set" in log
    assert "Bucket 1 added" in log
    assert "no auth" not in log and "out_of_scope" not in log
    assert "constraint" not in log.lower()


# --- guards ---

def _to_build_with_bucket(proj):
    mutate.add_bucket(proj, "a")
    mutate.set_phase(proj, state.PHASE_BUCKETS)
    mutate.set_phase(proj, state.PHASE_BUILD)


def test_phase_forward_skip_rejected(proj):
    with pytest.raises(ValueError, match="cannot skip"):
        mutate.set_phase(proj, state.PHASE_DONE)


def test_phase_backtrack_allowed(proj):
    mutate.set_phase(proj, state.PHASE_BUCKETS)
    mutate.set_phase(proj, state.PHASE_GOAL)  # backward ok
    assert state.load_state(proj)["phase"] == state.PHASE_GOAL


def test_start_requires_build_phase(proj):
    mutate.add_bucket(proj, "a")
    mutate.set_phase(proj, state.PHASE_BUCKETS)
    with pytest.raises(ValueError, match="phase 3-build"):
        mutate.start_bucket(proj, 1)


def test_start_requires_pending(proj):
    _to_build_with_bucket(proj)
    mutate.start_bucket(proj, 1)
    with pytest.raises(ValueError, match="not pending"):
        mutate.start_bucket(proj, 1)


def test_approve_requires_building(proj):
    _to_build_with_bucket(proj)
    with pytest.raises(ValueError, match="not building"):
        mutate.approve_bucket(proj, 1)


def test_bucket_bad_id_rejected(proj):
    _to_build_with_bucket(proj)
    with pytest.raises(ValueError, match="no bucket with id 99"):
        mutate.start_bucket(proj, 99)
