import asyncio
import time

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from configs.config import REMOTE_BENCH_DELAY_MS
from configs.db import SessionLocals
from enums.user_role import UserRole
from models.Users import User
from monitoring.metrics import observe_course_read
from schemas.Course import CourseCreate, CourseUpdate
from schemas.api_response import error_response, success_response
from security import get_current_active_user, get_current_user_db, require_roles
from services.CourseService import CourseService
from services.FailoverService import FailoverService

# Khởi tạo APIRouter quản lý các API liên quan đến học phần (môn học)
router = APIRouter(
    prefix="/courses",
    tags=["Course Management"],
)


@router.get("/replication/status")
async def get_course_replication_status(
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    """
    [Admin] API lấy thông tin trạng thái đồng bộ dữ liệu học phần.
    Trả về: Danh sách trạng thái online/offline của các site và số lượng sự kiện outbox tồn đọng.
    """
    try:
        status_data = CourseService.get_replication_status()
        return success_response(
            data=status_data,
            message="Lay trang thai replication hoc phan thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="REPLICATION_STATUS_FAILED",
        )


@router.post("/replication/recover")
async def recover_course_replication(
    target_site: str | None = None,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    """
    [Admin] API kích hoạt thủ công tiến trình đồng bộ dữ liệu học phần từ hàng đợi Outbox.
    Có thể chỉ định đồng bộ bù cho riêng một site cụ thể (target_site).
    """
    try:
        result = CourseService.run_replication_recovery(target_site)
        return success_response(
            data=result,
            message="Da kich hoat recovery replication hoc phan",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="REPLICATION_RECOVERY_FAILED",
        )


@router.get("/")
async def get_all_courses(
    current_user: User = Depends(get_current_active_user),
    read_mode: str = Query("auto", pattern="^(auto|local|remote)$"),
    target_site: str | None = Query(None, description="Site doc du lieu khi can benchmark remote"),
):
    """
    [Tất cả User] API lấy danh sách toàn bộ học phần trong hệ thống.
    Hỗ trợ các tham số phục vụ cho chạy thử nghiệm hiệu năng:
    - read_mode: auto (tự động điều hướng), local (ép đọc tại chỗ), remote (ép đọc từ xa).
    - target_site: Tên site đích khi ép chạy chế độ remote read.
    """
    # 1. Định tuyến kết nối DB đến site phù hợp
    db, served_site, effective_mode = _open_course_read_session(
        current_user=current_user,
        read_mode=read_mode,
        target_site=target_site,
    )
    # 2. Tính toán độ trễ mạng giả lập (nếu đọc remote)
    simulated_delay_ms = _get_simulated_remote_delay_ms(
        read_mode=effective_mode,
        source_site=current_user.MaCoSo.upper(),
        served_site=served_site,
    )
    # Bấm giờ đo đạc thời gian bắt đầu xử lý
    started_at = time.perf_counter()
    try:
        # 3. Tạo độ trễ mạng giả lập bằng sleep
        await _apply_simulated_remote_delay(simulated_delay_ms)
        
        # 4. Thực thi câu lệnh đọc danh sách học phần từ DB
        items, total = CourseService.get_all_courses(db)
        
        # 5. Ghi nhận thông số độ trễ vào Prometheus Client
        observe_course_read(
            endpoint="list",
            read_mode=effective_mode,
            source_site=current_user.MaCoSo.upper(),
            served_site=served_site,
            duration_seconds=time.perf_counter() - started_at,
            status="200",
        )
        return success_response(
            data={
                "items": [item for item in items],
                "total": total,
                "read_context": {
                    "source_site": current_user.MaCoSo.upper(),
                    "served_site": served_site,
                    "read_mode": effective_mode,
                    "simulated_network_delay_ms": simulated_delay_ms,
                },
            },
            message=f"Lay danh sach hoc phan thanh cong (tong: {total})",
            status=200,
        )
    except HTTPException as e:
        # Ghi nhận lỗi nếu có sự cố xảy ra
        observe_course_read(
            endpoint="list",
            read_mode=effective_mode,
            source_site=current_user.MaCoSo.upper(),
            served_site=served_site,
            duration_seconds=time.perf_counter() - started_at,
            status=str(e.status_code),
        )
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="FETCH_COURSES_FAILED",
        )
    finally:
        # Luôn đóng session database sau khi hoàn thành request để trả kết nối về pool
        db.close()


@router.get("/{ma_hoc_phan}")
async def get_course(
    ma_hoc_phan: str = Path(..., description="Ma hoc phan"),
    current_user: User = Depends(get_current_active_user),
    read_mode: str = Query("auto", pattern="^(auto|local|remote)$"),
    target_site: str | None = Query(None, description="Site doc du lieu khi can benchmark remote"),
):
    """
    [Tất cả User] API lấy thông tin chi tiết của một học phần.
    Tương tự API lấy danh sách, hàm này hỗ trợ định tuyến đọc, giả lập trễ mạng và ghi nhận metrics.
    """
    # 1. Định tuyến kết nối DB đến site phù hợp
    db, served_site, effective_mode = _open_course_read_session(
        current_user=current_user,
        read_mode=read_mode,
        target_site=target_site,
    )
    # 2. Tính toán độ trễ mạng giả lập
    simulated_delay_ms = _get_simulated_remote_delay_ms(
        read_mode=effective_mode,
        source_site=current_user.MaCoSo.upper(),
        served_site=served_site,
    )
    # Bấm giờ xử lý
    started_at = time.perf_counter()
    try:
        # 3. Tạo độ trễ mạng giả lập bằng sleep
        await _apply_simulated_remote_delay(simulated_delay_ms)
        
        # 4. Truy vấn DB lấy thông tin chi tiết của học phần
        course = CourseService.get_course_by_id(db, ma_hoc_phan.upper())
        
        # 5. Ghi nhận thông số vào bộ nhớ để Prometheus thu thập
        observe_course_read(
            endpoint="detail",
            read_mode=effective_mode,
            source_site=current_user.MaCoSo.upper(),
            served_site=served_site,
            duration_seconds=time.perf_counter() - started_at,
            status="200",
        )
        return success_response(
            data={
                "course": course,
                "read_context": {
                    "source_site": current_user.MaCoSo.upper(),
                    "served_site": served_site,
                    "read_mode": effective_mode,
                    "simulated_network_delay_ms": simulated_delay_ms,
                },
            },
            message=f"Lay chi tiet hoc phan '{ma_hoc_phan.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        # Ghi nhận lỗi nếu có sự cố xảy ra
        observe_course_read(
            endpoint="detail",
            read_mode=effective_mode,
            source_site=current_user.MaCoSo.upper(),
            served_site=served_site,
            duration_seconds=time.perf_counter() - started_at,
            status=str(e.status_code),
        )
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="COURSE_NOT_FOUND",
        )
    finally:
        # Luôn giải phóng kết nối database sau khi dùng xong
        db.close()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_course(
    course_in: CourseCreate,
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    """
    [Admin] API tạo mới một học phần.
    Thực hiện ghi dữ liệu tập trung vào site Primary và sinh sự kiện đồng bộ Outbox.
    """
    try:
        result = await CourseService.create_course(course_in, current_user)
        return success_response(
            data=result,
            message=f"Tao hoc phan '{result['course']['MaHocPhan']}' thanh cong",
            status=201,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="CREATE_COURSE_FAILED",
        )


@router.put("/{ma_hoc_phan}")
async def update_course(
    course_in: CourseUpdate,
    ma_hoc_phan: str = Path(..., description="Ma hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    """
    [Admin] API cập nhật thông tin học phần hiện có.
    Dữ liệu cập nhật ghi vào site Primary chính và lan truyền đồng bộ sang các site con qua Outbox.
    """
    try:
        result = await CourseService.update_course(ma_hoc_phan, course_in, current_user)
        return success_response(
            data=result,
            message=f"Cap nhat hoc phan '{result['course']['MaHocPhan']}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="UPDATE_COURSE_FAILED",
        )


@router.delete("/{ma_hoc_phan}")
async def delete_course(
    ma_hoc_phan: str = Path(..., description="Ma hoc phan"),
    current_user: User = Depends(require_roles(UserRole.Admin)),
):
    """
    [Admin] API xóa học phần khỏi hệ thống.
    Thực hiện xóa vật lý ở Primary và ghi nhận Outbox DELETE để các site con đồng bộ xóa theo.
    """
    try:
        result = await CourseService.delete_course(ma_hoc_phan, current_user)
        return success_response(
            data=result,
            message=f"Xoa hoc phan '{ma_hoc_phan.upper()}' thanh cong",
            status=200,
        )
    except HTTPException as e:
        return error_response(
            message=e.detail,
            status=e.status_code,
            error_code="DELETE_COURSE_FAILED",
        )


def _open_course_read_session(
    *,
    current_user: User,
    read_mode: str,
    target_site: str | None,
) -> tuple[Session, str, str]:
    """
    [Hàm bổ trợ] Mở kết nối Database phù hợp theo chế độ đọc đã yêu cầu.
    - auto: Sử dụng dịch vụ FailoverService để tự động tìm site Online tốt nhất.
    - local: Ép buộc kết nối tới site cục bộ của sinh viên (Offline sẽ báo lỗi).
    - remote: Ép buộc kết nối tới site được chỉ định từ xa (Offline hoặc trùng site cục bộ sẽ báo lỗi).
    """
    source_site = current_user.MaCoSo.upper()

    # 1. Chế độ tự động điều hướng kết nối an toàn
    if read_mode == "auto":
        served_site = FailoverService.resolve_read_site(
            preferred_site=source_site,
            auto_failover=True,
        )
        return SessionLocals[served_site](), served_site, "auto"

    # 2. Chế độ ép buộc đọc tại cơ sở cục bộ (Dùng cho Benchmark Local Read)
    if read_mode == "local":
        if not FailoverService.is_site_alive(source_site):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Site local '{source_site}' dang offline, khong the benchmark local read",
            )
        return SessionLocals[source_site](), source_site, "local"

    # 3. Chế độ ép buộc đọc từ cơ sở khác ở xa (Dùng cho Benchmark Remote Read)
    remote_site = (target_site or "").upper()
    if remote_site not in SessionLocals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_site khong hop le. Phai la HADONG, NGOCTRUC hoac HOALAC",
        )
    if remote_site == source_site:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remote read phai doc tu site khac voi site trong token",
        )
    if not FailoverService.is_site_alive(remote_site):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Site remote '{remote_site}' dang offline, khong the benchmark remote read",
        )
    return SessionLocals[remote_site](), remote_site, "remote"


def _get_simulated_remote_delay_ms(*, read_mode: str, source_site: str, served_site: str) -> int:
    """
    [Hàm bổ trợ] Tính toán độ trễ mạng giả lập dựa trên chế độ đọc học phần.
    Độ trễ chỉ được áp dụng khi:
    - Chế độ đọc được đặt cụ thể là "remote".
    - Cơ sở của sinh viên (source_site) khác với cơ sở phục vụ dữ liệu (served_site).
    Trả về: Số mili-giây trễ mạng giả lập (lấy từ config, mặc định 120ms).
    """
    if read_mode != "remote":
        return 0
    if source_site == served_site:
        return 0
    return REMOTE_BENCH_DELAY_MS


async def _apply_simulated_remote_delay(delay_ms: int) -> None:
    """
    [Hàm bổ trợ] Áp dụng độ trễ mạng giả lập bằng cách ngủ (sleep) bất đồng bộ.
    Giúp luồng API dừng hoạt động tạm thời mà không chặn luồng CPU của server (non-blocking).
    """
    if delay_ms <= 0:
        return
    await asyncio.sleep(delay_ms / 1000)
