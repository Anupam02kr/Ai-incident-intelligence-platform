import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.llm.prompt import build_prompt, format_log_evidence, format_screenshot_evidence
from core.llm.generator import extract_json, parse_analysis, analyze_incident
from core.llm.verify import verify_analysis, verify_citation, collect_known_references



def sample_evidence():
    return {
        "logs": [{
            "source_file": "HDFS_2k.log",
            "line_count": 6,
            "severity_counts": {"INFO": 5, "ERROR": 1},
            "top_templates": [("PacketResponder <*> for block <*> terminating", 3)],
            "rare_templates": [("writeBlock <*> received exception <*>", 1)],
        }],
        "screenshots": [{
            "source_file": "shot.png",
            "text": "ConnectionError: timeout",
            "needs_review": False,
        }],
    }


def test_build_prompt_includes_evidence_content():
    prompt = build_prompt(sample_evidence(), kb_hits=[], description="test incident")

    assert "test incident" in prompt
    assert "PacketResponder" in prompt
    assert "ConnectionError" in prompt
    assert "JSON" in prompt


def test_format_log_evidence_flags_rare_templates():
    text = format_log_evidence(sample_evidence()["logs"])
    assert "Rare/unusual" in text
    assert "writeBlock" in text


def test_format_screenshot_evidence_flags_low_confidence():
    shots = [{"source_file": "x.png", "text": "blah", "needs_review": True}]
    text = format_screenshot_evidence(shots)
    assert "LOW CONFIDENCE" in text


def test_empty_evidence_does_not_crash():
    empty = {"logs": [], "screenshots": []}
    prompt = build_prompt(empty, kb_hits=[])
    assert "No log evidence" in prompt
    assert "No screenshots" in prompt



def test_extract_json_handles_clean_json():
    raw = '{"category": "Database", "severity": "High"}'
    assert extract_json(raw) == raw


def test_extract_json_handles_markdown_fence():
    raw = '```json\n{"category": "Database"}\n```'
    result = extract_json(raw)
    assert result.strip() == '{"category": "Database"}'


def test_extract_json_handles_stray_text_around_it():
    raw = 'Here is the analysis:\n{"category": "Database"}\nHope that helps!'
    parsed = parse_analysis(raw)
    assert parsed == {"category": "Database"}


def test_parse_analysis_returns_none_on_garbage():
    assert parse_analysis("not json at all, sorry") is None


def test_parse_analysis_repairs_truncated_recommendations():
    broken = '''{
  "category": "Database",
  "severity": "High",
  "root_causes": [{"hypothesis": "disk issue", "confidence": 0.8}],
  "recommendations": [
    {
      "action": "restart service",
      "rationale": "restart service",
      "rationale: "restart service garbage garbage garbage'''

    result = parse_analysis(broken)
    assert result is not None
    assert result["category"] == "Database"
    assert result["severity"] == "High"
    assert len(result["root_causes"]) == 1
    assert "recommendations" not in result


def test_parse_analysis_repair_matches_real_observed_failure():
    real_broken = '''{
  "category": "Database",
  "category_confidence": 0.9,
  "severity": "High",
  "severity_reason": "repeated block termination errors",
  "summary": "DataNode reported repeated block termination errors.",
  "root_causes": [
    {
      "hypothesis": "DataNode's block handling mechanism is malfunctioning",
      "confidence": 0.8,
      "evidence": [
        {"type": "log", "ref": "PacketResponder <*> for block <*> terminating"},
        {"type": "kb", "ref": "runbook_disk_failure.md"}
      ]
    }
  ],
  "recommendations": [
    {
      "action": "Restart the DataNode service",
      "rationale": "Restart the DataNode service",
      "rationale: "Restart the DataNode service, "rationale: garbage garbage'''

    result = parse_analysis(real_broken)
    assert result is not None
    assert result["category"] == "Database"
    assert result["root_causes"][0]["evidence"][0]["ref"] == "PacketResponder <*> for block <*> terminating"


def test_parse_analysis_leaves_clean_json_untouched():
    clean = '{"category": "Network", "severity": "Low"}'
    result = parse_analysis(clean)
    assert result == {"category": "Network", "severity": "Low"}



def test_verify_citation_matches_known_template():
    known_templates = {"PacketResponder <*> for block <*> terminating"}
    citation = {"type": "log", "ref": "PacketResponder <*> for block <*> terminating"}
    assert verify_citation(citation, known_templates, set()) is True


def test_verify_citation_rejects_made_up_log_line():
    known_templates = {"PacketResponder <*> for block <*> terminating"}
    citation = {"type": "log", "ref": "something the model made up completely"}
    assert verify_citation(citation, known_templates, set()) is False


def test_verify_citation_matches_kb_source():
    known_sources = {"runbook_datanode.md"}
    citation = {"type": "kb", "ref": "runbook_datanode.md"}
    assert verify_citation(citation, set(), known_sources) is True


def test_verify_analysis_flags_unverified_citations():
    evidence = sample_evidence()
    analysis = {
        "root_causes": [{
            "hypothesis": "disk issue",
            "evidence": [
                {"type": "log", "ref": "PacketResponder <*> for block <*> terminating"},  # real
                {"type": "log", "ref": "totally made up line that never existed"},  # fake
            ],
        }]
    }

    result = verify_analysis(analysis, evidence, kb_hits=[])

    assert result["citation_check"]["total"] == 2
    assert result["citation_check"]["unverified"] == 1
    assert result["citation_check"]["all_verified"] is False
    assert result["root_causes"][0]["evidence"][0]["verified"] is True
    assert result["root_causes"][0]["evidence"][1]["verified"] is False


def test_analyze_incident_skips_model_when_no_kb_hits():
    result = analyze_incident(sample_evidence(), kb_hits=[], min_kb_hits=1)
    assert result["insufficient_evidence"] is True
    assert "reason" in result


if __name__ == "__main__":
    print("run with: pytest tests/test_llm.py -v")
    print("(these tests don't load the actual model - they test prompt building,")
    print(" JSON parsing, and citation verification in isolation)")
