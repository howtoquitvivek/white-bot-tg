"""Tests for administrator authentication, sessions, rate limiting, and CSRF protection."""

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.security.password import hash_password


async def test_admin_login_success(test_client: httpx.AsyncClient, test_admin: AdminUser) -> None:
    """Test successful administrator login returns 200, sets cookies, and yields CSRF token."""
    response = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "csrf_token" in data
    assert data["admin"]["username"] == "admin_test"
    assert data["admin"]["is_active"] is True

    # Check cookies set
    assert "admin_session" in response.cookies
    assert "csrf_token" in response.cookies


async def test_admin_login_invalid_credentials(test_client: httpx.AsyncClient, test_admin: AdminUser) -> None:
    """Test login with wrong password returns 401."""
    response = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "WrongPassword!"},
    )
    assert response.status_code == 401
    assert "Invalid username or password" in response.json()["detail"]


async def test_admin_login_nonexistent_user(test_client: httpx.AsyncClient) -> None:
    """Test login with nonexistent user returns 401."""
    response = await test_client.post(
        "/api/auth/login",
        json={"username": "ghost_admin", "password": "SomePassword123!"},
    )
    assert response.status_code == 401


async def test_admin_login_inactive_rejected(
    test_client: httpx.AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that deactivated administrator accounts cannot log in (403 Forbidden)."""
    inactive = AdminUser(
        username="inactive_admin",
        password_hash=hash_password("SuperSecret123!"),
        is_active=False,
    )
    db_session.add(inactive)
    await db_session.commit()

    response = await test_client.post(
        "/api/auth/login",
        json={"username": "inactive_admin", "password": "SuperSecret123!"},
    )
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


async def test_admin_login_rate_limiting(test_client: httpx.AsyncClient, test_admin: AdminUser) -> None:
    """Test that 5 failed login attempts trigger 429 Too Many Requests."""
    for _ in range(5):
        res = await test_client.post(
            "/api/auth/login",
            json={"username": "admin_test", "password": "wrong"},
        )
        assert res.status_code == 401

    # 6th attempt should be rate limited
    blocked_res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "wrong"},
    )
    assert blocked_res.status_code == 429
    assert "too many failed" in blocked_res.json()["detail"].lower()


async def test_get_current_admin_me(test_client: httpx.AsyncClient, test_admin: AdminUser) -> None:
    """Test /api/auth/me returns admin profile when authenticated, 401 when not."""
    # Unauthenticated
    unauth_res = await test_client.get("/api/auth/me")
    assert unauth_res.status_code == 401

    # Authenticate
    login_res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    assert login_res.status_code == 200

    # Query /me with cookies already stored on test_client
    me_res = await test_client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin_test"


async def test_admin_logout(test_client: httpx.AsyncClient, test_admin: AdminUser) -> None:
    """Test logout invalidates the session in storage and removes cookies."""
    # Login
    login_res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    csrf_token = login_res.json()["csrf_token"]

    # Logout
    logout_res = await test_client.post(
        "/api/auth/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_res.status_code == 200

    # Subsequent /me request should fail
    subsequent_res = await test_client.get("/api/auth/me")
    assert subsequent_res.status_code == 401


async def test_csrf_protection_on_state_changing_requests(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
) -> None:
    """Test that POST/PATCH/DELETE endpoints require a valid matching X-CSRF-Token."""
    login_res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    valid_csrf = login_res.json()["csrf_token"]

    # 1. Missing CSRF header -> 403
    res_no_csrf = await test_client.post(
        "/api/categories",
        json={"name": "Drama", "slug": "drama"},
    )
    assert res_no_csrf.status_code == 403
    assert "CSRF token missing or invalid" in res_no_csrf.json()["detail"]

    # 2. Invalid CSRF header -> 403
    res_bad_csrf = await test_client.post(
        "/api/categories",
        json={"name": "Drama", "slug": "drama"},
        headers={"X-CSRF-Token": "tampered_token_xyz"},
    )
    assert res_bad_csrf.status_code == 403

    # 3. Valid CSRF header -> 201 Created
    res_valid = await test_client.post(
        "/api/categories",
        json={"name": "Drama", "slug": "drama"},
        headers={"X-CSRF-Token": valid_csrf},
    )
    assert res_valid.status_code == 201
    assert res_valid.json()["slug"] == "drama"

