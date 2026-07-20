from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from configs.db import open_db_by_branch
from models.Users import User
from schemas.Teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherStatusUpdate,
    TeacherResponse,
    TeacherFilter,
)
from schemas.api_response import success_response, error_response
from security import get_current_user, get_current_active_user
from services.TeacherManagementService import TeacherManagementService

router = APIRouter(
    prefix="/teachers",
    tags=["Teacher Management"],
)


@router.get("/")
async def get_all_teachers(
    maCoSo: Optional[str] = Query(None, description="Lọc theo mã cơ sở"),
    maKhoa: Optional[str] = Query(None, description="Lọc theo mã khoa"),
    trangThai: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    keyword: Optional[str] = Query(None, description="Tìm kiếm theo mã, họ tên"),
    skip: int = Query(0, ge=0, description="Số bản ghi bỏ qua"),
    limit: int = Query(20, ge=1, le=100, description="Số bản ghi lấy"),
    current_user: User = Depends(get_current_user),
):
    """Lấy danh sách giảng viên với các filter."""
    db = open_db_by_branch(maCoSo or current_user.MaCoSo)
    try:
        filters = TeacherFilter(
            MaCoSo=maCoSo,
            MaKhoa=maKhoa,
            TrangThai=trangThai,
            keyword=keyword,
        )
        teachers, total, status_counts = TeacherManagementService.get_all_teachers(
            db, filters, skip, limit
        )
        return success_response(
            data={
                "items": [t for t in teachers],
                "total": total,
                "skip": skip,
                "limit": limit,
                "stats": status_counts,
            },
            message=f"Lấy danh sách giảng viên thành công (tổng: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_TEACHERS_FAILED",
        )


@router.get("/{ma_gv}")
async def get_teacher(
    ma_gv: str = Path(..., description="Mã giảng viên"),
    current_user: User = Depends(get_current_user),
):
    """Lấy thông tin giảng viên theo MaGV"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        teacher = TeacherManagementService.get_teacher_by_magv(db, ma_gv)
        return success_response(
            data=teacher,
            message=f"Lấy thông tin giảng viên '{ma_gv}' thành công",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="TEACHER_NOT_FOUND",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_teacher(
    teacher_in: TeacherCreate, current_user: User = Depends(get_current_active_user)
):
    """Tạo mới giảng viên (Admin only)"""
    try:
        teacher = await TeacherManagementService.create_teacher(
            teacher_in, current_user
        )
        return success_response(
            data=teacher,
            message=f"Tạo giảng viên '{teacher_in.MaGV}' thành công",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_TEACHER_FAILED",
        )


@router.put("/{ma_gv}")
async def update_teacher(
    ma_gv: str = Path(..., description="Mã giảng viên"),
    teacher_in: TeacherUpdate = None,
    current_user: User = Depends(get_current_active_user),
):
    """Cập nhật thông tin giảng viên (Admin only)"""
    db = open_db_by_branch(teacher_in.MaCoSo or current_user.MaCoSo)
    try:
        teacher = TeacherManagementService.update_teacher(
            db, ma_gv, teacher_in, current_user
        )
        return success_response(
            data=TeacherResponse.model_validate(teacher).model_dump(),
            message=f"Cập nhật giảng viên '{ma_gv}' thành công",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_TEACHER_FAILED",
        )


@router.patch("/{ma_gv}/status")
async def update_teacher_status(
    ma_gv: str = Path(..., description="Mã giảng viên"),
    status_update: TeacherStatusUpdate = None,
    current_user: User = Depends(get_current_active_user),
):
    """Cập nhật trạng thái giảng viên (Admin only)"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        teacher = TeacherManagementService.update_teacher_status(
            db, ma_gv, status_update, current_user
        )
        return success_response(
            data=TeacherResponse.model_validate(teacher).model_dump(),
            message=f"Cập nhật trạng thái giảng viên '{ma_gv}' thành công",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_TEACHER_STATUS_FAILED",
        )


@router.delete("/{ma_gv}")
async def delete_teacher(
    ma_gv: str = Path(..., description="Mã giảng viên"),
    current_user: User = Depends(get_current_active_user),
):
    """Xóa giảng viên (Admin only)"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        TeacherManagementService.delete_teacher(db, ma_gv, current_user)
        return success_response(
            data=None,
            message=f"Xóa giảng viên '{ma_gv}' thành công",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_TEACHER_FAILED",
        )
