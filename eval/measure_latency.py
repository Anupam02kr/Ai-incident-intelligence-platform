import time

from core.evidence import build_incident_evidence
from core.rag.knowledge_base import KnowledgeBase
from core.llm.generator import analyze_incident


def measure(log_path, image_paths=None, description=None, kb_path="data/chroma"):
    image_paths = image_paths or []
    timings = {}

    t0 = time.perf_counter()
    evidence = build_incident_evidence(
        log_paths=[log_path], image_paths=image_paths, description=description
    )
    timings["evidence_build (logs + OCR)"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    kb = KnowledgeBase(persist_path=kb_path)
    query = description or "incident analysis"
    kb_hits = kb.search(query, top_k=5)
    timings["kb_search"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    result = analyze_incident(evidence, kb_hits, description=description)
    timings["llm_analysis"] = time.perf_counter() - t0

    total = sum(timings.values())
    timings["TOTAL"] = total

    return timings, result


if __name__ == "__main__":
    import os

    log_path = "data/raw/hdfs/HDFS_2k.log"
    if not os.path.exists(log_path):
        print(f"skip: {log_path} not found")
    else:
        timings, result = measure(
            log_path,
            description="DataNode reporting repeated block termination errors",
            kb_path="eval/chroma_eval",  
        )

        print("latency breakdown:")
        for stage, seconds in timings.items():
            if stage != "TOTAL":
                print(f"  {stage:35s} {seconds:6.2f}s")
        print(f"  {'-' * 42}")
        print(f"  {'TOTAL':35s} {timings['TOTAL']:6.2f}s")

        target = 60.0
        status = "PASS" if timings["TOTAL"] < target else "FAIL"
        print(f"\nNFR-1 target: <{target:.0f}s -> {status}")

        print(f"\nresult category: {result.get('category', 'n/a')}")
