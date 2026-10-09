# Evaluator Module

**Owner:** P4

## Public Functions
- `classify(pairs: list[EvalPair]) -> list[Classification]`

## Backends

`EVALUATOR_BACKEND=mock` is a deterministic heuristic baseline. It uses both the
student proposition and rubric criterion: token overlap determines full,
partial, or no credit, while negation and known subject swaps identify likely
misconceptions. It is not a trained model and is labelled as demo/heuristic
mode in result provenance.

`cpu` and `gpu` load the configured transformer checkpoint. Missing weights
raise an error unless `EVALUATOR_ALLOW_MOCK_FALLBACK=true` is explicitly set.

Every evaluation pair must include non-empty `proposition_text` and
`criterion_text`; similarity is retrieval metadata and never determines a
label by itself.
