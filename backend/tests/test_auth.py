import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "username": "raj",
        "email": "raj@example.com",
        "password": "securepass",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "raj"
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    payload = {"username": "raj", "email": "raj@example.com", "password": "pass"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "raj", "email": "raj@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "raj", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "username": "raj", "email": "raj@example.com", "password": "pass123"
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "raj", "password": "wrong"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403  # no token


@pytest.mark.asyncio
async def test_me_with_token(client: AsyncClient):
    from tests.conftest import register_and_login
    token = await register_and_login(client)
    resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "testuser"
