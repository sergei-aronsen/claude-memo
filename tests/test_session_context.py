"""Unit tests for session_context project matching."""

from __future__ import annotations


def test_project_aliases_covers_common_variants():
    from session_context import _project_aliases

    aliases = _project_aliases("claude-memo")
    assert "claude-memo" in aliases
    assert "claude_memo" in aliases
    assert "claudememo" in aliases  # SLUG_RE stripped


def test_project_aliases_normalize_case():
    from session_context import _project_aliases

    aliases = _project_aliases("Claude-Memo")
    assert "claude-memo" in aliases
    # All entries lowercased
    assert all(a == a.lower() for a in aliases)


def test_load_project_context_returns_none_on_empty(tmp_vault, isolated_home):
    """A vault with no decisions/projects returns None instead of crashing."""
    from session_context import load_project_context

    # No memos saved yet → SQLite has no rows or no db at all.
    out = load_project_context(tmp_vault, "nonexistent-project")
    assert out is None
