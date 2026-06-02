import shutil
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from cv import analyze_screenshot
from database import Incident, IncidentStatus, get_db, init_db
from nlp import summarize_logs
from rag import RunbookQA, ingest_file, ingest_folder

cfg = get_settings()
runbooks = RunbookQA()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    if list(cfg.docs_dir.glob("*")):
        ingest_folder(cfg.docs_dir)
    yield


app = FastAPI(title=cfg.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NewIncident(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None


class IncidentOut(BaseModel):
    id: str
    title: str
    description: str | None
    status: IncidentStatus
    log_summary: str | None
    ocr_text: str | None
    cv_analysis: str | None
    rag_answer: str | None
    diagnosis: str | None

    model_config = {"from_attributes": True}


class AskRunbook(BaseModel):
    question: str = Field(min_length=3)
    incident_id: str | None = None


class LogBody(BaseModel):
    logs: str = Field(min_length=10)


def save_upload(upload: UploadFile, name: str):
    dest = cfg.uploads_dir / name
    with dest.open("wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/incidents", response_model=list[IncidentOut])
async def list_incidents(db: AsyncSession = Depends(get_db)):
    rows = await db.execute(select(Incident).order_by(Incident.created_at.desc()))
    return rows.scalars().all()


@app.post("/api/incidents", response_model=IncidentOut)
async def create_incident(body: NewIncident, db: AsyncSession = Depends(get_db)):
    row = Incident(
        id=str(uuid.uuid4()),
        title=body.title,
        description=body.description,
        status=IncidentStatus.OPEN,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


@app.get("/api/incidents/{incident_id}", response_model=IncidentOut)
async def get_one(incident_id: str, db: AsyncSession = Depends(get_db)):
    row = await db.get(Incident, incident_id)
    if not row:
        raise HTTPException(404, "not found")
    return row


@app.post("/api/nlp/summarize")
async def summarize(body: LogBody):
    return summarize_logs(body.logs)


@app.post("/api/cv/analyze")
async def cv_only(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "need an image file")
    path = save_upload(file, f"{uuid.uuid4()}_{file.filename}")
    try:
        return analyze_screenshot(path)
    except Exception as e:
        raise HTTPException(500, str(e)) from e


@app.post("/api/rag/query")
async def ask_runbook(body: AskRunbook, db: AsyncSession = Depends(get_db)):
    ctx = None
    if body.incident_id:
        inc = await db.get(Incident, body.incident_id)
        if inc:
            ctx = "\n".join(
                x for x in [inc.description, inc.log_summary, inc.ocr_text, inc.cv_analysis] if x
            )
    return runbooks.query(body.question, extra_context=ctx)


@app.post("/api/rag/ingest")
async def upload_runbook(file: UploadFile = File(...)):
    path = cfg.docs_dir / file.filename
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        n = ingest_file(path)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    return {"file": file.filename, "chunks": n}


@app.post("/api/incidents/{incident_id}/analyze", response_model=IncidentOut)
async def run_analysis(
    incident_id: str,
    logs: str | None = Form(None),
    question: str | None = Form(None),
    screenshot: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
):
    inc = await db.get(Incident, incident_id)
    if not inc:
        raise HTTPException(404, "not found")

    inc.status = IncidentStatus.ANALYZING
    extra_bits = []

    if logs:
        inc.log_excerpt = logs[: cfg.max_log_chars]
        out = summarize_logs(logs)
        inc.log_summary = out["summary"]
        if out["error_signals"]:
            extra_bits.append("\n".join(out["error_signals"][:6]))

    if screenshot and screenshot.filename:
        img_path = save_upload(screenshot, f"{incident_id}_{screenshot.filename}")
        inc.screenshot_path = str(img_path)
        shot = analyze_screenshot(img_path)
        inc.ocr_text = shot["ocr"]["text"]
        inc.cv_analysis = shot["analysis"]
        extra_bits.append(inc.cv_analysis)

    q = question or f"{inc.title} — {inc.description or 'no description'}"
    rag = runbooks.query(q, extra_context="\n".join(extra_bits) or inc.description)
    inc.rag_answer = rag["answer"]
    inc.diagnosis = inc.rag_answer
    inc.status = IncidentStatus.OPEN  # still open; analysis is just notes

    await db.commit()
    await db.refresh(inc)
    return inc
