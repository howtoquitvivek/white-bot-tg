"""Services package exporting domain logic and queries."""

from app.services.audit_service import create_audit_log
from app.services.category_service import (
    create_category,
    delete_category,
    get_category_by_id,
    get_category_by_slug,
    list_categories,
    list_categories_with_published_counts,
    update_category,
)
from app.services.collection_service import (
    create_collection,
    delete_collection,
    get_collection_by_id,
    list_collections,
    list_collections_with_published_counts,
    reorder_collection_videos,
    update_collection,
)
from app.services.stats_service import get_dashboard_stats
from app.services.telegram_storage import TelegramStorageService, TelegramVideoResult, telegram_storage
from app.services.upload_service import (
    get_upload_job,
    list_upload_jobs,
    process_video_upload,
)
from app.services.user_service import (
    UserNotFoundError,
    confirm_age,
    create_user,
    get_user_by_telegram_id,
    register_or_update_user,
)
from app.services.video_service import (
    archive_video,
    create_video,
    delete_video,
    get_video_by_id,
    list_videos,
    publish_video,
    unpublish_video,
    update_video,
)

__all__ = [
    "UserNotFoundError",
    "archive_video",
    "confirm_age",
    "create_audit_log",
    "create_category",
    "create_collection",
    "create_user",
    "create_video",
    "delete_category",
    "delete_collection",
    "delete_video",
    "get_category_by_id",
    "get_category_by_slug",
    "get_collection_by_id",
    "get_dashboard_stats",
    "get_upload_job",
    "get_user_by_telegram_id",
    "get_video_by_id",
    "list_categories",
    "list_categories_with_published_counts",
    "list_collections",
    "list_collections_with_published_counts",
    "list_upload_jobs",
    "list_videos",
    "process_video_upload",
    "publish_video",
    "register_or_update_user",
    "reorder_collection_videos",
    "telegram_storage",
    "TelegramStorageService",
    "TelegramVideoResult",
    "unpublish_video",
    "update_category",
    "update_collection",
    "update_video",
]
