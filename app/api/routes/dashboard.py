"""Dashboard statistics route."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_db
from app.api.schemas.dashboard import DashboardStatsResponse
from app.models.admin_user import AdminUser
from app.services.stats_service import get_dashboard_stats

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_stats(
    admin: AdminUser = Depends(get_current_admin),
    session: AsyncSession = Depends(get_db),
) -> DashboardStatsResponse:
    """Retrieve overview metrics and statistics for the admin dashboard."""
    stats = await get_dashboard_stats(session)
    return DashboardStatsResponse.model_validate(stats)

