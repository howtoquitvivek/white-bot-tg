"""Tests for Video Upload pipeline and Telegram Storage Service integration."""

import io
from pathlib import Path
from unittest.mock import AsyncMock, patch
import uuid

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_user import AdminUser
from app.models.category import Category
from app.models.upload_job import (
    UPLOAD_JOB_COMPLETED,
    UPLOAD_JOB_FAILED,
    UploadJob,
)
from app.models.video import VIDEO_STATUS_DRAFT, Video
from app.services.telegram_storage import TelegramStorageService, TelegramVideoResult


async def get_auth_csrf(test_client: httpx.AsyncClient) -> str:
    """Helper to authenticate test_client and return the CSRF token."""
    res = await test_client.post(
        "/api/auth/login",
        json={"username": "admin_test", "password": "SuperSecret123!"},
    )
    return res.json()["csrf_token"]


def make_dummy_mp4_bytes(size: int = 1024) -> bytes:
    """Create a minimal binary payload with an mp4 ftyp box header."""
    header = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom"
    return header + b"\x00" * max(0, size - len(header))


async def test_upload_video_success(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test successful video upload flow with mocked Telegram API."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    # Create a test category
    cat = Category(name="Action", slug="action", description="Action videos")
    db_session.add(cat)
    await db_session.commit()
    await db_session.refresh(cat)

    mock_result = TelegramVideoResult(
        file_id="tg_vid_abc_123",
        file_unique_id="unique_vid_123",
        chat_id=-1001234567890,
        message_id=999,
        duration=120,
        file_size=2048,
        mime_type="video/mp4",
        width=1920,
        height=1080,
    )

    with patch.object(
        TelegramStorageService,
        "upload_video",
        new=AsyncMock(return_value=mock_result),
    ) as mock_upload:
        payload_data = {
            "title": "Epic Car Chase",
            "description": "High-octane highway scene",
            "category_ids": str(cat.id),
        }
        files = {
            "file": ("chase.mp4", io.BytesIO(make_dummy_mp4_bytes(2048)), "video/mp4"),
        }

        response = await test_client.post(
            "/api/uploads",
            data=payload_data,
            files=files,
            headers=headers,
        )

        assert response.status_code == 201, response.text
        data = response.json()
        assert data["success"] is True
        video_data = data["video"]
        assert video_data["title"] == "Epic Car Chase"
        assert video_data["status"] == VIDEO_STATUS_DRAFT
        assert video_data["telegram_file_id"] == "tg_vid_abc_123"
        assert len(video_data["categories"]) == 1
        assert video_data["categories"][0]["name"] == "Action"

        # Verify UploadJob in DB
        job_id = uuid.UUID(data["job_id"])
        job = await db_session.get(UploadJob, job_id)
        assert job is not None
        assert job.status == UPLOAD_JOB_COMPLETED
        assert job.progress == 100
        assert job.video_id == uuid.UUID(video_data["id"])

        # Verify Telegram upload was called
        mock_upload.assert_awaited_once()


async def test_upload_video_unsupported_format(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
) -> None:
    """Test that non-video file formats are rejected."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    files = {
        "file": ("document.pdf", io.BytesIO(b"%PDF-1.4 dummy content"), "application/pdf"),
    }
    response = await test_client.post(
        "/api/uploads",
        data={"title": "Test PDF"},
        files=files,
        headers=headers,
    )

    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]


async def test_upload_video_file_too_large(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that file exceeding max size limit is rejected with 413."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    from app.config import get_settings

    # Set temporary small limit (1 KB) for testing
    settings = get_settings()
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_BYTES", 500)

    files = {
        "file": ("toolarge.mp4", io.BytesIO(make_dummy_mp4_bytes(1000)), "video/mp4"),
    }
    response = await test_client.post(
        "/api/uploads",
        data={"title": "Too Large Video"},
        files=files,
        headers=headers,
    )

    assert response.status_code == 413
    assert "exceeds maximum upload limit" in response.json()["detail"]


async def test_upload_video_telegram_failure_handling(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test error handling when Telegram upload fails."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    with patch.object(
        TelegramStorageService,
        "upload_video",
        new=AsyncMock(side_effect=RuntimeError("Bot was blocked by the channel")),
    ):
        files = {
            "file": ("failed.mp4", io.BytesIO(make_dummy_mp4_bytes(512)), "video/mp4"),
        }
        response = await test_client.post(
            "/api/uploads",
            data={"title": "Failing Video"},
            files=files,
            headers=headers,
        )

        assert response.status_code == 500
        assert "Video upload failed" in response.json()["detail"]

        # Verify failed UploadJob is recorded in database
        stmt = select(UploadJob).where(UploadJob.original_filename == "failed.mp4")
        result = await db_session.execute(stmt)
        job = result.scalars().first()
        assert job is not None
        assert job.status == UPLOAD_JOB_FAILED
        assert "Bot was blocked by the channel" in (job.error_message or "")


async def test_list_and_get_upload_jobs(
    test_client: httpx.AsyncClient,
    test_admin: AdminUser,
    db_session: AsyncSession,
) -> None:
    """Test GET /api/uploads and GET /api/uploads/{id}."""
    csrf = await get_auth_csrf(test_client)
    headers = {"X-CSRF-Token": csrf}

    job1 = UploadJob(original_filename="sample1.mp4", status=UPLOAD_JOB_COMPLETED, progress=100)
    job2 = UploadJob(original_filename="sample2.mp4", status=UPLOAD_JOB_FAILED, progress=50, error_message="Timeout")
    db_session.add_all([job1, job2])
    await db_session.commit()
    await db_session.refresh(job1)

    # List jobs
    list_res = await test_client.get("/api/uploads", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 2
    filenames = [j["original_filename"] for j in list_data["items"]]
    assert "sample1.mp4" in filenames
    assert "sample2.mp4" in filenames

    # Get single job
    get_res = await test_client.get(f"/api/uploads/{job1.id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["original_filename"] == "sample1.mp4"
    assert get_res.json()["status"] == UPLOAD_JOB_COMPLETED

