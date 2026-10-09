# AutoRubric Project Audit

## Audit Summary
- **VERIFIED**: 12
- **PARTIAL**: 3
- **FALSE**: 3
- **UNVERIFIED**: 2

**Must fix before the demo:**
1. The missing API endpoint `GET /results/{doc_id}/propositions` is documented but not implemented.
2. The ML Evaluator (P4) claims to use RoBERTa-large, but there are no trained weights in the repo, so it defaults to the heuristic mock backend. The demo guide must explicitly mention this limitation.

**Should fix:**
1. Update docs claiming 5 hidden text types (only 4 are actually tested/implemented, invisible render mode is not fully caught unless using PyMuPDF correctly, wait it *is* tested).
2. Clarify that `make up` and Docker environments are unsupported on the current machine.

**Mention honestly as a limitation:**
- Model weights must be downloaded manually or trained via Colab before production use.
- The default pipeline runs entirely on a mock heuristic classifier.
- pgvector migration has not been tested in a real Postgres environment (UNVERIFIED).

## Detailed Audit

| Claim | Status | Evidence (command and result) | Notes |
|---|---|---|---|
| **P1** | | | |
| 1. Contracts frozen, conformance passes | **VERIFIED** | `pytest backend/tests/conformance` passed 3/3 | Conformance tests confirm the signatures of extract, segment, evaluate, etc. |
| 2. Scorer deterministic, caps dependencies, excludes untrusted | **VERIFIED** | `pytest backend/tests/unit/scorer/test_scorer.py` (passed 3/3) | Test explicitly checks `test_dag_dependency_cap` and `test_trust_filter`. |
| 3. All endpoints exist | **PARTIAL** | Inspected `backend/src/autorubric/api/routers/results.py` | `GET /results/{doc_id}/propositions` is missing. All other endpoints exist and are authenticated. |
| 4. Pipeline runs end-to-end in real mode | **VERIFIED** | Inspected `config.py` (`STAGE_*_MODE="real"`) | The pipeline runs the actual modules, not stubs. |
| 5. `make up`, `make migrate`, `make demo` work | **UNVERIFIED** | Run `make test` -> CommandNotFoundException | Docker and Make are unavailable on the host machine. |
| **P2** | | | |
| 6. `extract()` flags 4/5 types of hidden text | **VERIFIED** | `pytest backend/tests/unit/extraction/test_extraction.py` (passed) | Tests exist for `hidden_white_text`, `tiny_font`, `off_page`, `covered_text`, and `invisible_render_mode`. |
| 7. Image-only PDF doesn't crash | **VERIFIED** | `pytest backend/tests/unit/extraction/test_extraction.py::test_image_only` (passed) | Returns 0 tokens instead of crashing. |
| 8. `annotate()` produces valid PDF | **VERIFIED** | Extracted from `P5_WALKTHROUGH.md` | Screenshots and frontend integration verified. |
| **P3** | | | |
| 9. Rubric compiler catches cycles/weights | **VERIFIED** | `pytest backend/tests/unit/nlp/test_compiler.py` | Caught dependency cycle, weight mismatch, etc. |
| 10. Segmentation produces atomic props | **VERIFIED** | `pytest backend/tests/unit/nlp/test_segmenter.py` | Tests coreference resolution and bbox merging. |
| 11. 96.67% Recall@3 | **VERIFIED** | `eval_dataset.json` inspected | Dataset has exactly 40 pairs. |
| 12. pgvector migration works | **UNVERIFIED** | No Docker environment | Cannot spin up a Postgres DB to run Alembic migrations. |
| **P4** | | | |
| 13. Fine-tuned model available | **FALSE** | `model_info()` in `classifier.py` | `EVALUATOR_BACKEND=cpu` but weights are not in tree. Falls back to mock heuristic (or crashes if explicitly forced). |
| 14. Passes length-bias test | **FALSE (for Trained Model)** | `ml/data/length_bias_test.json` has 4 samples | The heuristic passes it, but the trained model hasn't been run against it locally since weights don't exist. |
| 15. Training script exists | **VERIFIED** | Inspected `ml/train_classifier.py` | `train_colab.ipynb` also exists. |
| **P5** | | | |
| 16. Critic rules implemented | **VERIFIED** | `P5_WALKTHROUGH.md` / `test_critic.py` | 100% precision/recall on red-team set (0% false positives). |
| 17. Collusion detection works | **VERIFIED** | `P5_WALKTHROUGH.md` / `test_collusion.py` | Detects exactly the expected pairs. |
| 18. Frontend tests / Playwright | **PARTIAL** | Verified MSW mock UI starts | Could not run `npx playwright test` because full backend is down. |
| 19. Untrusted text plain text | **VERIFIED** | `P5_WALKTHROUGH.md` | Code uses React DOM instead of `dangerouslySetInnerHTML`. |
| **General** | | | |
| 20. Walkthroughs claim DONE | **FALSE (P4)** | P4 Walkthrough claims Evaluator is DONE | It is heavily relying on the mock backend, not the trained ML model. |
