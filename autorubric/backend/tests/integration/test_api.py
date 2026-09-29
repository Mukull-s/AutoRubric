import pytest
from httpx import AsyncClient, ASGITransport
from autorubric.api.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.asyncio
async def test_api_flow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Auth
        response = await ac.post("/auth/login", data={"username": "admin", "password": "admin"})
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
        # We need celery task in eager mode to process it right away, but we just mocked Celery
        response = await ac.post("/submissions", data=data, files=files, headers=headers)
        assert response.status_code == 200
        job_id = response.json()["job_id"]
        
        # Poll
        response = await ac.get(f"/jobs/{job_id}", headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "DONE"
