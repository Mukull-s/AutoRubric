import pytest
from autorubric.workers.celery_app import celery_app

@pytest.fixture(autouse=True)
def celery_eager():
    celery_app.conf.update(task_always_eager=True)
    yield
    celery_app.conf.update(task_always_eager=False)
