# Incident Intelligence

Incident Intelligence is an AI-powered IT Service Management (ITSM) and Incident Management system. It leverages Natural Language Processing (NLP), Computer Vision (CV), and Retrieval-Augmented Generation (RAG) to help DevOps and support engineers diagnose, triage, and resolve incidents faster.

## 🚀 Features

*   **Incident Tracking:** Create and manage support incidents.
*   **Log Summarization (NLP):** Automatically summarize large and dense server logs to extract the core causes of failures.
*   **Screenshot Analysis (CV):** Uses Optical Character Recognition (OCR) and Vision AI to analyze provided screenshots of errors and extract meaningful diagnostic text.
*   **Runbook Q&A (RAG):** AI assistant that understands your organization's runbooks and documentation. Ask questions about an incident, and the AI will search ingested runbooks to provide actionable fixes.
*   **Modern Web UI:** A fast, responsive frontend built with React 19 and Vite.

## 🛠 Tech Stack

**Backend:**
*   **Framework:** FastAPI (Python 3)
*   **Database:** SQLite via SQLAlchemy & aiosqlite
*   **AI/NLP:** LangChain, HuggingFace Transformers, OpenAI API (Optional)
*   **Vector DB:** ChromaDB (for Runbook RAG)
*   **Computer Vision:** OpenCV, PyTesseract (Tesseract OCR), Pillow

**Frontend:**
*   **Framework:** React 19
*   **Build Tool:** Vite

**Infrastructure & Deployment:**
*   **Containerization:** Docker & Docker Compose
*   **Orchestration:** Kubernetes (Deployment, PVC, ConfigMap manifests provided)
*   Web server proxy config using NGINX.

## 📂 Project Structure

```text
.
├── backend/            # FastAPI backend, DB connectivity, AI modules
│   ├── cv/             # Computer Vision: Screenshot analysis, OCR pipeline
│   ├── data/docs/      # Markdown runbooks for RAG ingestion
│   ├── database/       # SQLAlchemy models and SQLite setup
│   ├── nlp/            # Log text summarization
│   └── rag/            # Vector store retrieval and Question-Answering
├── docker/             # Dockerfile, docker-compose, and NGINX configs
├── frontend/           # React frontend client
└── k8s/                # Kubernetes deployment manifests
```

## 🏁 Getting Started

### Prerequisites
*   Docker and Docker Compose
*   *(Optional)* OpenAI API Key for advanced LLM capabilities.

### Running Locally with Docker Compose
The easiest way to get the stack running locally is via Docker Compose:

1. Copy the environment variables:
   ```bash
   # Add your OPENAI_API_KEY (if using OpenAI instead of local models)
   export OPENAI_API_KEY="your-api-key"
   ```
2. Build and start the containers:
   ```bash
   cd docker
   docker-compose up --build
   ```
3. Access the application:
   * **Frontend UI:** `http://localhost:3000`
   * **Backend API Docs (Swagger):** `http://localhost:8000/docs`

### Deploying to Kubernetes

To deploy the application in a Kubernetes cluster, apply the manifests in the `k8s/` directory:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/frontend-deployment.yaml
```

The services will be deployed into their respective namespace.

## 🤖 AI Features Configuration

- **Ingesting Runbooks:** The backend automatically reads and vector-ingests Markdown documents present in the `backend/data/docs/` folder heavily utilizing `Sentence-Transformers`. Add more `.md` files here and restart the backend to grow the Runbook QA knowledge base.
- **LLM Provider:** By default, it is configured for a local Huggingface provider or an OpenAI API provider depending on environment variables set in `docker-compose.yml` (`LLM_PROVIDER` / `OPENAI_API_KEY`).
