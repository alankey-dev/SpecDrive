import re

from specdrive import state


def test_playbook_is_cli_free():
    """The methodology must not tell the agent to run workflow CLI commands.

    The agent reads/writes .specdrive/ directly; only the bootstrap commands
    (init/install/validate/playbook) may be mentioned, and only as optional.
    """
    text = state.packaged_playbook()
    forbidden = re.compile(
        r"`specdrive (goal|decision|scope|constraint|phase|bucket|next|status|log-add|xcheck)"
    )
    assert not forbidden.search(text)


def test_playbook_documents_direct_file_management():
    text = state.packaged_playbook()
    assert "state.json" in text
    assert "decision-log.md" in text
    # It should make the no-CLI promise explicit.
    assert "no CLI" in text or "no CLI to call" in text
