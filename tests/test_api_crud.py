"""Tests for Video, Category, Collection, User, and Dashboard API endpoints."""

import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.collection_service import get_collection_by_id
from app.services.video_service import (
    VIDEO_STATUS_ARCHIVED,
    VIDEO_STATUS_DRAFT,
    VIDEO_STATUS_PUBLISHED,
    list_videos,
)


async def get_auth_csrf(test_client: httpx.AsyncClient) -> str:
    """Helper to authenticate test_client and return the CSRF token."""
    res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    return res.json()["csrf_token"]


async def test_unauthorized_endpoints_rejected(test_client: httpx.AsyncClient) -> None:
    """Verify that all admin endpoints reject unauthenticated requests with 401."""
    endpoints = [
        ("GET", "/api/dashboard/stats"),
        ("GET", "/api/videos"),
        ("POST", "/api/videos"),
        ("GET", f"/api/videos/{uuid.uuid4()}"),
        ("GET", "/api/categories"),
        ("POST", "/api/categories"),
        ("GET", "/api/collections"),
        ("POST", "/api/collections"),
        ("GET", "/api/users"),
    ]

    for method, path in endpoints:
        if method == "GET":
            res = await test_client.get(path)
        else:
            res = await test_client.post(path, json={})
        assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"


async def test_category_api_crud(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test full Category CRUD through API endpoints and verify audit logging."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    # 1. Create Category
    create_res = await test_client.post(
        "/api/categories",
        json={"name": "Sci-Fi", "slug": "sci-fi", "description": "Science fiction movies"},
        headers=headers,
    )
    assert create_res.status_code == 201
    cat_data = create_res.json()
    cat_id = cat_data["id"]
    assert cat_data["name"] == "Sci-Fi"
    assert cat_data["slug"] == "sci-fi"

    # Verify audit log
    audit_res = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "category.create")
    )
    assert audit_res.scalar_one_or_none() is not None

    # 2. List Categories
    list_res = await test_client.get("/api/categories")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1
    assert any(c["id"] == cat_id for c in list_res.json()["items"])

    # 3. Update Category
    patch_res = await test_client.patch(
        f"/api/categories/{cat_id}",
        json={"description": "Updated futuristic movies"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["description"] == "Updated futuristic movies"

    # 4. Delete Category
    del_res = await test_client.delete(f"/api/categories/{cat_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify deleted from list
    list_after = await test_client.get("/api/categories")
    assert not any(c["id"] == cat_id for c in list_after.json()["items"])


async def test_video_api_lifecycle(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test Video creation, publish, unpublish, archive, filtering, and public isolation."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    # 1. Create a category to link
    cat_res = await test_client.post(
        "/api/categories",
        json={"name": "Action", "slug": "action"},
        headers=headers,
    )
    cat_id = cat_res.json()["id"]

    # 2. Create Draft Video
    video_res = await test_client.post(
        "/api/videos",
        json={
            "title": "Mission Alpha",
            "description": "High stakes thriller",
            "category_ids": [cat_id],
            "duration": 180,
            "mime_type": "video/mp4",
        },
        headers=headers,
    )
    assert video_res.status_code == 201
    vid_data = video_res.json()
    vid_id = vid_data["id"]
    assert vid_data["status"] == VIDEO_STATUS_DRAFT
    assert len(vid_data["categories"]) == 1

    # Public catalog check: draft video must NOT appear in public catalog
    public_videos, public_total = await list_videos(db_session, public_only=True)
    assert not any(v.id == uuid.UUID(vid_id) for v in public_videos)

    # 3. Publish Video
    pub_res = await test_client.post(f"/api/videos/{vid_id}/publish", headers=headers)
    assert pub_res.status_code == 200
    assert pub_res.json()["status"] == VIDEO_STATUS_PUBLISHED
    assert pub_res.json()["published_at"] is not None

    # Public catalog check: published video MUST appear in public catalog
    public_videos, public_total = await list_videos(db_session, public_only=True)
    assert any(v.id == uuid.UUID(vid_id) for v in public_videos)

    # 4. Unpublish Video
    unpub_res = await test_client.post(f"/api/videos/{vid_id}/unpublish", headers=headers)
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == VIDEO_STATUS_DRAFT

    # Public catalog check: unpublished video must NOT appear
    public_videos, public_total = await list_videos(db_session, public_only=True)
    assert not any(v.id == uuid.UUID(vid_id) for v in public_videos)

    # 5. Archive Video
    arch_res = await test_client.post(f"/api/videos/{vid_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == VIDEO_STATUS_ARCHIVED

    # Public catalog check: archived video must NOT appear
    public_videos, public_total = await list_videos(db_session, public_only=True)
    assert not any(v.id == uuid.UUID(vid_id) for v in public_videos)

    # 6. Delete Video
    del_res = await test_client.delete(f"/api/videos/{vid_id}", headers=headers)
    assert del_res.status_code == 200


async def test_collection_api_and_duplicate_prevention(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test Collection CRUD, duplicate video entry prevention, and ordering."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    # Create 2 videos
    v1_res = await test_client.post(
        "/api/videos",
        json={"title": "Part 1", "status": "published"},
        headers=headers,
    )
    v2_res = await test_client.post(
        "/api/videos",
        json={"title": "Part 2", "status": "draft"},  # draft!
        headers=headers,
    )
    vid1 = v1_res.json()["id"]
    vid2 = v2_res.json()["id"]

    # 1. Create collection with duplicate entries [vid1, vid2, vid1]
    coll_res = await test_client.post(
        "/api/collections",
        json={
            "title": "Movie Trilogy",
            "description": "Complete collection",
            "status": "published",
            "video_ids": [vid1, vid2, vid1],  # Duplicate entry!
        },
        headers=headers,
    )
    assert coll_res.status_code == 201
    coll_data = coll_res.json()
    coll_id = coll_data["id"]

    # In admin view: duplicates should be stripped so exactly 2 videos exist
    assert len(coll_data["videos"]) == 2
    assert coll_data["videos"][0]["id"] == vid1
    assert coll_data["videos"][1]["id"] == vid2

    # 2. Public isolation check: published collection must NOT expose draft videos
    public_coll = await get_collection_by_id(db_session, uuid.UUID(coll_id), public_only=True)
    assert public_coll is not None
    # vid2 is draft, so it must not be visible to public users
    assert len(public_coll.collection_videos) == 1
    assert str(public_coll.collection_videos[0].video_id) == vid1

    # 3. Update collection reordering videos
    patch_res = await test_client.patch(
        f"/api/collections/{coll_id}",
        json={"video_ids": [vid2, vid1]},  # reversed order
        headers=headers,
    )
    assert patch_res.status_code == 200
    updated_coll = patch_res.json()
    assert updated_coll["videos"][0]["id"] == vid2
    assert updated_coll["videos"][1]["id"] == vid1

    # 4. Delete collection
    del_res = await test_client.delete(f"/api/collections/{coll_id}", headers=headers)
    assert del_res.status_code == 200


async def test_dashboard_stats_and_users_api(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test /api/dashboard/stats and /api/users endpoints."""
    await get_auth_csrf(test_client)

    # Insert a user
    user = User(
        telegram_id=999888777,
        username="tg_viewer",
        first_name="Viewer",
    )
    db_session.add(user)
    await db_session.commit()

    # 1. Dashboard stats
    stats_res = await test_client.get("/api/dashboard/stats")
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "videos" in stats
    assert "categories" in stats
    assert "collections" in stats
    assert "users" in stats
    assert stats["users"]["total"] >= 1
    assert isinstance(stats["recent_activity"], list)

    # 2. Users list
    users_res = await test_client.get("/api/users")
    assert users_res.status_code == 200
    users_data = users_res.json()
    assert users_data["total"] >= 1
    assert any(u["telegram_id"] == 999888777 for u in users_data["items"])

    # 3. Single user detail
    single_user_res = await test_client.get(f"/api/users/{user.id}")
    assert single_user_res.status_code == 200
    assert single_user_res.json()["username"] == "tg_viewer"
