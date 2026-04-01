"""
Tests for the companies API.
Fixture companies: ChatGPT (OpenAI), Eridu, Anthropic — as per spec.
"""
import pytest
from httpx import AsyncClient
from tests.conftest import register_and_login

COMPANIES = [
    {"company_name": "openai", "description": "AI research company behind ChatGPT",
     "company_type": "private", "location": "San Francisco, CA"},
    {"company_name": "eridu", "description": "Web3 infrastructure startup",
     "company_type": "private", "location": "Remote"},
    {"company_name": "anthropic", "description": "AI safety company",
     "company_type": "private", "location": "San Francisco, CA",
     "founders": ["Dario Amodei", "Daniela Amodei"]},
]


@pytest.mark.asyncio
async def test_create_company(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/companies", json=COMPANIES[2], headers=headers)
    assert resp.status_code == 201
    assert resp.json()["company_name"] == "anthropic"
    assert resp.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_create_duplicate_company(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/companies", json=COMPANIES[0], headers=headers)
    resp = await client.post("/api/v1/companies", json=COMPANIES[0], headers=headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_list_companies(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    for c in COMPANIES:
        await client.post("/api/v1/companies", json=c, headers=headers)
    resp = await client.get("/api/v1/companies", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_get_company_not_found(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.get("/api/v1/companies/unknownco", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_company(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    await client.post("/api/v1/companies", json=COMPANIES[2], headers=headers)
    resp = await client.put("/api/v1/companies/anthropic",
                            json={"mission": "AI for the long-term benefit of humanity"},
                            headers=headers)
    assert resp.status_code == 200
    assert "long-term benefit" in resp.json()["mission"]


@pytest.mark.asyncio
async def test_discover_creates_stub(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    resp = await client.post("/api/v1/companies/eridu/discover", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "discovering"
