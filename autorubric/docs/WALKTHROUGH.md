# AutoRubric Development Walkthrough

This document serves as a comprehensive walkthrough of the work done during the P1 to P5 development phases and outlines the remaining tasks and configurations needed to run the project.

## 1. Work Completed

### Phase 1 to 4: Core Engine and Frontend Foundation
- **Backend Architecture:** Built a FastAPI application with async database connections (`asyncpg`) and SQLAlchemy models (`Job`, `Rubric`, `Submission`, `Cohort`, `Result`).
- **Processing Pipeline:** Set up Celery tasks for asynchronous processing (`extract_text`, `grade_submission`, `collate_results`) backed by Redis.
- **Grading & Audit Harness:** Integrated an LLM-based grading pipeline and an audit framework (Critic and Collusion detectors).
- **Frontend App:** Built a Next.js App Router application with React Query for state management, providing a unified dashboard for job tracking, rubric building, submission uploading, cohort polling, and results viewing.

### Phase 5: Code Hardening & Final Verifications
- **Strict Linting & Type Safety:** 
  - Ran a comprehensive migration on the frontend codebase, changing all `@typescript-eslint/no-explicit-any` usages to `unknown` or strictly typed interfaces (e.g., `ResultData`, `JobInitial`).
  - Fixed Next.js build errors (e.g., handling possible `undefined` states on API query results).
  - Addressed `react-hooks/set-state-in-effect` warnings using `eslint-disable` where the Next.js hydration pattern necessitated it.
  - The frontend now passes `npm run lint` and `npm run build` without any errors or warnings.
- **Audit Rule Improvements:** 
  - Evaluated the Critic detector with a 32-case dataset, catching edge cases in injection prompts.
  - Refined rules to catch new adversarial patterns (e.g., `"system override"`, `"bypass checks"`) while eliminating false positives on natural grading statements like `"No credit is deserved for this answer"`.
  - Achieved a 100% pass rate in the Critic evaluation script (`scripts/evaluate_critic.py`).
- **Collusion Evaluation:**
  - Evaluated the Collusion detector with synthetic text data using `sentence-transformers/all-MiniLM-L6-v2`.
  - Confirmed the detection successfully ignores independent similar answers while flagging maliciously identical or subset documents based on their vector cosine similarity.
- **Playwright Setup:** Built automated mock-driven visual regression tests in `tests/screenshots.spec.ts` to capture the end-to-end UI states (Login, Rubric Builder, Cohort Progress, Collusion Heatmap).

---

## 2. Environment Setup & Configuration

You need a `.env` file at the root of `autorubric/` (a sample `.env.sample` has been generated for you).

### Secret Keys and Database URIs
1. **SECRET_KEY**: Generate a random secure key using `openssl rand -hex 32` or `python -c "import secrets; print(secrets.token_hex(32))"`.
2. **DATABASE_URL**: A standard PostgreSQL connection string. 
   - *Example local:* `postgresql+asyncpg://postgres:postgres@localhost:5432/autorubric`
   - *If using a managed service:* Get the connection string from your provider (e.g., Supabase) and ensure it starts with `postgresql+asyncpg://`.
3. **REDIS_URL**: 
   - *Example local:* `redis://localhost:6379/0`
   - You need Redis for Celery tasks.
4. **LLM API Keys**: Put your `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) to run the AI grading pipeline.

---

## 3. Pending/Remaining Tasks (Handoff to P1)

The frontend is hardened and fully typed, but the backend requires the Day 3/4 endpoints to be completed so the UI can connect to real data instead of mocks.

### Outstanding Backend API Endpoints (P1 Tasks)
The following endpoints must be implemented by the P1 backend developer:
- `GET /rubrics`: List all rubrics (needed for the dashboard/rubrics page).
- `GET /rubrics/{id}`: Fetch a specific rubric by ID.
- `GET /results/{doc_id}/propositions`: Return propositions (id, text, bboxes, `from_hidden_text`) for the frontend to show evidence.
- `GET /results/{doc_id}`: Must include critic verdicts (`flags` and `reason`) per criterion.
- `POST /submissions/batch`, `GET /cohorts/` list and detail endpoints are still pending from Day 3.

### Docker Environment (`make up`)
- **Error:** `unable to get image 'redis:7-alpine'` / `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.
- **Cause:** This error indicates Docker Desktop is not running or the WSL integration is failing on your host machine.
- **Action:** Ensure Docker Desktop is started. Once started, try running `make up` again. You may also need to manually test `docker pull redis:7-alpine` to ensure you are not blocked by a corporate firewall or proxy.

### Playwright Snapshots
- We have a screenshot capturing script (`npx playwright test tests/screenshots.spec.ts`). You need to run `npx playwright install` and re-run the tests locally if you want to regenerate the visual regression assets in `docs/screenshots/`.
