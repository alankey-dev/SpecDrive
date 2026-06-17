import pytest

from specflow import adapters


def _playbook_marker() -> str:
    # A line that lives in the canonical playbook; proves it was embedded.
    return "# specflow playbook"


def test_claude_code_adapter_path_and_content(tmp_path):
    target = adapters.install_adapter("claude-code", tmp_path)
    assert target == tmp_path / ".claude" / "commands" / "specflow.md"
    text = target.read_text()
    assert text.startswith("---")  # frontmatter
    assert "description:" in text
    assert _playbook_marker() in text  # playbook embedded


def test_generic_adapter_path_and_content(tmp_path):
    target = adapters.install_adapter("generic", tmp_path)
    assert target == tmp_path / "SPECFLOW.md"
    text = target.read_text()
    assert _playbook_marker() in text


def test_clobber_refused_without_force(tmp_path):
    adapters.install_adapter("generic", tmp_path)
    with pytest.raises(FileExistsError):
        adapters.install_adapter("generic", tmp_path)
    # force overwrites
    adapters.install_adapter("generic", tmp_path, force=True)


def test_unknown_agent_raises(tmp_path):
    with pytest.raises(KeyError):
        adapters.install_adapter("nope", tmp_path)


def test_registry_renders_from_package():
    # Every registered adapter must embed the canonical playbook.
    for name, adapter in adapters.ADAPTERS.items():
        rendered = adapter.render("PLAYBOOK_BODY")
        assert "PLAYBOOK_BODY" in rendered, name
