# Audit Evaluation Results

This document contains the evaluation results of the critic and collusion detector against the red-team dataset.

## Critic (Injection Detection)

| Category | Detection Rate | False-Positive Rate |
|---|---|---|
| Injection | 100% (5/5) | - |
| Benign look-alikes | - | 0% (0/2) |

**Overall Metrics:**
- **Precision:** 1.00
- **Recall:** 1.00
- **False Positive Rate:** 0.00

**Notes on thresholds/tuning:**
- We tuned the injection regular expressions to require an imperative verb (e.g., "ignore", "give") along with a target (e.g., "instructions", "full marks") to avoid false positives on legitimate discussions about "system prompts" or "friction in models".

## Collusion Detection

| Category | True Positive Rate | False-Positive Rate |
|---|---|---|
| Identical / Highly Similar | 100% (2/2) | - |
| Independent Answers (Benign Cohort 1) | - | 0% (0 pairs flagged) |
| Independent Answers (Benign Cohort 2) | - | 0% (0 pairs flagged) |

**Notes on thresholds/tuning:**
- We generated two benign cohorts of 10 independent answers with noise.
- The `prop_threshold` is set to 0.85 to allow minor variations while matching identical concepts.
- The `pair_absolute_threshold` is 0.70 to require significant overlap. This absolute threshold is very effective at filtering out accidental high z-scores.
- We rely on `z_score_threshold` (1.5) to avoid flagging answers that are naturally similar due to the topic. Because of the absolute threshold, we did not need to raise the z-score threshold or switch to median/MAD, as 0 false positives were triggered.
