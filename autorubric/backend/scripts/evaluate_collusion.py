import sys
import os
import json

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("sentence-transformers not installed. Installing...")
    os.system("pip install sentence-transformers")
    from sentence_transformers import SentenceTransformer

sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))
from autorubric.audit.collusion import detect, CollusionConfig

def run_evaluation():
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Synthetic Biology/CS answers
    docs = {
        "doc_benign_1": [
            "Photosynthesis is the process by which plants use sunlight to synthesize foods from carbon dioxide and water.",
            "The mitochondria is the powerhouse of the cell."
        ],
        "doc_benign_2": [
            "Cellular respiration involves glycolysis, the Krebs cycle, and the electron transport chain.",
            "Plants absorb light energy using chlorophyll in their chloroplasts."
        ],
        "doc_benign_3": [
            "In computer science, a stack is a LIFO data structure.",
            "A queue operates on a FIFO basis, where the first element added is the first one to be removed."
        ],
        "doc_colluder_1": [
            "A stack is a Last-In-First-Out data structure used in programming.",
            "The time complexity of binary search is O(log n)."
        ],
        "doc_colluder_2": [
            "A stack is a Last In First Out (LIFO) data structure in computer science.",
            "Binary search has an O(log n) time complexity."
        ],
        "doc_colluder_3": [
            "A stack is a LIFO data structure used in programming.",
            "The time complexity of binary search is O(log n)."
        ]
    }
    
    # Encode
    cohort_embeddings = {}
    for doc_id, props in docs.items():
        embeddings = model.encode(props)
        cohort_embeddings[doc_id] = {f"p{i}": v.tolist() for i, v in enumerate(embeddings)}
        
    config = CollusionConfig(prop_threshold=0.85, pair_absolute_threshold=0.70, z_score_threshold=1.0)
    report = detect(cohort_embeddings, config)
    
    print(f"Found {len(report.doc_pairs)} suspicious pairs.")
    for p in report.doc_pairs:
        print(f"Pair: {p.a} - {p.b} | Similarity: {p.similarity:.3f} | Matches: {p.matching_props}")
        
if __name__ == "__main__":
    run_evaluation()
