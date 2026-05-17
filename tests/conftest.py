"""Test fixtures for claude-memo.

Stubs sentence_transformers at session scope so unit tests run without
downloading the ~2GB multilingual-e5-large model. Tests that need the
real model can mark themselves with @pytest.mark.slow and load it
explicitly.
"""

from __future__ import annotations

import os
import shutil
import sys
import types

import numpy as np
import pytest

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts"))


def _install_sentence_transformers_stub() -> None:
    """Inject a fake sentence_transformers module before memo_engine imports it."""
    if "sentence_transformers" in sys.modules and not getattr(sys.modules["sentence_transformers"], "_is_stub", False):
        return

    class _StubModel:
        _is_stub = True

        def __init__(self, *args, **kwargs):
            self.dim = 384

        def encode(self, texts, **kwargs):
            if isinstance(texts, str):
                texts = [texts]
            # Deterministic non-zero vector derived from string hash so
            # cosine similarity between distinct strings is < 1.
            out = np.zeros((len(texts), self.dim), dtype="float32")
            for i, t in enumerate(texts):
                seed = abs(hash(t)) % (2**32)
                rng = np.random.default_rng(seed)
                out[i] = rng.standard_normal(self.dim).astype("float32")
                norm = np.linalg.norm(out[i])
                if norm > 0:
                    out[i] /= norm
            return out

    stub = types.ModuleType("sentence_transformers")
    stub.SentenceTransformer = _StubModel
    stub._is_stub = True
    sys.modules["sentence_transformers"] = stub


_install_sentence_transformers_stub()

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


@pytest.fixture
def tmp_vault(tmp_path, monkeypatch):
    """Initialize a minimal vault layout under tmp_path.

    Yields the vault path. Cleans the per-vault cache dir on teardown so
    parallel test runs do not collide.
    """
    vault = tmp_path / "vault"
    for sub in (
        "decisions",
        "patterns",
        "debug-logs",
        "insights",
        "tools",
        "references",
        "projects",
        "daily-logs",
    ):
        (vault / sub).mkdir(parents=True, exist_ok=True)
    (vault / "INDEX.md").write_text("# Test Vault Index\n\n", encoding="utf-8")

    from memo_utils import _vault_hash

    cache_root = tmp_path / "memo-cache"
    cache_root.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    cache_dir = cache_root / _vault_hash(str(vault))

    yield str(vault)

    if cache_dir.exists():
        shutil.rmtree(cache_dir, ignore_errors=True)


@pytest.fixture
def isolated_home(monkeypatch, tmp_path):
    """Redirect $HOME so ~/.cache/memo lands inside tmp_path."""
    monkeypatch.setenv("HOME", str(tmp_path))
    yield tmp_path
