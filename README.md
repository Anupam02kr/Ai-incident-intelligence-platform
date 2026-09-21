# Incident Intelligence

Incident Intelligence is an AI-powered IT Service Management (ITSM) and incident-management platform. It combines Natural Language Processing (NLP), Computer Vision (CV), and Retrieval-Augmented Generation (RAG) to help teams investigate incidents, understand technical evidence, and find relevant runbook guidance.

## 🚀 Features

- **Incident tracking:** Create, view, and manage support incidents.
- **Log summarization:** Summarize large server logs and extract important error signals.
- **Screenshot analysis:** Use OCR and computer vision to analyze screenshots of errors and extract diagnostic information.
- **Runbook Q&A:** Query Markdown runbooks using retrieval-augmented generation and receive actionable answers.
- **Incident analysis workflow:** Combine logs, screenshots, incident context, and runbook retrieval in a single analysis request.
- **Modern web UI:** React 19 frontend powered by Vite.
- **REST API:** FastAPI endpoints with automatically generated Swagger documentation.

## 🛠 Tech Stack

### Backend

- **Framework:** FastAPI
- **Runtime:** Python 3
- **Database:** SQLite with SQLAlchemy and aiosqlite
- **AI/NLP:** LangChain, Hugging Face Transformers, Sentence Transformers, and optional OpenAI integration
- **Vector store:** ChromaDB
- **Computer vision:** OpenCV, PyTesseract, and Pillow

### Frontend

- **Framework:** React 19
- **Build tool:** Vite

## 📂 Project Structure

```text
.
├── backend/                    # FastAPI backend and AI services
│   ├── app.py                  # FastAPI application and API routes
│   ├── config.py               # Environment-backed application settings
│   ├── cv/                     # Screenshot analysis and OCR pipeline
│   ├── data/docs/              # Markdown runbooks used by RAG
│   ├── database/               # SQLAlchemy models and SQLite setup
│   ├── nlp/                    # Log summarization
│   └── rag/                    # Runbook ingestion and question answering
├── frontend/                   # React/Vite frontend client
│   ├── src/                    # React application source
│   ├── package.json            # Frontend scripts and dependencies
│   └── vite.config.js          # Vite development server and API proxy
├── .env.example                # Optional environment configuration
└── README.md
```

## 🏁 Getting Started

### Prerequisites

- Python 3.10 or newer
- Node.js 18 or newer and npm
- Tesseract OCR installed and available on your system `PATH`
- Optional: an OpenAI API key for OpenAI-powered language-model features

> The project no longer includes the `docker/` or `k8s/` directories. Run the backend and frontend directly on your development machine.

### 1. Configure the environment

From the repository root, copy the example environment file:

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Set `OPENAI_API_KEY` and change `LLM_PROVIDER` only if you want to use an OpenAI provider. The default configuration uses local/offline retrieval where supported.

If Tesseract is not available on `PATH`, set `TESSERACT_CMD` in `.env` to the full path of the Tesseract executable.

### 2. Set up and run the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies and start the API:

```bash
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

The backend will create its local SQLite, upload, and vector-store directories under `backend/data/` as needed. Markdown files placed in `backend/data/docs/` are ingested when the application starts.

### 3. Set up and run the frontend

Open a second terminal from the repository root:

```bash
cd frontend
npm install
npm run dev
```

The Vite development server runs at:

- **Frontend:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **Swagger API docs:** `http://localhost:8000/docs`
- **Health check:** `http://localhost:8000/health`

The Vite configuration proxies `/api` and `/health` requests to the backend on port `8000`.

### Production frontend build

To create and preview a production frontend build:

```bash
cd frontend
npm run build
npm run preview
```

## 🤖 AI Features Configuration

### Runbook ingestion

Add Markdown runbooks to `backend/data/docs/`. The backend automatically loads available documents during startup. You can also upload a runbook through the API using the `/api/rag/ingest` endpoint.

### Language-model provider

The application supports local retrieval/model workflows and optional OpenAI integration. Configure the provider in `.env`:

```dotenv
LLM_PROVIDER=local
OPENAI_API_KEY=
```

### OCR configuration

PyTesseract requires the Tesseract OCR application to be installed separately. Ensure the executable is on your system `PATH`, or configure its location with `TESSERACT_CMD`.

## 🔌 Key API Endpoints

- `GET /health` — Check whether the API is running.
- `GET /api/incidents` — List incidents.
- `POST /api/incidents` — Create an incident.
- `GET /api/incidents/{incident_id}` — Retrieve an incident.
- `POST /api/incidents/{incident_id}/analyze` — Analyze logs, screenshots, and incident context.
- `POST /api/nlp/summarize` — Summarize log text.
- `POST /api/cv/analyze` — Analyze an uploaded screenshot.
- `POST /api/rag/query` — Ask a question about the runbooks.
- `POST /api/rag/ingest` — Ingest an uploaded runbook.

Interactive API documentation is available at `http://localhost:8000/docs` after starting the backend.

## 🧪 Development Notes

- Backend dependencies are pinned in `backend/requirements.txt`.
- Frontend dependencies and scripts are defined in `frontend/package.json`.
- Runtime data such as the SQLite database, uploaded files, and ChromaDB data is stored under `backend/data/`.
- Do not commit secrets or local runtime data. Use `.env` for local configuration and keep API keys out of source control.

## 📄 License

Add your project license information here when a license is selected.
