# Prompt: Module 1 (Platform), Day 2

Paste everything below the divider into your AI coding assistant, from the repo root on a fresh branch `feature/p1-day2`. Day 1 must be merged to `main` first.

---

You are continuing as a senior backend engineer on **AutoRubric**. Read `PROJECT_CONTEXT.md`, `MODULE_SPLIT.md`, `docs/contracts.md` and the existing code first. I am **P1**. Day 1 (contracts, stubs, fixtures, API, Docker, CI) is done. Today is Day 2: make the platform **reliable** and build the real **deterministic scorer**.

## Rules (unchanged)

- Touch only P1 folders: `api/`, `core/`, `workers/`, `pipeline/`, `scorer/`, `migrations/`, `deploy/`, `docker-compose.yml`, `.github/`, tests for those.
- **Do not edit `contracts/` directly.** Where a contract change is needed (Task 0), write it up in `docs/contract-change-proposals.md` and wait for approval from all 5. Prefer changes that add fields with defaults.
- Do not edit other modules' stub bodies. Glue code that adapts between modules lives in `pipeline/nodes.py`.
- Type hints, ruff, mypy, pytest all stay green. Commit after each task: `p1: <what>`.

## Task 0: Contract gaps to fix with the team (write proposals, do not merge contract edits alone)

Day 1 left these gaps. Write each as a short proposal in `docs/contract-change-proposals.md` with the exact model or signature, then implement only the P1-side glue that does not depend on approval.

1. **`classify()` has no text to classify.** `classify(pairs: list[Candidate])` only receives IDs and a similarity number, so P4's model cannot see the proposition or criterion text. Proposal: add an `EvalPair` model (`prop_id, criterion_id, proposition_text, criterion_text, similarity`) and change the signature to `classify(pairs: list[EvalPair]) -> list[Classification]`. `pipeline/nodes.py` builds `EvalPair`s from candidates + propositions + rubric, so P3 and P4 stay decoupled.
2. **Untyped signatures.** Propose concrete types: `embed_propositions(props) -> dict[str, list[float]]` (prop_id to vector) and `detect(cohort_embeddings: dict[str, dict[str, list[float]]]) -> CollusionReport` (doc_id to prop_id to vector).
3. **`CriterionResult` needs to explain itself.** Propose optional fields with defaults: `capped: bool = False`, `note: str = ""`, `source_classification_id: str | None = None`.
4. **`score()` signature.** Day 1 uses `score(classifications, rubric, verdicts=None)`. Propose making `verdicts` required, because a missing verdict must be treated as untrusted (see Task 3).
5. Make the stub for `annotate()` return a **valid one-page PDF** (generate it with PyMuPDF once and store it as a real fixture). The `%PDF-1.4 dummy` string will make P5's PDF viewer fail.

Ping the team in the PR description for each item. Until approved, keep the current signatures working.

## Task 1: Real authentication

Replace the hardcoded fake admin/token.

- Admin credentials from env (`ADMIN_EMAIL`, `ADMIN_PASSWORD_HASH`); hash with argon2 or bcrypt. Add `scripts/hash_password.py`.
- `POST /auth/login` returns a signed JWT (HS256, `JWT_SECRET` from env, expiry configurable).
- `get_current_user` dependency; **every route except `/health` and `/auth/login` requires a valid token**. Return 401 with the standard error format on missing, invalid or expired tokens.
- Tests: valid login, wrong password, expired token, tampered token, protected route without token.

## Task 2: Reliable pipeline execution

**Stage tracking**
- Wrap each LangGraph node in a decorator that (a) sets the job status to that stage before running, (b) writes a `job_events` row (`job_id, stage, started_at, finished_at, ok, error`) and (c) logs structured JSON with `job_id` and `stage`.
- Add a migration for `job_events`. Expose events in `GET /jobs/{id}` under `events`.
- Persist each stage's output as JSONB in `job_artifacts` (`job_id, stage, payload`). This is for debugging and for the collusion embeddings later. Never store raw PDF bytes in JSONB; store the file on a volume and keep the path.

**Retries and failure handling**
- Define exception classes in `core/errors.py`: `TransientError` (retry) and `PermanentError` (do not retry).
- Celery task: `autoretry_for=(TransientError,)`, max 3 retries, exponential backoff with jitter, `soft_time_limit` and `time_limit` from config, `acks_late=True`, `reject_on_worker_lost=True`.
- Idempotent: re-running a job must not create duplicate results or events for the same attempt. Use an upsert for `results`.
- **Dead-letter path:** after final failure, set status `FAILED`, save the error and traceback, and write a row to `failed_jobs`. Add `POST /jobs/{id}/retry` (auth required) to requeue a failed job.
- Status transitions must be valid (e.g. no `DONE` to `EXTRACTING`). Enforce in one function, `core/jobs.py::transition()`, and unit-test it.

**Demo script**
- Replace any `sleep` polling in `scripts/demo.sh` with a loop that polls `GET /jobs/{id}` until `DONE`, `FAILED` or `NEEDS_REVIEW`, with a timeout and a clear failure exit code.

## Task 3: The deterministic scorer (`scorer/`)

Implement `score(classifications, rubric, verdicts) -> ScoreResult` as a **pure function**: no I/O, no randomness, no clock, no global state. Put constants in `scorer/rules.py`, and document the rules in `scorer/README.md` and `docs/scoring-rules.md`.

**Rules (implement exactly; these are defaults the team can change in `rules.py`)**

1. **Trust filter (fail closed).** A classification counts only if a verdict exists for it with `trusted=True`. A classification with no verdict is treated as untrusted.
2. **One label per criterion.** Among trusted classifications for a criterion, pick the label with the highest credit under `rubric.credit_map`. Ties are broken by higher confidence, then by lexicographically smaller classification id. If there are no trusted classifications, the label is `NO_CREDIT`.
3. **Credit and marks.** `credit = credit_map[label]`, `marks = weight * credit`.
4. **DAG dependency cap.** Process criteria in topological order. If any prerequisite in `depends_on` ended as `NO_CREDIT` or `MISCONCEPTION`, then cap the dependent criterion's credit at `credit_map[PARTIAL_CREDIT]`, set `capped=True` and explain in `note`. The capping uses the prerequisite's **final** (already capped) credit.
5. **Needs review.** If any classification for a criterion is untrusted, mark that criterion's `trusted=False`. `ScoreResult.needs_review = True` if any criterion is untrusted. Untrusted items never add marks.
6. **Evidence.** `evidence_bboxes` = bboxes of the propositions behind the chosen classification (empty for NO_CREDIT with no evidence).
7. **Numbers.** Compute with `decimal.Decimal`, quantize to 2 decimal places (ROUND_HALF_UP), and convert at the boundary. `total = sum(marks)`, `max_total = sum(weights)`. Result must satisfy `0 <= total <= max_total`.
8. **Robustness.** Unknown criterion ids in classifications are ignored and reported in `note`. Duplicate classification ids raise `PermanentError`. A cyclic rubric raises `PermanentError` (the compiler should have caught it, but do not trust that).

**Tests (this is the most important test suite in the project)**
- Unit tests for each rule above, including: tie-breaking, dependency chain of 3, capped-then-capped-again, all untrusted, missing verdict, empty inputs, float drift (weights like 0.1 + 0.2).
- **Property tests with `hypothesis`**: shuffling the input lists never changes the output; `0 <= total <= max_total`; running twice gives identical output.
- **Audit test:** score once, store the exact inputs, load them from storage, score again, and assert byte-identical JSON output.

## Task 4: Store audit bundles and add a verify endpoint

- Add migration: `results.audit_bundle` (JSONB) holding `{rubric, classifications, verdicts, scorer_version}` at scoring time. Define `SCORER_VERSION` in `scorer/__init__.py`.
- The pipeline's score node saves the bundle together with the result.
- `POST /results/{doc_id}/verify` (auth required): reload the bundle, re-run `score()`, compare with the stored `ScoreResult`, and return `{match: bool, differences: [...]}`. Test it, including a tampered-result case that returns `match=false`.

## Task 5: Pipeline glue

In `pipeline/nodes.py`:
- Build `EvalPair`s (if Task 0.1 is approved; otherwise keep a clearly marked adapter) from candidates, propositions and rubric.
- Set `from_hidden_text` on propositions when any of their tokens has `is_hidden=True`, if the segmenter has not.
- After the audit node, if any verdict is untrusted, continue to scoring (the scorer handles it) and end with job status `NEEDS_REVIEW` instead of `DONE`.
- Store `embed_propositions` output in `job_artifacts` so the collusion endpoint can use it on Day 3.

## Task 6: Tests and CI

- Integration test: full pipeline on stubs reaches `DONE`; a variant where the audit stub returns an untrusted verdict reaches `NEEDS_REVIEW` with the right marks.
- Failure tests: a stage raising `TransientError` retries then succeeds; a stage raising `PermanentError` goes straight to `FAILED` and appears in `failed_jobs`.
- Add coverage reporting to CI with a minimum of 85% for `scorer/` and `core/`.

## Acceptance criteria (Day 2 done when)

- `make test` and `make lint` pass; CI is green.
- Login is real; unauthenticated calls return 401.
- `GET /jobs/{id}` shows per-stage events. Killing a stage with a transient error retries; a permanent error lands in `failed_jobs`, and `/jobs/{id}/retry` works.
- The scorer passes all unit, property and audit tests, and `POST /results/{doc_id}/verify` returns `match=true` on a fresh result.
- `docs/contract-change-proposals.md` lists items 0.1 to 0.5 and the team has been notified.

At the end, print: what changed, new commands or env vars, the scoring rules as implemented, and any assumptions.
