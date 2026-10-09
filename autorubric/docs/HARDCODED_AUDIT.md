# Hardcoded and fallback audit

This audit records the paths that could make different submissions appear to
have identical results.

| Location | What it does | Claim verified? | Risk | Fix |
|---|---|---:|---|---|
| `backend/src/autorubric/evaluator/classifier.py` | Defaults to the deterministic `mock` evaluator when `EVALUATOR_BACKEND` is unset. | Yes | Different papers can receive similar heuristic labels; this is not the trained model. | Mock remains available for local demos but is labelled in provenance; production rejects it unless explicitly allowed. |
| `backend/src/autorubric/pipeline/nodes.py` and `workers/tasks.py` | Celery previously sent only IDs and similarity, dropping proposition and criterion text. | Yes | Worker classified by similarity thresholds instead of answer content. | Celery now sends and validates the complete `EvalPair`. Missing text raises an error. |
| `backend/src/autorubric/api/routers/submissions.py` | Previously replaced missing database rubrics with a fixture or a default rubric. | Yes | A selected rubric could be silently ignored. | Missing rubric returns 404; database failures return 503. |
| `backend/src/autorubric/evaluator/stub.py` | Returns fixture classifications when evaluation stub mode is selected. | Yes | Every input can receive the same fixture result. | Stub remains test-only/demo functionality and real result provenance exposes stub usage. |
| `frontend/src/mocks/handlers.ts` and `MSWProvider.tsx` | Returns fixed frontend data when `NEXT_PUBLIC_USE_MOCKS=true`. | Yes | The UI is not connected to the backend. | A permanent `MOCK DATA` banner is shown while mocks are active. |
| `backend/src/autorubric/api/routers/jobs.py` | Previously returned a fabricated `DONE` job when storage lookup failed. | Yes | Failed or missing jobs looked successful. | Missing jobs return 404 and storage failures return 503. |
| `backend/src/autorubric/api/routers/results.py` | Previously verified missing results against fixture score data and could return success-shaped output. | Yes | A verification could say “match” without a real result. | Verification requires the stored audit bundle and returns 404 otherwise. |

## After the fixes

- The worker and in-process evaluator both receive the same typed input fields.
- A missing rubric, job, result, or audit bundle is no longer converted into
  demo data or a successful status.
- Stored results include evaluator and stage-mode provenance.
- The frontend displays the evaluator backend and warns when heuristic or stub
  data was used.

The full Docker/Postgres/Redis stack was not run in this environment. The
targeted evaluator/conformance run passed 15 tests; one existing test setup
failed because `autorubric.core.db` was not imported before the test fixture
patched it.
