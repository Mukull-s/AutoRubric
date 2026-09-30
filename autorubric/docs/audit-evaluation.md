# Audit Evaluation Results

This document contains the evaluation results of the critic and collusion detector against the red-team dataset.

## Critic (Injection Detection)

| Category | Detection Rate | False-Positive Rate |
|---|---|---|
| Injection | 100% (5/5) | - |
| Benign look-alikes | - | 0% (0/2) |

**Notes on thresholds/tuning:**
- We tuned the injection regular expressions to require an imperative verb (e.g., "ignore", "give") along with a target (e.g., "instructions", "full marks") to avoid false positives on legitimate discussions about "system prompts" or "friction in models".

## Collusion Detection

| Category | True Positive Rate | False-Positive Rate |
|---|---|---|
| Identical / Highly Similar | 100% (2/2) | - |
| Independent Answers | - | 0% |

**Notes on thresholds/tuning:**
- The `prop_threshold` is set to 0.85 to allow minor variations while matching identical concepts.
- The `pair_absolute_threshold` is 0.70 to require significant overlap.
- We rely on `z_score_threshold` (1.5) to avoid flagging answers that are naturally similar due to the topic.
