from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from configs.db import get_db
from enums.user_role import UserRole
from models.Users import User
from security import require_roles
from schemas.Department import DepartmentCreate, DepartmentUpdate, DepartmentResponse
from schemas.api_response import success_response, error_response
from services.DepartmentService import DepartmentService

router = APIRouter(
    prefix="/departments",
    tags=["Departments"]
)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_in: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Tạo mới khoa (Admin only)"""
    try:
        dept = await DepartmentService.create_department(db, dept_in, current_user)
        return success_response(
            data=DepartmentResponse.model_validate(dept).model_dump(),
            message=f"Tạo khoa '{dept_in.MaKhoa}' thành công",
            status=201
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_DEPARTMENT_FAILED"
        )
@router.get("/")
async def get_all_departments(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    try:
        departments = await DepartmentService.get_all_departments(db)
        return success_response(
            data=[DepartmentResponse.model_validate(d).model_dump() for d in departments],
            message=f"Lấy danh sách khoa thành công (tổng: {len(departments)})",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_DEPARTMENTS_FAILED"
        )


@router.put("/{MaKhoa}")
async def update_department(
    MaKhoa: str,
    dept_in: DepartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Cập nhật thông tin khoa (Admin only)"""
    try:
        dept = await DepartmentService.update_department(db, MaKhoa, dept_in)
        return success_response(
            data=DepartmentResponse.model_validate(dept).model_dump(),
            message=f"Cập nhật khoa '{MaKhoa}' thành công",
            status=200
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_DEPARTMENT_FAILED"
        )


@router.delete("/{MaKhoa}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    MaKhoa: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.Admin))
):
    """Xóa khoa (Admin only)"""
    try:
        await DepartmentService.delete_department(db, MaKhoa, current_user)
        return success_response(
            data=None,
            message=f"Xóa khoa '{MaKhoa}' thành công",
            status=status.HTTP_204_NO_CONTENT
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_DEPARTMENT_FAILED"
        )
