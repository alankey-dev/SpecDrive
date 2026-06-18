import pytest

from specdrive import adapters


def test_claude_code_adapter_path_and_content(tmp_path):
    target = adapters.install_adapter("claude-code", tmp_path)
    assert target == tmp_path / ".claude" / "commands" / "specdrive.md"
    text = target.read_text()
    assert text.startswith("---")  # frontmatter
    assert "description:" in text
    assert ".specdrive/playbook.md" in text  # points at the committed playbook


def test_generic_adapter_path_and_content(tmp_path):
    target = adapters.install_adapter("generic", tmp_path)
    assert target == tmp_path / "SPECDRIVE.md"
    assert ".specdrive/playbook.md" in target.read_text()


def test_dedicated_clobber_refused_without_force(tmp_path):
    adapters.install_adapter("generic", tmp_path)
    with pytest.raises(FileExistsError):
        adapters.install_adapter("generic", tmp_path)
    adapters.install_adapter("generic", tmp_path, force=True)  # force overwrites


def test_codex_and_pi_agent_share_agents_md(tmp_path):
    t1 = adapters.install_adapter("codex", tmp_path)
    t2 = adapters.install_adapter("pi-agent", tmp_path)
    assert t1 == t2 == tmp_path / "AGENTS.md"
    text = t1.read_text()
    # Both target the same managed block; installing both leaves exactly one.
    assert text.count(adapters.BLOCK_BEGIN) == 1
    assert text.count(adapters.BLOCK_END) == 1
    assert ".specdrive/playbook.md" in text


def test_shared_adapter_preserves_existing_content(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("# house rules\n\nrun the tests\n")
    adapters.install_adapter("codex", tmp_path)
    text = agents.read_text()
    assert "run the tests" in text
    assert adapters.BLOCK_BEGIN in text


def test_shared_adapter_replaces_block_in_place(tmp_path):
    adapters.install_adapter("codex", tmp_path)
    adapters.install_adapter("codex", tmp_path)  # idempotent, no force
    text = (tmp_path / "AGENTS.md").read_text()
    assert text.count(adapters.BLOCK_BEGIN) == 1


def test_unknown_agent_raises(tmp_path):
    with pytest.raises(KeyError):
        adapters.install_adapter("nope", tmp_path)


def test_no_adapter_tells_agent_to_run_a_cli():
    # The whole point of v2: the workflow is CLI-free. Adapters must not instruct
    # the agent to shell out to `specdrive <subcommand>`.
    import re

    forbidden = re.compile(r"`specdrive (goal|decision|scope|constraint|phase|bucket|next|status|log-add|xcheck)")
    for name, adapter in adapters.ADAPTERS.items():
        assert not forbidden.search(adapter.render()), name
