# AutoRubric

AutoRubric is a multi-agent explainable rubric-grading system.

## Quick Start (Local Windows / PowerShell)

### 1. Backend (Port 8000)
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn autorubric.api.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health/ready`

### 2. Frontend (Port 3000)
```powershell
cd frontend
npm run dev
```
- Web App: `http://localhost:3000`
- Default Login: `admin@example.com` / `admin`

## Docker Quick Start
```bash
cp .env.example .env
docker-compose up -d --build
```

## Structure
- `backend/`: FastAPI backend, Celery workers, ML pipeline.
- `ml/`: ML training scripts and notebooks.
- `frontend/`: Next.js frontend app.

## Module Owners
- **P1**: Platform, Orchestration & Scorer
- **P2**: Extraction & Annotation
- **P3**: NLP, Rubric & Retrieval
- **P4**: ML Evaluator
- **P5**: Frontend, Critic & Collusion
