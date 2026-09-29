# Prompt: Module 1 (Platform), Days 3 to 5 + P1 Walkthrough

Paste everything below the divider into your AI coding assistant, from the repo root on a fresh branch. Day 2 must be merged to `main` first.

**Note on days:** the project plan is 4 days. Day 3 is integration, Day 4 is hardening and delivery. "Day 5" below is an **overflow buffer**: use it only if you really have an extra day; otherwise its items are the things to cut. Do Day 3 and Day 4 in order, and do not start Day 5 items until both are finished.

---

You are continuing as a senior backend engineer on **AutoRubric**. Read `PROJECT_CONTEXT.md`, `MODULE_SPLIT.md`, `docs/contracts.md`, `docs/contract-change-proposals.md`, `docs/scoring-rules.md` and the current code first. I am **P1**. Days 1 and 2 are done (contracts, stubs, API, Docker, CI, auth, reliable pipeline, scorer, verify endpoint).

## Rules (unchanged)

- Touch only P1 folders (`api/`, `core/`, `workers/`, `pipeline/`, `scorer/`, `migrations/`, `deploy/`, `docker-compose.yml`, `.github/`, `scripts/`, `docs/`, and their tests). Never edit another module's folders. If a teammate's module is broken or late, adapt in `pipeline/nodes.py` or report it; do not fix it in their folder.
- **Verify, do not assume.** After each task, run the relevant commands (`make test`, `make lint`, `make up`, `make demo`) and only report what actually passed. If something cannot be run here, say so explicitly.
- ruff, mypy and pytest stay green. Commit per task: `p1: <what>`. Update `docs/P1_WALKTHROUGH.md` at the end of each day (see the last section).

---

# DAY 3: Integrate the real modules

## Task 1: Module wiring and safe fallbacks

- Add per-stage flags in `core/config.py`: `STAGE_<NAME>_MODE=real|stub` for extraction, segmentation, retrieval, evaluation, audit, annotation. The default is `real`. This lets you isolate a broken teammate module during the demo without code changes.
- Log clearly at startup which stages run in which mode.
- Evaluator: support `EVALUATOR_BACKEND=mock|cpu|gpu` (P4 provides the implementation; you only pass the value through). Default `cpu`. Model weights are **not** in git and **not** baked into the image: mount a volume (`models/`) and add `scripts/download_model.sh` that calls P4's download script. `make models` runs it.
- Add a `/health/ready` endpoint that checks Postgres, Redis, and that the model files exist (or reports the evaluator's mock mode).

## Task 2: Contract conformance tests (protects the whole team)

Create `backend/tests/conformance/` with one test per public function of every module (extraction, annotation, nlp x2, retrieval x2, evaluator, audit x2, scorer). Each test loads fixtures, calls the function, validates the output against the contract models, and checks basic invariants (e.g. every `Proposition.token_ids` exists in the input tokens, every `Candidate` references real propositions and criteria, every `Classification.prop_id` exists). Run these in CI so a teammate who breaks a contract gets a red build before it reaches the pipeline.

## Task 3: End-to-end with real fixture PDFs

- Use P2's fixture PDFs (clean, two-column, hidden-text, table) and P3's sample rubric.
- Integration test per fixture PDF: upload, run the full pipeline, assert final status and `ScoreResult` validity.
- Hidden-text PDF: assert that the job ends `NEEDS_REVIEW`, that the injected content earned **no marks**, and that the critic flag is visible in the result.
- If a teammate module is not merged yet, mark that test `xfail` with a reason, not deleted.

## Task 4: Bulk upload and cohorts

- Add `cohort_id` to submissions (migration).
- `POST /submissions/batch`: multiple PDFs + `rubric_id` + optional `cohort_id`; returns a list of `{filename, doc_id, job_id}`. Reject bad files individually without failing the whole batch.
- `GET /cohorts/{cohort_id}`: counts by status, list of docs with score and needs-review flag.
- Configure worker concurrency and a queue for GPU-heavy work (`evaluate`) separate from CPU work, so bulk uploads do not starve status calls.

## Task 5: Upload safety

- Validate uploads: PDF magic bytes (not just the extension), max size (config), max page count (check quickly with PyMuPDF), reject encrypted PDFs with a clear error.
- Store files on a volume with random names; never use the client filename in a path.
- Return the standard error format with 4xx codes. Add tests for each rejection case.

## Task 6: Results and annotated PDF

- After annotation, save the PDF on the volume and record its path. `GET /results/{doc_id}/pdf` streams it with the right content type (auth required).
- Results include `annotated_pdf_available`, `needs_review`, and per-criterion `capped` and `note` fields (if the contract change was approved).

## Task 7: Collusion endpoint

- After each job, `embed_propositions` output is already in `job_artifacts` (Day 2). `GET /cohorts/{id}/collusion`: gather the embeddings of all `DONE` or `NEEDS_REVIEW` docs in the cohort, call `detect(...)`, cache the `CollusionReport` in the DB keyed by the set of doc ids, and recompute only when the set changes.
- Handle cohorts with fewer than 2 docs (return an empty report, not an error).

## Day 3 acceptance

- A real typed PDF goes upload, through every real stage, to a score and an annotated PDF.
- Conformance tests run in CI. The hidden-text fixture ends `NEEDS_REVIEW` with no injected marks.
- Batch upload of 5 PDFs works and the cohort endpoint reports them.
- Update `docs/P1_WALKTHROUGH.md`.

---

# DAY 4: Harden, package, deliver

## Task 8: Reliability review

- Go through every endpoint and Celery task for unhandled exceptions, missing timeouts, missing transactions, and N+1 queries. Fix what you find and list what you fixed.
- Confirm that a worker crash mid-job leaves the job recoverable (`acks_late`, retry endpoint).
- Add DB indexes for the common lookups (job id, doc id, cohort id, status).

## Task 9: Security checklist

Verify and document in `docs/SECURITY.md` (state what is done and what is not):
- No secrets in the repo or images; `.env` ignored; production `JWT_SECRET` must be set (the app refuses to start with the default).
- All routes authenticated except `/health*` and `/auth/login`.
- Upload validation (Task 5), CORS limited to configured origins, error messages do not leak stack traces.
- Login attempts are rate limited (simple in-memory or Redis counter is enough).
- Dependency audit (`pip-audit`) result.

## Task 10: Clean-machine run and demo

- Test a **from-scratch** run: fresh clone, `cp .env.example .env`, `make up`, `make migrate`, `make models`, `make demo`. Fix every missing step. Document it exactly in `README.md`.
- `scripts/demo.sh` demonstrates three cases with real PDFs: (1) a clean answer gets a score and an annotated PDF, (2) the hidden-text PDF triggers `NEEDS_REVIEW`, (3) two near-duplicate PDFs in one cohort appear in the collusion report. Print a readable summary for each.
- `make demo-reset` clears demo data.

## Task 11: Load smoke test

- `scripts/load_test.py`: submit 20 PDFs in one batch, measure time to completion per stage and overall, report failures. Save the results table to `docs/performance.md`. Note the hardware used. This gives a real number for the report.

## Task 12: Documentation for the report

Generate, from the actual code (not from memory):
- `docs/architecture.md`: a Mermaid diagram of the pipeline, a sequence diagram of one submission (API, queue, worker, stages, DB), the job state machine, and the DB schema.
- `docs/RUNBOOK.md`: how to start, stop, view logs, retry a failed job, inspect the dead-letter table, reset the demo.
- OpenAPI: confirm every endpoint has summary, description and examples in the auto-generated docs at `/docs`.

## Task 13: Release

- Ensure CI is green on `main`, tag `v0.1.0`, and write `CHANGELOG.md`.
- Print a final checklist of what works, what is stubbed, and what is known to be broken.

## Day 4 acceptance

- Fresh-clone run works using only the README.
- The three-case demo works. Load test numbers recorded.
- `SECURITY.md`, `RUNBOOK.md`, `architecture.md`, `performance.md` exist.
- `main` is green and tagged. Update `docs/P1_WALKTHROUGH.md` for the last time.

---

# DAY 5: Overflow buffer (only if there is an extra day; otherwise skip)

Do these in order, and stop when time runs out:

1. Resume-from-stage: a retried job restarts at the failed stage using saved `job_artifacts`, not from scratch.
2. Metrics endpoint (Prometheus format): jobs by status, stage durations, failures.
3. Admin endpoints: list jobs, filter by status, re-run a document with a different rubric.
4. Rubric versioning: a result records the exact rubric version it was scored with.
5. Human review flow: `POST /results/{doc_id}/review` lets a reviewer approve or override an untrusted criterion, recording who and why; the scorer re-runs with the approved verdict, and the change is stored in the audit bundle.
6. Extra tests for the weakest coverage areas shown by the coverage report.

---

# The P1 walkthrough file (create it now, update it at the end of every day)

Create `docs/P1_WALKTHROUGH.md`. It is my personal guide to my module, and I will use it for the team demo and for the viva. **Build it by reading the actual repo and running the commands, not from memory. Mark anything you could not verify as "UNVERIFIED".**

Required sections:

1. **What P1 owns**: folders, public functions, and how P1 connects to P2 to P5 (a small table).
2. **Architecture in 60 seconds**: a plain-language paragraph plus a Mermaid diagram of the pipeline.
3. **Status board**: a table with columns `Item | Day | Status (DONE / IN PROGRESS / TODO / BLOCKED) | Evidence (test name, command, or file)`. Cover every task from Days 1 to 5, including the contract change proposals and whether the team approved each.
4. **File map**: every important file or folder in P1's area with a one-line explanation.
5. **How to run**: exact commands for start, test, demo, migrate, download models, and each stage mode flag.
6. **API reference**: table of endpoints (method, path, auth, purpose, example file).
7. **Scoring rules as implemented**: the rules from `docs/scoring-rules.md` in plain words with one worked numeric example (3 criteria, one dependency, one untrusted label) showing marks step by step.
8. **Key design decisions and why**: e.g. why the model outputs labels and not scores, why fail-closed on missing verdicts, why Decimal arithmetic, why stage flags, why audit bundles, why queues are split. Each in 2 to 3 sentences.
9. **Known limitations and risks**: honest list.
10. **What is left to do**: ordered to-do list with owner (P1 or another person) and dependencies on teammates.
11. **Viva prep**: 12 likely questions and short answers about P1's work (deterministic scoring, prompt-injection defence, retries, auditability, scalability, why Celery, why LangGraph, what happens when a worker dies, how a score is re-derived, and so on).
12. **Change log**: one line per day: what was completed, with date.

Rules for this file: keep sentences plain, no filler, and keep it consistent with the code. At the end of each day, update the status board and to-do list, and add the change-log line.

---

At the end of each day, print: what changed, commands to run, what was verified versus not verified, what the team must do next, and any assumptions.
