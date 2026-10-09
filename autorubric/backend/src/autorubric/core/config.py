import os
import re
from pathlib import Path
from dotenv import load_dotenv

# Try multiple locations to find .env (backend/.env, autorubric/.env, cwd)
_current_file = Path(__file__).resolve()
_possible_env_paths = [
    _current_file.parents[3] / ".env",          # backend/.env
    _current_file.parents[4] / ".env",          # autorubric/.env
    Path.cwd() / ".env",                        # cwd/.env
    Path.cwd() / "backend" / ".env",            # cwd/backend/.env
]
for p in _possible_env_paths:
    if p.exists():
        load_dotenv(p, override=False)

def _normalize_db_url(url: str) -> str:
    url = url.strip()
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url

def _normalize_redis_url(url: str) -> str:
    url = url.strip()
    # Handle if user copied 'redis-cli --tls -u redis://...' from Upstash
    match = re.search(r"(rediss?://\S+)", url)
    if match:
        url = match.group(1)
    # Upstash requires TLS (rediss://)
    if "upstash.io" in url and url.startswith("redis://"):
        url = "rediss://" + url[len("redis://"):]
    return url

class Config:
    APP_ENV = os.environ.get("APP_ENV", "dev").lower()
    DATABASE_URL = _normalize_db_url(os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/autorubric"))
    REDIS_URL = _normalize_redis_url(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
    JWT_SECRET = os.environ.get("JWT_SECRET", "jwtsecret")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    ALLOW_REGISTRATION = os.environ.get("ALLOW_REGISTRATION", "true").lower() == "true"
    REGISTRATION_CODE = os.environ.get("REGISTRATION_CODE", None)
    
    STAGE_EXTRACTION_MODE = os.environ.get("STAGE_EXTRACTION_MODE", "real")
    STAGE_SEGMENTATION_MODE = os.environ.get("STAGE_SEGMENTATION_MODE", "real")
    STAGE_RETRIEVAL_MODE = os.environ.get("STAGE_RETRIEVAL_MODE", "real")
    STAGE_EVALUATION_MODE = os.environ.get("STAGE_EVALUATION_MODE", "real")
    STAGE_AUDIT_MODE = os.environ.get("STAGE_AUDIT_MODE", "real")
    STAGE_ANNOTATION_MODE = os.environ.get("STAGE_ANNOTATION_MODE", "real")
    
    EVALUATOR_BACKEND = os.environ.get("EVALUATOR_BACKEND", "mock").lower() # mock, cpu, gpu
    EVALUATOR_ALLOW_MOCK_FALLBACK = os.environ.get("EVALUATOR_ALLOW_MOCK_FALLBACK", "false").lower() == "true"
    ALLOW_MOCK_EVALUATOR = os.environ.get("ALLOW_MOCK_EVALUATOR", "true").lower() == "true"
    EVALUATOR_MODEL_PATH = os.environ.get("EVALUATOR_MODEL_PATH", "")
    UPLOADS_DIR = os.environ.get("UPLOADS_DIR", "/app/uploads")


config = Config()

if config.APP_ENV == "prod" and (not config.JWT_SECRET or config.JWT_SECRET == "jwtsecret"):
    import secrets
    import logging
    logging.getLogger(__name__).warning("JWT_SECRET unset or default in prod; auto-generating a secure random secret.")
    config.JWT_SECRET = secrets.token_urlsafe(48)

if config.EVALUATOR_BACKEND not in {"mock", "cpu", "gpu"}:
    raise ValueError(
        f"Unsupported EVALUATOR_BACKEND={config.EVALUATOR_BACKEND!r}; "
        "choose mock, cpu, or gpu."
    )

if config.APP_ENV == "prod" and config.EVALUATOR_BACKEND == "mock" and not config.ALLOW_MOCK_EVALUATOR:
    raise ValueError("Production cannot use the mock evaluator unless ALLOW_MOCK_EVALUATOR=true.")
