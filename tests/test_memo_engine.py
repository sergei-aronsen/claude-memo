"""Unit tests for memo_engine."""

from __future__ import annotations

import json
import os
import signal

import numpy as np
import pytest


def test_embeddings_store_atomic_save(tmp_vault, isolated_home):
    """_save uses os.replace; no .tmp siblings linger after a clean run."""
    from memo_engine import EmbeddingsStore

    store = EmbeddingsStore(tmp_vault)
    store.embeddings = np.zeros((2, 384), dtype="float32")
    store.id_map = [1, 2]
    store._save()

    assert os.path.exists(store.emb_path)
    assert os.path.exists(store.map_path)
    assert not os.path.exists(store.emb_path + ".tmp")
    assert not os.path.exists(store.map_path + ".tmp")


def test_embeddings_store_length_mismatch_raises(tmp_vault, isolated_home):
    """Reader must refuse a torn pair (emb of N+1, map of N) rather than silently corrupt."""
    from memo_engine import EmbeddingsStore, get_embeddings_path, get_id_map_path

    np.save(open(get_embeddings_path(tmp_vault), "wb"), np.zeros((3, 384), dtype="float32"))
    with open(get_id_map_path(tmp_vault), "w") as f:
        json.dump([1, 2], f)

    with pytest.raises(RuntimeError, match="length mismatch"):
        EmbeddingsStore(tmp_vault)


def test_embeddings_store_inconsistent_pair_raises(tmp_vault, isolated_home):
    """emb file present without id_map (or vice versa) must raise — caller can rebuild."""
    from memo_engine import EmbeddingsStore, get_embeddings_path

    np.save(open(get_embeddings_path(tmp_vault), "wb"), np.zeros((1, 384), dtype="float32"))

    with pytest.raises(RuntimeError, match="inconsistent"):
        EmbeddingsStore(tmp_vault)


def test_embeddings_store_no_self_deadlock_under_vault_lock(tmp_vault, isolated_home):
    """Regression: EmbeddingsStore._load must NOT take LOCK_SH on write.lock.

    Bug introduced in 7103c70, fixed in c08f8ec. If LOCK_SH on the vault
    lock returns, _load self-deadlocks against the caller's own LOCK_EX.
    SIGALRM aborts within 5s to fail fast if the bug ever returns.
    """
    from memo_engine import EmbeddingsStore, VaultLock

    # Pre-create emb+map so _load takes the "both exist" path.
    store = EmbeddingsStore(tmp_vault)
    store.embeddings = np.zeros((1, 384), dtype="float32")
    store.id_map = [1]
    store._save()

    def _alarm(signum, frame):
        raise TimeoutError("EmbeddingsStore deadlocked under VaultLock")

    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(5)
    try:
        with VaultLock(tmp_vault):
            again = EmbeddingsStore(tmp_vault)
        assert len(again.id_map) == 1
    finally:
        signal.alarm(0)


def test_save_memo_and_index_atomic(tmp_vault, isolated_home):
    """A saved memo lands in SQLite under the same VaultLock — no intermediate gap."""
    from memo_engine import init_db
    from memo_utils import save_memo_and_index

    fp = save_memo_and_index(
        {
            "type": "insight",
            "title": "Atomic Save",
            "project": "p",
            "content": "x",
        },
        tmp_vault,
        source="test",
    )
    assert fp is not None and os.path.exists(fp)

    conn = init_db(tmp_vault)
    row = conn.execute(
        "SELECT title FROM notes WHERE filepath = ?",
        (os.path.relpath(fp, tmp_vault),),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row["title"] == "Atomic Save"


def test_search_vault_records_recall(tmp_vault, isolated_home):
    """A search hit must stamp last_recalled and bump recall_count."""
    from memo_engine import init_db, search_vault
    from memo_utils import save_memo_and_index

    fp = save_memo_and_index(
        {"type": "insight", "title": "Recall Target", "content": "alpha beta gamma"},
        tmp_vault,
        source="t",
    )
    assert fp is not None

    results = search_vault("alpha", tmp_vault, limit=5)
    assert results, "stub embedding model should still produce at least one hit"

    conn = init_db(tmp_vault)
    row = conn.execute(
        "SELECT last_recalled, recall_count FROM notes WHERE title = ?",
        ("Recall Target",),
    ).fetchone()
    conn.close()
    assert row["last_recalled"] is not None
    assert row["recall_count"] >= 1


def test_search_vault_track_recall_disabled(tmp_vault, isolated_home):
    """track_recall=False (internal callers) must not pollute recall stats."""
    from memo_engine import init_db, search_vault
    from memo_utils import save_memo_and_index

    save_memo_and_index(
        {"type": "insight", "title": "No Track", "content": "delta epsilon"},
        tmp_vault,
        source="t",
    )

    search_vault("delta", tmp_vault, limit=5, track_recall=False)

    conn = init_db(tmp_vault)
    row = conn.execute(
        "SELECT last_recalled, recall_count FROM notes WHERE title = ?",
        ("No Track",),
    ).fetchone()
    conn.close()
    assert row["last_recalled"] is None
    assert (row["recall_count"] or 0) == 0


def test_find_stale_notes_picks_old_and_never_recalled(tmp_vault, isolated_home):
    """Notes created long ago without any recall must appear in stale list."""
    from memo_engine import find_stale_notes, init_db
    from memo_utils import save_memo_and_index

    fp = save_memo_and_index(
        {"type": "insight", "title": "Ancient Note", "content": "x"},
        tmp_vault,
        source="t",
    )
    assert fp is not None

    # Backdate the created field directly in SQLite so the row predates
    # the cutoff; the production path stamps `created` to today.
    conn = init_db(tmp_vault)
    conn.execute("UPDATE notes SET created = '2020-01-01' WHERE title = ?", ("Ancient Note",))
    conn.commit()
    conn.close()

    stale = find_stale_notes(tmp_vault, days=30, limit=10)
    titles = {row["title"] for row in stale}
    assert "Ancient Note" in titles


def test_derive_tier_mapping():
    """Type-to-tier mapping matches the agreed taxonomy."""
    from memo_engine import derive_tier

    assert derive_tier("decision") == "semantic"
    assert derive_tier("pattern") == "procedural"
    assert derive_tier("tool") == "procedural"
    assert derive_tier("debug") == "episodic"
    assert derive_tier("insight") == "semantic"
    assert derive_tier("reference") == "semantic"
    assert derive_tier("project") == "semantic"
    assert derive_tier("daily-log") == "episodic"
    assert derive_tier(None) == "semantic"
    assert derive_tier("unknown-type") == "semantic"


def test_save_memo_writes_tier_to_frontmatter(tmp_vault, isolated_home):
    """save_memo derives and stores tier in YAML frontmatter."""
    from memo_utils import save_memo

    fp = save_memo({"type": "tool", "title": "Some Tool", "content": "x"}, tmp_vault, source="t")
    assert fp is not None
    text = open(fp).read()
    assert "tier: procedural" in text


def test_index_records_tier(tmp_vault, isolated_home):
    """After indexing, the SQLite row exposes the tier."""
    from memo_engine import init_db
    from memo_utils import save_memo_and_index

    fp = save_memo_and_index(
        {"type": "debug", "title": "Crash on boot", "content": "y"},
        tmp_vault,
        source="t",
    )
    assert fp is not None

    conn = init_db(tmp_vault)
    row = conn.execute("SELECT tier FROM notes WHERE title = ?", ("Crash on boot",)).fetchone()
    conn.close()
    assert row["tier"] == "episodic"


def test_polarity_detection_basic():
    """Polarity helper distinguishes positive / negative / neutral / ambiguous."""
    from memo_engine import _polarity

    assert _polarity("Works great in production") == "positive"
    assert _polarity("This is broken and deprecated") == "negative"
    assert _polarity("Some neutral description here") is None
    assert _polarity("Works but is also broken") is None
    assert _polarity("Работает стабильно в проде") == "positive"
    assert _polarity("Сломано, не использовать") == "negative"


def test_find_contradictions_flags_opposed_polarity(tmp_vault, isolated_home, monkeypatch):
    """Two near-duplicates with opposite polarity must appear in contradictions."""
    from memo_engine import EmbeddingsStore, find_contradictions, init_db
    from memo_utils import save_memo_and_index

    a = save_memo_and_index(
        {"type": "insight", "title": "X works in production", "content": "use this approach"},
        tmp_vault,
        source="t",
    )
    b = save_memo_and_index(
        {"type": "insight", "title": "X is broken", "content": "do not use, deprecated"},
        tmp_vault,
        source="t",
    )
    assert a and b

    # Force the two embeddings into the contradiction band [0.80, 0.97].
    # Stub embeddings are random per text, so synthesize a controlled pair:
    # all-ones vs all-ones with the first 20 entries negated → cosine ~ 0.90
    # for the stub's 384-dim space (cos = (dim - 2*flipped) / dim = 0.896).
    store = EmbeddingsStore(tmp_vault)
    assert store.embeddings is not None and len(store.id_map) >= 2
    dim = store.embeddings.shape[1]
    vec = np.ones(dim, dtype="float32")
    vec /= np.linalg.norm(vec)
    near = np.ones(dim, dtype="float32")
    near[:20] = -1.0
    near /= np.linalg.norm(near)
    store.embeddings[0] = vec
    store.embeddings[1] = near
    store._save()

    pairs = find_contradictions(tmp_vault, sim_low=0.80, sim_high=0.99)
    titles = {(p["title_a"], p["title_b"]) for p in pairs}
    found = any({"X works in production", "X is broken"} <= set(pair) for pair in titles)
    assert found, f"expected contradiction pair, got {pairs}"
    # Conn cleanup so SQLite file is not held open beyond test scope.
    init_db(tmp_vault).close()


def test_search_diversifies_by_project(tmp_vault, isolated_home):
    """max_per_project caps how many head hits come from one project."""
    from memo_engine import search_vault
    from memo_utils import save_memo_and_index

    # 4 notes in project A, 4 in project B, all sharing a keyword so FTS
    # makes every one a candidate.
    for i in range(4):
        save_memo_and_index(
            {"type": "insight", "title": f"A note {i}", "project": "proj-a", "content": "zephyr alpha"},
            tmp_vault,
            source="t",
        )
        save_memo_and_index(
            {"type": "insight", "title": f"B note {i}", "project": "proj-b", "content": "zephyr beta"},
            tmp_vault,
            source="t",
        )

    results = search_vault("zephyr", tmp_vault, limit=4, max_per_project=2, track_recall=False)
    projects = [r["project"] for r in results]
    assert len(results) == 4
    assert projects.count("proj-a") <= 2
    assert projects.count("proj-b") <= 2


def test_search_excludes_archived_and_superseded(tmp_vault, isolated_home):
    """Notes flagged archived/superseded must not appear in default results."""
    from memo_engine import init_db, search_vault
    from memo_utils import save_memo_and_index

    save_memo_and_index(
        {"type": "insight", "title": "Dead Note", "content": "quokka facts"},
        tmp_vault,
        source="t",
    )
    save_memo_and_index(
        {"type": "insight", "title": "Live Note", "content": "quokka facts"},
        tmp_vault,
        source="t",
    )

    conn = init_db(tmp_vault)
    conn.execute("UPDATE notes SET status = 'archived' WHERE title = ?", ("Dead Note",))
    conn.commit()
    conn.close()

    titles = {r["title"] for r in search_vault("quokka", tmp_vault, limit=10, track_recall=False)}
    assert "Live Note" in titles
    assert "Dead Note" not in titles

    # include_superseded=True surfaces it again.
    titles_all = {
        r["title"] for r in search_vault("quokka", tmp_vault, limit=10, track_recall=False, include_superseded=True)
    }
    assert "Dead Note" in titles_all


def test_find_duplicates_threshold(tmp_vault, isolated_home):
    """Identical embed_text (title + tags + body) → cos sim 1.0 → dup pair returned."""
    from memo_engine import find_duplicates
    from memo_utils import save_memo_and_index

    # save_memo's O_EXCL retry gives the second file a `-1` suffix, so two
    # memos with identical title + content end up as separate files with
    # identical embed_text → stub embedding is bit-identical → cos sim 1.0.
    a = save_memo_and_index(
        {"type": "insight", "title": "Same Title", "project": "p", "content": "shared body"},
        tmp_vault,
        source="t",
    )
    b = save_memo_and_index(
        {"type": "insight", "title": "Same Title", "project": "p", "content": "shared body"},
        tmp_vault,
        source="t",
    )
    assert a and b and a != b

    pairs = find_duplicates(tmp_vault, threshold=0.99)
    assert pairs, "expected at least one duplicate pair"
    flat = {t for pair in pairs for t in (pair["title_a"], pair["title_b"])}
    assert "Same Title" in flat
    assert all(p["similarity"] >= 0.99 for p in pairs)
