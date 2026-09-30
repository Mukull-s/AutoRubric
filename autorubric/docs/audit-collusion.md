# Collusion Detection Method

The collusion detector identifies suspiciously similar submissions within a cohort. It uses a purely mathematical approach over the embeddings of extracted propositions, without additional LLM calls.

## Steps

1. **L2 Normalization**: All proposition vectors for a document are L2-normalized.
2. **Greedy Matching**: For each pair of documents in a cohort, we compute a cosine similarity matrix between all their propositions. We greedily match the most similar propositions above `prop_threshold` (default 0.85). Each proposition can only match once.
3. **Similarity Score Calculation**: 
   The pair's overall similarity is calculated as an unweighted average of two components:
   - *Match fraction*: The number of matched propositions divided by the number of propositions in the shorter document.
   - *Mean matched similarity*: The average similarity of the matched propositions.
4. **Cohort Baseline and Thresholding**:
   - We check if the pair's similarity exceeds `pair_absolute_threshold` (default 0.70). If not, we ignore it.
   - If the cohort contains at least 5 documents, we calculate the mean and standard deviation of all pair similarities in the cohort. A pair is flagged only if its Z-score is above `z_score_threshold` (default 1.5), meaning it stands out from the natural similarity of answers to the same questions.
   - For small cohorts (< 5 documents), the Z-score check is skipped, and any pair above the absolute threshold is flagged.

## Limitations

- **Topic Convergence**: Legitimate, correct answers often share vocabulary and concepts, meaning their embeddings might be naturally similar. The Z-score check mitigates this, but short answers with low variance across the cohort can still be falsely flagged.
- **Paraphrasing**: Advanced paraphrasing or structural changes might yield proposition embeddings below the threshold, bypassing detection.
- **Intent**: The detector cannot prove intent (e.g. who copied from whom, or if it was an innocent coincidence), it only flags similarities for human review.
