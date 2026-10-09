import pytest
from httpx import AsyncClient
import os
from sqlalchemy import text
from autorubric.core.config import config
from autorubric.api.deps import get_current_user

@pytest.mark.asyncio
@pytest.mark.xfail(reason="P2 has not merged fixture PDFs yet")
async def test_e2e_clean_pdf(client: AsyncClient, db_session):
    pass # upload clean.pdf, wait for DONE, assert score

@pytest.mark.asyncio
@pytest.mark.xfail(reason="P2 has not merged fixture PDFs yet")
async def test_e2e_two_column_pdf(client: AsyncClient, db_session):
    pass # upload two_column.pdf, wait for DONE, assert score

@pytest.mark.asyncio
@pytest.mark.xfail(reason="P2 has not merged fixture PDFs yet")
async def test_e2e_hidden_text_pdf(client: AsyncClient, db_session):
    pass # upload hidden_text.pdf, wait for NEEDS_REVIEW, assert critic flag

@pytest.mark.asyncio
@pytest.mark.xfail(reason="P2 has not merged fixture PDFs yet")
async def test_e2e_table_pdf(client: AsyncClient, db_session):
    pass # upload table.pdf, wait for DONE, assert score
