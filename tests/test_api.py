import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

FAKE_EVIDENCE = {
    "logs": [{"top_templates": [("test template", 5)]}],
    "screenshots": [],
    "total_log_lines": 10,
    "combined_severity_counts": {"INFO": 10},
    "any_screenshot_needs_review": False,
}
FAKE_LLM_RESULT = {"category": "Database", "parse_failed": False}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_rejects_empty_request():
    response = client.post("/analyze", data={})
    assert response.status_code == 400


def test_analyze_returns_combined_result():
    with patch("api.main.build_incident_evidence", return_value=FAKE_EVIDENCE), \
         patch("api.main.get_kb") as mock_get_kb, \
         patch("api.main.analyze_incident", return_value=FAKE_LLM_RESULT), \
         patch("api.main.get_classifier", return_value=None):

        mock_get_kb.return_value.search.return_value = []

        response = client.post("/analyze", data={"description": "test incident"})

        assert response.status_code == 200
        body = response.json()
        assert body["llm_analysis"]["category"] == "Database"
        assert body["evidence_summary"]["total_log_lines"] == 10


def test_analyze_cleans_up_uploaded_files():
    with patch("api.main.build_incident_evidence", return_value=FAKE_EVIDENCE), \
         patch("api.main.get_kb") as mock_get_kb, \
         patch("api.main.analyze_incident", return_value=FAKE_LLM_RESULT), \
         patch("api.main.get_classifier", return_value=None), \
         patch("api.main.os.remove") as mock_remove:

        mock_get_kb.return_value.search.return_value = []

        files = {"logs": ("test.log", b"fake log content", "text/plain")}
        response = client.post("/analyze", data={"description": "test"}, files=files)

        assert response.status_code == 200
        assert mock_remove.called


def test_kb_status_returns_chunk_count():
    with patch("api.main.get_kb") as mock_get_kb:
        mock_get_kb.return_value.count.return_value = 42
        response = client.get("/kb/status")
        assert response.status_code == 200
        assert response.json() == {"total_chunks": 42}


if __name__ == "__main__":
    print("run with: pytest tests/test_api.py -v")
