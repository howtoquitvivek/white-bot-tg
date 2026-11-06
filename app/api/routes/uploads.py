"""Upload routes for streaming videos directly to the Telegram private channel."""

import json
import logging
from typing import Any, Dict, List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db, verify_csrf
from app.api.schemas.video import VideoResponse
from app.models.admin_user import AdminUser
from app.models.upload_job import UploadJob
from app.services.audit_service import create_audit_log
from app.services.upload_service import (
    get_upload_job,
    list_upload_jobs,
    process_video_upload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/uploads", tags=["uploads"])


def parse_category_ids(raw_categories: Optional[str]) -> Optional[List[uuid.UUID]]:
    """Parse comma-separated or JSON string of category UUIDs."""
    if not raw_categories or not raw_categories.strip():
        return None

    cleaned = raw_categories.strip()
    result_ids: List[uuid.UUID] = []

    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            parsed_list = json.loads(cleaned)
            for item in parsed_list:
                result_ids.append(uuid.UUID(str(item).strip()))
            return result_ids
        except (json.JSONDecodeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category UUID format in JSON array: {exc}",
            )

    for item in cleaned.split(","):
        val = item.strip()
        if val:
            try:
                result_ids.append(uuid.UUID(val))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid category UUID format: '{val}'",
                )

    return result_ids


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    summary="Upload video directly to Telegram storage channel",
)
async def upload_video_endpoint(
    file: UploadFile = File(..., description="Video file to upload"),
    title: str = Form(..., min_length=1, max_length=255, description="Video title"),
    description: Optional[str] = Form(None, description="Optional video description"),
    category_ids: Optional[str] = Form(None, description="Comma-separated or JSON list of category UUIDs"),
    channel_id: Optional[str] = Form(None, description="Optional override for target Telegram channel ID"),
    current_admin: AdminUser = Depends(get_current_admin),
    _: None = Depends(verify_csrf),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Upload a video file, stream to disk, send to Telegram, and create video record as draft."""
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must have a valid filename.",
        )

    parsed_cats = parse_category_ids(category_ids)

    try:
        video, job = await process_video_upload(
            session=session,
            upload_file=file,
            title=title,
            description=description,
            category_ids=parsed_cats,
            channel_id=channel_id,
        )

        await create_audit_log(
            session=session,
            admin_id=current_admin.id,
            action="upload_video",
            entity_type="video",
            entity_id=str(video.id),
            metadata={
                "title": video.title,
                "file_id": video.telegram_file_id,
                "job_id": str(job.id),
                "file_size": video.file_size,
            },
        )

        return {
            "success": True,
            "message": "Video uploaded to Telegram successfully and saved as draft.",
            "video": VideoResponse.model_validate(video),
            "job_id": str(job.id),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Upload endpoint failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video upload failed: {str(exc)}",
        )


@router.get(
    "",
    summary="List upload jobs",
)
async def list_uploads_endpoint(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """List upload jobs with pagination."""
    jobs, total = await list_upload_jobs(session=session, limit=limit, offset=offset)
    return {
        "items": [
            {
                "id": str(j.id),
                "original_filename": j.original_filename,
                "status": j.status,
                "progress": j.progress,
                "error_message": j.error_message,
                "video_id": str(j.video_id) if j.video_id else None,
                "created_at": j.created_at.isoformat(),
                "updated_at": j.updated_at.isoformat(),
            }
            for j in jobs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/{job_id}",
    summary="Get upload job status",
)
async def get_upload_job_endpoint(
    job_id: uuid.UUID,
    current_admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve status and details of a specific upload job."""
    job = await get_upload_job(session=session, job_id=job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Upload job with ID '{job_id}' not found.",
        )

    return {
        "id": str(job.id),
        "original_filename": job.original_filename,
        "status": job.status,
        "progress": job.progress,
        "error_message": job.error_message,
        "video_id": str(job.video_id) if job.video_id else None,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }
