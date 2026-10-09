from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, JSON, DateTime, Boolean, Enum, Index, func
from sqlalchemy.dialects.postgresql import JSONB
from autorubric.contracts import JobStatus
import datetime
import uuid
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import JSONB, UUID

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from autorubric.core.config import config

class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36).
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                try:
                    return uuid.UUID(str(value))
                except Exception:
                    return value
            return value

from sqlalchemy.pool import NullPool

connect_args = {"check_same_thread": False} if "sqlite" in config.DATABASE_URL else {}
pool_kwargs = {"poolclass": NullPool} if "sqlite" not in config.DATABASE_URL else {}
engine = create_async_engine(config.DATABASE_URL, echo=False, connect_args=connect_args, **pool_kwargs)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()
JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")

class User(Base):
    __tablename__ = "users"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, default="teacher", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_users_email_lower", func.lower(email), unique=True),
    )

class RubricModel(Base):
    __tablename__ = "rubrics"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    data = Column(JSON_TYPE, nullable=False)

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
    payload = Column(JSON_TYPE, nullable=False)

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
    data = Column(JSON_TYPE, nullable=False)
    total_score = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
    audit_bundle = Column(JSON_TYPE, nullable=True)

class CollusionCache(Base):
    __tablename__ = "collusion_cache"
    cohort_id = Column(String, primary_key=True)
    doc_ids_hash = Column(String, nullable=False)
    report = Column(JSON_TYPE, nullable=False)
