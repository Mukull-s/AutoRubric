from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, rubrics, submissions, jobs, results, cohort

app = FastAPI(title="AutoRubric API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rubrics.router, prefix="/rubrics", tags=["rubrics"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(cohort.router, prefix="/cohort", tags=["cohort"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}
