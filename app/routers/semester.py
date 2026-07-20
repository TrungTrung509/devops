from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from enums.user_role import UserRole
from models.Users import User
from schemas.Semester import SemesterCreate, SemesterUpdate
from schemas.api_response import error_response, success_response
from security import get_current_active_user, get_current_user_db, require_roles
from services.SemesterService import SemesterService

router = APIRouter(
    prefix="/semesters",
    tags=["Semester Management"],
)


@router.get("/")
async def get_all_semesters(
    db: Session = Depends(get_current_user_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        items, total = SemesterService.get_all_semesters(db)
        return success_response(
            data={"items": [item for item in items], "total": total},
            message=f"Lay danh sach hoc ky thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_SEMESTERS_FAILED",
        )


@router.get("/{ma_hoc_ky}")
async def get_semester(
    ma_hoc_ky: str = Path(..., description="Ma hoc ky"),
    db: Session = Depends(get_current_user_db),
    current_user: User = Depends(get_current_active_user),
):
    try:
        semester = SemesterService.get_semester_by_id(db, ma_hoc_ky.upper())
        return success_response(
            data=semester,
            message=f"Lay chi tiet hoc ky '{ma_hoc_ky.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="SEMESTER_NOT_FOUND",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_semester(
    semester_in: SemesterCreate,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        semester = await SemesterService.create_semester(semester_in, current_user)
        return success_response(
            data=semester.model_dump(),
            message=f"Tao hoc ky '{semester.MaHocKy}' thanh cong",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_SEMESTER_FAILED",
        )


@router.put("/{ma_hoc_ky}")
async def update_semester(
    semester_in: SemesterUpdate,
    ma_hoc_ky: str = Path(..., description="Ma hoc ky"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        semester = await SemesterService.update_semester(ma_hoc_ky, semester_in, current_user)
        return success_response(
            data=semester.model_dump(),
            message=f"Cap nhat hoc ky '{semester.MaHocKy}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_SEMESTER_FAILED",
        )


@router.delete("/{ma_hoc_ky}")
async def delete_semester(
    ma_hoc_ky: str = Path(..., description="Ma hoc ky"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        await SemesterService.delete_semester(ma_hoc_ky, current_user)
        return success_response(
            data=None,
            message=f"Xoa hoc ky '{ma_hoc_ky.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_SEMESTER_FAILED",
        )
