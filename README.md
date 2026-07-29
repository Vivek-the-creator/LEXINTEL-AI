# LexIntel AI

**Multi-Agent Smart Court & Legal Intelligence Platform**

LexIntel is a full-stack legal intelligence application built with a FastAPI backend and a React/Vite frontend. It combines secure user authentication, case management, evidence uploads, conversation memory, semantic search, and AI agents for legal document intelligence, research, case retrieval, evidence analysis, prediction, strategy planning, drafting, and reporting.

---

## What the Project Includes

- Backend API with FastAPI, MongoDB, and AI orchestration
- Frontend dashboard with React, Vite, Tailwind CSS, and protected routes
- JWT authentication and user/case management
- File upload support for PDFs, images, text, audio, and video
- Conversation memory storage for multi-turn interactions
- FAISS-powered semantic vector search and retrieval
- Groq LLM integration through an abstraction layer
- Modular agent pipeline using LangGraph
- Phase 3 legal intelligence agents for end-to-end workflows

---

## Core Features

- Authentication, user profiles, and case workspaces
- Secure file uploads and document ingestion
- Document intelligence with OCR and structure extraction
- Legal research using retrieval-augmented generation (RAG)
- Similar case retrieval from case judgment vectors
- Evidence analysis with timeline generation and duplicate detection
- Outcome prediction with AI reasoning and disclaimers
- Legal strategy recommendations
- Draft legal document generation
- Explainable case reports and summaries

---

## AI Agent Overview

### Case Intelligence Agents

- **Document Intelligence**
  - Extracts text from uploaded PDFs, images, and raw text
  - Uses OCR fallback for image-based or scanned files
  - Detects parties, dates, organizations, legal sections, and document type
  - Generates structured summaries, entities, and chunked documents

- **Legal Research**
  - Builds legal research context from the case summary
  - Retrieves relevant legal provisions from a FAISS-backed legal index
  - Identifies applicable acts, sections, remedies, and legal principles

- **Similar Case Retrieval**
  - Performs semantic search against a case judgments index
  - Returns enriched case summaries, citations, and verdict context

- **Evidence Analysis**
  - Catalogs uploaded evidence files and extracts metadata
  - Detects duplicate evidence and file categories
  - Produces a chronological evidence timeline and missing evidence hints

### Decision Support Agents

- **Outcome Prediction**
  - Estimates case success probability and risk
  - Produces reasoning-based predictions with an explicit disclaimer

- **Strategy Planning**
  - Recommends ranked legal strategies with pros, cons, and next steps
  - Uses document intelligence, legal research, and outcome prediction data

- **Legal Drafting**
  - Generates draft legal documents with placeholders for lawyer review
  - Includes disclaimers and professional formatting guidance

- **Report Explainability**
  - Synthesizes the full case intelligence workflow into a single report
  - Includes evidence, legal rationale, similar cases, and explanation chains

---

## Architecture Summary

### Backend

- FastAPI server with modular route structure
- MongoDB for sessions, users, and conversation memory
- Groq LLM provider via `app.ai.llm.groq_provider`
- Sentence-transformers embeddings and FAISS vector store
- LangGraph state graph orchestration
- PaddleOCR and pypdf for document extraction

### Frontend

- React + Vite + Tailwind CSS user interface
- Protected dashboard and case management routes
- Upload, conversation, reports, and case detail pages
- Axios-based API client system

### Pipeline Design

- `BaseAgent` provides retry handling, logging, and LLM integration
- `LexIntelOrchestrator` routes requests through pipeline nodes
- `LexIntelState` is shared state passed between nodes
- `PromptRegistry` centralizes all prompt templates
- RAG indexes are built and queried through FAISS vector storage

---

## Project Structure

- `backend/`
  - `main.py` — FastAPI application entry point
  - `app/api/routes/` — auth, users, uploads, AI, agents, and cases endpoints
  - `app/ai/` — AI agents, LLM abstraction, RAG, prompts, memory, and orchestration
  - `app/core/` — configuration, security, and exception handling
  - `app/db/` — MongoDB connection helper
- `frontend/`
  - React application built with Vite and Tailwind CSS
- `uploads/` — local uploaded file storage
- `vector_store/` — FAISS index artifacts and metadata

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- MongoDB (local or Atlas)
- Groq API key

---

## Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit backend/.env with JWT_SECRET_KEY, MONGODB_URL, GROQ_API_KEY, and any provider settings
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open API docs at `http://localhost:8000/api/docs`

---

## Frontend Setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open the app at `http://localhost:5173`

---

## Key Backend Environment Variables

- `JWT_SECRET_KEY` — required secret for auth tokens
- `MONGODB_URL` — database connection string
- `GROQ_API_KEY` — Groq LLM key
- `LLM_PROVIDER` — `groq` by default
- `LLM_MODEL` — e.g. `llama3-8b-8192`
- `LLM_TEMPERATURE` — model temperature
- `LLM_MAX_TOKENS` — max completion tokens
- `LLM_TIMEOUT` — request timeout seconds
- `LLM_MAX_RETRIES` — retry attempts for LLM calls
- `LLM_STREAMING` — enable response streaming
- `EMBEDDING_MODEL` — transformer model for embeddings
- `EMBEDDING_DEVICE` — `cpu` or `cuda`
- `VECTOR_STORE_DIR` — FAISS index storage path
- `RAG_CHUNK_SIZE` — text chunk size for indexing
- `RAG_CHUNK_OVERLAP` — overlap between chunks
- `RAG_TOP_K` — default retrieval count
- `RAG_SIMILARITY_THRESHOLD` — minimum similarity score
- `MEMORY_MAX_HISTORY` — stored message count per session
- `UPLOAD_DIR` — uploads storage directory

---

## Selected API Endpoints

### AI Infrastructure

- `GET /api/ai/health` — AI infrastructure health check
- `GET /api/ai/llm/ping` — verify LLM provider connectivity
- `POST /api/ai/llm/complete` — direct LLM completion (streaming supported)
- `POST /api/ai/agent/run` — execute a named pipeline
- `POST /api/ai/agent/stream` — stream pipeline output
- `POST /api/ai/embeddings/embed` — generate an embedding
- `POST /api/ai/vector/index` — index text into FAISS
- `POST /api/ai/vector/search` — semantic vector search

### Phase 3 Agents

- `POST /api/agents/document-intelligence/run`
- `POST /api/agents/document-intelligence/upload`
- `POST /api/agents/legal-research/run`
- `POST /api/agents/similar-cases/run`
- `POST /api/agents/evidence-analysis/run`
- `POST /api/agents/evidence-analysis/upload`

---

## Testing

Run backend tests from the `backend` directory:

```bash
cd backend
pytest
```

---

## Notes

- This repository already includes core auth, dashboard, file upload, AI orchestration, RAG, and agent APIs.
- The AI stack is designed for transparency and extension: new agents can be added without changing the pipeline infrastructure.
- All generated legal output is informational and must be reviewed by qualified legal professionals before use.

---

## Recommended Next Steps

- Populate FAISS indexes with legal provisions and case judgments
- Add frontend UI flows for Phase 3 agent outputs
- Harden authentication, validation, and production deployment settings
- Extend the user-facing case workspace and report export features
