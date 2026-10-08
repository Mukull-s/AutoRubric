from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .routers import auth, rubrics, submissions, jobs, results, cohort
from autorubric.core.config import config
from sqlalchemy import text
from autorubric.core.db import AsyncSessionLocal, engine, Base
import redis.asyncio as redis
import os

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables if they don't exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Database table auto-creation skipped or failed: {e}")

    logger.info(f"Stage Modes - Extraction: {config.STAGE_EXTRACTION_MODE}, Segmentation: {config.STAGE_SEGMENTATION_MODE}")
    logger.info(f"Stage Modes - Retrieval: {config.STAGE_RETRIEVAL_MODE}, Evaluation: {config.STAGE_EVALUATION_MODE}")
    logger.info(f"Stage Modes - Audit: {config.STAGE_AUDIT_MODE}, Annotation: {config.STAGE_ANNOTATION_MODE}")
    logger.info(f"Evaluator Backend: {config.EVALUATOR_BACKEND}")
    yield

app = FastAPI(title="AutoRubric API", lifespan=lifespan)

# Allow localhost, Vercel deployments, Render deployments, and custom domains
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "https://auto-rubric.vercel.app",
    "https://autorubric.vercel.app",
    "https://autorubric-backend-jbrg.onrender.com",
]
if cors_origins_env:
    for o in cors_origins_env.split(","):
        if o.strip() and o.strip() not in allowed_origins:
            allowed_origins.append(o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def cors_headers_middleware(request: Request, call_next):
    origin = request.headers.get("origin") or "*"
    if request.method == "OPTIONS":
        return Response(
            content="OK",
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
            },
        )
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(f"Unhandled error processing {request.method} {request.url.path}: {exc}", exc_info=True)
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "error": str(exc)},
        )

    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    origin = request.headers.get("origin") or "*"
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "error": str(exc)},
        headers={
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rubrics.router, prefix="/rubrics", tags=["rubrics"])
app.include_router(submissions.router, prefix="/submissions", tags=["submissions"])
app.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
app.include_router(results.router, prefix="/results", tags=["results"])
app.include_router(cohort.router, prefix="/cohort", tags=["cohort"])
app.include_router(cohort.router, prefix="/cohorts", tags=["cohorts"])



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
    if config.EVALUATOR_BACKEND not in ("mock", "stub"):
        allow_fallback = os.environ.get("EVALUATOR_ALLOW_MOCK_FALLBACK", "false").lower() == "true"
        if not allow_fallback and not os.path.exists("/app/models") and not os.path.exists("../models"):
            return {"status": "unhealthy", "reason": "Model files missing"}
            
    return {"status": "ready"}

