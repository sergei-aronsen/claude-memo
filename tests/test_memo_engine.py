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

    np.save(open(get_embeddings_path(tmp_vault), "wb"),
            np.zeros((3, 384), dtype="float32"))
    with open(get_id_map_path(tmp_vault), "w") as f:
        json.dump([1, 2], f)

    with pytest.raises(RuntimeError, match="length mismatch"):
        EmbeddingsStore(tmp_vault)


def test_embeddings_store_inconsistent_pair_raises(tmp_vault, isolated_home):
    """emb file present without id_map (or vice versa) must raise — caller can rebuild."""
    from memo_engine import EmbeddingsStore, get_embeddings_path

    np.save(open(get_embeddings_path(tmp_vault), "wb"),
            np.zeros((1, 384), dtype="float32"))

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


def test_find_duplicates_threshold(tmp_vault, isolated_home):
    """Identical embed_text (title + tags + body) → cos sim 1.0 → dup pair returned."""
    from memo_engine import find_duplicates
    from memo_utils import save_memo_and_index

    # save_memo's O_EXCL retry gives the second file a `-1` suffix, so two
    # memos with identical title + content end up as separate files with
    # identical embed_text → stub embedding is bit-identical → cos sim 1.0.
    a = save_memo_and_index(
        {"type": "insight", "title": "Same Title", "project": "p", "content": "shared body"},
        tmp_vault, source="t",
    )
    b = save_memo_and_index(
        {"type": "insight", "title": "Same Title", "project": "p", "content": "shared body"},
        tmp_vault, source="t",
    )
    assert a and b and a != b

    pairs = find_duplicates(tmp_vault, threshold=0.99)
    assert pairs, "expected at least one duplicate pair"
    flat = {t for pair in pairs for t in (pair["title_a"], pair["title_b"])}
    assert "Same Title" in flat
    assert all(p["similarity"] >= 0.99 for p in pairs)
