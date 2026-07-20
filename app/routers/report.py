from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from enums.user_role import UserRole
from models.Users import User
from schemas.Overview import AdminOverviewResponse
from schemas.Report import (
    BranchRegistrationStatsResponse,
    CrossBranchEnrollmentStatsResponse,
    OpenSectionStatsResponse,
    ReportSummaryResponse,
    SectionOccupancyStatsResponse,
    TopCourseStatsResponse,
)
from security import get_current_active_user
from services.OverviewService import OverviewService
from services.ReportService import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Statistics"],
)


def _ensure_admin(current_user: User) -> None:
    if current_user.role != UserRole.Admin:
        raise HTTPException(status_code=403, detail="Chi Admin moi co quyen xem bao cao nay.")


@router.get("/summary", response_model=ReportSummaryResponse)
async def get_enrollment_summary(
    scope: str = Query(..., description="Scope: 'site' or 'global'"),
    maCoSo: Optional[str] = Query(None, description="Ma co so neu scope la site"),
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)

    if scope == "site":
        if not maCoSo:
            raise HTTPException(status_code=400, detail="Can cung cap maCoSo khi scope la 'site'")
        return ReportService.get_site_summary(maCoSo.upper(), maHocKy)

    if scope == "global":
        return ReportService.get_global_summary(maHocKy)

    raise HTTPException(status_code=400, detail="Scope khong hop le. Su dung 'site' hoac 'global'")


@router.get("/distributed/students-by-branch", response_model=BranchRegistrationStatsResponse)
async def get_students_by_branch_report(
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    sourceSite: str = Query("HADONG", description="Site dung de chay distributed query"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)
    return ReportService.get_branch_registration_stats(ma_hk=maHocKy, source_site=sourceSite)


@router.get("/distributed/top-course", response_model=TopCourseStatsResponse)
async def get_top_course_report(
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    sourceSite: str = Query("HADONG", description="Site dung de chay distributed query"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)
    return ReportService.get_top_course_stats(ma_hk=maHocKy, source_site=sourceSite)


@router.get("/distributed/cross-branch-students", response_model=CrossBranchEnrollmentStatsResponse)
async def get_cross_branch_students_report(
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    sourceSite: str = Query("HADONG", description="Site dung de chay distributed query"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)
    return ReportService.get_cross_branch_enrollment_stats(ma_hk=maHocKy, source_site=sourceSite)


@router.get("/distributed/section-occupancy", response_model=SectionOccupancyStatsResponse)
async def get_section_occupancy_report(
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    sourceSite: str = Query("HADONG", description="Site dung de chay distributed query"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)
    return ReportService.get_section_occupancy_stats(ma_hk=maHocKy, source_site=sourceSite)


@router.get("/distributed/open-sections", response_model=OpenSectionStatsResponse)
async def get_open_sections_report(
    groupBy: str = Query(..., description="branch hoac department"),
    maHocKy: Optional[str] = Query(None, description="Ma hoc ky"),
    sourceSite: str = Query("HADONG", description="Site dung de chay distributed query"),
    current_user: User = Depends(get_current_active_user),
):
    _ensure_admin(current_user)
    return ReportService.get_open_section_stats(
        group_by=groupBy,
        ma_hk=maHocKy,
        source_site=sourceSite,
    )


@router.get("/admin-overview/{entity}", response_model=AdminOverviewResponse)
async def get_admin_entity_overview(
    entity: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    Lay thong ke tong quan cho mot entity (Admin only).
    Entity: teachers | students | courses | semesters | classrooms | class-sections
    """
    _ensure_admin(current_user)
    return OverviewService.get_overview(entity)
