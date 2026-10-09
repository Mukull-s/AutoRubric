from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from .routers import auth, rubrics, submissions, jobs, results, cohort
from autorubric.core.config import config
from sqlalchemy import text
from autorubric.core.db import AsyncSessionLocal, engine, Base
import redis.asyncio as redis
import os
from autorubric.evaluator import model_info

import json
from pathlib import Path
from autorubric.core.db import AsyncSessionLocal, engine, Base, User, RubricModel
from autorubric.core.security import get_password_hash
from sqlalchemy import select

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

    # Seed default admin and rubric if DB is empty
    try:
        async with AsyncSessionLocal() as session:
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com").lower()
            admin_pass = os.environ.get("ADMIN_PASS", os.environ.get("ADMIN_PASSWORD", "admin"))
            stmt = select(User).where(User.email == admin_email)
            existing_admin = (await session.execute(stmt)).scalar_one_or_none()
            if not existing_admin:
                admin_user = User(
                    email=admin_email,
                    password_hash=get_password_hash(admin_pass),
                    role="admin",
                    full_name="Default Administrator",
                    is_active=True
                )
                session.add(admin_user)
                await session.commit()
                logger.info(f"Default admin user seeded: {admin_email}")

            rubric_stmt = select(RubricModel)
            existing_rubric = (await session.execute(rubric_stmt)).scalars().first()
            if not existing_rubric:
                fixture_paths = [
                    Path(__file__).resolve().parents[4] / "backend" / "tests" / "fixtures" / "rubrics" / "rubric.json",
                    Path(__file__).resolve().parents[3] / "demo" / "rubric.json"
                ]
                for fp in fixture_paths:
                    if fp.exists():
                        with open(fp, encoding="utf-8") as f:
                            data = json.load(f)
                            model = RubricModel(id=data["id"], title=data.get("title", "Biology Basics"), data=data)
                            session.add(model)
                            await session.commit()
                            logger.info(f"Default rubric seeded into database: {data['id']}")
                            break
    except Exception as e:
        logger.warning(f"Database table seeding note: {e}")

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
]
if cors_origins_env:
    for o in cors_origins_env.split(","):
        if o.strip():
            allowed_origins.append(o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*(\.vercel\.app|\.onrender\.com)",
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
            
    return {
        "status": "ready",
        "provenance": {
            "evaluator": model_info(),
            "stage_modes": {
                "extraction": config.STAGE_EXTRACTION_MODE,
                "segmentation": config.STAGE_SEGMENTATION_MODE,
                "retrieval": config.STAGE_RETRIEVAL_MODE,
                "evaluation": config.STAGE_EVALUATION_MODE,
                "audit": config.STAGE_AUDIT_MODE,
                "annotation": config.STAGE_ANNOTATION_MODE,
            },
            "fixture_data_used": any(
                mode == "stub"
                for mode in (
                    config.STAGE_EXTRACTION_MODE,
                    config.STAGE_SEGMENTATION_MODE,
                    config.STAGE_RETRIEVAL_MODE,
                    config.STAGE_EVALUATION_MODE,
                    config.STAGE_AUDIT_MODE,
                    config.STAGE_ANNOTATION_MODE,
                )
            ),
        },
    }
