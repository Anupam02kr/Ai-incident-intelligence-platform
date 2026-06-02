import re
from functools import lru_cache

from transformers import pipeline

from config import get_settings

# noisy lines bubble up first
_BAD_LINE = re.compile(
    r"error|exception|fatal|traceback|timeout|refused|oom|5\d{2}",
    re.I,
)


def pick_interesting_lines(text: str, limit=30) -> list[str]:
    hits = []
    for line in text.splitlines():
        line = line.strip()
        if line and _BAD_LINE.search(line):
            hits.append(line)
    return hits[:limit]


def trim_log(text: str) -> str:
    cfg = get_settings()
    text = text.strip()
    if len(text) <= cfg.max_log_chars:
        return text
    half = cfg.max_log_chars // 2
    return text[:half] + "\n...snip...\n" + text[-half:]


@lru_cache(maxsize=1)
def _bart():
    model = get_settings().summarization_model
    return pipeline("summarization", model=model, device=-1)


def summarize_logs(log_text: str) -> dict:
    body = trim_log(log_text)
    signals = pick_interesting_lines(body)

    if len(body.split()) < 25:
        summary = body
    else:
        summary = _try_bart(body) or _fallback_summary(body)

    return {
        "summary": summary,
        "error_signals": signals,
        "line_count": len(log_text.splitlines()),
        "char_count": len(log_text),
    }


def _try_bart(text: str) -> str | None:
    try:
        out = _bart()(text[:3500], max_length=160, min_length=30, do_sample=False, truncation=True)
        return out[0]["summary_text"]
    except Exception:
        return None


def _fallback_summary(text: str) -> str:
    lines = pick_interesting_lines(text, limit=10)
    if lines:
        return "Noisy lines:\n" + "\n".join(f"  {ln[:180]}" for ln in lines)
    preview = [ln.strip() for ln in text.splitlines() if ln.strip()][:6]
    return "Head of log:\n" + "\n".join(preview)
