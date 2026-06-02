import re
from pathlib import Path

from cv.ocr_pipeline import read_screenshot

_ERR = re.compile(r"error|failed|5\d{2}|exception|denied|timeout", re.I)


def analyze_screenshot(path: Path) -> dict:
    ocr = read_screenshot(path)
    hits = []
    for line in ocr["lines"]:
        if _ERR.search(line):
            hits.append(line[:200])

    if any(re.search(r"5\d{2}|fatal", ln, re.I) for ln in hits):
        severity = "high"
    elif hits:
        severity = "medium"
    else:
        severity = "low"

    if not hits:
        note = f"OCR ok ({ocr['line_count']} lines, ~{ocr['avg_confidence']}% conf). Nothing scary jumped out."
    else:
        note = f"Found {len(hits)} suspicious strings in the screenshot — worth checking against logs."

    return {"ocr": ocr, "findings": hits, "severity": severity, "analysis": note}
