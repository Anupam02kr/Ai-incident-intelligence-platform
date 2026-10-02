from collections import Counter

from core.logs.normalizer import normalize_file
from core.logs.template_miner import mine_templates, top_templates, rare_templates
from core.ocr.ocr import extract_text

def build_log_evidence(log_path, openssh_year=None, rare_threshold=3):
    rows = normalize_file(log_path, openssh_year=openssh_year)
    tagged_rows, template_counts = mine_templates(rows)

    severity_counts = Counter(r["level"] for r in tagged_rows)

    return {
        "source_file": log_path,
        "line_count": len(rows),
        "severity_counts": dict(severity_counts),
        "top_templates": top_templates(template_counts, n=10),
        "rare_templates": rare_templates(template_counts, threshold=rare_threshold),
        "rows": tagged_rows,  
    }


def build_screenshot_evidence(image_paths):
    """Runs OCR on however many screenshots were uploaded and collects
    the results. Screenshots below the confidence threshold get flagged
    so the UI can prompt for a correction (FR-13) before this gets used
    downstream.
    """
    screenshots = []
    for path in image_paths:
        result = extract_text(path)
        screenshots.append({
            "source_file": path,
            "text": result["text"],
            "avg_confidence": result["avg_confidence"],
            "needs_review": result["needs_review"],
        })
    return screenshots


def build_incident_evidence(log_paths=None, image_paths=None, description=None, openssh_year=None):
    """The main entry point - takes whatever evidence the user uploaded
    (any combination of logs, screenshots, a text description) and
    returns one evidence object covering all of it. Any of the three
    can be left out; this is meant to handle FR-4's "any combination"
    requirement.
    """
    log_paths = log_paths or []
    image_paths = image_paths or []

    logs = [build_log_evidence(p, openssh_year=openssh_year) for p in log_paths]
    screenshots = build_screenshot_evidence(image_paths)

    combined_severity = Counter()
    for log in logs:
        combined_severity.update(log["severity_counts"])

    needs_review = any(s["needs_review"] for s in screenshots)

    return {
        "description": description,
        "logs": logs,
        "screenshots": screenshots,
        "combined_severity_counts": dict(combined_severity),
        "total_log_lines": sum(l["line_count"] for l in logs),
        "any_screenshot_needs_review": needs_review,
    }


if __name__ == "__main__":
    import os

    hdfs_path = "data/raw/hdfs/HDFS_2k.log"
    if not os.path.exists(hdfs_path):
        print(f"skip: {hdfs_path} not found yet")
    else:
        evidence = build_incident_evidence(
            log_paths=[hdfs_path],
            description="DataNode reporting intermittent block terminations",
        )
        print(f"total log lines: {evidence['total_log_lines']}")
        print(f"combined severity: {evidence['combined_severity_counts']}")
        print(f"top templates: {evidence['logs'][0]['top_templates'][:3]}")
