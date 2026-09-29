# AutoRubric

AutoRubric is a multi-agent explainable rubric-grading system.

## Quick Start

```bash
cp .env.example .env
make up
make demo
```

## Structure
- `backend/`: FastAPI backend, Celery workers, ML pipeline.
- `ml/`: ML training scripts and notebooks.
- `frontend/`: Next.js frontend app.

## Branch and PR Rules
- Branch names: `feature/<module>-<task>`
- Merge small and often (at least twice a day).
- Contracts changes require approvals from all 5 owners.
- Ensure CI is green before merging.

## Module Owners
- **P1**: Platform, Orchestration & Scorer
- **P2**: Extraction & Annotation
- **P3**: NLP, Rubric & Retrieval
- **P4**: ML Evaluator
- **P5**: Frontend, Critic & Collusion
