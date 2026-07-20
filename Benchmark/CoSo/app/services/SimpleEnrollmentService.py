import time
import random
from fastapi import HTTPException
from configs.db import open_db_by_branch
from repositories.repos import ClassSectionRepo, EnrollmentRepo
from models.models import Enrollment, EnrollmentTransfer
from sqlalchemy import text
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.exc import TimeoutError as SQLAlchemyTimeoutError, OperationalError, IntegrityError
from monitoring.metrics import CONFLICT_CHECK_DURATION, LOCK_HOLD_DURATION, DB_ERRORS_TOTAL

MAX_RETRIES = 3

def get_site_prefix(identifier: str) -> str:
    for p in ["HD", "HL", "NT"]:
        if p in identifier.upper():
            return p
    return "HD"

class SimpleEnrollmentService:

    @staticmethod
    def _check_overlap(new_class, old_classes):
        for old_c in old_classes:
            if not old_c:
                continue
            if new_class.ThuTrongTuan == old_c.ThuTrongTuan:
                s1 = new_class.TietBatDau
                e1 = s1 + new_class.SoTiet - 1
                s2 = old_c.TietBatDau
                e2 = s2 + old_c.SoTiet - 1
                if max(s1, s2) <= min(e1, e2):
                    return True
        return False

    # ĐĂNG KÝ / ĐỔI LỚP
    @staticmethod
    def register_simple(user_id: str, ma_lop_hp: str):
        home_site = get_site_prefix(user_id)
        target_site = get_site_prefix(ma_lop_hp)

        try:
            # Bước 1: Lấy thông tin lớp mới
            with open_db_by_branch(target_site) as db:
                new_class = ClassSectionRepo.get_by_id(db, ma_lop_hp)
            if not new_class:
                raise HTTPException(status_code=404, detail="Không tìm thấy lớp")

            # Bước 2: Kiểm tra đã đăng ký cùng MaHP chưa
            old_enrollment = old_site = None
            with open_db_by_branch(home_site) as db:
                for en in EnrollmentRepo.get_student_enrollments(db, user_id):
                    if en.MaHP == new_class.MaHP and en.MaHocKy == new_class.MaHocKy:
                        old_enrollment, old_site = en, home_site
                        break

                if not old_enrollment:
                    for tr in EnrollmentRepo.get_student_transfers(db, user_id):
                        if tr.MaHP == new_class.MaHP:
                            old_enrollment, old_site = tr, tr.TargetSite
                            break

            # Nếu đã đăng ký cùng môn → Đổi lớp (có retry deadlock)
            if old_enrollment:
                return SimpleEnrollmentService._swap_with_retry(
                    user_id, home_site,
                    old_enrollment.MaLopHP, old_site,
                    ma_lop_hp, target_site,
                )

            # Đăng ký mới: kiểm tra trùng lịch trước
            t0 = time.perf_counter()
            try:
                old_classes = []
                with open_db_by_branch(home_site) as db:
                    local = EnrollmentRepo.get_student_enrollments(db, user_id)
                    transfers = EnrollmentRepo.get_student_transfers(db, user_id)
                    for en in local:
                        old_classes.append(ClassSectionRepo.get_by_id(db, en.MaLopHP))

                if transfers:
                    def _fetch(tr):
                        with open_db_by_branch(tr.TargetSite) as db_r:
                            return ClassSectionRepo.get_by_id(db_r, tr.MaLopHP)
                    with ThreadPoolExecutor(max_workers=min(len(transfers), 4)) as ex:
                        old_classes.extend(filter(None, ex.map(_fetch, transfers)))

                if SimpleEnrollmentService._check_overlap(new_class, old_classes):
                    raise HTTPException(status_code=409, detail="Trùng lịch học")
            finally:
                CONFLICT_CHECK_DURATION.labels(app="coso").observe(time.perf_counter() - t0)

            return SimpleEnrollmentService._do_enroll(user_id, home_site, ma_lop_hp, target_site)

        except (SQLAlchemyTimeoutError, TimeoutError):
            DB_ERRORS_TOTAL.labels(type="pool_exhaustion", app="coso").inc()
            raise HTTPException(status_code=503, detail="Connection pool timeout")
        except IntegrityError as e:
            msg = str(e).lower()
            if "uq_dk_user_hp_hk" in msg or "duplicate key" in msg:
                raise HTTPException(status_code=409, detail="Sinh viên đã đăng ký học phần này trong học kỳ")
            raise HTTPException(status_code=400, detail=f"Lỗi ràng buộc database: {e}")
        except OperationalError as e:
            msg = str(e).lower()
            label = "deadlock" if "deadlock" in msg else ("timeout" if "timeout" in msg else "db_other")
            DB_ERRORS_TOTAL.labels(type=label, app="coso").inc()
            raise HTTPException(status_code=503, detail="Database operational error")

    @staticmethod
    def _do_enroll(user_id, home_site, ma_lop_hp, target_site):
        """Ghi bản ghi đăng ký vào DB. Nếu cùng site thì 1 transaction, khác site thì 2 transaction."""
        sites = list({home_site, target_site})
        dbs = {s: open_db_by_branch(s) for s in sites}
        t0 = time.perf_counter()
        try:
            for db in dbs.values():
                db.execute(text("SET lock_timeout = '2s'"))

            # Lock và kiểm tra sĩ số lớp mới
            sec = ClassSectionRepo.get_by_id_for_update(dbs[target_site], ma_lop_hp)
            if sec.SiSoHienTai >= sec.SiSoToiDa:
                raise HTTPException(status_code=400, detail="Lớp đầy")

            dbs[target_site].add(Enrollment(userId=user_id, MaLopHP=ma_lop_hp, MaHP=sec.MaHP, MaHocKy=sec.MaHocKy))
            sec.SiSoHienTai += 1

            if home_site != target_site:
                dbs[home_site].add(EnrollmentTransfer(userId=user_id, MaLopHP=ma_lop_hp, MaHP=sec.MaHP, TargetSite=target_site))

            for db in dbs.values():
                db.commit()

            LOCK_HOLD_DURATION.labels(type="enroll", app="coso").observe(time.perf_counter() - t0)
            return {"status": "Success", "type": "new", "message": f"Đăng ký ({home_site} → {target_site})"}
        except Exception:
            for db in dbs.values():
                db.rollback()
            LOCK_HOLD_DURATION.labels(type="enroll_fail", app="coso").observe(time.perf_counter() - t0)
            raise
        finally:
            for db in dbs.values():
                db.close()

    @staticmethod
    def _swap_with_retry(user_id, home_site, old_ma_lop_hp, old_site, new_ma_lop_hp, new_site):
        """Đổi lớp với retry khi gặp deadlock (tối đa MAX_RETRIES lần, exponential backoff)."""
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                return SimpleEnrollmentService._do_swap(
                    user_id, home_site, old_ma_lop_hp, old_site, new_ma_lop_hp, new_site,
                )
            except (HTTPException, OperationalError) as e:
                is_retryable = (
                    (isinstance(e, HTTPException) and e.status_code == 503)
                    or "deadlock" in str(e).lower()
                    or "lock timeout" in str(e).lower()
                )
                if not is_retryable:
                    raise
                last_exc = e
                time.sleep(0.1 * (2 ** attempt) + random.uniform(0, 0.05))
        raise last_exc or HTTPException(status_code=503, detail="Deadlock sau 3 lần retry")

    @staticmethod
    def _do_swap(user_id, home_site, old_ma_lop_hp, old_site, new_ma_lop_hp, new_site):
        """Cancel lớp cũ + Enroll lớp mới (best-effort, không có recovery log)."""
        dbs = {s: open_db_by_branch(s) for s in {home_site, old_site, new_site}}
        t0 = time.perf_counter()
        try:
            for db in dbs.values():
                db.execute(text("SET lock_timeout = '2s'"))

            # Giải phóng lớp cũ
            old_sec = ClassSectionRepo.get_by_id_for_update(dbs[old_site], old_ma_lop_hp)
            if old_sec:
                old_en = dbs[old_site].query(Enrollment).filter_by(userId=user_id, MaLopHP=old_ma_lop_hp).first()
                if old_en:
                    dbs[old_site].delete(old_en)
                    old_sec.SiSoHienTai = max(0, old_sec.SiSoHienTai - 1)
                    dbs[old_site].flush()

            # Chiếm lớp mới
            new_sec = ClassSectionRepo.get_by_id_for_update(dbs[new_site], new_ma_lop_hp)
            if new_sec.SiSoHienTai >= new_sec.SiSoToiDa:
                raise HTTPException(status_code=400, detail="Lớp mới đã đầy")
            dbs[new_site].add(Enrollment(userId=user_id, MaLopHP=new_ma_lop_hp, MaHP=new_sec.MaHP, MaHocKy=new_sec.MaHocKy))
            new_sec.SiSoHienTai += 1

            # Cập nhật bảng transfer ở home (nếu đăng ký chéo)
            if home_site != old_site:
                old_tr = dbs[home_site].query(EnrollmentTransfer).filter_by(userId=user_id, MaLopHP=old_ma_lop_hp).first()
                if old_tr:
                    dbs[home_site].delete(old_tr)
            if home_site != new_site:
                dbs[home_site].add(EnrollmentTransfer(userId=user_id, MaLopHP=new_ma_lop_hp, MaHP=new_sec.MaHP, TargetSite=new_site))

            for db in dbs.values():
                db.commit()

            LOCK_HOLD_DURATION.labels(type="swap", app="coso").observe(time.perf_counter() - t0)
            return {"status": "Success", "type": "swap", "message": f"Đổi lớp {old_ma_lop_hp} → {new_ma_lop_hp}"}
        except Exception:
            for db in dbs.values():
                db.rollback()
            LOCK_HOLD_DURATION.labels(type="swap_fail", app="coso").observe(time.perf_counter() - t0)
            raise
        finally:
            for db in dbs.values():
                db.close()

    # HỦY ĐĂNG KÝ
    @staticmethod
    def cancel_simple(user_id: str, ma_lop_hp: str):
        home_site = get_site_prefix(user_id)
        target_site = get_site_prefix(ma_lop_hp)
        dbs = {s: open_db_by_branch(s) for s in {home_site, target_site}}
        t0 = time.perf_counter()
        try:
            for db in dbs.values():
                db.execute(text("SET lock_timeout = '2s'"))

            en = dbs[target_site].query(Enrollment).filter_by(userId=user_id, MaLopHP=ma_lop_hp).first()
            if not en:
                raise HTTPException(status_code=404, detail="Chưa đăng ký lớp này")

            sec = ClassSectionRepo.get_by_id_for_update(dbs[target_site], ma_lop_hp)
            dbs[target_site].delete(en)
            if sec:
                sec.SiSoHienTai = max(0, sec.SiSoHienTai - 1)

            if home_site != target_site:
                tr = dbs[home_site].query(EnrollmentTransfer).filter_by(userId=user_id, MaLopHP=ma_lop_hp).first()
                if tr:
                    dbs[home_site].delete(tr)

            for db in dbs.values():
                db.commit()

            LOCK_HOLD_DURATION.labels(type="cancel", app="coso").observe(time.perf_counter() - t0)
            return {"status": "Success", "message": f"Hủy ({home_site} → {target_site})"}
        except (SQLAlchemyTimeoutError, TimeoutError):
            DB_ERRORS_TOTAL.labels(type="pool_exhaustion", app="coso").inc()
            raise HTTPException(status_code=503, detail="Connection pool timeout")
        except OperationalError as e:
            msg = str(e).lower()
            label = "deadlock" if "deadlock" in msg else ("timeout" if "timeout" in msg else "db_other")
            DB_ERRORS_TOTAL.labels(type=label, app="coso").inc()
            raise HTTPException(status_code=503, detail="Database operational error")
        except Exception:
            for db in dbs.values():
                db.rollback()
            LOCK_HOLD_DURATION.labels(type="cancel_fail", app="coso").observe(time.perf_counter() - t0)
            raise
        finally:
            for db in dbs.values():
                db.close()
