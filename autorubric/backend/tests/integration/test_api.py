import pytest
from httpx import AsyncClient, ASGITransport
import uuid
from autorubric.core.security import create_access_token, get_password_hash
from autorubric.core.db import User
from autorubric.api.main import app
import sys
from unittest.mock import AsyncMock, patch, MagicMock
import autorubric.core.db

from autorubric.contracts import JobStatus

class MockJob:
    def __init__(self, job_id="job-test"):
        self.id = job_id
        self.submission_id = f"doc-{job_id}"
        self.status = JobStatus.DONE
        self.error = None
        self.created_at = None
        self.updated_at = None

# Mock AsyncSessionLocal before imports
class MockResult:
    def scalars(self): return self
    def first(self): return None
    def all(self): return []

mock_session = AsyncMock()
mock_session.execute.return_value = MockResult()
mock_session.get.side_effect = lambda model, ident: MockJob(ident)
mock_session_local = MagicMock()
mock_session_local.return_value.__aenter__.return_value = mock_session
sys.modules['autorubric.core.db'].AsyncSessionLocal = mock_session_local
autorubric.core.db.AsyncSessionLocal = mock_session_local

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.fixture(autouse=True)
def override_get_current_user(monkeypatch):
    async def mock_get_current_user():
        return User(id=uuid.uuid4(), email="test@example.com", role="admin")
    from autorubric.api.deps import get_current_user
    app.dependency_overrides[get_current_user] = mock_get_current_user
    monkeypatch.setattr("autorubric.core.db.AsyncSessionLocal", mock_session_local)
    monkeypatch.setattr("autorubric.api.routers.jobs.AsyncSessionLocal", mock_session_local)
    monkeypatch.setattr("autorubric.api.routers.submissions.AsyncSessionLocal", mock_session_local)
    monkeypatch.setattr("autorubric.api.routers.rubrics.AsyncSessionLocal", mock_session_local)
    monkeypatch.setattr("autorubric.api.routers.cohort.AsyncSessionLocal", mock_session_local)
    yield
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_api_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        token = "fake-token-because-we-mocked-deps"
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
