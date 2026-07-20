from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from configs.db import open_db_by_branch
from models.Users import User
from schemas.Student import (
    StudentCreate,
    StudentFilter,
    StudentResponse,
    StudentStatusUpdate,
    StudentUpdate,
)
from schemas.api_response import error_response, success_response
from security import get_current_user, get_current_active_user, get_current_user_db
from sqlalchemy.orm import Session
from services.StudentManagementService import StudentManagementService

router = APIRouter(
    prefix="/students",
    tags=["Student Management"],
)


@router.get("/")
async def get_all_students(
    maCoSo: Optional[str] = Query(None, description="Loc theo ma co so"),
    maKhoa: Optional[str] = Query(None, description="Loc theo ma khoa"),
    trangThai: Optional[str] = Query(None, description="Loc theo trang thai"),
    keyword: Optional[str] = Query(None, description="Tim kiem theo ma, ho ten"),
    skip: int = Query(0, ge=0, description="So ban ghi bo qua"),
    limit: int = Query(20, ge=1, le=100, description="So ban ghi lay"),
    # db: Session = Depends(get_current_user_db),
    current_user: User = Depends(get_current_user),
):
    db = open_db_by_branch(maCoSo or current_user.MaCoSo)
    try:
        filters = StudentFilter(
            MaCoSo=maCoSo,
            MaKhoa=maKhoa,
            TrangThai=trangThai,
            keyword=keyword,
        )
        students, total, status_counts = StudentManagementService.get_all_students(db, filters, skip, limit)
        return success_response(
            data={
                "items": [StudentResponse.model_validate(item).model_dump() for item in students],
                "total": total,
                "skip": skip,
                "limit": limit,
                "stats": status_counts,
            },
            message=f"Lay danh sach sinh vien thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_STUDENTS_FAILED",
        )


@router.get("/{ma_sv}")
async def get_student(
    ma_sv: str = Path(..., description="Mã sinh viên"),
    current_user: User = Depends(get_current_user)
):
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        student = StudentManagementService.get_student_by_masv(db, ma_sv)
        return success_response(
            data=StudentResponse.model_validate(student).model_dump(),
            message=f"Lay thong tin sinh vien '{ma_sv}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="STUDENT_NOT_FOUND",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_student(
    student_in: StudentCreate,
    current_user: User = Depends(get_current_active_user)
):
    """Tạo mới sinh viên (Admin only)"""
    try:
        student = await StudentManagementService.create_student(student_in, current_user)
        return success_response(
            data=student,
            message=f"Tạo sinh viên '{student_in.MaSV}' thành công",
            status=201
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_STUDENT_FAILED",
        )


@router.put("/{ma_sv}")
async def update_student(
    ma_sv: str = Path(..., description="Mã sinh viên"),
    student_in: StudentUpdate = None,
    current_user: User = Depends(get_current_active_user)
):
    """Cập nhật thông tin sinh viên (Admin only)"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        student = StudentManagementService.update_student(db, ma_sv, student_in, current_user)
        return success_response(
            data=student,
            message=f"Cập nhật sinh viên '{ma_sv}' thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_STUDENT_FAILED",
        )


@router.patch("/{ma_sv}/status")
async def update_student_status(
    ma_sv: str = Path(..., description="Mã sinh viên"),
    status_update: StudentStatusUpdate = None,
    current_user: User = Depends(get_current_active_user)
):
    """Cập nhật trạng thái sinh viên (Admin only)"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        student = StudentManagementService.update_student_status(db, ma_sv, status_update, current_user)
        return success_response(
            data=student,
            message=f"Cập nhật trạng thái sinh viên '{ma_sv}' thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_STUDENT_STATUS_FAILED",
        )


@router.delete("/{ma_sv}")
async def delete_student(
    ma_sv: str = Path(..., description="Mã sinh viên"),
    current_user: User = Depends(get_current_active_user)
):
    """Xóa sinh viên (Admin only)"""
    db = open_db_by_branch(current_user.MaCoSo)
    try:
        StudentManagementService.delete_student(db, ma_sv, current_user)
        return success_response(
            data=None,
            message=f"Xoa sinh vien '{ma_sv}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_STUDENT_FAILED",
        )
