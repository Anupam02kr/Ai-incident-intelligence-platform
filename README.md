# AI Incident Intelligence Platform

Upload system logs, error screenshots, and a short description of what
happened — get back a classified, evidence-cited incident analysis with
a root cause hypothesis and recommended next steps, grounded in a
knowledge base of runbooks and past incidents.

Built as a lean, local-first alternative to enterprise AIOps tools
(Datadog Bits AI, Dynatrace Davis AI, etc.): no cloud dependency, no
paid infrastructure, and every claim the system makes is checked against
the actual evidence it was given before being shown to the user.

## Why this exists

Most AI incident tools connect to live telemetry you already have in
a platform you're paying for. This one doesn't assume that. It's
upload-based, runs entirely on a laptop GPU, and is explicit about what
it doesn't know — if there's nothing in the knowledge base relevant to
an incident, it says so instead of guessing. See
[Limitations](#limitations) below for what that honesty costs.

## Architecture

```
Streamlit UI  →  FastAPI backend
                    ├─ Log normalizer + Drain3 template mining
                    ├─ OCR (screenshots)
                    └─ RAG pipeline
                          ↓
                    ChromaDB (vector store)
                          ↓
                    LLM (Phi-3-mini-4k-instruct, 4-bit)
                          ↓
                 Citation-verified analysis
       (classification · summary · root cause · recommendations)
                          ↑
              XGBoost classifier (independent second opinion)
```

Full requirements are in `SRS_AI_Incident_Intelligence_Platform.pdf`
and `PRD_AI_Incident_Intelligence_Platform.pdf`.

## Features

- **Log parsing** for heterogeneous formats (HDFS, OpenSSH out of the
  box; falls back gracefully on unknown formats) into a common schema
- **Drain3 template mining** — clusters thousands of log lines into a
  handful of patterns, flags rare/unusual ones
- **OCR** on error screenshots (EasyOCR), with low-confidence results
  flagged for review before being trusted as evidence
- **RAG retrieval** over a ChromaDB knowledge base of runbooks
- **LLM analysis** (summary, root cause, recommendations) that only
  uses the evidence it was given — and says "insufficient evidence"
  rather than inventing a cause when retrieval comes up empty
- **Citation verification** — every log line or source the LLM cites
  is checked against the real evidence; fabricated citations are
  flagged, not silently trusted
- **XGBoost classifier** as an independent, fast, measurable second
  opinion on incident category
- **FastAPI backend** + **Streamlit UI**, fully local

## Measured results

| Metric | Target | Result |
|---|---|---|
| Classification macro-F1 | ≥ 0.75 | **0.844** (XGBoost, 180-sample synthetic dataset, 6 categories) |
| Retrieval hit-rate@5 | ≥ 0.80 | **1.000** (20 hand-built queries, 10-runbook KB) |
| End-to-end latency | < 60s | **~62s** (RTX 3050 Laptop GPU, 4GB VRAM, HDFS 2k-line sample) |
| Grounding/citation accuracy | ≥ 90% | not yet formally measured |
| Setup time on a clean machine | < 10 min | not yet measured |

Notes on these numbers, for anyone checking them:
- The classifier's dataset is **synthetic** (template-generated), not
  real incident tickets — stated upfront rather than implied otherwise.
- Hit-rate@5 was measured on a small (10-document), clearly-distinct
  knowledge base. A production KB with hundreds of overlapping
  documents would likely score lower — this number reflects the setup
  it was measured on, not a general claim.
- Latency was measured against a 2,000-line log sample, not the 10MB
  file the original target describes; expect it to scale with log
  size.

## Tech stack

Python · FastAPI · Streamlit · ChromaDB · Sentence-Transformers
(`all-MiniLM-L6-v2`) · HuggingFace Transformers · Phi-3-mini-4k-instruct
(4-bit via bitsandbytes) · XGBoost · scikit-learn · Drain3 · EasyOCR ·
PyTorch (CUDA)

## Setup

```bash
git clone <this repo>
cd incident-intelligence
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
```

`requirements.txt` includes the CUDA index for GPU-enabled torch. If
you're on a different GPU/driver or want CPU-only, see the comments at
the top of that file.

### Download sample data (optional, for the demo)

HDFS and OpenSSH 2k-line samples from
[Loghub](https://github.com/logpai/loghub) — see `data/README.md` for
exact files and where to put them.

### Build the knowledge base

```bash
python -c "
from core.rag.knowledge_base import KnowledgeBase
from core.rag.evaluate import ingest_runbooks

kb = KnowledgeBase(persist_path='data/chroma')
n = ingest_runbooks(kb, docs_dir='eval/kb_docs')
print(f'ingested {n} runbooks, {kb.count()} total chunks')
"
```

### Train the classifier

```bash
python core/classify/data.py    # generates eval/incident_dataset.csv
python core/classify/train.py   # trains, evaluates, saves eval/classifier.pkl
```

### Run it

Two terminals:

```bash
# terminal 1
uvicorn api.main:app --reload

# terminal 2
streamlit run app/main.py
```

Visit `http://localhost:8501` for the UI, or `http://127.0.0.1:8000/docs`
for the raw API.

## Running the evaluation suite

```bash
python -m core.rag.evaluate      # retrieval hit-rate@5
python -m eval.measure_latency   # end-to-end latency breakdown
pytest tests/ -v                 # full test suite
```

## Project structure

```
incident-intelligence/
├── app/main.py              # Streamlit UI
├── api/main.py               # FastAPI routes
├── core/
│   ├── logs/                 # normalizer, Drain3 template mining
│   ├── ocr/                  # screenshot text extraction
│   ├── rag/                  # knowledge base, retrieval, eval
│   ├── classify/             # XGBoost classifier + synthetic data
│   ├── llm/                  # prompting, generation, citation verification
│   └── evidence.py           # combines all evidence into one object
├── data/                     # sample logs, chroma DB, uploads
├── eval/                     # datasets, eval queries, metrics scripts
├── tests/                    # unit tests, one file per module
├── requirements.txt
└── SRS / PRD (PDF)
```

## Limitations

This matters more than the metrics table above, so it gets its own
section rather than a footnote.

**This system cannot solve a genuinely novel problem it has no
knowledge of.** It's RAG-based: the LLM only reasons using the
knowledge base and the evidence it's given. For an incident with no
matching runbook or precedent, it correctly says "insufficient
evidence" instead of inventing a plausible-sounding but unfounded
answer (`FR-25`) — this is a deliberate design choice, not a bug, but
it means the tool does not replace engineering judgment for new
failure modes.

What it does provide even in that case:
- Automated log parsing, template mining, and anomaly surfacing — the
  "first 20 minutes" of manual log triage, done instantly
- A system that gets more useful over time: every incident resolved
  manually and written up becomes retrievable knowledge for next time
- Every commercial AI incident tool (Datadog, Dynatrace, and similar)
  has this same fundamental ceiling — it isn't a gap specific to this
  project, it's the honest boundary of the RAG approach in general

**Other known limitations:**
- LLM generation occasionally requires a repair pass on malformed JSON
  output (see `core/llm/generator.py` — `repair_truncated_json`); not
  every generation is clean on the first try with a small (3.8B) model
- The classifier's training data is synthetic, not real tickets
- Retrieval quality was measured on a small, curated knowledge base —
  real-world performance on a larger, messier KB is untested
- Not evaluated for multi-incident or cascading-failure scenarios

## Dataset citation

Sample logs from Loghub:

Zhu, J., He, S., He, P., Liu, J., Lyu, M.R. "Loghub: A Large Collection
of System Log Datasets for AI-driven Log Analytics." ISSRE 2023.
