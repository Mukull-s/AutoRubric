# Report Promises vs. Actual Implementation

| Promised Feature | Implementation Status | Notes |
|---|---|---|
| Eight-stage pipeline | **Implemented** | LangGraph pipeline orchestrates extract, segment, retrieve, evaluate, audit, score, annotate. |
| QLoRA fine-tuned Mistral-7B | **Not done** | Dropped due to time constraints (listed as a risk cut). |
| Fine-tuned RoBERTa-large | **Partial** | Fine-tuning scripts & Colab notebook exist, but weights are not trained/checked in yet. |
| PaddleOCR for handwriting | **Not done** | Explicitly dropped as a risk cut; only typed/selectable PDFs are supported. |
| Visual bounding-box annotation | **Implemented** | PyMuPDF draws green/red rectangles onto the graded PDFs. |
| Adversarial critic | **Implemented** | Rule-based critic successfully flags hidden text and injection phrases with 0% FPR. |
| Collusion detection | **Implemented** | Uses proposition vector embeddings and Z-score baselines to flag near-duplicates. |
| Deterministic scorer | **Implemented** | Caps scores on missing dependencies; purely arithmetic scoring. |
| Next.js dashboard | **Implemented** | Full UI with MSW mock mode and real API integration. |
| pgvector retrieval | **Partial** | Code exists, but `sentence-transformers` uses cosine similarity via matrix dot products locally during tests. |
| SciEntsBank benchmark results | **Implemented** | Dataset is mapped 5-to-4; test lengths/bias invariance evaluated. |
| Human-grader agreement study | **Not done** | System evaluations were strictly programmatic (Recall@3, red-team limits); no live human study conducted. |
