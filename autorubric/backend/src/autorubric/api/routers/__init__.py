from .auth import router as auth_router
from .rubrics import router as rubrics_router
from .submissions import router as submissions_router
from .jobs import router as jobs_router
from .results import router as results_router
from .cohort import router as cohort_router

__all__ = [
    "auth_router",
    "rubrics_router",
    "submissions_router",
    "jobs_router",
    "results_router",
    "cohort_router"
]
