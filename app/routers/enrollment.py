from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from models.Users import User
from schemas.Enrollment import (
    EnrollmentCreate,
    EnrollmentHistoryResponse,
    ScheduleResponse,
    StudentInClassResponse,
    SwapEnrollmentRequest,
    StudentTimetableItem,
)
from schemas.api_response import error_response, success_response
from security import get_current_active_user
from enums.user_role import UserRole
from services.EnrollmentService import EnrollmentService
from services.KafkaQueueService import KafkaQueueService

# Khởi tạo APIRouter quản lý các API liên quan đến đăng ký học phần
router = APIRouter(
    prefix="/enrollments",
    tags=["Enrollments"],
)


@router.post("/register")
async def register_course(
    enroll_in: EnrollmentCreate,
    current_user: User = Depends(get_current_active_user),
):
    """
    [Sinh viên] API đăng ký lớp học phần mới.
    Mô tả luồng hoạt động:
    1. Kiểm tra vai trò của người đăng nhập (phải là Sinh viên).
    2. Đẩy yêu cầu vào hàng đợi tin nhắn Kafka thông qua `KafkaQueueService.publish_and_wait`
       để xếp hàng xử lý bất đồng bộ, tránh nghẽn luồng đồng thời và kiểm soát tranh chấp chỗ cuối cùng.
    3. Đợi kết quả trả về từ Kafka Worker (nơi thực tế chạy giao dịch 3PC).
    4. Trả về kết quả đăng ký thành công hoặc báo lỗi chi tiết.
    """
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới được đăng ký học phần.")

    result = await KafkaQueueService.publish_and_wait(current_user, enroll_in)

    if result.status == "Success":
        return success_response(
            data=result.model_dump(),
            message=result.message,
            status=201
        )

    return error_response(
        message=result.message or "Đăng ký thất bại",
        status=400,
        error_code=result.error_code or "REGISTRATION_FAILED",
        details="; ".join(result.reasons) if result.reasons else result.message
    )


@router.get("/history", response_model=List[EnrollmentHistoryResponse])
def get_enrollment_history(
    maHocKy: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """
    [Sinh viên] API lấy lịch sử các lớp học phần sinh viên đã đăng ký trong học kỳ chỉ định.
    """
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới được xem lịch sử.")

    return EnrollmentService.get_history(
        current_user.userId,
        current_user.MaCoSo,
        maHocKy
    )


@router.delete("/cancel")
def cancel_registration(
    maLopHP: str = Query(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    [Sinh viên] API hủy đăng ký lớp học phần.
    API này sẽ kích hoạt giao thức giao dịch phân tán 3PC ở chế độ CANCEL (Hủy)
    để xóa bản ghi đăng ký chéo site và hoàn lại sĩ số cho lớp.
    """
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới được hủy đăng ký.")

    try:
        EnrollmentService.cancel(
            current_user.userId,
            maLopHP,
            current_user.MaCoSo
        )
        return success_response(message="Hủy đăng ký thành công")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timetable", response_model=List[ScheduleResponse])
def get_my_timetable(
    maHocKy: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """
    [Sinh viên] API lấy thời khóa biểu cá nhân của sinh viên trong học kỳ chỉ định.
    """
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới có thời khóa biểu.")

    return EnrollmentService.get_student_timetable(
        current_user.userId,
        current_user.MaCoSo,
        maHocKy
    )


@router.get("/my-timetable")
def get_my_timetable_enriched(
    maHocKy: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """Lấy thời khóa biểu sinh viên với đầy đủ thông tin lớp, phòng, giảng viên."""
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới có thời khóa biểu.")

    items = EnrollmentService.get_student_timetable_enriched(
        current_user.userId,
        current_user.MaCoSo,
        maHocKy
    )
    return success_response(
        data=items,
        message=f"Lấy thời khóa biểu thành công (tổng: {len(items)} lớp)",
        status=200,
    )

@router.get("/class-students", response_model=List[StudentInClassResponse])
def get_class_students(
    maLopHP: str = Query(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    [Admin / Giảng viên] API xem danh sách sinh viên đã đăng ký tham gia của một lớp học phần.
    """
    if current_user.role not in [UserRole.Admin, UserRole.GiangVien]:
        raise HTTPException(status_code=403, detail="Bạn không có quyền xem danh sách sinh viên lớp này.")

    return EnrollmentService.get_students_by_class(maLopHP)


@router.post("/swap")
def swap_course(
    swap_data: SwapEnrollmentRequest,
    current_user: User = Depends(get_current_active_user),
):
    """
    [Sinh viên] API đổi lớp học phần (Swap/Switch).
    Cho phép sinh viên rút khỏi lớp học phần cũ và đăng ký lớp học phần mới trên cùng một giao dịch 3PC duy nhất.
    """
    if current_user.role != UserRole.SinhVien:
        raise HTTPException(status_code=403, detail="Chỉ sinh viên mới được đổi lớp.")

    ma_sv = getattr(current_user, "MaSV", current_user.userId)
    
    success = EnrollmentService.swap_class(
        current_user,
        swap_data.old_ma_lop_hp,
        swap_data.new_ma_lop_hp
    )
    
    if success:
        return success_response(message="Đổi lớp thành công")
    
    return error_response(message="Đổi lớp thất bại", status=400)
