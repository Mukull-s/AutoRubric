import pytest
from httpx import AsyncClient, ASGITransport
from jose import jwt
from datetime import datetime, timedelta
from autorubric.core.config import config
import sys
from unittest.mock import AsyncMock, patch, MagicMock

import autorubric.core.db
# Mock AsyncSessionLocal before imports
class MockResult:
    def scalars(self): return self
    def first(self): return None

mock_session = AsyncMock()
mock_session.execute.return_value = MockResult()
mock_session_local = MagicMock()
mock_session_local.return_value.__aenter__.return_value = mock_session
sys.modules['autorubric.core.db'].AsyncSessionLocal = mock_session_local
autorubric.core.db.AsyncSessionLocal = mock_session_local

from autorubric.api.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_auth_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
        assert response.status_code == 200
        assert "access_token" in response.json()

@pytest.mark.asyncio
async def test_auth_wrong_password():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/auth/login", data={"username": "admin@example.com", "password": "wrong"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_protected_without_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/jobs/job-123")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_expired_token():
    expire = datetime.utcnow() - timedelta(minutes=1)
    to_encode = {"sub": "admin@example.com", "exp": expire}
    encoded_jwt = jwt.encode(to_encode, config.JWT_SECRET, algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/jobs/job-123", headers={"Authorization": f"Bearer {encoded_jwt}"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_tampered_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/jobs/job-123", headers={"Authorization": "Bearer fake.tampered.token"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_api_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Auth
        response = await ac.post("/auth/login", data={"username": "admin@example.com", "password": "admin"})
        assert response.status_code == 200
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create rubric
        rubric_data = {
            "id": "r_test",
            "title": "Test",
            "criteria": [{"id": "c1", "description": "Test", "weight": 1.0, "depends_on": []}],
            "credit_map": {"FULL_CREDIT": 1.0, "PARTIAL_CREDIT": 0.5, "NO_CREDIT": 0.0, "MISCONCEPTION": 0.0},
            "max_score": 1.0
        }
        response = await ac.post("/rubrics", json=rubric_data, headers=headers)
        assert response.status_code == 200
        
        # Submission
        files = {"file": ("dummy.pdf", b"%PDF-1.4\n%dummy", "application/pdf")}
        data = {"rubric_id": "r_test"}
        
        # We need to mock validate_pdf so it doesn't reject our dummy bytes
        from unittest.mock import patch
        with patch("autorubric.api.routers.submissions.validate_pdf"):
            response = await ac.post("/submissions", data=data, files=files, headers=headers)
            
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Poll
        response = await ac.get(f"/jobs/{job_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "DONE"
