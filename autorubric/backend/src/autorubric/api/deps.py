from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from autorubric.core.security import decode_access_token
from autorubric.core.db import AsyncSessionLocal, User
from sqlalchemy import select
from typing import AsyncGenerator

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

async def get_db_session() -> AsyncGenerator:
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(token: str = Depends(oauth2_scheme), session = Depends(get_db_session)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user

