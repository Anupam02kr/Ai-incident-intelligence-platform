import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image, ImageDraw, ImageFont
from core.evidence import build_log_evidence, build_incident_evidence

HDFS_SAMPLE = "data/raw/hdfs/HDFS_2k.log"


def make_error_screenshot(path):
    img = Image.new("RGB", (700, 150), color="black")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 24
        )
    except OSError:
        font = ImageFont.load_default()
    draw.text((20, 20), "DiskFullError disk quota exceeded", fill="white", font=font)
    img.save(path)
    return path


def test_log_evidence_has_expected_shape():
    if not os.path.exists(HDFS_SAMPLE):
        return  

    evidence = build_log_evidence(HDFS_SAMPLE)
    assert evidence["line_count"] > 0
    assert "severity_counts" in evidence
    assert "top_templates" in evidence


def test_incident_evidence_combines_logs_and_screenshot():
    if not os.path.exists(HDFS_SAMPLE):
        return

    screenshot_path = make_error_screenshot("/tmp/test_incident_screenshot.png")
    evidence = build_incident_evidence(
        log_paths=[HDFS_SAMPLE],
        image_paths=[screenshot_path],
        description="test incident",
    )

    assert evidence["description"] == "test incident"
    assert evidence["total_log_lines"] > 0
    assert len(evidence["screenshots"]) == 1
    assert "disk" in evidence["screenshots"][0]["text"].lower() or \
           "quota" in evidence["screenshots"][0]["text"].lower()


def test_incident_evidence_handles_logs_only():
    if not os.path.exists(HDFS_SAMPLE):
        return

    evidence = build_incident_evidence(log_paths=[HDFS_SAMPLE])
    assert evidence["screenshots"] == []
    assert evidence["description"] is None
    assert evidence["any_screenshot_needs_review"] is False


if __name__ == "__main__":
    print("run with: pytest tests/test_evidence.py -v")
