import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.rag.knowledge_base import chunk_text, KnowledgeBase

TEST_KB_PATH = os.path.join(tempfile.gettempdir(), "test_kb_pytest")


def teardown_module(module):
    if os.path.exists(TEST_KB_PATH):
        shutil.rmtree(TEST_KB_PATH, ignore_errors=True)


def test_chunk_text_splits_long_text():
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=400, overlap_ratio=0.12)

    assert len(chunks) == 3
    assert len(chunks[0].split()) == 400


def test_chunk_text_overlap_between_consecutive_chunks():
    text = " ".join(f"word{i}" for i in range(1000))
    chunks = chunk_text(text, chunk_size=400, overlap_ratio=0.12)

    overlap = set(chunks[0].split()) & set(chunks[1].split())
    assert len(overlap) == 48  # 12% of 400


def test_chunk_text_short_text_stays_one_chunk():
    text = "just a few words here"
    chunks = chunk_text(text, chunk_size=400)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_empty_string_returns_no_chunks():
    assert chunk_text("") == []


def test_ingest_and_search_returns_the_relevant_chunk():
    try:
        kb = KnowledgeBase(persist_path=TEST_KB_PATH)
    except Exception as e:
        import pytest
        pytest.skip(f"couldn't load embedding model (probably no internet): {e}")

    kb.ingest_document(
        "When a DataNode reports repeated block termination errors, "
        "check disk health first with smartctl.",
        source="runbook_datanode.md",
    )
    kb.ingest_document(
        "SSH authentication failures from an unfamiliar IP usually "
        "indicate a brute-force attempt, check auth.log.",
        source="runbook_ssh.md",
    )

    results = kb.search("DataNode block termination, disk problem?", top_k=1)
    assert results[0]["source"] == "runbook_datanode.md"


if __name__ == "__main__":
    print("run with: pytest tests/test_knowledge_base.py -v")
    print("(the ingest/search test needs internet the first time, to download the embedding model)")
