import pytest
from httpx import AsyncClient
from tests.conftest import register_and_login


@pytest.mark.asyncio
async def test_upsert_and_list_investments(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    # Create prerequisite records
    await client.post("/api/v1/companies",
                      json={"company_name": "anthropic", "company_type": "private"},
                      headers=headers)
    await client.post("/api/v1/investors",
                      json={"investor_name": "Google Ventures", "investor_type": "corporate"},
                      headers=headers)

    # Upsert an investment
    resp = await client.post("/api/v1/investments", json={
        "company_name": "anthropic",
        "investor_name": "Google Ventures",
        "series_name": "Series C",
        "amount_invested_usd": 300_000_000,
        "investor_role": "lead",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["series_name"] == "Series C"

    # List investments for company
    resp2 = await client.get("/api/v1/companies/anthropic/investments", headers=headers)
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1


@pytest.mark.asyncio
async def test_upsert_is_idempotent(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/companies",
                      json={"company_name": "openai"}, headers=headers)
    await client.post("/api/v1/investors",
                      json={"investor_name": "Sequoia Capital", "investor_type": "vc_firm"},
                      headers=headers)

    payload = {
        "company_name": "openai", "investor_name": "Sequoia Capital",
        "series_name": "Seed", "amount_invested_usd": -1,
    }
    await client.post("/api/v1/investments", json=payload, headers=headers)
    # second upsert with updated amount
    payload["amount_invested_usd"] = 10_000_000
    resp = await client.post("/api/v1/investments", json=payload, headers=headers)
    assert resp.status_code == 201

    # Should still be 1 row
    r = await client.get("/api/v1/companies/openai/investments", headers=headers)
    assert len(r.json()) == 1
    assert r.json()[0]["amount_invested_usd"] == 10_000_000
