# AutoRubric: 5-Module Split (4-Day Plan)

Read `PROJECT_CONTEXT.md` first. Each person owns one module and one set of folders. Modules connect only through `contracts/` and one public function each, so nobody edits another person's code.

| # | Module | Folders owned | Public function(s) |
|---|---|---|---|
| P1 | Platform, Orchestration & Scorer | `platform/`, `scorer/`, `docker-compose.yml`, `.github/` | `score(classifications, rubric) -> ScoreResult`, REST API, pipeline graph |
| P2 | Extraction & Annotation | `extraction/`, `annotation/` | `extract(pdf_bytes) -> list[Token]`, `annotate(pdf_bytes, ScoreResult) -> bytes` |
| P3 | NLP, Rubric & Retrieval | `nlp/`, `retrieval/` | `compile_rubric(json) -> Rubric`, `segment(tokens) -> list[Proposition]`, `match(props, rubric) -> list[Candidate]`, `embed_propositions(props)` |
| P4 | ML Evaluator | `ml/`, `evaluator/` | `classify(pairs) -> list[Classification]` |
| P5 | Frontend, Critic & Collusion | `frontend/`, `audit/` | `audit(...) -> list[CriticVerdict]`, `detect(cohort_embeddings) -> CollusionReport` |

---

## Day-by-day overview

| Day | Goal | Checkpoint at end of day |
|---|---|---|
| **1** | Contracts frozen, repo + Docker up, stubs and fixtures for every module, each person's standalone skeleton | Stub pipeline runs end to end on fixture data |
| **2** | Each module works standalone on real logic | Every public function passes its own tests on fixtures |
| **3** | Replace stubs with real modules, frontend on real API, critic + annotation working | Real typed PDF goes upload -> score -> annotated PDF |
| **4** | Bug fixes, evaluation numbers, collusion demo, README, report/demo | Frozen `main`, demo rehearsed |

Rule of the 4 days: **at the end of each day, merge to `main` and run the stub or real pipeline together for 15 minutes.** If something is late, ship the simpler version and move on.

---

## Day 1, first 2 hours: everyone together

1. **P1** creates the repo, branch protection and the `contracts/` folder.
2. All 5 write and agree on the Pydantic models listed in `PROJECT_CONTEXT.md` section 6, plus the credit map `g`.
3. Each person commits their own **fixtures** in `tests/fixtures/`: sample input and expected output JSON for their public function.
4. Merge `contracts/` to `main`. From now on, changes need all 5 approvals.

After this, everyone works alone in their own folders.

---

## P1: Platform, Orchestration & Scorer

**Goal:** the skeleton that runs everything, plus the deterministic scorer.

**Day 1**
- Monorepo, `docker-compose` (FastAPI, Redis, Postgres+pgvector, Celery worker), `.env.example`, CODEOWNERS, PR template, GitHub Actions (lint + pytest).
- FastAPI endpoints (stubbed): `POST /rubrics`, `POST /submissions`, `GET /jobs/{id}`, `GET /results/{doc_id}`, `GET /cohort/{id}/collusion`.
- **Publish an OpenAPI/JSON example for each endpoint by mid-day** so P5 can build the frontend mock.
- LangGraph pipeline with **stub nodes** returning fixture data for every stage, so the whole flow runs end to end by end of day.

**Day 2**
- Postgres schema + Alembic migration: users, jobs, submissions, rubrics, results. (P3 adds vector tables in their own migration file.)
- Celery task per stage with retries, timeouts, and status updates after each stage (`QUEUED ... DONE/FAILED`).
- **Scorer:** `Score = sum(w_i * g(label_i))`. Pure function, no randomness. Respect DAG dependencies (if a prerequisite criterion gets NO_CREDIT, cap the dependent one; document the rule). Handle untrusted verdicts: mark as "needs review" and exclude or hold, as agreed with P5.
- Scorer tests: edge cases plus an **audit test** that re-derives the score from stored labels and gets the identical number.
- Simple JWT auth (a single hard-coded admin user is fine for a demo).

**Day 3**
- Swap each stub node for the real module as it lands on `main` (P2, P3, P4, P5 tell you when).
- Store results and evidence bboxes in DB; serve annotated PDF via `GET /results/{doc_id}/pdf`.
- Integration tests using fixture PDFs.

**Day 4**
- Fix pipeline bugs, error handling for failed jobs, demo script (`make demo`), README run instructions, final Docker check on a clean machine.

**Done when:** `docker compose up` then upload a PDF and rubric -> get a score and annotated PDF, and the audit test passes.

---

## P2: Extraction & Annotation

**Goal:** PDF -> positioned tokens, and later scores -> highlighted PDF.

**Day 1**
- `extract()` stub returning fixture tokens.
- Build the **fixture PDF set** (min. 4): clean single column, two column, one with **hidden white text** containing an injection phrase, one with a table. Commit them with expected token JSON. Everyone else depends on these, so push them early.
- Basic PyMuPDF word extraction (`page.get_text("words")`) into `Token` objects.

**Day 2**
- Full `extract()` for typed PDFs: word-level bboxes in one consistent coordinate system, multi-page, `block_id` for paragraph grouping.
- **Hidden-text detection:** set `is_hidden=True` for white or near-white text, font size below a threshold, off-page positions, and text overlapped by shapes. Test on the hidden-text fixture.
- Helper `bboxes_for(token_ids) -> list[bbox]` (P3 and P1 will use it).
- Start `annotate()`: draw rectangles on a PDF with PyMuPDF from a list of bboxes.

**Day 3**
- Finish `annotate(pdf_bytes, ScoreResult)`: green boxes for credit evidence, red for misconceptions, a margin note per box (criterion, label, marks), and a summary page at the end.
- PaddleOCR fallback for image-only pages (only if time; else document it as a limitation).
- Merge `extract()` to `main` early on Day 2 evening so P3 can use real tokens.

**Day 4**
- Fix bbox alignment issues on odd PDFs, test on 2-3 real answer PDFs, screenshots of annotated output for the report.

**Done when:** a typed PDF returns correct tokens with bboxes, hidden text is flagged, and a `ScoreResult` produces a readable highlighted PDF.

---

## P3: NLP, Rubric & Retrieval

**Goal:** tokens -> atomic propositions -> candidate rubric matches.

**Day 1**
- Rubric JSON schema doc + a sample rubric with dependencies in `tests/fixtures/`.
- Stubs for `compile_rubric`, `segment`, `match`, `embed_propositions`.
- Install spaCy model and coreference component; confirm they run on a laptop.

**Day 2**
- **Rubric compiler:** validate JSON, build a DAG with `networkx`, detect cycles, missing ids and bad weights, produce topological order, return `Rubric`.
- **Segmentation:** `segment(tokens)`. Sentence split, break compound sentences into atomic claims, resolve pronouns via coreference, keep `token_ids` and bboxes on each `Proposition`. Skip tokens where `is_hidden=True`? **No: keep them and keep the flag** so P5's critic can see them; mark the proposition as coming from hidden text.
- **Embeddings + pgvector:** embed rubric criteria with a small sentence-transformer (CPU), store in pgvector with an index, own migration file.

**Day 3**
- `match()`: top-k cosine retrieval per proposition, similarity threshold, return `Candidate` list. Tune k and threshold on 20-30 hand-labelled pairs.
- `embed_propositions()` for P5's collusion detector.
- Retrieval recall@k on the labelled set.

**Day 4**
- Fix edge cases (very short answers, lists, bullets), write up retrieval numbers for the report.

**Done when:** a token list + rubric returns clean propositions with correct bboxes and sensible top-k candidate criteria, and recall@k is measured.

---

## P4: ML Evaluator

**Goal:** `classify(proposition, criterion) -> label + confidence`.

**Day 1 (start training early, it is the longest job)**
- Download SemEval-2013 SciEntsBank. Map its labels to the 4-way taxonomy and **write the mapping down** in `ml/LABEL_MAPPING.md`.
- Create train/val/test splits. Check class balance.
- `classify()` stub returning fixture labels **plus a mock evaluator** (random or keyword-based) so the pipeline can run with no GPU.
- Colab notebook set up and tested with a tiny run.

**Day 2**
- **Primary model: RoBERTa-large** fine-tune (fast, safe on T4). Input format: `(criterion text, proposition text) -> label`. Log with TensorBoard or W&B.
- Add synthetic examples for weak classes (MISCONCEPTION, verbose-but-empty answers) if metrics show imbalance.
- Save the model to Hugging Face Hub or Drive. **Do not put weights in git**; add a `download_model.sh`.

**Day 3**
- `classify(batch)` serving wrapper: batching, confidence score (softmax probability), CPU-capable path so teammates can run it.
- Metrics: accuracy, macro-F1, confusion matrix, per-class results.
- **Length-bias test:** pad a correct/incorrect answer with filler and check whether labels change.
- Stretch: Mistral-7B QLoRA run if RoBERTa is done and time remains.

**Day 4**
- Final metrics report and model card, fix serving bugs, hand the exact model download instructions to P1.

**Done when:** `classify()` returns valid labels with confidence on the fixture inputs, metrics and the length-bias result are recorded, and a CPU fallback exists.

---

## P5: Frontend, Critic & Collusion

**Goal:** the user interface plus the two audit components.

**Day 1**
- Next.js app skeleton. Build against a **mock API** (MSW or static JSON) using P1's endpoint examples, so you never wait on the backend.
- Stubs for `audit()` and `detect()` with fixture outputs.
- Draft list of critic rules.

**Day 2**
- Pages: login, rubric upload/paste, PDF upload (multiple files), job status (polling), results page (per-criterion label, credit, total).
- **Critic** `audit(classifications, tokens, propositions)` rules:
  - proposition came from `is_hidden` text -> untrusted
  - instruction-like phrases ("ignore previous", "give full marks", "system prompt", etc.) -> untrusted
  - very high confidence but low retrieval similarity -> flag
  - label contradicts another label on the same criterion -> flag
  - Untrusted items get `trusted=False` with a reason; they go to "needs human review", not the score.

**Day 3**
- Connect the frontend to P1's real API. Embedded viewer for the annotated PDF. Show critic flags on the results page.
- **Collusion:** `detect(cohort_embeddings)`: per-student fingerprint (mean of proposition embeddings), pairwise cosine matrix, threshold, list matching propositions. Uses P3's `embed_propositions()`.
- Build the red-team set: 3-4 PDFs with injections and 2-3 near-duplicate submissions.

**Day 4**
- Collusion heatmap in the dashboard (stretch), detection rates on the red-team set, UI polish, screenshots for the report.

**Done when:** a user can upload PDFs and a rubric in the UI, watch job status, see results and the annotated PDF, injected PDFs get flagged, and near-duplicates show up in the collusion report.

---

## Dependency map (who waits for whom)

| Needs | From | By when |
|---|---|---|
| Contracts | All | Day 1, hour 2 |
| Endpoint examples | P1 -> P5 | Day 1, midday |
| Fixture PDFs + token JSON | P2 -> P3, P5 | Day 1 evening |
| Real `extract()` | P2 -> P3 | Day 2 evening |
| Rubric sample + schema | P3 -> P1, P5 | Day 1 |
| `classify()` mock | P4 -> P1 | Day 1 |
| Trained model | P4 -> P1 | Day 3 morning |
| `embed_propositions()` | P3 -> P5 | Day 3 morning |
| Untrusted-verdict handling rule | P5 <-> P1 | Day 2 |
| `ScoreResult` with evidence bboxes | P1 -> P2 | Day 3 (fixture available from Day 1) |

Nobody is ever blocked because every dependency has a **fixture from Day 1**.

---

## GitHub workflow

**Repo layout**
```
autorubric/
├─ contracts/                  # shared, all approve changes
├─ platform/  scorer/          # P1
├─ extraction/  annotation/    # P2
├─ nlp/  retrieval/            # P3
├─ ml/  evaluator/             # P4
├─ frontend/  audit/           # P5
├─ tests/fixtures/             # sample PDFs, rubrics, expected JSON
├─ docs/
├─ docker-compose.yml  .github/  .env.example  README.md
```

**Rules (kept light for 4 days)**
- `main` is protected: PR required, **1 review**, CI green. Reviews should take minutes, not hours; review quickly.
- Branch names: `feature/<module>-<task>`, e.g. `feature/p3-segmenter`. Delete after merge.
- **Merge small and often** (at least twice a day). Long-lived branches cause conflicts.
- CODEOWNERS maps folders to owners, so a PR touching another person's folder asks them for review.
- Only P1 edits `docker-compose.yml`, `.github/`, root config. Others ask P1 via an issue or chat.
- Each module exposes only its public function(s); import nothing else from another module.
- Add dependencies to your own `requirements.txt` / `package.json` only; P1 merges them into the Docker build.
- `.gitignore`: model weights, `.env`, `node_modules`, `__pycache__`, big PDFs (use small fixtures only).
- Commit messages: `p3: add coreference to segmenter`.

**If two people need the same file:** stop, message, and let the owner make the change.

---

## Risk cuts (in this order if time is short)

1. Drop Mistral-7B; ship RoBERTa-large only.
2. Drop PaddleOCR; typed PDFs only.
3. Drop the collusion heatmap; keep the JSON/table report.
4. Simplify the annotation engine to boxes without margin notes.
5. Simplify the DAG rule to "prerequisite NO_CREDIT caps dependent at PARTIAL".

**Never cut:** contracts, deterministic scorer, hidden-text detection, the end-to-end demo.

---

## Workload balance

P1 and P4 are the heaviest. If someone falls behind on Day 2, the easiest handoffs are:
- **Scorer** from P1 to P3 (small and self-contained), or
- **Collusion detector** from P5 to P2.

Decide at the Day 2 checkpoint, not later.
