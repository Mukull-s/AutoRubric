from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, JSON, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from autorubric.contracts import JobStatus
import datetime

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from autorubric.core.config import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

class RubricModel(Base):
    __tablename__ = "rubrics"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    rubric_id = Column(String, nullable=False)
    cohort_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    submission_id = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class JobEvent(Base):
    __tablename__ = "job_events"
    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    ok = Column(Boolean, nullable=True)
    error = Column(String, nullable=True)

class JobArtifact(Base):
    __tablename__ = "job_artifacts"
    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    payload = Column(JSONB, nullable=False)

class FailedJob(Base):
    __tablename__ = "failed_jobs"
    id = Column(String, primary_key=True)
    job_id = Column(String, nullable=False)
    error = Column(String, nullable=False)
    traceback = Column(String, nullable=False)
    failed_at = Column(DateTime, default=datetime.datetime.utcnow)

class Result(Base):
    __tablename__ = "results"
    doc_id = Column(String, primary_key=True)
    rubric_id = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    total_score = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
    audit_bundle = Column(JSONB, nullable=True)

class CollusionCache(Base):
    __tablename__ = "collusion_cache"
    cohort_id = Column(String, primary_key=True)
    doc_ids_hash = Column(String, nullable=False)
    report = Column(JSONB, nullable=False)
