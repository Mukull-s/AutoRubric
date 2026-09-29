from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .routers import auth, rubrics, submissions, jobs, results, cohort
from autorubric.core.config import config
from sqlalchemy import text
from autorubric.core.db import AsyncSessionLocal
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Stage Modes - Extraction: {config.STAGE_EXTRACTION_MODE}, Segmentation: {config.STAGE_SEGMENTATION_MODE}")
    logger.info(f"Stage Modes - Retrieval: {config.STAGE_RETRIEVAL_MODE}, Evaluation: {config.STAGE_EVALUATION_MODE}")
    logger.info(f"Stage Modes - Audit: {config.STAGE_AUDIT_MODE}, Annotation: {config.STAGE_ANNOTATION_MODE}")
    logger.info(f"Evaluator Backend: {config.EVALUATOR_BACKEND}")
    yield

app = FastAPI(title="AutoRubric API", lifespan=lifespan)

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

@app.get("/health/ready")
async def health_ready():
    # Check Postgres
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        return {"status": "unhealthy", "reason": f"Postgres: {e}"}
    
    # Check Redis
    try:
        r = redis.from_url(config.REDIS_URL)
        await r.ping()
        await r.close()
    except Exception as e:
        return {"status": "unhealthy", "reason": f"Redis: {e}"}
        
    # Check model files
    if config.EVALUATOR_BACKEND != "mock":
        if not os.path.exists("/app/models") and not os.path.exists("../models"): # For local dev
            return {"status": "unhealthy", "reason": "Model files missing"}
            
    return {"status": "ready"}
