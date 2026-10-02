import json
RESPONSE_SCHEMA_EXAMPLE = {
    "category": "Database",
    "category_confidence": 0.8,
    "severity": "High",
    "severity_reason": "short reason here",
    "summary": "a short summary, under 150 words",
    "root_causes": [
        {
            "hypothesis": "what you think happened",
            "confidence": 0.7,
            "evidence": [
                {"type": "log", "ref": "exact quoted log line or template"},
                {"type": "kb", "ref": "runbook_name.md"}
            ]
        }
    ],
    "recommendations": [
        {"priority": 1, "action": "what to do", "rationale": "why"}
    ]
}

SYSTEM_INSTRUCTIONS = """You are an incident analysis assistant. You will be given evidence from \
system logs, OCR'd error screenshots, and relevant knowledge base excerpts. Your job is to \
figure out what category of incident this is, summarize what happened, propose root causes, \
and recommend actions.

Rules you must follow:
1. Only use information given to you in the evidence below. Do not invent log lines, error \
messages, or facts that are not present in the evidence.
2. Include EXACTLY ONE root cause and EXACTLY ONE recommendation. Do not add more.
3. Keep the summary under 40 words. Keep each recommendation's action and rationale under \
15 words each. Be terse - short phrases, not full paragraphs.
4. Every root cause must cite specific evidence - either a log line/template that actually \
appears in the input, or a knowledge base source that was given to you.
5. Never repeat the same word or phrase multiple times in a row.
6. Respond with ONLY a JSON object matching the schema shown below. No text before or after \
the JSON, no markdown code fences, no extra commentary.

Schema:
""" + json.dumps(RESPONSE_SCHEMA_EXAMPLE, indent=2)


def format_log_evidence(log_evidence_list, max_rare_templates=5, max_template_chars=150):
    """Turns the log evidence (from core/evidence.py) into readable text
    for the prompt. We give the LLM template stats rather than raw lines -
    the SRS decided this on purpose (section 7) since raw logs are huge
    and repetitive and would blow past the model's context window.

    Two safety valves here: max_rare_templates caps how many rare
    templates get listed, and max_template_chars caps how long any
    single template string can be. Both matter because Drain doesn't
    always fully mask everything - a template with an unmasked stack
    trace or a long unique message can be hundreds of tokens on its
    own, and a handful of those is enough to blow the budget even with
    a small template count (this bit us: 5850 tokens from what looked
    like a modest amount of evidence).
    """
    if not log_evidence_list:
        return "No log evidence provided."

    def clip(template):
        return template if len(template) <= max_template_chars else template[:max_template_chars] + "...(truncated)"

    sections = []
    for log in log_evidence_list:
        lines = [f"Log file: {log['source_file']} ({log['line_count']} lines)"]
        lines.append(f"Severity counts: {log['severity_counts']}")

        lines.append("Top templates:")
        for template, count in log["top_templates"]:
            lines.append(f"  [{count}x] {clip(template)}")

        rare = log["rare_templates"]
        if rare:
            shown = rare[:max_rare_templates]
            lines.append(f"Rare/unusual templates (showing {len(shown)} of {len(rare)}):")
            for template, count in shown:
                lines.append(f"  [{count}x] {clip(template)}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)


def format_screenshot_evidence(screenshots, max_chars=1500):
    if not screenshots:
        return "No screenshots provided."

    sections = []
    for shot in screenshots:
        flag = " (LOW CONFIDENCE - may contain OCR errors)" if shot["needs_review"] else ""
        text = shot["text"]
        if len(text) > max_chars:
            text = text[:max_chars] + " ...(truncated)"
        sections.append(f"Screenshot text{flag}:\n{text}")

    return "\n\n".join(sections)


def format_kb_context(kb_hits, max_chars_per_hit=600):
    if not kb_hits:
        return "No relevant knowledge base entries found."

    sections = []
    for hit in kb_hits:
        text = hit["text"]
        if len(text) > max_chars_per_hit:
            text = text[:max_chars_per_hit] + " ...(truncated)"
        sections.append(f"[Source: {hit['source']}]\n{text}")

    return "\n\n".join(sections)


def build_prompt(evidence, kb_hits, description=None):
    """evidence is the dict from core/evidence.py's build_incident_evidence,
    kb_hits is what KnowledgeBase.search() returned for this incident.
    Puts it all together into the final prompt text.
    """
    parts = [SYSTEM_INSTRUCTIONS, "\n---\n"]

    if description:
        parts.append(f"User-provided description:\n{description}\n")

    parts.append("Log evidence:\n" + format_log_evidence(evidence.get("logs", [])))
    parts.append("\nScreenshot evidence:\n" + format_screenshot_evidence(evidence.get("screenshots", [])))
    parts.append("\nKnowledge base context:\n" + format_kb_context(kb_hits))
    parts.append("\n---\nRespond with the JSON analysis now.")

    return "\n".join(parts)
