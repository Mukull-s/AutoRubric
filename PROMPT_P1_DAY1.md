# Prompt: Module 1 (Platform), Day 1

Paste everything below the line into your AI coding assistant (Claude Code, Cursor, etc.) from an empty repo folder. Put `PROJECT_CONTEXT.md` and `MODULE_SPLIT.md` in the folder first so the assistant can read them.

---

You are a senior backend engineer setting up a production-grade monorepo for **AutoRubric**, a multi-agent explainable rubric-grading system. Read `PROJECT_CONTEXT.md` and `MODULE_SPLIT.md` in this folder first. I am **P1 (Platform, Orchestration & Scorer)**. Four teammates own the other modules, and we have 4 days total. Today is Day 1.

## Goal for today

1. Create the production repo structure below.
2. Freeze the shared contracts as Pydantic models.
3. Create **stub implementations of every module's public function** (returning fixture data) so the full pipeline runs end to end by the end of today.
4. Bring up Docker Compose, the FastAPI gateway (stubbed endpoints), the Celery worker and CI.

Do not implement real OCR, NLP, ML or scoring logic today. The scorer gets a first simple version only if everything else is done.

## Hard rules

- **Do not name any folder or package `platform`.** It shadows Python's standard library. Use `api/` and `core/` instead.
- One Python package, `autorubric`, in a `src/` layout under `backend/`. Python 3.11.
- Each module exposes **one public function** from its package `__init__.py`. The pipeline imports only that. Teammates will replace the stub body without changing the signature.
- Stubs must load JSON from `backend/tests/fixtures/<module>/` so they are realistic and swappable.
- Type hints everywhere. Ruff (lint + format), mypy (basic), pytest.
- No secrets in code. All config via environment variables through `pydantic-settings`.
- Never commit model weights, `.env`, or large files.

## Target structure

```
autorubric/
├─ backend/
│  ├─ pyproject.toml              # one project; optional extras per module: extraction, nlp, ml, audit
│  ├─ alembic.ini
│  ├─ migrations/                 # P1 base migration; P3 adds a separate vector migration later
│  ├─ src/autorubric/
│  │  ├─ contracts/               # SHARED, changes need all 5 approvals
│  │  │  ├─ enums.py              # Label, JobStatus
│  │  │  ├─ document.py           # Token, Proposition
│  │  │  ├─ rubric.py             # Rubric, Criterion, CreditMap
│  │  │  ├─ grading.py            # Candidate, Classification, CriticVerdict, ScoreResult
│  │  │  └─ collusion.py          # CollusionReport
│  │  ├─ core/                    # P1: config.py, logging.py, db.py, errors.py, security.py
│  │  ├─ api/                     # P1: main.py, deps.py, routers/{rubrics,submissions,jobs,results,cohort,auth}.py, schemas/
│  │  ├─ workers/                 # P1: celery_app.py, tasks.py
│  │  ├─ pipeline/                # P1: graph.py (LangGraph), nodes.py, state.py
│  │  ├─ scorer/                  # P1: score(classifications, rubric) -> ScoreResult
│  │  ├─ extraction/              # P2: extract(pdf_bytes) -> list[Token]              (stub today)
│  │  ├─ annotation/              # P2: annotate(pdf_bytes, ScoreResult) -> bytes      (stub today)
│  │  ├─ nlp/                     # P3: compile_rubric(json) -> Rubric ; segment(tokens) -> list[Proposition]  (stub today)
│  │  ├─ retrieval/               # P3: match(props, rubric) -> list[Candidate] ; embed_propositions(props)    (stub today)
│  │  ├─ evaluator/               # P4: classify(pairs) -> list[Classification]        (stub today)
│  │  └─ audit/                   # P5: critic.py audit(...) -> list[CriticVerdict] ; collusion.py detect(...) -> CollusionReport (stubs today)
│  └─ tests/
│     ├─ unit/<module>/
│     ├─ integration/             # end-to-end pipeline test on stubs
│     └─ fixtures/{extraction,nlp,retrieval,evaluator,audit,scorer,annotation,rubrics}/
├─ ml/                            # P4: training scripts, configs, notebooks (empty README today)
├─ frontend/                      # P5: Next.js app (empty README today)
├─ deploy/
│  ├─ backend.Dockerfile
│  └─ worker.Dockerfile           # can share a base image
├─ docs/
│  ├─ architecture.md
│  ├─ api-examples/               # JSON request/response example per endpoint (P5 needs these TODAY)
│  └─ contracts.md
├─ scripts/                       # dev helpers, e.g. seed.py, demo.sh
├─ .github/
│  ├─ workflows/ci.yml
│  ├─ pull_request_template.md
│  └─ CODEOWNERS
├─ docker-compose.yml
├─ Makefile
├─ .env.example
├─ .gitignore
├─ .editorconfig
└─ README.md
```

Give every subpackage an `__init__.py` that exports only its public function(s), and a short `README.md` stating the owner, the function signature and what is stubbed.

## Task 1: Contracts (Pydantic v2, `contracts/`)

Implement exactly these models. Add docstrings and one example each (`model_config` `json_schema_extra`).

- `Label` enum: `FULL_CREDIT, PARTIAL_CREDIT, NO_CREDIT, MISCONCEPTION`
- `JobStatus` enum: `QUEUED, EXTRACTING, SEGMENTING, RETRIEVING, EVALUATING, AUDITING, SCORING, ANNOTATING, DONE, FAILED, NEEDS_REVIEW`
- `BBox`: `x, y, w, h` floats (PDF points, origin top-left) plus `page: int`
- `Token`: `id, text, page, bbox, block_id, is_hidden: bool = False`
- `Proposition`: `id, doc_id, text, token_ids, page, bboxes: list[BBox], from_hidden_text: bool = False`
- `Criterion`: `id, description, weight (>0), depends_on: list[str] = []`
- `CreditMap`: defaults FULL=1.0, PARTIAL=0.5, NO_CREDIT=0.0, MISCONCEPTION=0.0 (configurable)
- `Rubric`: `id, title, criteria: list[Criterion], credit_map: CreditMap, max_score` (weights sum validated)
- `Candidate`: `prop_id, criterion_id, similarity`
- `Classification`: `id, prop_id, criterion_id, label, confidence (0..1)`
- `CriticVerdict`: `classification_id, trusted: bool, reason: str, flags: list[str]`
- `CriterionResult`: `criterion_id, label, credit, marks, evidence_bboxes: list[BBox], trusted: bool`
- `ScoreResult`: `doc_id, rubric_id, per_criterion: list[CriterionResult], total, max_total, needs_review: bool`
- `CollusionReport`: `cohort_id, doc_pairs: [{a, b, similarity, matching_props: list[str]}]`

Also write `docs/contracts.md` summarising them in a table. Add a unit test that every model round-trips through JSON.

## Task 2: Stubs and fixtures for every module

For each public function, create the function with the **final signature** and a body that reads fixture JSON and returns validated contract objects. Create the fixture files with small but realistic data (a 3-criterion rubric with one dependency, about 6 tokens per criterion, propositions, candidates, classifications including one MISCONCEPTION, and a critic verdict list with one untrusted item). Keep all fixture IDs consistent across files so the stubs chain together correctly.

## Task 3: Pipeline orchestration (P1 core)

- `pipeline/state.py`: a typed state (`doc_id`, `rubric`, `pdf_bytes`, `tokens`, `propositions`, `candidates`, `classifications`, `verdicts`, `score`, `annotated_pdf`, `status`, `error`).
- `pipeline/graph.py`: a **LangGraph** graph with one node per stage: extract -> segment -> retrieve -> evaluate -> audit -> score -> annotate. Each node calls only the module's public function, updates state, and reports status.
- Untrusted verdicts must not be silently scored: pass them to the scorer, which marks them for review.
- `workers/celery_app.py` and `tasks.py`: one Celery task `run_pipeline(job_id)` that runs the graph, updates job status in Postgres after every stage, has retries with backoff and a timeout, and sets FAILED with the error message on exception.

## Task 4: API (FastAPI, `api/`)

Endpoints (all working with the stubs; async; Pydantic request/response schemas; consistent error format):

- `POST /auth/login` (simple JWT, single seeded admin user from env vars)
- `POST /rubrics` (JSON body, validated against `Rubric`), `GET /rubrics/{id}`
- `POST /submissions` (multipart: PDF + `rubric_id`; returns `job_id`, enqueues Celery task)
- `GET /jobs/{job_id}` (status, timestamps, error)
- `GET /results/{doc_id}` (`ScoreResult`) and `GET /results/{doc_id}/pdf` (annotated PDF)
- `GET /cohort/{cohort_id}/collusion` (`CollusionReport`)
- `GET /health`

Save one request and response JSON example per endpoint in `docs/api-examples/` **as soon as the schemas exist**. Enable CORS for `http://localhost:3000`.

## Task 5: Database

SQLAlchemy 2.0 (async) models and one Alembic base migration: `users`, `rubrics`, `submissions`, `jobs`, `results`. Store rubric and score JSON as JSONB. Leave a comment that P3 will add vector tables in a **separate** migration file.

## Task 6: Docker and dev experience

- `docker-compose.yml`: `api`, `worker`, `redis`, `postgres` (use the `pgvector/pgvector` image), health checks, named volumes, env from `.env`.
- Dockerfiles in `deploy/` (multi-stage, non-root user).
- `Makefile` targets: `up`, `down`, `logs`, `migrate`, `test`, `lint`, `fmt`, `demo`.
- `.env.example` with every variable documented.
- `scripts/demo.sh`: logs in, posts the sample rubric, uploads a sample PDF, polls the job, prints the result.

## Task 7: Repo hygiene and CI

- `.github/workflows/ci.yml`: on PR, run ruff, mypy, pytest (spin up postgres and redis services for the integration test).
- `.github/CODEOWNERS`: map folders to placeholder handles `@P1`..`@P5` per `MODULE_SPLIT.md`; `contracts/` requires all five.
- `.github/pull_request_template.md`: what changed, module owner, contract changes (Y/N), tests added, how to verify.
- `.gitignore` (weights, `.env`, `node_modules`, `__pycache__`, `.venv`, large PDFs).
- `README.md`: project summary, quick start (`cp .env.example .env && make up && make demo`), structure, branch and PR rules, module owners.

## Task 8: Tests

- Unit: contracts round-trip, each stub returns valid contract objects.
- Integration: run the LangGraph pipeline on stubs end to end and assert the final `ScoreResult` validates and status reaches `DONE`.
- API: use `httpx.AsyncClient` to test auth, rubric creation, submission and job polling (Celery in eager mode).

## Order of work

1. Repo skeleton + `pyproject.toml` + lint/test config
2. Contracts + tests
3. Fixtures + stubs for all modules
4. Pipeline graph + integration test (must pass)
5. DB models + migration
6. API + Celery + API tests
7. Docker Compose + Makefile + demo script
8. CI + CODEOWNERS + PR template + README + `docs/api-examples/`

Commit after each numbered step with messages like `p1: add contracts`. Work on branch `feature/p1-bootstrap` and open one PR to `main` at the end.

## Acceptance criteria (Day 1 done when)

- `cp .env.example .env && make up && make demo` runs the full stubbed pipeline and prints a valid `ScoreResult`.
- `make test` and `make lint` pass, and CI is green.
- `docs/api-examples/` contains examples for all endpoints.
- Every teammate's folder exists with a stub, a fixture and a README, so they can start replacing the stub immediately.
- Nothing outside the P1 folders contains real logic yet.

At the end, print a short summary: what was created, the exact commands to run, the list of stub signatures, and anything you had to assume.
