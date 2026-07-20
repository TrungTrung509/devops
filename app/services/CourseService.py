from typing import Any, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.user_role import UserRole
from enums.types import CourseType
from models.Courses import Course
from models.Departments import Departments
from models.Users import User
from repositories.CourseRepo import CourseRepo
from schemas.Course import CourseCreate, CourseResponse, CourseUpdate
from services.FailoverService import FailoverService
from services.ReplicationService import ReplicationService


class CourseService:
    """
    Service quản lý Nghiệp vụ Học phần (Môn học).
    Chịu trách nhiệm thực thi các logic nghiệp vụ, giao dịch (Transactions) ghi dữ liệu tập trung,
    xác thực quyền Admin, và điều phối đồng bộ hóa dữ liệu (Outbox Replication).
    """

    @staticmethod
    def get_all_courses(db: Session) -> Tuple[list[Course], int]:
        """
        Lấy danh sách tất cả các học phần trong DB được truyền vào.
        Trả về: tuple gồm (danh sách học phần, tổng số lượng bản ghi).
        """
        query = CourseRepo.base_query(db)
        total = query.count()
        items = query.order_by(Course.MaHocPhan.asc()).all()
        return items, total

    @staticmethod
    def get_course_by_id(db: Session, ma_hoc_phan: str) -> Course:
        """
        Lấy thông tin chi tiết một học phần theo mã.
        Nếu không tìm thấy môn học, ném ra lỗi HTTP 404.
        """
        course = CourseRepo.get_by_id(db, ma_hoc_phan)
        if not course:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay hoc phan voi ma: {ma_hoc_phan}",
            )
        return course

    @staticmethod
    async def create_course(course_in: CourseCreate, current_user: User) -> dict[str, Any]:
        """
        [Admin] Thêm mới một học phần vào hệ thống.
        Quy trình xử lý giao dịch (Transaction):
        1. Kiểm tra quyền Admin của user.
        2. Mở kết nối (session) tới site Primary hiện tại.
        3. Xác thực tính hợp lệ của dữ liệu (mã học phần chưa tồn tại, mã khoa phải hợp lệ).
        4. Chèn bản ghi học phần mới vào site Primary.
        5. Gọi ReplicationService để chèn các sự kiện đồng bộ PENDING vào bảng Outbox của Primary.
        6. Commit giao dịch (nếu có lỗi sẽ Rollback hoàn toàn).
        7. Sau khi commit thành công, kích hoạt gửi ngay lập tức sự kiện Outbox này sang các site con.
        """
        CourseService._ensure_admin(current_user)
        primary_session = CourseService._open_primary_session()

        try:
            course_code = course_in.MaHocPhan.upper()
            department_code = course_in.MaKhoa.upper()
            CourseService._validate_course_payload(
                so_tin_chi=course_in.SoTinChi,
                so_tiet_ly_thuyet=course_in.SoTietLyThuyet,
                so_tiet_thuc_hanh=course_in.SoTietThucHanh,
                loai_hoc_phan=course_in.LoaiHocPhan,
            )

            # Kiểm tra trùng lặp mã môn học
            if CourseRepo.get_by_id(primary_session, course_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ma hoc phan '{course_code}' da ton tai",
                )

            # Kiểm tra sự tồn tại của khoa quản lý môn học
            CourseService._ensure_department_exists(primary_session, department_code)

            # Tạo đối tượng môn học mới
            course = Course(
                MaHocPhan=course_code,
                TenHocPhan=course_in.TenHocPhan,
                SoTinChi=course_in.SoTinChi,
                SoTietLyThuyet=course_in.SoTietLyThuyet,
                SoTietThucHanh=course_in.SoTietThucHanh,
                LoaiHocPhan=course_in.LoaiHocPhan,
                MaKhoa=department_code,
                MoTa=course_in.MoTa,
                TrangThai=course_in.TrangThai,
            )
            primary_session.add(course)
            primary_session.flush() # Đẩy dữ liệu tạm thời xuống DB để lấy ID/Ngày tạo tự động sinh
            
            # Ghi sự kiện vào hàng đợi Outbox trên cùng một transaction của DB Primary
            events = ReplicationService.stage_course_upsert(primary_session, course)
            primary_session.commit() # Xác nhận lưu trữ hoàn toàn dữ liệu và log outbox
            primary_session.refresh(course)

            # Thực hiện đồng bộ ngay sang các site Replica
            replication = CourseService._dispatch_replication(events)
            return {
                "course": CourseResponse.model_validate(course).model_dump(),
                "replication": replication,
            }
        except Exception as e:
            primary_session.rollback() # Hoàn tác mọi thay đổi nếu gặp bất kỳ lỗi nào
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Primary write failed: {str(e)}",
            )
        finally:
            primary_session.close()

    @staticmethod
    async def update_course(
        ma_hoc_phan: str,
        course_in: CourseUpdate,
        current_user: User,
    ) -> dict[str, Any]:
        """
        [Admin] Cập nhật thông tin học phần hiện có.
        Quy trình xử lý giao dịch tương tự như tạo mới:
        - Mở session tới Primary, tìm kiếm bản ghi cũ.
        - Cập nhật các trường thông tin thay đổi.
        - Ghi sự kiện cập nhật vào bảng Outbox của Primary.
        - Commit giao dịch và kích hoạt đồng bộ hóa ngay lập tức sang các site con.
        """
        CourseService._ensure_admin(current_user)
        primary_session = CourseService._open_primary_session()

        try:
            course_code = ma_hoc_phan.upper()
            existing = CourseRepo.get_by_id(primary_session, course_code)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay hoc phan voi ma: {course_code}",
                )

            # Đọc dữ liệu cập nhật
            update_data = course_in.model_dump(exclude_unset=True)
            if "MaKhoa" in update_data and update_data["MaKhoa"]:
                update_data["MaKhoa"] = update_data["MaKhoa"].upper()
                CourseService._ensure_department_exists(primary_session, update_data["MaKhoa"])

            CourseService._validate_course_payload(
                so_tin_chi=update_data.get("SoTinChi", existing.SoTinChi),
                so_tiet_ly_thuyet=update_data.get("SoTietLyThuyet", existing.SoTietLyThuyet),
                so_tiet_thuc_hanh=update_data.get("SoTietThucHanh", existing.SoTietThucHanh),
                loai_hoc_phan=update_data.get("LoaiHocPhan", existing.LoaiHocPhan),
            )

            # Gán giá trị mới cho học phần
            for field, value in update_data.items():
                setattr(existing, field, value)

            primary_session.flush()
            # Ghi sự kiện UPSERT vào Outbox của Primary
            events = ReplicationService.stage_course_upsert(primary_session, existing)
            primary_session.commit()
            primary_session.refresh(existing)

            # Đồng bộ ngay dữ liệu cập nhật sang các site Replica con
            replication = CourseService._dispatch_replication(events)
            return {
                "course": CourseResponse.model_validate(existing).model_dump(),
                "replication": replication,
            }
        except Exception as e:
            primary_session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Primary update failed: {str(e)}",
            )
        finally:
            primary_session.close()

    @staticmethod
    async def delete_course(ma_hoc_phan: str, current_user: User) -> dict[str, Any]:
        """
        [Admin] Xóa học phần khỏi hệ thống.
        Quy trình xử lý giao dịch:
        - Mở session tới Primary, tìm kiếm bản ghi cũ.
        - Ghi sự kiện DELETE vào bảng Outbox của Primary để các site Replica nhận lệnh xóa theo.
        - Xóa vật lý học phần ở site Primary chính.
        - Commit giao dịch và gửi lệnh xóa đồng bộ sang các site con ngay lập tức.
        """
        CourseService._ensure_admin(current_user)
        primary_session = CourseService._open_primary_session()

        try:
            course_code = ma_hoc_phan.upper()
            existing = CourseRepo.get_by_id(primary_session, course_code)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay hoc phan voi ma: {course_code}",
                )

            # Ghi sự kiện DELETE vào Outbox trước khi xóa thực tế ở Primary
            events = ReplicationService.stage_course_delete(primary_session, course_code)
            primary_session.delete(existing)
            primary_session.commit()

            # Đồng bộ hóa lệnh xóa sang các site Replica
            replication = CourseService._dispatch_replication(events)
            return {
                "course_code": course_code,
                "replication": replication,
            }
        except Exception as e:
            primary_session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Primary delete failed: {str(e)}",
            )
        finally:
            primary_session.close()

    @staticmethod
    def get_replication_status() -> dict[str, Any]:
        """
        Lấy báo cáo tổng hợp trạng thái đồng bộ dữ liệu học phần hiện hành.
        Thực hiện quét/cập nhật trạng thái sống của các site trước khi xuất dữ liệu.
        """
        ReplicationService.refresh_site_statuses()
        return ReplicationService.get_replication_status()

    @staticmethod
    def run_replication_recovery(target_site: str | None = None) -> dict[str, Any]:
        """
        Kích hoạt thủ công tiến trình đồng bộ phục hồi dữ liệu từ hàng đợi Outbox.
        Thường gọi khi có yêu cầu phục hồi đồng bộ khẩn cấp tới một site cụ thể (target_site).
        """
        if target_site:
            ReplicationService.refresh_site_statuses()
        return ReplicationService.dispatch_outbox_events(target_site=target_site)

    @staticmethod
    def _dispatch_replication(events: list[Any]) -> dict[str, Any]:
        """
        [Hàm nội bộ] Gọi hàm đồng bộ hóa outbox của ReplicationService cho danh sách sự kiện chỉ định.
        Nếu gặp sự cố kết nối, hàm sẽ tự động bắt lỗi và báo cáo là đang 'pending' để không làm đổ vỡ
        transaction ghi ở Primary đã commit trước đó.
        """
        event_ids = [event.EventId for event in events]
        try:
            return ReplicationService.dispatch_outbox_events(event_ids=event_ids)
        except Exception as exc:
            return {
                "primary_site": FailoverService.get_current_primary_site(auto_failover=False),
                "attempted": len(event_ids),
                "delivered": 0,
                "pending": len(event_ids),
                "failed": 0,
                "events": [],
                "error": str(exc),
            }

    @staticmethod
    def _open_primary_session() -> Session:
        """
        [Hàm nội bộ] Mở Session database kết nối tới site Primary hiện tại qua FailoverService.
        """
        return FailoverService.open_primary_session(auto_failover=True)

    @staticmethod
    def _ensure_admin(current_user: User) -> None:
        """
        [Hàm nội bộ] Ràng buộc quyền: Đảm bảo người dùng hiện tại phải có vai trò Admin.
        Nếu không phải Admin, chặn và ném ra lỗi HTTP 403 Forbidden.
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can manage courses",
            )

    @staticmethod
    def _ensure_department_exists(db: Session, ma_khoa: str) -> None:
        """
        [Hàm nội bộ] Xác thực xem mã khoa quản lý môn học có tồn tại trong database hay không.
        Nếu không tồn tại, báo lỗi yêu cầu truyền mã khoa hợp lệ.
        """
        department = db.query(Departments).filter(Departments.MaKhoa == ma_khoa).first()
        if not department:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"MaKhoa khong hop le: {ma_khoa}",
            )

    @staticmethod
    def _validate_course_payload(
        so_tin_chi: int,
        so_tiet_ly_thuyet: int,
        so_tiet_thuc_hanh: int,
        loai_hoc_phan: CourseType,
    ) -> None:
        """
        [Hàm nội bộ] Xác thực các ràng buộc nghiệp vụ của học phần:
        - Số tín chỉ phải lớn hơn 0.
        - Phải có ít nhất số tiết lý thuyết hoặc thực hành lớn hơn 0.
        - Loại học phần phải thuộc enum hợp lệ.
        """
        if so_tiet_ly_thuyet == 0 and so_tiet_thuc_hanh == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hoc phan phai co it nhat mot loai so tiet",
            )
        if so_tin_chi <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="So tin chi phai lon hon 0",
            )
        if not isinstance(loai_hoc_phan, CourseType):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"LoaiHocPhan khong hop le. Phai la {[e.value for e in CourseType]}",
            )
