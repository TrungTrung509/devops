from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from enums.user_role import UserRole
from models.Users import User
from schemas.api_response import error_response, success_response
from security import require_roles
from services.FailoverService import FailoverService

router = APIRouter(
    prefix="/failover",
    tags=["Failover"],
)


class ManualFailoverRequest(BaseModel):
    target_site: str
    reason: Optional[str] = None


class AutoFailoverRequest(BaseModel):
    reason: Optional[str] = None


class AutoFailoverConfigRequest(BaseModel):
    enabled: bool


@router.get("/status")
async def get_failover_status(
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        return success_response(
            data=FailoverService.get_failover_status(),
            message="Lay trang thai failover thanh cong",
            status=200,
        )
    except Exception as exc:
        return error_response(
            message=str(exc),
            status=500,
            error_code="FAILOVER_STATUS_FAILED",
        )


@router.post("/manual")
async def manual_failover(
    payload: ManualFailoverRequest,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        return success_response(
            data=FailoverService.manual_failover(payload.target_site, payload.reason),
            message=f"Da promote '{payload.target_site.upper()}' thanh primary moi",
            status=200,
        )
    except Exception as exc:
        status_code = getattr(exc, "status_code", 500)
        detail = getattr(exc, "detail", str(exc))
        return error_response(
            message=detail,
            status=status_code,
            error_code="MANUAL_FAILOVER_FAILED",
        )


@router.post("/auto")
async def auto_failover(
    payload: AutoFailoverRequest,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        result = FailoverService.trigger_auto_failover(payload.reason)
        return success_response(
            data=result,
            message="Da chay auto failover",
            status=200,
        )
    except Exception as exc:
        status_code = getattr(exc, "status_code", 500)
        detail = getattr(exc, "detail", str(exc))
        return error_response(
            message=detail,
            status=status_code,
            error_code="AUTO_FAILOVER_FAILED",
        )


@router.post("/config/auto")
async def set_auto_failover(
    payload: AutoFailoverConfigRequest,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        return success_response(
            data=FailoverService.set_auto_failover(payload.enabled),
            message="Cap nhat cau hinh auto failover thanh cong",
            status=200,
        )
    except Exception as exc:
        return error_response(
            message=str(exc),
            status=500,
            error_code="FAILOVER_CONFIG_FAILED",
        )
