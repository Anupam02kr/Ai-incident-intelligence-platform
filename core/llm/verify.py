def collect_known_references(evidence, kb_hits):
    """Builds the set of things that are legitimately citable: every log
    template that was shown to the model, and every KB source it was
    given. A citation is only valid if it matches one of these.
    """
    known_templates = set()
    for log in evidence.get("logs", []):
        for template, _ in log["top_templates"]:
            known_templates.add(template)
        for template, _ in log["rare_templates"]:
            known_templates.add(template)

    known_kb_sources = {hit["source"] for hit in kb_hits}

    return known_templates, known_kb_sources


def verify_citation(citation, known_templates, known_kb_sources):
    """A single citation is valid if its ref matches (or is contained
    within, or contains) something we know is real. We're a bit lenient
    with exact matching since the model might paraphrase slightly or
    quote a substring - but the core content still has to actually be
    present somewhere in what we gave it.
    """
    ref = citation.get("ref", "").strip()
    citation_type = citation.get("type")

    if not ref:
        return False

    if citation_type == "log":
        for template in known_templates:
            if ref in template or template in ref:
                return True
        return False

    if citation_type == "kb":
        for source in known_kb_sources:
            if ref == source or source in ref:
                return True
        return False

    return False


def verify_analysis(analysis, evidence, kb_hits):
    """Goes through every root cause's citations in the LLM's output and
    checks each one against the real evidence. Returns the analysis with
    an extra 'verified' flag added per citation, plus a summary of how
    many citations didn't check out. Doesn't silently drop bad citations -
    better to flag them and let the caller decide (e.g. show a warning
    in the UI) than hide the problem.
    """
    known_templates, known_kb_sources = collect_known_references(evidence, kb_hits)

    total_citations = 0
    unverified_citations = 0

    for root_cause in analysis.get("root_causes", []):
        for citation in root_cause.get("evidence", []):
            total_citations += 1
            is_valid = verify_citation(citation, known_templates, known_kb_sources)
            citation["verified"] = is_valid
            if not is_valid:
                unverified_citations += 1

    analysis["citation_check"] = {
        "total": total_citations,
        "unverified": unverified_citations,
        "all_verified": unverified_citations == 0,
    }

    return analysis
