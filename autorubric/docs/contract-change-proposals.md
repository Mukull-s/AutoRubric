# Contract Change Proposals

## P5

1. **The critic cannot see retrieval similarity.**
   The planned rule "high confidence but weak retrieval" needs the `Candidate.similarity` values, but `audit()` does not receive candidates.
   **Proposal:** Change signature to `audit(classifications, tokens, propositions, candidates: list[Candidate] | None = None)`. The argument is optional so nothing breaks.

2. **The dashboard cannot show proposition text.**
   `ScoreResult` and `CollusionReport` carry only ids and bboxes, but a reviewer needs to read the evidence and the shared sentences.
   **Proposal:** Expose `GET /results/{doc_id}/propositions` (id, text, page, bboxes, `from_hidden_text`) or embed text in the responses.

3. **Critic verdicts should reach the UI.**
   **Proposal:** Add `flags` (list of strings/objects) and `review_reasons` to the result response, per criterion.

4. **`CollusionReport.matching_props` format.**
   **Proposal:** Make each entry `"<prop_id_in_a>::<prop_id_in_b>"`.
