# Contract Change Proposals

@P1 @P2 @P3 @P4 @P5

Here are the contract changes needed based on Day 1 learnings. I've implemented the P1-side glue for these changes, but they should not be merged until everyone approves.

### 1. `classify()` has no text to classify
Currently, `classify(pairs: list[Candidate])` only receives IDs and a similarity number. P4's model cannot see the proposition or criterion text.
**Proposal:** Add an `EvalPair` model and change the signature to `classify(pairs: list[EvalPair]) -> list[Classification]`.
```python
class EvalPair(BaseModel):
    prop_id: str
    criterion_id: str
    proposition_text: str
    criterion_text: str
    similarity: float
```
`pipeline/nodes.py` builds `EvalPair`s from candidates + propositions + rubric, so P3 and P4 stay decoupled.

### 2. Untyped signatures in Retrieval and Audit
Currently, `embed_propositions` and `detect` lack concrete types.
**Proposal:** Update signatures:
- `embed_propositions(props: list[Proposition]) -> dict[str, list[float]]` (maps `prop_id` to vector).
- `detect(cohort_embeddings: dict[str, dict[str, list[float]]]) -> CollusionReport` (maps `doc_id` to `prop_id` to vector).

### 3. `CriterionResult` needs to explain itself
Currently, `CriterionResult` does not explain capping or provide details on its score.
**Proposal:** Add optional fields with defaults:
```python
capped: bool = False
note: str = ""
source_classification_id: str | None = None
```

### 4. `score()` signature
Currently, `score(classifications, rubric, verdicts=None)` has an optional `verdicts` argument.
**Proposal:** Make `verdicts` required: `score(classifications: list[Classification], rubric: Rubric, verdicts: list[CriticVerdict]) -> ScoreResult`. A missing verdict must be treated as untrusted, so the scorer needs to explicitly receive them.

### 5. `annotate()` stub PDF validity
Currently, the stub for `annotate()` returns a dummy string (`%PDF-1.4 dummy`) which fails valid PDF parsing.
**Proposal:** Replace the dummy bytes with a valid one-page PDF generated with PyMuPDF to be used as a real fixture.
