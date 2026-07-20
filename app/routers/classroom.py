from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from enums.user_role import UserRole
from models.Users import User
from schemas.Classroom import ClassroomCreate, ClassroomResponse, ClassroomUpdate, ClassroomFilter
from schemas.api_response import error_response, success_response
from security import get_current_active_user, require_roles
from services.ClassroomService import ClassroomService

router = APIRouter(
    prefix="/classrooms",
    tags=["Classroom Management"],
)


@router.get("/")
async def get_all_classrooms(
    keyword: Optional[str] = Query(None, description="Tìm kiếm theo mã phòng, tên phòng"),
    maCoSo: Optional[str] = Query(None, description="Lọc theo mã cơ sở"),
    loaiPhong: Optional[str] = Query(None, description="Lọc theo loại phòng"),
    trangThai: Optional[str] = Query(None, description="Lọc theo trạng thái"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        filters = ClassroomFilter(
            keyword=keyword,
            MaCoSo=maCoSo,
            LoaiPhong=loaiPhong,
            TrangThai=trangThai,
        )
        items, total = ClassroomService.get_all_classrooms(filters)
        return success_response(
            data={"items": [ClassroomResponse.model_validate(item).model_dump() for item in items], "total": total},
            message=f"Lay danh sach phong hoc thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_CLASSROOMS_FAILED",
        )


@router.get("/{ma_phong}")
async def get_classroom(
    ma_phong: str = Path(..., description="Ma phong"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        classroom = ClassroomService.get_classroom_by_id(ma_phong)
        return success_response(
            data=ClassroomResponse.model_validate(classroom).model_dump(),
            message=f"Lay chi tiet phong hoc '{ma_phong.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CLASSROOM_NOT_FOUND",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_classroom(
    classroom_in: ClassroomCreate,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        classroom = await ClassroomService.create_classroom(classroom_in, current_user)
        return success_response(
            data=classroom.model_dump(),
            message=f"Tao phong hoc '{classroom.MaPhong}' thanh cong",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_CLASSROOM_FAILED",
        )


@router.put("/{ma_phong}")
async def update_classroom(
    classroom_in: ClassroomUpdate,
    ma_phong: str = Path(..., description="Ma phong"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        classroom = await ClassroomService.update_classroom(ma_phong, classroom_in, current_user)
        return success_response(
            data=classroom.model_dump(),
            message=f"Cap nhat phong hoc '{classroom.MaPhong}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_CLASSROOM_FAILED",
        )


@router.delete("/{ma_phong}")
async def delete_classroom(
    ma_phong: str = Path(..., description="Ma phong"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        await ClassroomService.delete_classroom(ma_phong, current_user)
        return success_response(
            data=None,
            message=f"Xoa phong hoc '{ma_phong.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_CLASSROOM_FAILED",
        )
