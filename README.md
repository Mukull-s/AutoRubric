# AutoRubric

AutoRubric is a multi-agent explainable rubric-grading system featuring automated rubric compilation, semantic proposition evaluation, and adversarial audit checks.

---

## Current Running Services

| Service | Local URL | Description | Default Credentials |
| :--- | :--- | :--- | :--- |
| **Backend API (FastAPI)** | `http://localhost:8000` | REST API, OpenAPI docs at `/docs`, Health at `/health/ready` | `admin@example.com` / `admin` |
| **Frontend (Next.js)** | `http://localhost:3000` | Web UI (Rubrics, Submissions, Evaluation Dashboard) | Sign in with backend admin credentials |

---

## How to Run Locally (Native / Windows PowerShell)

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- Virtual environment at `AutoRubric/autorubric/backend/.venv`

> **Note on Folder Structure:**
> Check your current directory prompt (`Get-Location`):
> - If you are in `D:\projects\capstone-1`: go to `AutoRubric\autorubric\...`
> - If you are in `D:\projects\capstone-1\AutoRubric`: go to `autorubric\...`

---

### 1. Start the Backend (FastAPI - Port 8000)

In your first terminal:

```powershell
# Navigate to the backend directory:
# If you are in D:\projects\capstone-1:
cd D:\projects\capstone-1\AutoRubric\autorubric\backend

# Activate the virtual environment:
.\.venv\Scripts\Activate.ps1

# Start the server:
python -m uvicorn autorubric.api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Direct one-line command (if already in backend folder):**
```powershell
.\.venv\Scripts\python.exe -m uvicorn autorubric.api.main:app --host 127.0.0.1 --port 8000 --reload
```


- **Health check:** [http://localhost:8000/health/ready](http://localhost:8000/health/ready)
- **API Swagger docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Start the Frontend (Next.js - Port 3000)

In a second terminal:

```powershell
# Navigate to the frontend directory:
# If you are in D:\projects\capstone-1:
cd D:\projects\capstone-1\AutoRubric\autorubric\frontend

# Start Next.js development server:
npm run dev
```

> If port 3000 is reported in use, see the Troubleshooting section below.

- **Web App:** [http://localhost:3000](http://localhost:3000)
- **Default Login:** `admin@example.com` / `admin`

### 3. (Optional) Run the Celery Worker

The backend includes in-process background task execution for quick evaluations. If you want a dedicated standalone worker:

```powershell
cd autorubric\backend
.\.venv\Scripts\Activate.ps1

# Note: On Windows, use the solo pool
celery -A autorubric.workers.celery_app worker -P solo -l INFO
```

---

## How to Run with Docker Compose

If Docker Desktop is running:

```bash
cd autorubric
cp .env.example .env
docker compose up -d --build
```

---

## Verification & Health Check

1. **Backend Health Check:**
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/ready" -Method Get
   # Expected output: {"status": "ready"}
   ```

2. **Frontend UI:**
   Navigate to [http://localhost:3000](http://localhost:3000) and log in with:
   - **Username:** `admin@example.com`
   - **Password:** `admin`

3. **Run Backend Test Suite:**
   ```powershell
   cd autorubric\backend
   .\.venv\Scripts\python.exe -m pytest
   ```
