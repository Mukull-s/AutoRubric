from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, JSON, DateTime, Boolean, Enum
from sqlalchemy.dialects.postgresql import JSONB
from autorubric.contracts import JobStatus
import datetime

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
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True)
    submission_id = Column(String, nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.QUEUED)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Result(Base):
    __tablename__ = "results"
    doc_id = Column(String, primary_key=True)
    rubric_id = Column(String, nullable=False)
    data = Column(JSONB, nullable=False)
    total_score = Column(Float, nullable=False)
    needs_review = Column(Boolean, default=False)
