from fastapi import APIRouter, HTTPException, status, Request, Depends
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from autorubric.core.config import config
from autorubric.core.security import get_password_hash, verify_password, create_access_token
from autorubric.core.db import User
from autorubric.api.deps import get_db_session, get_current_user
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import redis.asyncio as redis

router = APIRouter()
logger = logging.getLogger(__name__)

COMMON_PASSWORDS = {"password123", "password1234", "qwertyuiop", "1234567890"}

redis_client = None
if config.REDIS_URL:
    redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)

async def check_rate_limit(request: Request, email: str = None):
    if not redis_client:
        return
    ip = request.client.host if request.client else "127.0.0.1"
    keys = [f"rl:ip:{ip}"]
    if email:
        keys.append(f"rl:email:{email}")
        
    try:
        for key in keys:
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, 900)
            if count > 10:
                ttl = await redis_client.ttl(key)
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts",
                    headers={"Retry-After": str(ttl if ttl > 0 else 900)}
                )
    except redis.RedisError as e:
        if config.APP_ENV == "dev":
            logger.warning(f"Redis unavailable for rate limiting: {e}")
        else:
            raise HTTPException(status_code=500, detail="Internal server error")
    except HTTPException:
        raise

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    registration_code: str | None = None

    @validator('password')
    def validate_password(cls, v, values):
        if len(v) < 10 or len(v) > 128:
            raise ValueError("Password must be between 10 and 128 characters")
        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("Password is too common")
        if 'email' in values and values['email'] and v.lower() == values['email'].lower():
            raise ValueError("Password cannot be the same as email")
        return v

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(request: Request, body: RegisterRequest, session: AsyncSession = Depends(get_db_session)):
    await check_rate_limit(request, body.email)
    
    if not config.ALLOW_REGISTRATION:
        raise HTTPException(status_code=403, detail="Registration is disabled")
    
    if config.REGISTRATION_CODE and body.registration_code != config.REGISTRATION_CODE:
        raise HTTPException(status_code=403, detail="Invalid registration code")

    email_lower = body.email.lower()
    
    stmt = select(User).where(User.email == email_lower)
    existing_user = (await session.execute(stmt)).scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")
        
    new_user = User(
        email=email_lower,
        password_hash=get_password_hash(body.password),
        full_name=body.full_name,
        role="teacher",
        is_active=True
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    
    token = create_access_token({
        "sub": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=str(new_user.id),
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, session: AsyncSession = Depends(get_db_session)):
    content_type = request.headers.get("content-type", "")
    username = None
    password = None

    if "application/json" in content_type:
        try:
            body = await request.json()
            username = body.get("username")
            password = body.get("password")
        except Exception:
            pass
    else:
        try:
            form = await request.form()
            username = form.get("username")
            password = form.get("password")
        except Exception:
            pass

    if not username or not password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    await check_rate_limit(request, username)

    email_lower = username.lower()
    stmt = select(User).where(User.email == email_lower)
    user = (await session.execute(stmt)).scalar_one_or_none()
    
    invalid_creds = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not user:
        verify_password(password, "$argon2id$v=19$m=65536,t=3,p=4$dummy$dummy")
        raise invalid_creds
        
    if not user.is_active:
        raise invalid_creds
        
    if not verify_password(password, user.password_hash):
        raise invalid_creds
        
    user.last_login_at = datetime.utcnow()
    await session.commit()
    
    token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    })
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            full_name=user.full_name,
            role=user.role
        )
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role
    )
