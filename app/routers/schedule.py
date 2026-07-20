from fastapi import APIRouter, Depends, HTTPException, Path

from models.Users import User
from schemas.api_response import error_response, success_response
from security import get_current_active_user
from services.ScheduleManagementService import ScheduleManagementService

router = APIRouter(
    prefix="/schedules",
    tags=["Schedule Management"],
)


@router.get("/")
async def get_all_schedules(
    current_user: User = Depends(get_current_active_user),
):
    try:
        items, total = ScheduleManagementService.get_all_schedules()
        return success_response(
            data={"items": [item.model_dump() for item in items], "total": total},
            message=f"Lay danh sach lich hoc thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_SCHEDULES_FAILED",
        )


@router.get("/{ma_lich}")
async def get_schedule(
    ma_lich: str = Path(..., description="Ma lich"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        schedule = ScheduleManagementService.get_schedule_by_id(ma_lich)
        return success_response(
            data=schedule.model_dump(),
            message=f"Lay chi tiet lich hoc '{ma_lich.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="SCHEDULE_NOT_FOUND",
        )
