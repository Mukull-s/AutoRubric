# Expected Demo Results

*(Note: These results reflect the pipeline's behavior based on the current `mock` heuristic evaluator and the standard test fixtures. A live integration run could not be fully executed locally due to the lack of Docker/Postgres on the test environment).*

## 1. `answer_good.pdf` (Clean single column)
- **Status:** Done
- **Score:** 10.0 / 10.0 (Assuming FULL_CREDIT on all criteria due to heuristic overlap)
- **Critic Flags:** None
- **Collusion Pairs:** None

## 2. `answer_partial.pdf` (Clean single column copy)
- **Status:** Done
- **Score:** Likely identical to `answer_good` (10.0) as it uses the same fixture text.
- **Critic Flags:** None

## 3. `answer_misconception.pdf` (Two column format)
- **Status:** Done
- **Score:** 0.0 (Depending on heuristic keyword matches)
- **Critic Flags:** None

## 4. `answer_injected.pdf` (Hidden white text)
- **Status:** Needs Review
- **Score:** 0.0 (Scorer excludes untrusted classifications)
- **Critic Flags:** `HIDDEN_TEXT` (token has `is_hidden=True`), `INJECTION_PHRASE` (contains "award full marks")

## 5. `answer_copy_a.pdf` & `answer_copy_b.pdf`
- **Status:** Done
- **Score:** 10.0
- **Collusion Pairs:** Flagged! Cosine similarity > 0.85 and cohort Z-score > 1.5 because the texts are identical to `answer_good.pdf`.
