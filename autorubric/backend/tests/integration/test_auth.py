import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timedelta
import uuid

from autorubric.core.security import create_access_token, get_password_hash
from autorubric.core.db import User
from autorubric.api.main import app
from autorubric.core.config import config

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture
def mock_db_users():
    return {}

@pytest.fixture(autouse=True)
def mock_session_local(monkeypatch, mock_db_users):
    class MockResult:
        def __init__(self, obj):
            self.obj = obj
        def scalar_one_or_none(self):
            return self.obj

    class MockSession:
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
        async def execute(self, stmt):
            # Very basic mock for select(User).where(User.email == email)
            # Find the email in the stmt string
            stmt_str = str(stmt).lower()
            for email, user in mock_db_users.items():
                if email in stmt_str or email in str(stmt.compile().params):
                    return MockResult(user)
            return MockResult(None)
            
        def add(self, obj):
            if isinstance(obj, User):
                mock_db_users[obj.email] = obj
                
        async def commit(self): pass
        async def refresh(self, obj): pass

    monkeypatch.setattr("autorubric.api.routers.auth.AsyncSessionLocal", lambda: MockSession())
    monkeypatch.setattr("autorubric.api.deps.AsyncSessionLocal", lambda: MockSession())
    return MockSession

@pytest.fixture
def registered_user(mock_db_users):
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash=get_password_hash("Password123!"),
        full_name="Test User",
        role="teacher",
        is_active=True
    )
    mock_db_users[user.email] = user
    return user

@pytest.mark.asyncio
async def test_register_success(mock_db_users):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "StrongPassword123!",
            "full_name": "New User"
        })
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["role"] == "teacher"
        assert "password_hash" not in data["user"]
        
        # Passwords stored hashed (query the database)
        user = mock_db_users["newuser@example.com"]
        assert user.password_hash != "StrongPassword123!"

@pytest.mark.asyncio
async def test_register_duplicate_email(registered_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "email": "TEST@example.com", # different case
            "password": "AnotherPassword123!"
        })
        assert response.status_code == 409

@pytest.mark.asyncio
async def test_register_weak_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "email": "weak@example.com",
            "password": "password123"
        })
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_register_role_cannot_be_set():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/register", json={
            "email": "adminwannabe@example.com",
            "password": "StrongPassword123!",
            "role": "admin" # trying to set admin
        })
        assert response.status_code == 201
        assert response.json()["user"]["role"] == "teacher" # still teacher

@pytest.mark.asyncio
async def test_login_success(registered_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "username": "test@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
        assert registered_user.last_login_at is not None

@pytest.mark.asyncio
async def test_login_wrong_password(registered_user):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "username": "test@example.com",
            "password": "WrongPassword!"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_login_unknown_email():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "username": "nobody@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_login_inactive_user(registered_user):
    registered_user.is_active = False
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", json={
            "username": "test@example.com",
            "password": "Password123!"
        })
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_auth_me(registered_user):
    token = create_access_token({"sub": str(registered_user.id), "email": registered_user.email})
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
