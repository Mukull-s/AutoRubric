# AutoRubric Demo Guide

This guide provides a step-by-step script for presenting AutoRubric. It is designed to be executable even if you haven't touched the code in days.

## 1. Prerequisites
- **Software:** Docker Desktop, Python 3.11+, Node.js 20+.
- **Ports:** 
  - Backend API: `8000`
  - Frontend UI: `3000`
  - Postgres: `5432`
  - Redis: `6379`
- **Login Credentials:**
  - Email: `admin@example.com`
  - Password: `admin`

## 2. One-Time Setup
*(Run these commands in separate terminal windows)*

**A. Start the Backend Infrastructure (Docker required):**
```bash
docker compose up -d --build
```
*Expected Output:* Containers starting for api, worker, redis, postgres.
*Time:* ~1-2 minutes.

**B. Download ML Evaluator Weights:**
Because we don't commit 1.5GB model weights to git, you need to download them once:
```bash
make models  # (Or run bash scripts/download_model.sh)
```
*Expected Output:* Weights downloaded to `ml/checkpoint`.
*Time:* ~1 minute.

**C. Start the Frontend:**
```bash
cd frontend
npm install
npx cross-env NEXT_PUBLIC_USE_MOCKS=false npm run dev
```
*Expected Output:* Next.js server running on `localhost:3000`.

## 3. Start / Stop / Reset
- **Start All:** `docker compose up -d` & `npm run dev`
- **Stop All:** `docker compose down` & Ctrl+C on frontend.
- **Reset Demo Data:** `docker compose down -v` (wipes the postgres database clean).

## 4. 10-Minute Demo Script

1. **The Problem (30s):** "Grading subjective answers at scale is hard. LLMs are biased and hallucinate grades. AutoRubric breaks student answers into atomic claims, maps them to rubric criteria, and evaluates them deterministically using a transparent 4-way label system."
2. **Open the Rubric:** Navigate to `http://localhost:3000`. Log in with `admin@example.com` / `admin`. Open the "Photosynthesis" rubric to show the criteria and dependencies (e.g., C3 depends on C2).
3. **Good Answer:** Click Upload. Select `demo/answer_good.pdf`. Show the job status progressing from queued to done. Open the result: show the FULL_CREDIT labels, the math adding up the score, and click to view the green annotated PDF boxes.
4. **Verify Score:** Point out that scores are derived via pure arithmetic (Weight × Label Credit). Click the "Verify score" button to show that the system can mathematically re-derive the score from the stored labels.
5. **Adversarial Injection:** Upload `demo/answer_injected.pdf`. Show that instead of hallucinating a 10/10, the Critic intercepts it. The status becomes "Needs Review" due to `HIDDEN_TEXT` and `INJECTION_PHRASE`.
6. **Collusion Detection:** Upload `demo/answer_copy_a.pdf` and `answer_copy_b.pdf`. Go to the Cohort view. Show the collusion heatmap flagging these two documents as near-duplicates with a Z-score > 1.5.
7. **Architecture:** Briefly show the 5-module split diagram (P1-P5).
8. **Results & Limitations:** Show the 96.67% retrieval accuracy. Honestly state limitations: currently relies on a lexical heuristic fallback if RoBERTa weights aren't downloaded, and complex coreference (across distant paragraphs) is hard.

## 5. Self-Test Checklist
If something feels broken, run these individual checks:
- **Backend Tests:** `pytest backend/tests` (**VERIFIED** - Passes 93/93)
- **Scorer Audit:** `pytest backend/tests/unit/scorer/test_audit.py` (**VERIFIED**)
- **Extraction (Hidden Text):** `pytest backend/tests/unit/extraction/test_extraction.py` (**VERIFIED**)
- **Collusion Eval:** `pytest backend/tests/unit/audit/test_collusion.py` (**VERIFIED**)
- **Frontend Mock Mode:** `cd frontend && npx cross-env NEXT_PUBLIC_USE_MOCKS=true npm run dev` (**VERIFIED** - Loads UI completely without Docker).

## 6. 2-Minute Code Tour
- **`backend/src/autorubric/scorer/`**: Show `score()`. Explain it's a pure function—no AI involved here.
- **`backend/src/autorubric/nlp/segmenter.py`**: Show how it preserves token IDs for bounding boxes.
- **`backend/src/autorubric/evaluator/classifier.py`**: Show the `_classify_mock` fallback vs `_classify_torch` PyTorch implementation.
- **`backend/src/autorubric/audit/critic.py`**: Show the hardcoded rules array that intercepts prompt injections.

## 7. Troubleshooting / Fallbacks
| Failure | Fix / Fallback |
|---|---|
| Cannot run Docker / API fails | Stop frontend, run `NEXT_PUBLIC_USE_MOCKS=true npm run dev` to demo the UI via MSW. |
| Model weights missing / too slow | Ensure `EVALUATOR_BACKEND=mock` in `.env` to use the lightning-fast heuristic fallback. |
| PyMuPDF fails to extract | Show the pre-captured screenshots in `docs/screenshots/`. |

## 8. Likely Teacher Questions
- **Q: How do you prevent length bias?**
  - **A:** We break essays into atomic propositions. Padding doesn't increase the score because we only evaluate single claims against the rubric.
- **Q: How does collusion detection avoid false positives?**
  - **A:** We use a cohort baseline (Z-score > 1.5) and a hard absolute threshold (> 0.70) on cosine similarity.
- **Q: What happens if the Critic crashes?**
  - **A:** AutoRubric fails closed. If a verdict is missing or throws an error, the submission is marked untrusted.
