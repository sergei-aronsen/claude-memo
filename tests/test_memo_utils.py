"""Unit tests for memo_utils."""

from __future__ import annotations

import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest


def test_vault_hash_deterministic(tmp_path):
    from memo_utils import _vault_hash

    p = str(tmp_path)
    assert _vault_hash(p) == _vault_hash(p)
    assert len(_vault_hash(p)) == 16
    assert _vault_hash(p) != _vault_hash(str(tmp_path / "other"))


def test_save_memo_o_excl_collision(tmp_vault, isolated_home):
    """Same slug saved twice produces two distinct files, no overwrite."""
    from memo_utils import save_memo

    memo = {
        "type": "insight",
        "title": "Same Title",
        "project": "test",
        "content": "first",
    }
    f1 = save_memo(memo, tmp_vault, source="t")
    memo["content"] = "second"
    f2 = save_memo(memo, tmp_vault, source="t")

    assert f1 is not None and f2 is not None
    assert f1 != f2
    assert os.path.exists(f1) and os.path.exists(f2)
    assert "first" in open(f1).read()
    assert "second" in open(f2).read()


def test_save_memo_concurrent_no_loss(tmp_vault, isolated_home):
    """20 threads racing on the same slug must all produce a saved file."""
    from memo_utils import save_memo

    def worker(i):
        return save_memo(
            {
                "type": "insight",
                "title": "Race Title",
                "project": "race",
                "content": f"writer {i}",
            },
            tmp_vault,
            source="race",
        )

    with ThreadPoolExecutor(max_workers=20) as ex:
        out = list(ex.map(worker, range(20)))

    assert all(out), "every save must succeed (no None)"
    assert len(set(out)) == 20, "every save must land on a distinct file"


def test_daily_log_write_concurrent_lines_intact(tmp_vault, isolated_home):
    """50 threads writing lines via daily_log_write produce 50 complete lines."""
    from memo_utils import daily_log_write

    def worker(i):
        daily_log_write(tmp_vault, f"line-{i:03d}-{'x' * 200}\n")

    with ThreadPoolExecutor(max_workers=50) as ex:
        list(ex.map(worker, range(50)))

    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    log_path = os.path.join(tmp_vault, "daily-logs", f"{today}.md")
    assert os.path.exists(log_path)

    text = open(log_path).read()
    # Each line should match the pattern; no torn writes.
    written = [ln for ln in text.splitlines() if ln.startswith("line-")]
    assert len(written) == 50
    for ln in written:
        assert ln.count("x") == 200, f"torn line: {ln[:60]}"


def test_append_to_index_monthly_header(tmp_vault, isolated_home):
    """append_to_index inserts a month header exactly once per month."""
    from memo_utils import append_to_index

    fake = os.path.join(tmp_vault, "insights", "fake.md")
    open(fake, "w").close()

    for i in range(3):
        append_to_index(tmp_vault, fake, f"title {i}", "t")

    index = open(os.path.join(tmp_vault, "INDEX.md")).read()
    from datetime import datetime

    month = datetime.now().strftime("%Y-%m")
    assert index.count(f"## {month}") == 1
    assert index.count("[[insights/fake]]") == 3


def test_call_llm_returns_none_on_transport_failure(monkeypatch):
    """call_llm must return None (not '') when urllib.request raises."""
    monkeypatch.setenv("MEMO_API_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("MEMO_API_FALLBACK_MODEL", raising=False)

    import urllib.request

    def _fail(*a, **k):
        raise OSError("simulated transport error")

    monkeypatch.setattr(urllib.request, "urlopen", _fail)

    from memo_utils import call_llm

    out = call_llm("hi", max_tokens=10)
    assert out is None


def test_call_llm_returns_empty_string_on_legitimate_empty(monkeypatch):
    """Empty content list from a successful HTTP 200 must return '' — not None.

    Distinguishing '' from None is what stopped call_llm from double-billing
    Haiku on "no memo-worthy content" sessions (audit N0-1).
    """
    monkeypatch.setenv("MEMO_API_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("MEMO_API_FALLBACK_MODEL", raising=False)

    import io
    import json
    import urllib.request

    class _Resp:
        def __init__(self, payload):
            self._buf = io.BytesIO(json.dumps(payload).encode("utf-8"))

        def __enter__(self):
            return self

        def __exit__(self, *a):
            pass

        def read(self):
            return self._buf.read()

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *a, **k: _Resp({"content": []}),
    )

    from memo_utils import call_llm

    out = call_llm("hi", max_tokens=10)
    assert out == ""


def test_get_memo_dir_creates_outside_vault(tmp_vault, isolated_home):
    """Cache lives under ~/.cache/memo/<hash>/, never inside the vault."""
    from memo_utils import get_memo_dir

    cache = get_memo_dir(tmp_vault)
    assert os.path.isdir(cache)
    assert not cache.startswith(tmp_vault), "cache must not live inside vault"
    assert os.path.expanduser("~/.cache/memo") in cache
