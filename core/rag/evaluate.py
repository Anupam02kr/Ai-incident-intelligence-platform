import os

from core.rag.knowledge_base import KnowledgeBase

def ingest_runbooks(kb, docs_dir="eval/kb_docs"):
    """Loads every .md file in docs_dir into the knowledge base."""
    count = 0
    for filename in sorted(os.listdir(docs_dir)):
        if filename.endswith(".md"):
            path = os.path.join(docs_dir, filename)
            kb.ingest_file(path)
            count += 1
    return count


def hit_rate_at_k(kb, eval_queries, k=5):
    """Runs every (query, expected_source) pair through the kb and checks
    if expected_source shows up anywhere in the top k results. Returns
    the overall hit rate plus per-query detail so you can see exactly
    which queries missed, not just the aggregate number.
    """
    results = []
    hits = 0

    for query, expected_source in eval_queries:
        search_results = kb.search(query, top_k=k)
        retrieved_sources = [r["source"] for r in search_results]
        hit = expected_source in retrieved_sources

        if hit:
            hits += 1

        results.append({
            "query": query,
            "expected": expected_source,
            "retrieved": retrieved_sources,
            "hit": hit,
        })

    hit_rate = hits / len(eval_queries) if eval_queries else 0.0

    return {
        "hit_rate": hit_rate,
        "hits": hits,
        "total": len(eval_queries),
        "details": results,
    }


if __name__ == "__main__":
    from eval.retrieval_queries import EVAL_QUERIES

    kb = KnowledgeBase(persist_path="eval/chroma_eval")
    if kb.count() == 0:
        n = ingest_runbooks(kb)
        print(f"ingested {n} runbooks into a fresh eval KB")
    else:
        print(f"reusing existing eval KB with {kb.count()} chunks")

    result = hit_rate_at_k(kb, EVAL_QUERIES, k=5)

    print(f"\nhit-rate@5: {result['hit_rate']:.3f} ({result['hits']}/{result['total']})")

    misses = [d for d in result["details"] if not d["hit"]]
    if misses:
        print(f"\n{len(misses)} missed queries:")
        for m in misses:
            print(f"  query: '{m['query']}'")
            print(f"    expected: {m['expected']}")
            print(f"    got:      {m['retrieved']}")
    else:
        print("\nall queries hit their expected source")
