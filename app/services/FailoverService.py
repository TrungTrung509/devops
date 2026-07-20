import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from configs.sites import COMMON_WRITE_SITE, get_all_sites


class FailoverService:
    # Site ghi chính mặc định ban đầu (thường là HADONG)
    DEFAULT_PRIMARY_SITE = COMMON_WRITE_SITE.upper()
    
    # Thư mục và đường dẫn file lưu trữ trạng thái failover dưới ổ cứng
    STATE_DIR = Path(__file__).resolve().parents[1] / ".runtime"
    STATE_FILE = STATE_DIR / "failover_state.json"
    
    # Khóa Lock dùng để đồng bộ hóa luồng (thread-safety), tránh xung đột khi đọc/ghi file trạng thái
    _LOCK = Lock()

    @staticmethod
    def get_state() -> dict[str, Any]:
        """
        Lấy trạng thái failover hiện tại từ file lưu trữ JSON.
        Hàm này sử dụng cơ chế khóa Lock để tránh việc nhiều request cùng ghi file một lúc gây lỗi.
        """
        with FailoverService._LOCK:
            state = FailoverService._load_state_unlocked()
            FailoverService._save_state_unlocked(state)
            return state

    @staticmethod
    def get_current_primary_site(auto_failover: bool = True) -> str:
        """
        Lấy ID của site đóng vai trò Primary (site ghi chính) hiện tại.
        Nếu site Primary được lưu trong file trạng thái bị chết (Offline):
        - Nếu bật auto_failover: Tự động gọi cơ chế bầu chọn để tìm site Primary mới còn hoạt động.
        - Nếu tắt auto_failover: Vẫn trả về site cũ hoặc site mặc định.
        """
        state = FailoverService.get_state()
        current = FailoverService._normalize_site(state.get("current_primary_site"))
        
        # Nếu site Primary hiện tại vẫn đang hoạt động tốt, trả về nó
        if current and FailoverService.is_site_alive(current):
            return current
            
        # Nếu site Primary hiện tại chết và bật chế độ tự động failover
        if auto_failover and state.get("auto_failover_enabled", True):
            return FailoverService.trigger_auto_failover(
                reason=f"Primary site '{current or FailoverService.DEFAULT_PRIMARY_SITE}' is unavailable"
            )["current_primary_site"]
            
        if current:
            return current
        return FailoverService.DEFAULT_PRIMARY_SITE

    @staticmethod
    def open_primary_session(auto_failover: bool = True) -> Session:
        """
        Mở kết nối database (SQLAlchemy Session) trực tiếp đến site Primary hiện hành.
        Hàm này được dùng khi backend cần thực hiện các thao tác Ghi (INSERT, UPDATE, DELETE).
        """
        primary_site = FailoverService.get_current_primary_site(auto_failover=auto_failover)
        return SessionLocals[primary_site]()

    @staticmethod
    def resolve_read_site(
        preferred_site: Optional[str] = None,
        *,
        auto_failover: bool = True,
    ) -> str:
        """
        Quyết định site nào sẽ phục vụ truy vấn Đọc dữ liệu (Read redirection).
        Thứ tự ưu tiên xử lý:
        1. Ưu tiên site mong muốn của người dùng (ví dụ: site cục bộ của sinh viên).
        2. Nếu site cục bộ chết, chuyển sang site Primary hiện tại.
        3. Nếu site Primary cũng chết, quét toàn bộ các site còn lại và kết nối tới site đầu tiên còn sống.
        4. Nếu không còn site nào sống, ném ra lỗi hệ thống (HTTP 503).
        """
        site = FailoverService._normalize_site(preferred_site)
        # 1. Đọc ở site mong muốn nếu nó còn sống (Local Read)
        if site and FailoverService.is_site_alive(site):
            return site

        # 2. Nếu sập, thử đọc ở site Primary chính
        primary_site = FailoverService.get_current_primary_site(auto_failover=auto_failover)
        if FailoverService.is_site_alive(primary_site):
            return primary_site

        # 3. Nếu sập nốt, tìm bất kỳ site nào còn hoạt động để đọc dự phòng
        for candidate in FailoverService.get_alive_sites():
            return candidate

        # 4. Trường hợp xấu nhất: Tất cả database của tất cả các site đều sập
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong con site nao kha dung",
        )

    @staticmethod
    def open_read_session(
        preferred_site: Optional[str] = None,
        *,
        auto_failover: bool = True,
    ) -> Session:
        """
        Mở kết nối database (SQLAlchemy Session) tới site được chỉ định để thực hiện truy vấn đọc.
        Có áp dụng logic tự động chuyển hướng đọc nếu site được chỉ định bị chết.
        """
        resolved_site = FailoverService.resolve_read_site(
            preferred_site=preferred_site,
            auto_failover=auto_failover,
        )
        return SessionLocals[resolved_site]()

    @staticmethod
    def get_alive_sites(exclude_site: Optional[str] = None) -> list[str]:
        """
        Quét qua toàn bộ các site trong hệ thống và trả về danh sách các site đang Online.
        Cho phép loại trừ một site cụ thể ra khỏi danh sách kiểm tra (exclude_site).
        """
        excluded = FailoverService._normalize_site(exclude_site)
        alive_sites = []
        for site_id in SessionLocals:
            if excluded and site_id == excluded:
                continue
            if FailoverService.is_site_alive(site_id):
                alive_sites.append(site_id)
        return alive_sites

    @staticmethod
    def is_site_alive(site_id: str) -> bool:
        """
        Kiểm tra sức khỏe (Ping) của một site cụ thể xem còn sống (Online) hay đã chết (Offline).
        Thực hiện bằng cách thử mở kết nối và chạy câu lệnh SQL siêu nhẹ 'SELECT 1'.
        """
        normalized = FailoverService._normalize_site(site_id)
        if not normalized:
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
    def manual_failover(target_site: str, reason: Optional[str] = None) -> dict[str, Any]:
        """
        Cho phép Quản trị viên (Admin) chủ động chuyển đổi site ghi chính (Primary) sang site khác thủ công.
        Thường dùng khi chuẩn bị bảo trì nâng cấp hệ thống ở site cũ.
        Yêu cầu site được chọn làm Primary mới phải đang hoạt động bình thường (Online).
        """
        normalized = FailoverService._normalize_site(target_site)
        if normalized is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Site khong hop le: {target_site}",
            )
        if not FailoverService.is_site_alive(normalized):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Khong the promote site '{normalized}' vi site nay dang offline",
            )

        with FailoverService._LOCK:
            state = FailoverService._load_state_unlocked()
            previous = FailoverService._normalize_site(state.get("current_primary_site"))
            
            # Ghi nhận thông tin chuyển đổi thủ công
            state["current_primary_site"] = normalized
            state["last_failover_mode"] = "manual"
            state["last_failover_reason"] = reason or f"Manual failover to {normalized}"
            state["previous_primary_site"] = previous
            state["last_failover_at"] = datetime.utcnow().isoformat()
            
            FailoverService._save_state_unlocked(state)
            return FailoverService._build_status_payload(state)

    @staticmethod
    def trigger_auto_failover(reason: Optional[str] = None) -> dict[str, Any]:
        """
        Cơ chế bầu chọn Primary tự động (Auto Failover).
        Được gọi tự động khi phát hiện Primary cũ bị sập. Hàm này sẽ duyệt qua danh sách các site
        bản sao theo thứ tự ưu tiên, kiểm tra site nào còn sống và nâng cấp nó lên làm Primary mới.
        Nếu không có bất kỳ site nào còn sống, hệ thống sẽ báo lỗi không thể hoạt động.
        """
        with FailoverService._LOCK:
            state = FailoverService._load_state_unlocked()
            current = FailoverService._normalize_site(state.get("current_primary_site"))
            
            # Nếu site Primary cũ đột nhiên sống lại khi đang chuẩn bị failover, giữ nguyên trạng thái
            if current and FailoverService.is_site_alive(current):
                return FailoverService._build_status_payload(state)

            # Quét tìm ứng viên mới thay thế
            for candidate in FailoverService._site_order():
                if candidate == current:
                    continue
                if FailoverService.is_site_alive(candidate):
                    # Tiến hành nâng cấp ứng viên còn sống làm Primary mới
                    state["current_primary_site"] = candidate
                    state["previous_primary_site"] = current
                    state["last_failover_mode"] = "auto"
                    state["last_failover_reason"] = (
                        reason or f"Auto failover promoted {candidate}"
                    )
                    state["last_failover_at"] = datetime.utcnow().isoformat()
                    FailoverService._save_state_unlocked(state)
                    return FailoverService._build_status_payload(state)

        # Trường hợp xấu nhất: Không có site nào sống để bầu lên làm Primary
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Khong tim thay site song de auto failover",
        )

    @staticmethod
    def set_auto_failover(enabled: bool) -> dict[str, Any]:
        """
        Bật hoặc tắt chức năng tự động chuyển vùng dự phòng (Auto Failover).
        """
        with FailoverService._LOCK:
            state = FailoverService._load_state_unlocked()
            state["auto_failover_enabled"] = enabled
            FailoverService._save_state_unlocked(state)
            return FailoverService._build_status_payload(state)

    @staticmethod
    def get_failover_status() -> dict[str, Any]:
        """
        Lấy báo cáo tổng hợp về trạng thái failover hiện tại.
        Trả về: Site chính hiện tại là ai, lịch sử failover, và danh sách trạng thái Online/Offline của từng site.
        """
        state = FailoverService.get_state()
        payload = FailoverService._build_status_payload(state)
        payload["sites"] = [
            {
                "site_id": site_id,
                "is_alive": FailoverService.is_site_alive(site_id),
                "role": "PRIMARY" if site_id == payload["current_primary_site"] else "REPLICA",
            }
            for site_id in FailoverService._site_order()
        ]
        return payload

    @staticmethod
    def _default_state() -> dict[str, Any]:
        """
        Khởi tạo trạng thái failover mặc định ban đầu cho hệ thống.
        """
        return {
            "current_primary_site": FailoverService.DEFAULT_PRIMARY_SITE,
            "previous_primary_site": None,
            "last_failover_mode": "default",
            "last_failover_reason": None,
            "last_failover_at": None,
            "auto_failover_enabled": True,
        }

    @staticmethod
    def _load_state_unlocked() -> dict[str, Any]:
        """
        Đọc nội dung file JSON lưu trạng thái failover dưới ổ cứng lên bộ nhớ RAM.
        Nếu file chưa tồn tại hoặc bị lỗi cấu trúc, trả về cấu hình mặc định.
        """
        FailoverService.STATE_DIR.mkdir(parents=True, exist_ok=True)
        if not FailoverService.STATE_FILE.exists():
            return FailoverService._default_state()

        try:
            data = json.loads(FailoverService.STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return FailoverService._default_state()

        state = FailoverService._default_state()
        state.update(data)
        state["current_primary_site"] = FailoverService._normalize_site(state.get("current_primary_site")) or FailoverService.DEFAULT_PRIMARY_SITE
        state["previous_primary_site"] = FailoverService._normalize_site(state.get("previous_primary_site"))
        state["auto_failover_enabled"] = bool(state.get("auto_failover_enabled", True))
        return state

    @staticmethod
    def _save_state_unlocked(state: dict[str, Any]) -> None:
        """
        Lưu đè trạng thái failover mới từ bộ nhớ RAM xuống file JSON dưới ổ cứng.
        """
        FailoverService.STATE_DIR.mkdir(parents=True, exist_ok=True)
        FailoverService.STATE_FILE.write_text(
            json.dumps(state, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _build_status_payload(state: dict[str, Any]) -> dict[str, Any]:
        """
        Lọc cấu trúc dữ liệu thô để tạo thành payload phản hồi chuẩn cho API.
        """
        return {
            "current_primary_site": FailoverService._normalize_site(state.get("current_primary_site")),
            "previous_primary_site": FailoverService._normalize_site(state.get("previous_primary_site")),
            "last_failover_mode": state.get("last_failover_mode"),
            "last_failover_reason": state.get("last_failover_reason"),
            "last_failover_at": state.get("last_failover_at"),
            "auto_failover_enabled": bool(state.get("auto_failover_enabled", True)),
        }

    @staticmethod
    def _normalize_site(site_id: Optional[str]) -> Optional[str]:
        """
        Chuẩn hóa tên site (viết hoa) và xác minh xem site này có tồn tại
        trong danh sách kết nối database của hệ thống hay không.
        """
        if not site_id:
            return None
        candidate = str(site_id).upper()
        return candidate if candidate in SessionLocals else None

    @staticmethod
    def _site_order() -> list[str]:
        """
        Trả về danh sách các site được sắp xếp theo thứ tự ưu tiên bầu chọn.
        """
        ordered = []
        for site_id in get_all_sites().keys():
            normalized = FailoverService._normalize_site(site_id)
            if normalized is not None and normalized not in ordered:
                ordered.append(normalized)
        for site_id in SessionLocals:
            if site_id not in ordered:
                ordered.append(site_id)
        return ordered
