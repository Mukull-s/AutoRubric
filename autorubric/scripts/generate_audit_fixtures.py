import json
from autorubric.contracts import Classification, Token, Proposition, BBox
from pathlib import Path

# Classifications
cl1 = Classification(id="cl1", prop_id="p1", criterion_id="c1", label="FULL_CREDIT", confidence=0.9, reasoning="Good")
cl2 = Classification(id="cl2", prop_id="p2", criterion_id="c1", label="FULL_CREDIT", confidence=0.95, reasoning="Good")

# Tokens
t1 = Token(id="t1", text="Normal", page=1, bbox=BBox(x=0, y=0, w=10, h=10, page=1), block_id="b1", is_hidden=False)
t2 = Token(id="t2", text="Hidden", page=1, bbox=BBox(x=0, y=0, w=10, h=10, page=1), block_id="b1", is_hidden=True)

# Propositions
p1 = Proposition(id="p1", doc_id="doc1", page=1, bboxes=[BBox(x=0, y=0, w=10, h=10, page=1)], text="Normal text", token_ids=["t1"])
p2 = Proposition(id="p2", doc_id="doc1", page=1, bboxes=[BBox(x=0, y=0, w=10, h=10, page=1)], text="Hidden text", token_ids=["t2"])

base_dir = Path("backend/tests/fixtures/audit")
base_dir.mkdir(parents=True, exist_ok=True)

with open(base_dir / "input_classifications.json", "w") as f:
    json.dump([cl1.model_dump(), cl2.model_dump()], f, indent=4)

with open(base_dir / "input_tokens.json", "w") as f:
    json.dump([t1.model_dump(), t2.model_dump()], f, indent=4)

with open(base_dir / "input_propositions.json", "w") as f:
    json.dump([p1.model_dump(), p2.model_dump()], f, indent=4)

# Embeddings: doc1 and doc2 are identical. doc3 and doc4 are different.
doc1 = {"p1": [1.0, 0.0, 0.0]}
doc2 = {"p2": [1.0, 0.0, 0.0]}
doc3 = {"p3": [0.0, 1.0, 0.0]}
doc4 = {"p4": [0.0, 0.0, 1.0]}
embeddings = {"doc1": doc1, "doc2": doc2, "doc3": doc3, "doc4": doc4}
with open(base_dir / "cohort_embeddings.json", "w") as f:
    json.dump(embeddings, f, indent=4)
