from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from typing import Optional

from models.Users import User

from enums.user_role import UserRole
from schemas.ClassSection import CourseSectionCreate, CourseSectionUpdate, ScheduleCreate, ScheduleUpdate
from schemas.api_response import error_response, success_response
from security import get_current_active_user, require_roles
from services.ClassSectionService import ClassSectionService

router = APIRouter(
    prefix="/class-sections",
    tags=["Class Section Management"],
)


@router.get("/my-teaching")
async def get_my_teaching_sections(
    current_user: User = Depends(require_roles(UserRole.GiangVien)),
):
    try:
        items, total = ClassSectionService.get_my_teaching_sections(current_user)
        return success_response(
            data={"items": [item.model_dump() for item in items], "total": total},
            message=f"Lay danh sach lop hoc phan giang day thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_MY_CLASS_SECTIONS_FAILED",
        )


@router.get("/my-teaching/schedules")
async def get_my_teaching_schedules(
    current_user: User = Depends(require_roles(UserRole.GiangVien)),
):
    """Lấy tất cả lịch học của các lớp giảng viên đang phụ trách."""
    try:
        schedules = ClassSectionService.get_my_teaching_schedules(current_user)
        return success_response(
            data=schedules,
            message=f"Lấy lịch dạy thành công ({len(schedules)} buổi)",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_TEACHING_SCHEDULES_FAILED",
        )


@router.get("/")
async def get_all_class_sections(
    keyword: Optional[str] = Query(None, description="Tìm theo mã hoặc tên lớp HP"),
    MaCoSo: Optional[str] = Query(None, description="Mã cơ sở: HADONG, NGOCTRUC, HOALAC"),
    HinhThucHoc: Optional[str] = Query(None, description="Hình thức học: Offline, Online, Hybrid"),
    TrangThaiLop: Optional[str] = Query(None, description="Trạng thái lớp: Mo, Dong, Huy"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        items, total = ClassSectionService.get_all_sections(
            keyword=keyword,
            MaCoSo=MaCoSo,
            HinhThucHoc=HinhThucHoc,
            TrangThaiLop=TrangThaiLop,
        )
        return success_response(
            data={"items": [item.model_dump() for item in items], "total": total},
            message=f"Lay danh sach lop hoc phan thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_CLASS_SECTIONS_FAILED",
        )


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_class_section(
    section_in: CourseSectionCreate,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        section = await ClassSectionService.create_section(section_in, current_user)
        return success_response(
            data=section.model_dump(),
            message=f"Tao lop hoc phan '{section.MaLopHP}' thanh cong",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_CLASS_SECTION_FAILED",
        )


@router.get("/{ma_lop_hp}/schedules")
async def get_class_section_schedules(
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        schedules = ClassSectionService.get_section_schedules(ma_lop_hp)
        return success_response(
            data=[item.model_dump() for item in schedules],
            message=f"Lay lich hoc cua lop '{ma_lop_hp.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_SCHEDULES_FAILED",
        )


@router.post("/{ma_lop_hp}/schedules", status_code=status.HTTP_201_CREATED)
async def add_class_section_schedule(
    schedule_in: ScheduleCreate,
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        schedule = await ClassSectionService.add_schedule(ma_lop_hp, schedule_in, current_user)
        return success_response(
            data=schedule.model_dump(),
            message=f"Them lich hoc '{schedule.MaLich}' cho lop '{ma_lop_hp.upper()}' thanh cong",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_SCHEDULE_FAILED",
        )


@router.put("/{ma_lop_hp}/schedules/{ma_lich}")
async def update_class_section_schedule(
    schedule_in: ScheduleUpdate,
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    ma_lich: str = Path(..., description="Ma lich hoc"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        schedule = await ClassSectionService.update_schedule(ma_lop_hp, ma_lich, schedule_in, current_user)
        return success_response(
            data=schedule.model_dump(),
            message=f"Cap nhat lich hoc '{schedule.MaLich}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_SCHEDULE_FAILED",
        )


@router.delete("/{ma_lop_hp}/schedules/{ma_lich}")
async def delete_class_section_schedule(
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    ma_lich: str = Path(..., description="Ma lich hoc"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        await ClassSectionService.delete_schedule(ma_lop_hp, ma_lich, current_user)
        return success_response(
            data=None,
            message=f"Xoa lich hoc '{ma_lich.upper()}' cua lop '{ma_lop_hp.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_SCHEDULE_FAILED",
        )


@router.get("/{ma_lop_hp}/enrollments")
async def get_class_section_enrollments(
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin, UserRole.GiangVien)),
):
    try:
        enrollments = ClassSectionService.get_section_enrollments(ma_lop_hp, current_user)
        return success_response(
            data=[item.model_dump() for item in enrollments],
            message=f"Lay danh sach dang ky cua lop '{ma_lop_hp.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_ENROLLMENTS_FAILED",
        )


@router.get("/{ma_lop_hp}")
async def get_class_section_detail(
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(get_current_active_user),
):
    try:
        section = ClassSectionService.get_section_by_id(ma_lop_hp)
        return success_response(
            data=section.model_dump(),
            message=f"Lay chi tiet lop hoc phan '{ma_lop_hp.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CLASS_SECTION_NOT_FOUND",
        )


@router.put("/{ma_lop_hp}")
async def update_class_section(
    section_in: CourseSectionUpdate,
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        section = await ClassSectionService.update_section(ma_lop_hp, section_in, current_user)
        return success_response(
            data=section.model_dump(),
            message=f"Cap nhat lop hoc phan '{section.MaLopHP}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_CLASS_SECTION_FAILED",
        )


@router.delete("/{ma_lop_hp}")
async def delete_class_section(
    ma_lop_hp: str = Path(..., description="Ma lop hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    try:
        await ClassSectionService.delete_section(ma_lop_hp, current_user)
        return success_response(
            data=None,
            message=f"Xoa lop hoc phan '{ma_lop_hp.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_CLASS_SECTION_FAILED",
        )
