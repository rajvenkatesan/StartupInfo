import pytest
from httpx import AsyncClient
from tests.conftest import register_and_login


async def _seed_job(client, headers) -> str:
    await client.post("/api/v1/companies",
                      json={"company_name": "anthropic"}, headers=headers)
    resp = await client.post("/api/v1/jobs", json={
        "company_name": "anthropic",
        "title": "Senior ML Engineer",
        "location": "San Francisco, CA",
        "job_type": "full_time",
    }, headers=headers)
    return resp.json()["job_id"]


@pytest.mark.asyncio
async def test_create_and_list_application(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    job_id = await _seed_job(client, headers)

    resp = await client.post("/api/v1/applications", json={
        "job_id": job_id,
        "company_name": "anthropic",
        "status": "applied",
        "applied_date": "2026-03-31",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.json()["status"] == "applied"

    list_resp = await client.get("/api/v1/applications", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_update_application_status(client: AsyncClient):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    job_id = await _seed_job(client, headers)

    app_resp = await client.post("/api/v1/applications", json={
        "job_id": job_id, "company_name": "anthropic", "status": "wishlist",
    }, headers=headers)
    app_id = app_resp.json()["application_id"]

    update = await client.put(f"/api/v1/applications/{app_id}",
                              json={"status": "interview", "notes": "Had a great call"},
                              headers=headers)
    assert update.status_code == 200
    assert update.json()["status"] == "interview"
    assert "great call" in update.json()["notes"]


@pytest.mark.asyncio
async def test_application_isolation_between_users(client: AsyncClient):
    """User A should not see User B's applications."""
    token_a = await register_and_login(client, "alice", "pass1")
    token_b = await register_and_login(client, "bob", "pass2")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    job_id = await _seed_job(client, headers_a)

    await client.post("/api/v1/applications",
                      json={"job_id": job_id, "company_name": "anthropic"},
                      headers=headers_a)

    resp_b = await client.get("/api/v1/applications", headers=headers_b)
    assert resp_b.json() == []
