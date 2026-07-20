from functools import wraps
import time
import random
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import InternalError, OperationalError
from models.NhatKyThaoTac import NhatKyThaoTac
from enums.status import BuocGiaoTac, TrangThaiGiaoTac
from configs.db import get_log_session

def _site_of(ma_lop_hp: str) -> str:
    """Giải mã tên site từ MaLopHP. Ví dụ: 'HADONG_CS001' → 'HADONG'."""
    if not ma_lop_hp or "_" not in ma_lop_hp:
        return "HADONG" 
    return ma_lop_hp.split("_")[0].upper()

def _log_step(
    log_db: Session,
    tx_id: str,
    ma_lop_hp: str,
    ma_sv: str,
    buoc: BuocGiaoTac,
    chi_tiet: str | None = None,
    trang_thai: TrangThaiGiaoTac = TrangThaiGiaoTac.DANG_CHAY,
    ma_co_so: str | None = None,
) -> None:
    """Ghi một bước vào NhatKyThaoTac (session autocommit, không ảnh hưởng đến TX chính)."""
    try:
        log_db.add(NhatKyThaoTac(
            MaGiaoTac=tx_id,
            MaLopHP=ma_lop_hp,
            MaSV=ma_sv,
            MaCoSo=ma_co_so,
            Buoc=buoc,
            ChiTiet=chi_tiet,
            TrangThai=trang_thai
        ))
        log_db.commit()
    except Exception:
        log_db.rollback()

def _log_retry_attempt(func_name: str, args, kwargs, retries: int, max_retries: int, wait_time: float):
    """Hàm bổ trợ trích xuất thông tin nghiệp vụ và ghi log thao tác khi có retry."""
    try:
        ma_sv, ma_lop = "UNKNOWN", "UNKNOWN"
        
        # Trích xuất tham số dựa theo hàm được gọi
        if func_name == "register":
            user = kwargs.get("user") or (args[0] if len(args) > 0 else None)
            enroll_in = kwargs.get("enroll_in") or (args[1] if len(args) > 1 else None)
            if user:
                ma_sv = getattr(user, "userId", getattr(user, "MaSV", "UNKNOWN"))
            if enroll_in:
                ma_lop = getattr(enroll_in, "MaLopHP", "UNKNOWN")
        elif func_name == "cancel":
            ma_sv = kwargs.get("user_id") or (args[0] if len(args) > 0 else "UNKNOWN")
            ma_lop = kwargs.get("ma_lop_hp") or (args[1] if len(args) > 1 else "UNKNOWN")
        
        tx_id = kwargs.get("tx_id") or f"RETRY-LOG-{int(time.time())}"
        site = _site_of(str(ma_lop))
        
        with get_log_session(site) as log_db:
            # Ghi nhận bước Rollback do lỗi
            _log_step(log_db, tx_id, str(ma_lop), str(ma_sv), BuocGiaoTac.ROLLBACK,
                      f"Giao dịch đã được rollback do xung đột tài nguyên. Sẽ thử lại sau {wait_time:.2f}s.",
                      TrangThaiGiaoTac.THANH_CONG, ma_co_so=site)
            # Ghi nhận bước bắt đầu Thử lại
            _log_step(log_db, tx_id, str(ma_lop), str(ma_sv), BuocGiaoTac.RETRY,
                      f"Bắt đầu thực hiện lại lần {retries}/{max_retries}.",
                      TrangThaiGiaoTac.DANG_CHAY, ma_co_so=site)
    except Exception:
        pass


def retry_on_deadlock(max_retries=3, initial_wait=0.1):
    """Tự động thử lại khi gặp Deadlock (hoặc 409 Conflict) """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (InternalError, OperationalError, HTTPException) as e:
                    # 1. Kiểm tra xem có phải lỗi xung đột/deadlock không
                    is_conflict = (
                        (isinstance(e, HTTPException) and e.status_code == status.HTTP_409_CONFLICT) or
                        ("deadlock detected" in str(e).lower() or "40p01" in str(e).lower())
                    )
                    
                    if not is_conflict or attempt == max_retries - 1:
                        raise

                    # 2. Tính thời gian chờ
                    wait_time = initial_wait * (2 ** (attempt + 1)) + random.uniform(0, 0.1)

                    # 3. Ghi log kể chuyện vào DB và thử lại
                    _log_retry_attempt(func.__name__, args, kwargs, attempt + 2, max_retries, wait_time)
                    time.sleep(wait_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator
