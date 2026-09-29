# Shared Data Contracts

These are the shared data contracts for the AutoRubric system, defined as Pydantic models.

| Model | Fields |
|---|---|
| `Label` | `FULL_CREDIT`, `PARTIAL_CREDIT`, `NO_CREDIT`, `MISCONCEPTION` |
| `JobStatus` | `QUEUED`, `EXTRACTING`, `SEGMENTING`, `RETRIEVING`, `EVALUATING`, `AUDITING`, `SCORING`, `ANNOTATING`, `DONE`, `FAILED`, `NEEDS_REVIEW` |
| `BBox` | `x, y, w, h` (floats, PDF points, origin top-left), `page` (int) |
| `Token` | `id, text, page, bbox, block_id, is_hidden` |
| `Proposition` | `id, doc_id, text, token_ids, page, bboxes, from_hidden_text` |
| `Criterion` | `id, description, weight (>0), depends_on` |
| `CreditMap` | Maps `Label`s to floats: `FULL_CREDIT`, `PARTIAL_CREDIT`, `NO_CREDIT`, `MISCONCEPTION` |
| `Rubric` | `id, title, criteria, credit_map, max_score` |
| `Candidate` | `prop_id, criterion_id, similarity` |
| `Classification` | `id, prop_id, criterion_id, label, confidence (0..1)` |
| `CriticVerdict` | `classification_id, trusted, reason, flags` |
| `CriterionResult` | `criterion_id, label, credit, marks, evidence_bboxes, trusted` |
| `ScoreResult` | `doc_id, rubric_id, per_criterion, total, max_total, needs_review` |
| `CollusionReport` | `cohort_id, doc_pairs` (each pair has `a, b, similarity, matching_props`) |
