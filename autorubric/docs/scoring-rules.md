# Scoring Rules

1. **Trust filter (fail closed).** A classification counts only if a verdict exists for it with `trusted=True`. A classification with no verdict is treated as untrusted.
2. **One label per criterion.** Among trusted classifications for a criterion, pick the label with the highest credit under `rubric.credit_map`. Ties are broken by higher confidence, then by lexicographically smaller classification id. If there are no trusted classifications, the label is `NO_CREDIT`.
3. **Credit and marks.** `credit = credit_map[label]`, `marks = weight * credit`.
4. **DAG dependency cap.** Process criteria in topological order. If any prerequisite in `depends_on` ended as `NO_CREDIT` or `MISCONCEPTION`, then cap the dependent criterion's credit at `credit_map[PARTIAL_CREDIT]`, set `capped=True` and explain in `note`. The capping uses the prerequisite's **final** (already capped) credit.
5. **Needs review.** If any classification for a criterion is untrusted, mark that criterion's `trusted=False`. `ScoreResult.needs_review = True` if any criterion is untrusted. Untrusted items never add marks.
6. **Evidence.** `evidence_bboxes` = bboxes of the propositions behind the chosen classification (empty for NO_CREDIT with no evidence).
7. **Numbers.** Compute with `decimal.Decimal`, quantize to 2 decimal places (ROUND_HALF_UP), and convert at the boundary. `total = sum(marks)`, `max_total = sum(weights)`. Result must satisfy `0 <= total <= max_total`.
8. **Robustness.** Unknown criterion ids in classifications are ignored and reported in `note`. Duplicate classification ids raise `PermanentError`. A cyclic rubric raises `PermanentError`.
