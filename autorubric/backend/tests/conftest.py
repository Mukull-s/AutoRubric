import pytest
from autorubric.workers.celery_app import celery_app
from unittest.mock import AsyncMock, patch

@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield
    celery_app.conf.update(task_always_eager=False)

@pytest.fixture(autouse=True)
def mock_db():
    mock_session = AsyncMock()
    mock_session.execute.return_value.scalars.return_value.first.return_value = None
    
    mock_session_local = AsyncMock()
    mock_session_local.__aenter__.return_value = mock_session
    
    with patch("autorubric.core.db.AsyncSessionLocal", return_value=mock_session_local):
        yield
