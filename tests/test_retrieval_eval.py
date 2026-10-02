import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.rag.evaluate import hit_rate_at_k


class FakeKB:
    """Stands in for the real KnowledgeBase so these tests don't need to
    load the actual embedding model - we're testing the hit-rate
    counting logic here, not retrieval quality itself (that's what
    running eval/retrieval_queries.py against the real KB is for).
    """
    def __init__(self, canned_results):
        self.canned_results = canned_results

    def search(self, query, top_k=5):
        return self.canned_results.get(query, [])[:top_k]


def test_hit_rate_counts_correctly():
    kb = FakeKB({
        "q1": [{"source": "a.md"}, {"source": "b.md"}],
        "q2": [{"source": "x.md"}],
    })
    queries = [("q1", "a.md"), ("q2", "b.md")]  

    result = hit_rate_at_k(kb, queries, k=5)

    assert result["hits"] == 1
    assert result["total"] == 2
    assert result["hit_rate"] == 0.5


def test_hit_rate_all_hits():
    kb = FakeKB({"q1": [{"source": "a.md"}]})
    result = hit_rate_at_k(kb, [("q1", "a.md")], k=5)
    assert result["hit_rate"] == 1.0


def test_hit_rate_all_misses():
    kb = FakeKB({"q1": [{"source": "wrong.md"}]})
    result = hit_rate_at_k(kb, [("q1", "a.md")], k=5)
    assert result["hit_rate"] == 0.0


def test_hit_rate_respects_k_cutoff():
    kb = FakeKB({"q1": [{"source": "wrong1.md"}, {"source": "wrong2.md"}, {"source": "a.md"}]})
    result = hit_rate_at_k(kb, [("q1", "a.md")], k=2)
    assert result["hit_rate"] == 0.0


def test_details_record_what_was_retrieved():
    kb = FakeKB({"q1": [{"source": "a.md"}]})
    result = hit_rate_at_k(kb, [("q1", "a.md")], k=5)
    assert result["details"][0]["retrieved"] == ["a.md"]
    assert result["details"][0]["hit"] is True


if __name__ == "__main__":
    print("run with: pytest tests/test_retrieval_eval.py -v")
