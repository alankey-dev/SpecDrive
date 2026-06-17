from specdrive import mutate, state


def st(**kw):
    s = state.default_state()
    s.update(kw)
    return s


def test_goal_phase_empty():
    assert "set the goal" in mutate.next_step(st(phase="1-goal"))


def test_goal_phase_needs_decision():
    msg = mutate.next_step(st(phase="1-goal", goal="g"))
    assert "core decision" in msg


def test_goal_phase_ready():
    msg = mutate.next_step(st(phase="1-goal", goal="g", core_decision="d"))
    assert "phase 2-buckets" in msg


def test_buckets_phase_empty():
    assert "add buckets" in mutate.next_step(st(phase="2-buckets"))


def test_buckets_phase_with_buckets():
    msg = mutate.next_step(st(phase="2-buckets",
                             buckets=[{"id": 1, "name": "a", "status": "pending"}]))
    assert "phase 3-build" in msg


def test_build_pending():
    msg = mutate.next_step(st(phase="3-build",
                             buckets=[{"id": 1, "name": "a", "status": "pending"}],
                             current_bucket=1))
    assert "bucket start 1" in msg


def test_build_building():
    msg = mutate.next_step(st(phase="3-build",
                             buckets=[{"id": 1, "name": "a", "status": "building"}],
                             current_bucket=1))
    assert "bucket approve 1" in msg


def test_build_all_approved():
    msg = mutate.next_step(st(phase="3-build",
                             buckets=[{"id": 1, "name": "a", "status": "approved"}],
                             current_bucket=None))
    assert "phase done" in msg


def test_done():
    assert "Summarise" in mutate.next_step(st(phase="done"))


def test_unknown_phase():
    assert "Unknown phase" in mutate.next_step(st(phase="weird"))
