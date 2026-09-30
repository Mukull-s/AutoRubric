import numpy as np
from autorubric.audit.collusion import detect, CollusionConfig

def generate_benign_cohort(size, props_per_doc, dim=256, noise_level=0.3):
    # Benign cohorts tend to be similar because they answer the same question.
    # So we create a "base answer" and add noise to it.
    base_answer = np.random.randn(props_per_doc, dim)
    base_answer /= np.linalg.norm(base_answer, axis=1, keepdims=True)
    
    embeddings = {}
    for d in range(size):
        doc_props = {}
        for p in range(props_per_doc):
            # add noise
            noise = np.random.randn(dim) * noise_level
            vec = base_answer[p] + noise
            vec /= np.linalg.norm(vec)
            doc_props[f"p{p}"] = vec.tolist()
        embeddings[f"doc_{d}"] = doc_props
    return embeddings

def evaluate_cohort(embeddings):
    config = CollusionConfig(prop_threshold=0.85, pair_absolute_threshold=0.70, z_score_threshold=1.5)
    report = detect(embeddings, config)
    print(f"Total pairs flagged: {len(report.doc_pairs)}")
    
    # Let's run detect with very low thresholds to see the raw stats
    from autorubric.audit.collusion import detect as det
    r2 = det(embeddings, CollusionConfig(prop_threshold=0.0, pair_absolute_threshold=0.0, z_score_threshold=-10))
    sims = [p.similarity for p in r2.doc_pairs]
    if sims:
        print(f"Mean similarity: {np.mean(sims):.3f}, std: {np.std(sims):.3f}, max: {np.max(sims):.3f}")
    else:
        print("No pairs matched at all.")

print("Testing Benign Cohort 1 (size 10):")
c1 = generate_benign_cohort(10, 5, noise_level=0.4)
evaluate_cohort(c1)

print("\nTesting Benign Cohort 2 (size 10):")
c2 = generate_benign_cohort(10, 5, noise_level=0.4)
evaluate_cohort(c2)
