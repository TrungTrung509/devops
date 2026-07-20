import hashlib

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from configs.db import SessionLocals, engines

from .context import Enrollment3PCContext


class Enrollment3PCDB:
    """
    Module hỗ trợ Cơ sở dữ liệu cho 3PC (Enrollment3PCDB).
    Chịu trách nhiệm quản lý kết nối đồng thời đến nhiều site DB,
    ping kiểm tra kết nối, ghim kết nối (pinned sessions),
    và quản lý khóa Advisory Lock phân tán của PostgreSQL.
    """

    @staticmethod
    def normalize_site(site: str | None) -> str:
        """
        [Hàm bổ trợ] Chuẩn hóa tên viết hoa của site DB (ví dụ: 'hadong' -> 'HADONG').
        """
        return (site or "").upper()

    @staticmethod
    def is_site_alive(site: str) -> bool:
        """
        [Hàm bổ trợ] Ping thử tới một site DB cụ thể (bằng cách chạy lệnh SELECT 1 nhanh)
        để kiểm tra xem site đó còn hoạt động (Online) hay đã sập (Offline).
        """
        normalized = Enrollment3PCDB.normalize_site(site)
        if normalized not in SessionLocals:
            return False

        session = SessionLocals[normalized]()
        try:
            session.execute(text("SELECT 1"))
            return True
        except OperationalError:
            session.rollback()
            return False
        finally:
            session.close()

    @staticmethod
    def ensure_sites_alive(sites, detail: str) -> None:
        """
        [Hàm bổ trợ] Đảm bảo danh sách các site được chỉ định đều đang hoạt động tốt (Online).
        Nếu phát hiện có site sập, ném ra lỗi HTTP 503 để ngắt giao dịch 3PC ngay lập tức.
        """
        normalized_sites = {
            Enrollment3PCDB.normalize_site(site)
            for site in sites
            if Enrollment3PCDB.normalize_site(site)
        }
        offline = [site for site in normalized_sites if not Enrollment3PCDB.is_site_alive(site)]
        if offline:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"{detail}: {', '.join(sorted(offline))}",
            )

    @staticmethod
    def open_pinned_sessions(sites) -> tuple[dict[str, Session], dict[str, object]]:
        """
        Mở và giữ cố định (ghim) kết nối database (Sessions & Connections) đến danh sách các site tham gia.
        Việc ghim này giúp duy trì trạng thái giao dịch phân tán thống nhất trong suốt quá trình chạy 3PC.
        """
        sessions: dict[str, Session] = {}
        connections: dict[str, object] = {}
        normalized_sites = {
            Enrollment3PCDB.normalize_site(site)
            for site in sites
            if Enrollment3PCDB.normalize_site(site) in engines
        }
        for site in normalized_sites:
            connection = engines[site].connect()
            session = SessionLocals[site](bind=connection)
            connections[site] = connection
            sessions[site] = session
        return sessions, connections

    @staticmethod
    def close_pinned_sessions(sessions: dict[str, Session], connections: dict[str, object]) -> None:
        """
        Đóng an toàn toàn bộ các Sessions và Connections DB đã ghim trước đó.
        Giải phóng các kết nối trả về cho connection pool.
        """
        for session in sessions.values():
            session.close()
        for connection in connections.values():
            connection.close()

    @staticmethod
    def current_site(session: Session) -> str:
        """
        [Hàm bổ trợ] Xác định xem SQLAlchemy Session hiện tại đang trỏ tới site DB nào
        bằng cách đối chiếu URL của engine liên kết.
        """
        url = str(session.get_bind().engine.url)
        for site, engine in engines.items():
            if str(engine.url) == url:
                return site
        raise RuntimeError("Khong xac dinh duoc site cua session")

    @staticmethod
    def acquire_locks(
        ctx: Enrollment3PCContext,
        sessions: dict[str, Session],
    ) -> list[tuple[str, int]]:
        """
        Xin cấp phát các khóa Advisory Lock phân tán (pg_try_advisory_lock) trên các site DB.
        Hàm này lặp qua danh sách khóa cần lấy (định nghĩa ở _lock_entries).
        - Nếu lấy thành công trên tất cả các site: Trả về danh sách khóa đã lấy.
        - Nếu bị trùng/chiếm khóa ở bất kỳ site nào: Tự động giải phóng các khóa đã xin trước đó
          và ném lỗi HTTP 409 Conflict yêu cầu sinh viên thử lại sau.
        """
        acquired: list[tuple[str, int]] = []
        for site, lock_key in Enrollment3PCDB._lock_entries(ctx):
            session = sessions.get(site)
            if session is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Không mở được session tại {site}",
                )

            # Thử lấy khóa phân tán thô trên PostgreSQL
            granted = session.execute(
                text("SELECT pg_try_advisory_lock(:lock_key)"),
                {"lock_key": lock_key},
            ).scalar()
            
            if not granted:
                # Nếu bị trùng lock, lập tức nhả các lock đã chiếm trước đó để tránh treo hệ thống
                Enrollment3PCDB.release_locks(sessions, acquired)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Tài nguyên đăng ký đã bị chiếm, vui lòng thử lại",
                )
            acquired.append((site, lock_key))
        return acquired

    @staticmethod
    def release_locks(sessions: dict[str, Session], acquired: list[tuple[str, int]]) -> None:
        """
        Giải phóng (nhả) các Advisory Lock đã xin trước đó trên PostgreSQL của các site tương ứng.
        Sử dụng thứ tự ngược lại (LIFO - Last In First Out) để giải phóng an toàn.
        """
        for site, lock_key in reversed(acquired):
            session = sessions.get(site)
            if session is None:
                continue
            try:
                session.execute(
                    text("SELECT pg_advisory_unlock(:lock_key)"),
                    {"lock_key": lock_key},
                )
            except Exception:
                session.rollback()

    @staticmethod
    def _lock_entries(ctx: Enrollment3PCContext) -> list[tuple[str, int]]:
        """
        [Hàm nội bộ] Sinh danh sách các thẻ khóa cần thiết cho giao dịch đăng ký/đổi lớp:
        1. Khóa theo Sinh viên (`user-semester`): Tránh tình trạng 1 SV bấm gửi nhiều request
           đăng ký trùng học kỳ cùng lúc trên các tab trình duyệt khác nhau.
        2. Khóa theo Lớp học phần mới (`section`): Tránh Lost Update khi nhiều SV cùng đăng ký vào chỗ cuối.
        3. Khóa theo Lớp học phần cũ (`section`): Dùng khi đổi lớp, khóa lớp cũ để trừ sĩ số an toàn.
        
        *Đặc điểm kỹ thuật:* Sắp xếp danh sách khóa theo thứ tự bảng chữ cái để phòng tránh hiện tượng
        khóa chéo (Deadlock) giữa các luồng giao dịch đồng thời.
        """
        entries: list[tuple[str, int]] = []

        # Tạo khóa theo phạm vi SV đăng ký trong học kỳ
        user_scope = f"user-semester:{ctx.user_id}:{ctx.target_ma_hoc_ky}"
        for site in ctx.lock_sites:
            entries.append((site, Enrollment3PCDB._lock_key(user_scope)))

        # Tạo khóa cho lớp học phần mới
        entries.append((
            ctx.site_new,
            Enrollment3PCDB._lock_key(f"section:{ctx.site_new}:{ctx.target_ma_lop_hp}"),
        ))
        
        # Tạo khóa cho lớp học phần cũ (nếu có thao tác đổi lớp)
        if ctx.site_old and ctx.old_ma_lop_hp:
            entries.append((
                ctx.site_old,
                Enrollment3PCDB._lock_key(f"section:{ctx.site_old}:{ctx.old_ma_lop_hp}"),
            ))

        # Sắp xếp các khóa để tránh Deadlock
        return sorted(set(entries), key=lambda item: (item[0], item[1]))

    @staticmethod
    def _lock_key(value: str) -> int:
        """
        [Hàm nội bộ] Chuyển đổi chuỗi logic của nhãn khóa thành mã băm (Hash) kiểu số nguyên 64-bit.
        Đáp ứng tham số kiểu số nguyên của hàm pg_try_advisory_lock của PostgreSQL.
        """
        digest = hashlib.sha256(value.encode("utf-8")).digest()
        return int.from_bytes(digest[:8], byteorder="big", signed=False) & 0x7FFFFFFFFFFFFFFF
