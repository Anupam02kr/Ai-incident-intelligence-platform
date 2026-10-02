import os
import shutil
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from core.evidence import build_incident_evidence
from core.rag.knowledge_base import KnowledgeBase
from core.llm.generator import analyze_incident
from core.classify.train import load_trained, predict as classify_predict


app = FastAPI(title="AI Incident Intelligence Platform")

UPLOAD_DIR = "data/uploads"
KB_PATH = "data/chroma"
CLASSIFIER_PATH = "eval/classifier.pkl"

os.makedirs(UPLOAD_DIR, exist_ok=True)


_kb = None
_classifier = None


def get_kb():
    global _kb
    if _kb is None:
        _kb = KnowledgeBase(persist_path=KB_PATH)
    return _kb


def get_classifier():
    global _classifier
    if _classifier is None:
        if os.path.exists(CLASSIFIER_PATH):
            _classifier = load_trained(CLASSIFIER_PATH)
        else:
            _classifier = False  
    return _classifier


def save_upload(upload_file):
    """Saves an uploaded file to disk under a unique name and returns the
    path. Keeps the original extension so downstream code (which checks
    file extensions) still works correctly.
    """
    ext = os.path.splitext(upload_file.filename)[1]
    dest_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(upload_file.file, f)
    return dest_path


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
async def analyze(
    description: str = Form(None),
    logs: list[UploadFile] = File(None),
    images: list[UploadFile] = File(None),
):
    """Main endpoint - FR-4/FR-31. Accepts any combination of log files,
    screenshots, and a text description, and returns the full analysis:
    classifier category, LLM-generated summary/root-cause/recommendations
    with citation verification.
    """
    logs = logs or []
    images = images or []

    if not logs and not images and not description:
        raise HTTPException(status_code=400, detail="Provide at least one of: logs, images, description")

    log_paths = [save_upload(f) for f in logs]
    image_paths = [save_upload(f) for f in images]

    try:
        evidence = build_incident_evidence(
            log_paths=log_paths, image_paths=image_paths, description=description
        )

        kb = get_kb()
        query = description or " ".join(
            template for log in evidence["logs"] for template, _ in log["top_templates"][:3]
        )
        kb_hits = kb.search(query, top_k=5) if query.strip() else []

        llm_result = analyze_incident(evidence, kb_hits, description=description)

        classifier_result = None
        classifier = get_classifier()
        if classifier and description:
            classifier_result = classify_predict(classifier, description)

        return {
            "evidence_summary": {
                "total_log_lines": evidence["total_log_lines"],
                "combined_severity_counts": evidence["combined_severity_counts"],
                "any_screenshot_needs_review": evidence["any_screenshot_needs_review"],
            },
            "classifier": classifier_result,
            "llm_analysis": llm_result,
        }
    finally:
        for path in log_paths + image_paths:
            if os.path.exists(path):
                os.remove(path)


@app.post("/kb/ingest")
async def kb_ingest(file: UploadFile = File(...), doc_type: str = Form("runbook")):
    """FR-14. Adds a document (runbook, past incident writeup, etc.) to
    the knowledge base so future /analyze calls can retrieve it.
    """
    path = save_upload(file)
    try:
        kb = get_kb()
        chunk_count = kb.ingest_file(path, doc_type=doc_type)
        return {"filename": file.filename, "chunks_added": chunk_count, "kb_total_chunks": kb.count()}
    finally:
        if os.path.exists(path):
            os.remove(path)


@app.get("/kb/status")
def kb_status():
    kb = get_kb()
    return {"total_chunks": kb.count()}
