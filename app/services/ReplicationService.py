import json
from datetime import datetime
from typing import Any, Iterable, Optional

from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.status import CourseStatus
from enums.types import CourseType
from models.Courses import Course
from models.ReplicationOutbox import ReplicationOutbox
from models.SiteStatus import SiteStatus
from repositories.CourseRepo import CourseRepo
from services.FailoverService import FailoverService


class ReplicationService:
    """
    Service quản lý Đồng bộ hóa Dữ liệu (Replication).
    Thực hiện lưu vết thay đổi dữ liệu học phần vào hàng đợi (Outbox),
    điều phối đẩy dữ liệu sang các site con, tự động phát hiện trạng thái site (Online/Offline)
    và đồng bộ phục hồi dữ liệu khi có site sống lại.
    """
    
    ENTITY_COURSE = "Course"
    OP_UPSERT = "UPSERT"
    OP_DELETE = "DELETE"
    STATUS_PENDING = "PENDING"
    STATUS_DONE = "DONE"
    STATUS_FAILED = "FAILED"
    STATUS_ONLINE = "ONLINE"
    STATUS_OFFLINE = "OFFLINE"
    STATUS_ERROR = "ERROR"
    STATUS_UNKNOWN = "UNKNOWN"

    @staticmethod
    def stage_course_upsert(primary_db: Session, course: Course) -> list[ReplicationOutbox]:
        """
        Đưa sự kiện thêm mới hoặc cập nhật học phần vào hàng đợi Outbox.
        Hàm này tuần tự hóa môn học thành payload JSON và tạo bản ghi lưu vào DB.
        """
        payload = ReplicationService._course_to_payload(course)
        return ReplicationService._stage_events(
            primary_db=primary_db,
            entity_type=ReplicationService.ENTITY_COURSE,
            entity_id=course.MaHocPhan,
            operation=ReplicationService.OP_UPSERT,
            payload=payload,
        )

    @staticmethod
    def stage_course_delete(primary_db: Session, course_code: str) -> list[ReplicationOutbox]:
        """
        Đưa sự kiện xóa học phần vào hàng đợi Outbox.
        """
        return ReplicationService._stage_events(
            primary_db=primary_db,
            entity_type=ReplicationService.ENTITY_COURSE,
            entity_id=course_code,
            operation=ReplicationService.OP_DELETE,
            payload={"MaHocPhan": course_code},
        )

    @staticmethod
    def dispatch_outbox_events(
        event_ids: Optional[Iterable[int]] = None,
        target_site: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Quét hàng đợi Outbox và đồng bộ hóa các sự kiện tồn đọng sang các site Replica.
        - Tìm các sự kiện có trạng thái PENDING hoặc FAILED ở site Primary hiện tại.
        - Có thể lọc cụ thể theo danh sách ID sự kiện (event_ids) hoặc site đích (target_site).
        - Tiến hành gửi từng sự kiện và trả về báo cáo tổng hợp.
        """
        primary_site = FailoverService.get_current_primary_site(auto_failover=True)
        primary_db = SessionLocals[primary_site]()
        try:
            ReplicationService._ensure_site_rows(primary_db)
            
            # Lọc các sự kiện chưa hoàn thành (PENDING hoặc FAILED)
            query = primary_db.query(ReplicationOutbox).filter(
                ReplicationOutbox.Status.in_(
                    [ReplicationService.STATUS_PENDING, ReplicationService.STATUS_FAILED]
                )
            )
            if event_ids:
                query = query.filter(ReplicationOutbox.EventId.in_(list(event_ids)))
            if target_site:
                query = query.filter(ReplicationOutbox.TargetSite == target_site.upper())

            # Sắp xếp theo thứ tự thời gian tạo tăng dần (FIFO - First In First Out) để đảm bảo tính tuần tự
            events = query.order_by(
                ReplicationOutbox.CreatedAt.asc(),
                ReplicationOutbox.EventId.asc(),
            ).all()
            
            summary = {
                "primary_site": primary_site,
                "attempted": len(events),
                "delivered": 0,
                "pending": 0,
                "failed": 0,
                "events": [],
            }

            # Gửi từng sự kiện đồng bộ
            for event in events:
                result = ReplicationService._dispatch_single_event(primary_db, event)
                primary_db.commit() # Commit trạng thái mới của sự kiện (DONE/PENDING/FAILED) vào Primary
                summary["events"].append(result)
                if result["status"] == ReplicationService.STATUS_DONE:
                    summary["delivered"] += 1
                elif result["status"] == ReplicationService.STATUS_PENDING:
                    summary["pending"] += 1
                else:
                    summary["failed"] += 1

            return summary
        finally:
            primary_db.close()

    @staticmethod
    def refresh_site_statuses() -> list[dict[str, Any]]:
        """
        Cập nhật trạng thái hoạt động thực tế (ONLINE/OFFLINE) của tất cả các site DB.
        Bằng cách ping thử từng site (ngoại trừ site Primary chính được coi là ONLINE).
        Lưu thông tin sức khỏe và nhịp tim (heartbeat) vào bảng SiteStatus của Primary.
        """
        primary_site = FailoverService.get_current_primary_site(auto_failover=True)
        primary_db = SessionLocals[primary_site]()
        try:
            ReplicationService._ensure_site_rows(primary_db)
            now = datetime.utcnow()
            for site_id in SessionLocals:
                if site_id == primary_site:
                    # Site Primary mặc định coi là ONLINE
                    ReplicationService._update_site_row(
                        primary_db,
                        site_id,
                        status=ReplicationService.STATUS_ONLINE,
                        heartbeat=now,
                        success_at=now,
                        error=None,
                    )
                    continue

                # Thử ping site con
                available, error = ReplicationService._ping_site(site_id)
                ReplicationService._update_site_row(
                    primary_db,
                    site_id,
                    status=(
                        ReplicationService.STATUS_ONLINE
                        if available
                        else ReplicationService.STATUS_OFFLINE
                    ),
                    heartbeat=now,
                    success_at=now if available else None,
                    error=error,
                )

            primary_db.commit()
            return ReplicationService._serialize_site_rows(primary_db)
        finally:
            primary_db.close()

    @staticmethod
    def get_replication_status() -> dict[str, Any]:
        """
        Lấy báo cáo chi tiết về tình trạng đồng bộ.
        Bao gồm: trạng thái các site, số lượng sự kiện Outbox theo từng trạng thái, và danh sách 20 sự kiện đang chờ xử lý gần nhất.
        """
        primary_site = FailoverService.get_current_primary_site(auto_failover=True)
        primary_db = SessionLocals[primary_site]()
        try:
            ReplicationService._ensure_site_rows(primary_db)
            primary_db.commit()
            
            # Thống kê số bản ghi Outbox theo từng trạng thái (DONE/PENDING/FAILED)
            outbox_counts = {
                row.Status: row.count
                for row in primary_db.query(
                    ReplicationOutbox.Status,
                    func.count(ReplicationOutbox.EventId).label("count"),
                )
                .group_by(ReplicationOutbox.Status)
                .all()
            }
            # Lấy danh sách 20 sự kiện đang bị nghẽn
            pending_events = (
                primary_db.query(ReplicationOutbox)
                .filter(
                    ReplicationOutbox.Status.in_(
                        [ReplicationService.STATUS_PENDING, ReplicationService.STATUS_FAILED]
                    )
                )
                .order_by(
                    ReplicationOutbox.CreatedAt.asc(),
                    ReplicationOutbox.EventId.asc(),
                )
                .limit(20)
                .all()
            )
            return {
                "primary_site": primary_site,
                "sites": ReplicationService._serialize_site_rows(primary_db),
                "outbox": {
                    "counts": outbox_counts,
                    "pending_events": [
                        {
                            "event_id": event.EventId,
                            "entity_type": event.EntityType,
                            "entity_id": event.EntityId,
                            "operation": event.Operation,
                            "target_site": event.TargetSite,
                            "status": event.Status,
                            "retry_count": event.RetryCount,
                            "last_error": event.LastError,
                            "created_at": event.CreatedAt,
                        }
                        for event in pending_events
                    ],
                },
            }
        finally:
            primary_db.close()

    @staticmethod
    def _stage_events(
        primary_db: Session,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: dict[str, Any],
    ) -> list[ReplicationOutbox]:
        """
        [Hàm nội bộ] Thực hiện tạo các dòng sự kiện trong hàng đợi Outbox hướng tới từng site replica con.
        """
        ReplicationService._ensure_site_rows(primary_db)
        events = []
        payload_json = json.dumps(jsonable_encoder(payload), ensure_ascii=False)
        primary_site = FailoverService.get_current_primary_site(auto_failover=True)

        # Duyệt qua tất cả các site bản sao còn lại để tạo bản ghi đồng bộ tương ứng
        for target_site in ReplicationService._replica_sites(primary_site):
            event = ReplicationOutbox(
                EntityType=entity_type,
                EntityId=entity_id,
                Operation=operation,
                Payload=payload_json,
                SourceSite=primary_site,
                TargetSite=target_site,
                Status=ReplicationService.STATUS_PENDING,
            )
            primary_db.add(event)
            events.append(event)

        # Cập nhật thông số nhịp tim của Primary
        ReplicationService._update_site_row(
            primary_db,
            primary_site,
            status=ReplicationService.STATUS_ONLINE,
            heartbeat=datetime.utcnow(),
            success_at=datetime.utcnow(),
            error=None,
        )
        return events

    @staticmethod
    def _dispatch_single_event(primary_db: Session, event: ReplicationOutbox) -> dict[str, Any]:
        """
        [Hàm nội bộ] Thực hiện gửi một sự kiện Outbox cụ thể sang site đích chỉ định.
        Hàm này xử lý lỗi kết nối DB rất chi tiết:
        - Nếu site đích bị sập (lỗi kết nối vật lý OperationalError): Đặt lại trạng thái PENDING,
          tăng số lần thử lại (RetryCount), đánh dấu site đích OFFLINE.
        - Nếu site đích bị lỗi dữ liệu hoặc SQL khác: Đặt trạng thái FAILED, ghi nhận lỗi, đánh dấu site đích ERROR.
        - Nếu thành công: Đồng bộ dữ liệu học phần, đặt trạng thái DONE, đánh dấu site đích ONLINE.
        """
        target_site = event.TargetSite.upper()
        target_db = SessionLocals[target_site]()
        try:
            # Ping thử site đích
            target_db.execute(text("SELECT 1"))
            payload = json.loads(event.Payload)
            
            # Đồng bộ dữ liệu học phần sang database đích
            ReplicationService._apply_event(target_db, event, payload)
            target_db.commit() # Xác nhận lưu trữ ở site đích

            # Đánh dấu sự kiện đã đồng bộ xong
            event.Status = ReplicationService.STATUS_DONE
            event.LastError = None
            event.ProcessedAt = datetime.utcnow()
            
            # Ghi nhận site đích hoạt động tốt
            ReplicationService._update_site_row(
                primary_db,
                target_site,
                status=ReplicationService.STATUS_ONLINE,
                heartbeat=datetime.utcnow(),
                success_at=datetime.utcnow(),
                error=None,
            )
            return {
                "event_id": event.EventId,
                "target_site": target_site,
                "status": ReplicationService.STATUS_DONE,
            }
        except OperationalError as exc:
            # Lỗi mất kết nối mạng vật lý tới site đích
            target_db.rollback()
            event.Status = ReplicationService.STATUS_PENDING
            event.RetryCount += 1
            event.LastError = ReplicationService._truncate_error(exc)
            
            # Ghi nhận site đích đã sập để hệ thống failover biết đường tránh
            ReplicationService._update_site_row(
                primary_db,
                target_site,
                status=ReplicationService.STATUS_OFFLINE,
                heartbeat=datetime.utcnow(),
                error=event.LastError,
            )
            return {
                "event_id": event.EventId,
                "target_site": target_site,
                "status": ReplicationService.STATUS_PENDING,
                "error": event.LastError,
            }
        except (SQLAlchemyError, ValueError, KeyError, json.JSONDecodeError) as exc:
            # Lỗi nghiệp vụ SQL hoặc lỗi định dạng dữ liệu JSON không đồng bộ được
            target_db.rollback()
            event.Status = ReplicationService.STATUS_FAILED
            event.RetryCount += 1
            event.LastError = ReplicationService._truncate_error(exc)
            
            # Ghi nhận site đích bị lỗi dữ liệu
            ReplicationService._update_site_row(
                primary_db,
                target_site,
                status=ReplicationService.STATUS_ERROR,
                heartbeat=datetime.utcnow(),
                error=event.LastError,
            )
            return {
                "event_id": event.EventId,
                "target_site": target_site,
                "status": ReplicationService.STATUS_FAILED,
                "error": event.LastError,
            }
        finally:
            target_db.close()

    @staticmethod
    def _apply_event(target_db: Session, event: ReplicationOutbox, payload: dict[str, Any]) -> None:
        """
        [Hàm nội bộ] Thực thi câu lệnh ghi dữ liệu vật lý (UPSERT hoặc DELETE) trên Database của site con.
        Đảm bảo cấu trúc dữ liệu ở site con khớp hoàn toàn với dữ liệu ở Primary.
        """
        if event.EntityType != ReplicationService.ENTITY_COURSE:
            raise ValueError(f"Unsupported entity type: {event.EntityType}")

        course_code = event.EntityId.upper()
        course = CourseRepo.get_by_id(target_db, course_code)

        # 1. Thao tác xóa môn học
        if event.Operation == ReplicationService.OP_DELETE:
            if course:
                target_db.delete(course)
            return

        if event.Operation != ReplicationService.OP_UPSERT:
            raise ValueError(f"Unsupported operation: {event.Operation}")

        # Chuẩn hóa dữ liệu học phần
        mapped_data = {
            "MaHocPhan": course_code,
            "TenHocPhan": payload["TenHocPhan"],
            "SoTinChi": payload["SoTinChi"],
            "SoTietLyThuyet": payload["SoTietLyThuyet"],
            "SoTietThucHanh": payload["SoTietThucHanh"],
            "LoaiHocPhan": CourseType(payload["LoaiHocPhan"]),
            "MaKhoa": payload["MaKhoa"],
            "MoTa": payload.get("MoTa"),
            "TrangThai": CourseStatus(payload["TrangThai"]),
            "NgayTao": datetime.fromisoformat(payload["NgayTao"]),
        }

        # 2. Thao tác chèn mới môn học
        if course is None:
            target_db.add(Course(**mapped_data))
            return

        # 3. Thao tác cập nhật môn học
        for field, value in mapped_data.items():
            setattr(course, field, value)

    @staticmethod
    def _course_to_payload(course: Course) -> dict[str, Any]:
        """
        [Hàm nội bộ] Tuần tự hóa đối tượng môn học sang Dictionary thô để lưu thành JSON Payload.
        """
        return {
            "MaHocPhan": course.MaHocPhan,
            "TenHocPhan": course.TenHocPhan,
            "SoTinChi": course.SoTinChi,
            "SoTietLyThuyet": course.SoTietLyThuyet,
            "SoTietThucHanh": course.SoTietThucHanh,
            "LoaiHocPhan": course.LoaiHocPhan.value,
            "MaKhoa": course.MaKhoa,
            "MoTa": course.MoTa,
            "TrangThai": course.TrangThai.value,
            "NgayTao": course.NgayTao.isoformat(),
        }

    @staticmethod
    def _ping_site(site_id: str) -> tuple[bool, Optional[str]]:
        """
        [Hàm nội bộ] Gửi lệnh ping SELECT 1 thử tới một site để kiểm tra kết nối DB.
        """
        session = SessionLocals[site_id]()
        try:
            session.execute(text("SELECT 1"))
            return True, None
        except OperationalError as exc:
            session.rollback()
            return False, ReplicationService._truncate_error(exc)
        finally:
            session.close()

    @staticmethod
    def _ensure_site_rows(primary_db: Session) -> None:
        """
        [Hàm nội bộ] Đảm bảo trong bảng SiteStatus có đầy đủ dòng đại diện cho 3 cơ sở dữ liệu.
        Nếu thiếu, hàm sẽ tự động chèn dòng mới với trạng thái mặc định UNKNOWN.
        """
        current_primary = FailoverService.get_current_primary_site(auto_failover=True)
        existing = {
            row.SiteId: row
            for row in primary_db.query(SiteStatus)
            .filter(SiteStatus.SiteId.in_(list(SessionLocals.keys())))
            .all()
        }

        for site_id in SessionLocals:
            if site_id in existing:
                continue
            primary_db.add(
                SiteStatus(
                    SiteId=site_id,
                    Role=("PRIMARY" if site_id == current_primary else "REPLICA"),
                    Status=(
                        ReplicationService.STATUS_ONLINE
                        if site_id == current_primary
                        else ReplicationService.STATUS_UNKNOWN
                    ),
                )
            )

        primary_db.flush()

    @staticmethod
    def _update_site_row(
        primary_db: Session,
        site_id: str,
        *,
        status: str,
        heartbeat: Optional[datetime] = None,
        success_at: Optional[datetime] = None,
        error: Optional[str] = None,
    ) -> None:
        """
        [Hàm nội bộ] Cập nhật thông số sức khỏe của một site trong bảng SiteStatus ở Primary.
        """
        current_primary = FailoverService.get_current_primary_site(auto_failover=True)
        row = primary_db.query(SiteStatus).filter(SiteStatus.SiteId == site_id).first()
        if row is None:
            row = SiteStatus(
                SiteId=site_id,
                Role=("PRIMARY" if site_id == current_primary else "REPLICA"),
            )
            primary_db.add(row)

        row.Role = "PRIMARY" if site_id == current_primary else "REPLICA"
        row.Status = status
        row.LastHeartbeat = heartbeat or datetime.utcnow()
        if success_at is not None:
            row.LastSuccessAt = success_at
        row.LastError = error

    @staticmethod
    def _serialize_site_rows(primary_db: Session) -> list[dict[str, Any]]:
        """
        [Hàm nội bộ] Chuyển đổi dữ liệu các dòng SiteStatus thành danh sách Dictionary thô để làm payload trả về.
        """
        return [
            {
                "site_id": row.SiteId,
                "role": row.Role,
                "status": row.Status,
                "last_heartbeat": row.LastHeartbeat,
                "last_success_at": row.LastSuccessAt,
                "last_error": row.LastError,
                "updated_at": row.UpdatedAt,
            }
            for row in primary_db.query(SiteStatus).order_by(SiteStatus.SiteId.asc()).all()
        ]

    @staticmethod
    def _replica_sites(primary_site: str) -> list[str]:
        """
        [Hàm nội bộ] Trả về danh sách các site con (Replica), loại trừ site chính (Primary).
        """
        return [site for site in SessionLocals if site != primary_site]

    @staticmethod
    def _truncate_error(exc: Exception) -> str:
        """
        [Hàm nội bộ] Rút gọn nội dung thông báo ngoại lệ lỗi (Exception) tối đa 500 ký tự để lưu vào cột LastError.
        """
        return str(exc)[:500]
