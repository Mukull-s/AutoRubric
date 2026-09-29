import os

class Config:
    DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/autorubric")
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    SECRET_KEY = os.environ.get("SECRET_KEY", "supersecret")
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@example.com")
    ADMIN_PASSWORD_HASH = os.environ.get("ADMIN_PASSWORD_HASH", "$2b$12$XnPs0wsVFTB9pj5EANy8wuW7NGlE2TyUPfqMsLotDLj7M6KBevWsi") # default 'admin'
    JWT_SECRET = os.environ.get("JWT_SECRET", "jwtsecret")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

config = Config()
