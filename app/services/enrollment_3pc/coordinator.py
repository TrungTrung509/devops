from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy import text

from fastapi import HTTPException, status

from configs.db import SessionLocals, engines
from enums.status import EnrollmentAction, EnrollmentTransactionState, LogStatus, BuocGiaoTac, TrangThaiGiaoTac, RecoveryAction
from sqlalchemy.exc import OperationalError, InternalError
from models.CourseSections import CourseSection
from repositories.RecoveryLogRepo import RecoveryLogRepo
from repositories.EnrollmentTransactionRepo import EnrollmentTransactionRepo

from schemas.Enrollment import EnrollmentCreate, RegistrationResult
from services.utils import retry_on_deadlock

from .context import Enrollment3PCContext
from .db import Enrollment3PCDB
from .domain import Enrollment3PCDomain


class Enrollment3PCCoordinator:
    """
    Bộ Điều phối Cam kết Ba Pha (Enrollment3PCCoordinator).
    Chịu trách nhiệm thực thi giao thức cam kết 3 pha (3-Phase Commit) cho các thao tác
    Đăng ký môn học, Chuyển lớp, và Hủy đăng ký chéo site.
    Đồng thời chạy luồng tự phục hồi (Recovery) cho các giao dịch bị treo (In-doubt transactions).
    """
    
    # Khoảng thời gian (giây) tối đa để coi một giao dịch bị treo ở pha Prepare là hết hạn (stale)
    RECOVERY_STALE_SECONDS = 30

    @staticmethod
    @retry_on_deadlock(max_retries=3)
    def register(user, enroll_in: EnrollmentCreate) -> RegistrationResult:
        """
        [Nghiệp vụ Đăng ký mới hoặc Chuyển lớp]
        Luồng xử lý 3 Pha:
        1. [Chuẩn bị - Phase 1]:
           - Đảm bảo tất cả 3 site DB đều đang hoạt động tốt.
           - Mở các DB sessions liên cơ sở và ghim chúng (pinned).
           - Phân tích ngữ cảnh: Xác định site lớp học mới (site_new), site của SV (site_home), site cũ (site_old) và khởi tạo Context.
           - Ghi log kỹ thuật bước "BEGIN".
           - Kiểm tra điều kiện nghiệp vụ sơ bộ (siêu nhanh) -> Snapshot check.
           - Xin khóa Advisory Lock phân tán trên các site để tránh tranh chấp transaction.
           - Tạo dòng trạng thái giao dịch (EnrollmentTransaction) ở mức "INIT" trên các site.
           - Thực hiện khóa dòng (Row Lock - SELECT FOR UPDATE) trên các bảng lớp học phần ở các site.
           - Kiểm tra điều kiện sĩ số cuối cùng và đổi trạng thái giao dịch sang "PREPARED".
        2. [Báo trước cam kết - Phase 2]:
           - Điều phối viên gửi lệnh chuyển trạng thái giao dịch sang "PRECOMMIT" trên tất cả các site.
        3. [Cam kết thực tế - Phase 3]:
           - Gọi `_commit_register` để ghi nhận nghiệp vụ thực tế (chèn đăng ký mới, xóa lớp cũ nếu đổi lớp).
           - Nếu có site con bị sập ở bước này: Trả về kết quả Success nhưng báo hệ thống sẽ Recovery sau (In-doubt state).
           - Nếu tất cả thành công: Đổi trạng thái giao dịch sang "COMMITTED", ghi log thành công, giải phóng khóa và đóng sessions.
        """
        # Bước 1.1: Đảm bảo các site DB đều online
        Enrollment3PCDB.ensure_sites_alive(
            SessionLocals.keys(),
            detail="Không thể đăng ký học phần khi một cơ sở đang offline",
        )

        # Mở và giữ các connection tới các site để chuẩn bị giao dịch phân tán
        sessions, connections = Enrollment3PCDB.open_pinned_sessions(SessionLocals.keys())
        acquired_locks: list[tuple[str, int]] = []
        ctx: Enrollment3PCContext | None = None

        ma_sv = enroll_in.MaSV if hasattr(enroll_in, 'MaSV') else user.userId
        txn_id = Enrollment3PCCoordinator._new_txn_id() # Tạo ID giao dịch duy nhất
        site_new = "HADONG" # Site mặc định ghi log nếu chưa phân tích được context
        
        try:
            # Bước 1.2: Xác định phạm vi site lớp mới và site sv từ token
            site_new, _, section_new = Enrollment3PCDomain.find_section_context(sessions, enroll_in.MaLopHP)
            site_home = Enrollment3PCDB.normalize_site(user.MaCoSo)
            if site_home not in sessions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Mã cơ sở không hợp lệ: {site_home}",
                )

            # Xác định xem sinh viên có đăng ký cũ (đổi lớp) ở site nào không
            existing_enrollment, site_old = Enrollment3PCDomain.find_existing_enrollment(
                sessions,
                user.userId,
                section_new.MaHP,
                section_new.MaHocKy,
            )

            # Khởi tạo đối tượng Context lưu thông tin luồng giao dịch 3PC
            ctx = Enrollment3PCCoordinator._build_register_context(
                txn_id=txn_id,
                user_id=user.userId,
                ma_sv=ma_sv,
                ghi_chu=None,
                site_home=site_home,
                site_new=site_new,
                site_old=site_old,
                section_new=section_new,
                existing_enrollment=existing_enrollment,
                lock_sites=list(sessions.keys()),
            )

            # Ghi log kỹ thuật: Bắt đầu giao dịch 3PC
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "BEGIN", "Bắt đầu giao dịch 3PC", "DANG_CHAY")

            # Bước 2. Kiểm tra điều kiện nghiệp vụ sơ bộ (chưa khóa dữ liệu)
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "KIEM_TRA_SO_BO", "Đang xác thực điều kiện đăng ký sơ bộ", "DANG_CHAY")
            Enrollment3PCDomain.snapshot_check_eligibility(ctx, sessions)

            # Bước 3. Khóa tài nguyên phân tán (Advisory Locks)
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "KHOA_PHAN_TAN", "Đang lấy Advisory Lock phân tán trên tất cả site", "DANG_CHAY")
            acquired_locks = Enrollment3PCDB.acquire_locks(ctx, sessions)

            # Tạo bản ghi trạng thái giao dịch 3PC (EnrollmentTransaction) ở trạng thái INIT
            EnrollmentTransactionRepo.create_or_reset_rows(ctx, sessions)

            # Khóa dòng dữ liệu (Row Lock) lớp học phần trên database để kiểm tra sĩ số cuối cùng
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "KHOA_LOP_HP_DB", "Đang thực hiện Row Lock các lớp học phần", "DANG_CHAY")
            locked_section = Enrollment3PCDomain.prepare_lock_rows(ctx, sessions)

            # Xác thực sĩ số cuối cùng của lớp học phần
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "KIEM_TRA_SI_SO_CUOI", "Đang xác thực sĩ số và trạng thái cuối cùng", "DANG_CHAY")
            Enrollment3PCDomain.prepare_validate(locked_section)
            
            # Kết thúc Pha 1 (Prepare) -> Chuyển trạng thái sang PREPARED
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.PREPARED,
                "Tất cả participant đã hoàn tất prepare",
            )
            
            # Khởi động Pha 2 (Pre-commit) -> Chuyển trạng thái sang PRECOMMIT
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.PRECOMMIT,
                "Coordinator đã chuyển sang pha pre-commit",
            )
            
            # Khởi động Pha 3 (Commit) -> Thực thi ghi cơ sở dữ liệu nghiệp vụ
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "INSERT", "Bắt đầu ghi vào CSDL", "DANG_CHAY")

            enrollment_id, failed_sites = Enrollment3PCCoordinator._commit_register(ctx, sessions)
            
            # Trường hợp có site con bị sập trong pha Commit -> Trả về Success nhưng sẽ tự phục hồi sau
            if failed_sites:
                return RegistrationResult(
                    MaLopHP=ctx.target_ma_lop_hp,
                    status="Success",
                    message=(
                        "Giao dịch đã vào pha pre-commit. Hệ thống sẽ tự động recovery cho các cơ sở: "
                        + ", ".join(failed_sites)
                    ),
                    enrollment_id=enrollment_id,
                    action=ctx.action.value,
                    old_ma_lop_hp=ctx.old_ma_lop_hp,
                )

            # Nếu tất cả site commit nghiệp vụ thành công -> Chuyển trạng thái giao dịch sang COMMITTED
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.COMMITTED,
                "Tất cả participant đã commit thành công",
            )
            
            # Tính toán sĩ số lớp học phần mới để ghi log nghiệp vụ chi tiết
            try:
                target_sec = sessions[ctx.site_new].query(CourseSection).filter(CourseSection.MaLopHP == ctx.target_ma_lop_hp).first()
                new_sz = target_sec.SiSoHienTai if target_sec else 1
                old_sz = new_sz - 1
                log_detail = f"{ctx.target_ma_lop_hp} ({old_sz} -> {new_sz})."
                
                if ctx.old_ma_lop_hp and ctx.site_old:
                    old_sec = sessions[ctx.site_old].query(CourseSection).filter(CourseSection.MaLopHP == ctx.old_ma_lop_hp).first()
                    if old_sec:
                        old_new_sz = old_sec.SiSoHienTai
                        old_old_sz = old_new_sz + 1
                        log_detail = f" {ctx.target_ma_lop_hp} ({old_sz} -> {new_sz}), {ctx.old_ma_lop_hp} ({old_old_sz} -> {old_new_sz})."
            except Exception:
                log_detail = "Đăng ký/Đổi lớp thành công."
                
            # Ghi nhận log thao tác hoàn thành
            Enrollment3PCCoordinator._log_3pc_step(site_new, ctx.txn_id, ctx.target_ma_lop_hp, ma_sv, "COMMIT", log_detail, "THANH_CONG")

            return RegistrationResult(
                MaLopHP=ctx.target_ma_lop_hp,
                status="Success",
                message="Đổi lớp thành công" if ctx.old_ma_lop_hp else "Đăng ký thành công",
                enrollment_id=enrollment_id,
                action=ctx.action.value,
                old_ma_lop_hp=ctx.old_ma_lop_hp,
            )
        except HTTPException as exc:
            should_retry = exc.status_code == status.HTTP_409_CONFLICT and (
                "giao dich khac su dung" in exc.detail
                or "bị chiếm" in exc.detail
            )

            # Cập nhật trạng thái bước hiện tại sang THẤT BẠI
            Enrollment3PCCoordinator._fail_current_3pc_step(site_new, txn_id, exc.detail)

            if should_retry:
                # Gặp lỗi tranh chấp lock thì ném lên để hàm retry_on_deadlock thử lại giao dịch khác
                raise

            # Hủy bỏ giao dịch 3PC trên các site (Aborted)
            if ctx is not None:
                EnrollmentTransactionRepo.mark_aborted(ctx, sessions, exc.detail)

            return RegistrationResult(
                MaLopHP=enroll_in.MaLopHP.upper(),
                status="Failed",
                message=exc.detail,
            )
        except Exception as exc:
            # Xử lý khi gặp lỗi deadlock của Database
            if isinstance(exc, (OperationalError, InternalError)):
                err_msg = str(exc).lower()
                if "deadlock detected" in err_msg or "40p01" in err_msg:
                    raise
            if ctx is not None:
                EnrollmentTransactionRepo.mark_aborted(ctx, sessions, str(exc))
            
            # Cập nhật bước hiện tại sang THẤT BẠI
            Enrollment3PCCoordinator._fail_current_3pc_step(site_new, txn_id, str(exc))

            return RegistrationResult(
                MaLopHP=enroll_in.MaLopHP.upper(),
                status="Failed",
                message=str(exc),
            )
        finally:
            # Giải phóng tất cả Advisory Locks và đóng các DB Sessions
            Enrollment3PCDB.release_locks(sessions, acquired_locks)
            Enrollment3PCDB.close_pinned_sessions(sessions, connections)

    @staticmethod
    @retry_on_deadlock(max_retries=3)
    def cancel(user_id: str, ma_lop_hp: str, site_home: str) -> None:
        """
        [Nghiệp vụ Hủy đăng ký học phần]
        Tương tự luồng đăng ký học phần, luồng Hủy đăng ký cũng chạy giao thức 3 pha:
        - Prepare: Ping site, mở session, lấy Advisory Lock, chèn transaction logs ở trạng thái INIT, Row Lock dòng đăng ký.
        - Pre-commit: coordinator gửi lệnh chuyển sang trạng thái PRECOMMIT.
        - Commit: Xóa dòng đăng ký nghiệp vụ trong DB con (`_commit_cancel`), hoàn lại sĩ số cho lớp.
        - Kết thúc: Chuyển trạng thái transaction sang COMMITTED và đóng session.
        """
        normalized_home = Enrollment3PCDB.normalize_site(site_home)
        alive_sites = [site for site in SessionLocals if Enrollment3PCDB.is_site_alive(site)]
        sessions, connections = Enrollment3PCDB.open_pinned_sessions(alive_sites)
        acquired_locks: list[tuple[str, int]] = []
        ctx: Enrollment3PCContext | None = None

        try:
            # 1. Tìm thông tin đăng ký học phần cũ của sinh viên
            enrollment, site_target = Enrollment3PCDomain.find_enrollment_by_class(
                sessions,
                user_id,
                ma_lop_hp,
            )
            if enrollment is None or site_target is None:
                if len(alive_sites) != len(SessionLocals):
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Không thể xác định đầy đủ trạng thái đăng ký khi một cơ sở đang offline",
                    )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy thông tin đăng ký",
                )

            # Ràng buộc: các site liên quan phải online
            required_sites = {site_target, normalized_home}
            Enrollment3PCDB.ensure_sites_alive(
                required_sites,
                detail="Không thể hủy đăng ký khi cơ sở liên quan đang offline",
            )

            # Xác định lớp học phần đích cần hủy
            target_section = sessions[site_target].query(CourseSection).filter(
                CourseSection.MaLopHP == enrollment.MaLopHP
            ).first()
            if target_section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy lớp học phần: {ma_lop_hp.upper()}",
                )

            # Khởi tạo Context cho luồng Hủy đăng ký
            ctx = Enrollment3PCContext(
                txn_id=Enrollment3PCCoordinator._new_txn_id(),
                coordinator_site=normalized_home,
                action=EnrollmentAction.CANCEL,
                user_id=user_id,
                site_home=normalized_home,
                site_new=site_target,
                site_old=None,
                target_ma_lop_hp=target_section.MaLopHP,
                target_ma_hp=target_section.MaHP,
                target_ma_hoc_ky=target_section.MaHocKy,
                old_ma_lop_hp=None,
                ghi_chu=None,
                lock_sites=sorted(required_sites),
            )

            Enrollment3PCCoordinator._log_3pc_step(ctx.site_new, ctx.txn_id, ctx.target_ma_lop_hp, user_id, "BEGIN", "Bắt đầu giao dịch hủy đăng ký", "DANG_CHAY")

            # Giai đoạn 1: Prepare (Khóa Advisory Lock, khởi tạo Transaction log, Row lock)
            Enrollment3PCCoordinator._log_3pc_step(ctx.site_new, ctx.txn_id, ctx.target_ma_lop_hp, user_id, "KHOA_PHAN_TAN", "Đang lấy Advisory Lock phân tán để hủy đăng ký", "DANG_CHAY")
            acquired_locks = Enrollment3PCDB.acquire_locks(ctx, sessions)

            EnrollmentTransactionRepo.create_or_reset_rows(ctx, sessions)

            Enrollment3PCCoordinator._log_3pc_step(ctx.site_new, ctx.txn_id, ctx.target_ma_lop_hp, user_id, "KHOA_LOP_HP_DB", "Đang thực hiện Row Lock bản ghi để hủy", "DANG_CHAY")
            Enrollment3PCDomain.prepare_cancel(ctx, sessions)
            
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.PREPARED,
                "Tất cả participant đã hoàn tất prepare",
            )
            
            # Giai đoạn 2: Pre-commit
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.PRECOMMIT,
                "Coordinator đã chuyển sang pha pre-commit",
            )

            # Giai đoạn 3: Commit (Xóa bản ghi đăng ký nghiệp vụ)
            Enrollment3PCCoordinator._log_3pc_step(ctx.site_new, ctx.txn_id, ctx.target_ma_lop_hp, user_id, "INSERT", "Bắt đầu xóa dữ liệu khỏi CSDL", "DANG_CHAY")
            _, failed_sites = Enrollment3PCCoordinator._commit_cancel(ctx, sessions)
            if failed_sites:
                return

            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.COMMITTED,
                "Tất cả participant đã commit thành công",
            )
            
            # Tính toán lại sĩ số sau khi hủy thành công để ghi log nghiệp vụ
            try:
                target_sec = sessions[ctx.site_new].query(CourseSection).filter(CourseSection.MaLopHP == ctx.target_ma_lop_hp).first()
                new_sz = target_sec.SiSoHienTai if target_sec else 0
                old_sz = new_sz + 1
                log_detail = f"Hủy thành công. {ctx.target_ma_lop_hp} ({old_sz} -> {new_sz})."
            except Exception:
                log_detail = "Hủy đăng ký thành công."
                
            Enrollment3PCCoordinator._log_3pc_step(ctx.site_new, ctx.txn_id, ctx.target_ma_lop_hp, user_id, "COMMIT", log_detail, "THANH_CONG")

        except Exception as exc:
            if ctx is not None:
                EnrollmentTransactionRepo.mark_aborted(ctx, sessions, "Hủy đăng ký thất bại")
                Enrollment3PCCoordinator._fail_current_3pc_step(ctx.site_new, ctx.txn_id, str(exc))

            raise
        finally:
            Enrollment3PCDB.release_locks(sessions, acquired_locks)
            Enrollment3PCDB.close_pinned_sessions(sessions, connections)

    @staticmethod
    def recover_in_doubt_transactions() -> dict[str, int]:
        """
        [Tiến trình chạy ngầm tự động Recovery giao dịch phân tán]
        Định kỳ quét các giao dịch 3PC bị treo (In-doubt transactions).
        - Nếu giao dịch bị kẹt sau pha PRECOMMIT: Ép commit bù trên toàn bộ các site tham gia.
        - Nếu giao dịch hết hạn (stale) trước pha PRECOMMIT: Ép hủy bỏ (ABORT) giao dịch trên các site con.
        Trả về: Số giao dịch đã tự động commit bù hoặc tự động abort thành công.
        """
        # Xác định mốc thời gian quá hạn (30 giây trước)
        cutoff = datetime.utcnow() - timedelta(seconds=Enrollment3PCCoordinator.RECOVERY_STALE_SECONDS)
        pending_commit, stale_abort = EnrollmentTransactionRepo.collect_recovery_candidates(cutoff)

        committed = 0
        aborted = 0
        
        # 1. Ép Commit các giao dịch bị kẹt ở pha Pre-commit
        for txn_id in sorted(pending_commit):
            if Enrollment3PCCoordinator._recover_precommit_transaction(txn_id):
                committed += 1

        # 2. Ép Abort các giao dịch hết hạn ở pha Prepare
        for txn_id in sorted(stale_abort):
            if Enrollment3PCCoordinator._abort_transaction_records(txn_id, force=False):
                aborted += 1

        return {
            "recovered_commits": committed,
            "recovered_aborts": aborted,
        }

    @staticmethod
    def _commit_register(
        ctx: Enrollment3PCContext,
        sessions,
    ) -> tuple[int | None, list[str]]:
        """
        [Hàm nội bộ] Ra lệnh commit nghiệp vụ đăng ký/đổi lớp ở các site tham gia.
        Trả về: ID bản ghi đăng ký mới và danh sách các site bị lỗi commit (nếu có).
        """
        enrollment_id: int | None = None
        failed_sites: list[str] = []

        for site in ctx.participant_sites:
            try:
                current_id = Enrollment3PCDomain.commit_site(ctx, sessions[site], site)
                if site == ctx.site_new and current_id is not None:
                    enrollment_id = current_id
            except Exception:
                sessions[site].rollback()
                failed_sites.append(site)

        return enrollment_id, failed_sites

    @staticmethod
    def _commit_cancel(
        ctx: Enrollment3PCContext,
        sessions,
    ) -> tuple[None, list[str]]:
        """
        [Hàm nội bộ] Ra lệnh commit nghiệp vụ hủy đăng ký lớp học ở các site con.
        """
        failed_sites: list[str] = []
        for site in ctx.participant_sites:
            try:
                Enrollment3PCDomain.commit_site(ctx, sessions[site], site)
            except Exception:
                sessions[site].rollback()
                failed_sites.append(site)
        return None, failed_sites

    @staticmethod
    def _recover_precommit_transaction(txn_id: str) -> bool:
        """
        [Hàm nội bộ] Phục hồi và ép commit giao dịch ở trạng thái PRECOMMIT.
        Yêu cầu tất cả các site liên quan phải online. Thực hiện:
        - Xin khóa Advisory Lock phân tán.
        - Ghi đè thay đổi dữ liệu nghiệp vụ ở các site con.
        - Chuyển đổi trạng thái giao dịch sang COMMITTED.
        - Ghi nhật ký phục hồi (Recovery Log) thành công vào bảng NhatKyPhucHoi.
        """
        ctx = EnrollmentTransactionRepo.load_context(txn_id)
        if ctx is None:
            return False

        # Nếu giao dịch đã bị đánh dấu ABORTED từ trước, thực hiện hủy bỏ
        if EnrollmentTransactionRepo.has_state(txn_id, EnrollmentTransactionState.ABORTED):
            return Enrollment3PCCoordinator._abort_transaction_records(txn_id, force=True)
            
        # Đảm bảo các site liên quan đều online để recovery commit đồng bộ
        if not all(Enrollment3PCDB.is_site_alive(site) for site in ctx.participant_sites):
            return False

        sessions, connections = Enrollment3PCDB.open_pinned_sessions(ctx.lock_sites)
        acquired_locks: list[tuple[str, int]] = []
        try:
            acquired_locks = Enrollment3PCDB.acquire_locks(ctx, sessions)
            for site in ctx.participant_sites:
                try:
                    Enrollment3PCDomain.commit_site(ctx, sessions[site])
                except Exception:
                    sessions[site].rollback()
                    return False
            
            # Cập nhật trạng thái giao dịch 3PC sang COMMITTED
            EnrollmentTransactionRepo.set_state(
                ctx,
                sessions,
                EnrollmentTransactionState.COMMITTED,
                "Recovery đã hoàn tất commit cho tất cả participant",
            )
            
            # Ghi log phục hồi kỹ thuật vào bảng NhatKyPhucHoi của coordinator site
            with SessionLocals[ctx.coordinator_site]() as db:
                RecoveryLogRepo.append_recovery_log(
                    db,
                    txn_id=ctx.txn_id,
                    user_id=ctx.user_id,
                    ma_lop_hp=ctx.target_ma_lop_hp,
                    action=RecoveryAction.FORCED_COMMIT,
                    ma_co_so=ctx.coordinator_site,
                    status=LogStatus.SUCCESS,
                    message="Recovery thành công: Ép Commit giao dịch In-doubt (Pre-commit)"
                )

            return True
        finally:
            Enrollment3PCDB.release_locks(sessions, acquired_locks)
            Enrollment3PCDB.close_pinned_sessions(sessions, connections)

    @staticmethod
    def _abort_transaction_records(txn_id: str, force: bool) -> bool:
        """
        [Hàm nội bộ] Phục hồi và ép hủy bỏ (Abort) các giao dịch hết hạn (Timeout).
        Cập nhật trạng thái của giao dịch tại các site con còn sống sang ABORTED.
        Ghi nhật ký phục hồi thành công vào bảng NhatKyPhucHoi.
        """
        ctx = EnrollmentTransactionRepo.load_context(txn_id)
        if ctx is None:
            return False

        sessions, connections = Enrollment3PCDB.open_pinned_sessions(
            [site for site in ctx.transaction_sites if Enrollment3PCDB.is_site_alive(site)]
        )
        try:
            for site in ctx.transaction_sites:
                session = sessions.get(site)
                if session is None:
                    continue

                row = EnrollmentTransactionRepo.get_by_txn_and_site(session, ctx.txn_id, site)
                if row is None:
                    continue
                if row.State == EnrollmentTransactionState.PRECOMMIT and not force:
                    # Giao dịch đã đi vào Pre-commit thì không được tự ý Abort trừ khi bị ép buộc
                    return False
                if row.State == EnrollmentTransactionState.COMMITTED:
                    # Giao dịch đã commit thì giữ nguyên
                    continue

                # Hủy bỏ giao dịch 3PC tại site con này
                row.State = EnrollmentTransactionState.ABORTED
                row.Message = "Recovery đã abort giao dịch do bị trễ ở pha prepare"
                session.commit()

            # Ghi log phục hồi kỹ thuật vào bảng NhatKyPhucHoi
            with SessionLocals[ctx.coordinator_site]() as db:
                RecoveryLogRepo.append_recovery_log(
                    db,
                    txn_id=ctx.txn_id,
                    user_id=ctx.user_id,
                    ma_lop_hp=ctx.target_ma_lop_hp,
                    action=RecoveryAction.FORCED_ABORT,
                    ma_co_so=ctx.coordinator_site,
                    status=LogStatus.SUCCESS,
                    message="Recovery thành công: Hủy bỏ giao dịch treo (Timeout/Stale)"
                )

            return True
        finally:
            Enrollment3PCDB.close_pinned_sessions(sessions, connections)

    @staticmethod
    def _build_register_context(
        *,
        txn_id: str,
        user_id: str,
        ma_sv: str | None,
        ghi_chu: str | None,
        site_home: str,
        site_new: str,
        site_old: str | None,
        section_new,
        existing_enrollment,
        lock_sites: list[str],
    ) -> Enrollment3PCContext:
        """
        [Hàm nội bộ] Khởi tạo đối tượng Context lưu trữ ngữ cảnh giao dịch 3PC.
        """
        return Enrollment3PCContext(
            txn_id=txn_id,
            coordinator_site=site_home,
            action=EnrollmentAction.SWITCH if existing_enrollment else EnrollmentAction.REGISTER,
            user_id=user_id,
            ma_sv=ma_sv,
            site_home=site_home,
            site_new=site_new,
            site_old=site_old,
            target_ma_lop_hp=section_new.MaLopHP,
            target_ma_hp=section_new.MaHP,
            target_ma_hoc_ky=section_new.MaHocKy,
            old_ma_lop_hp=existing_enrollment.MaLopHP if existing_enrollment else None,
            ghi_chu=ghi_chu,
            lock_sites=sorted(lock_sites),
        )

    @staticmethod
    def _new_txn_id() -> str:
        """
        [Hàm nội bộ] Sinh mã định danh giao dịch phân tán ngẫu nhiên dạng UUID.
        """
        return uuid4().hex

    @staticmethod
    def _log_3pc_step(site: str, tx_id: str, ma_lop_hp: str, ma_sv: str | None, buoc: str, chi_tiet: str, trang_thai: str):
        """
        [Hàm nội bộ] Ghi log hoạt động nghiệp vụ vào bảng NhatKyThaoTac.
        *Đặc điểm kỹ thuật đặc biệt:* Sử dụng kết nối thô độc lập (Direct Connection)
        với cơ chế AUTOCOMMIT để bản ghi log được commit ngay lập tức xuống DB.
        Giúp lưu giữ thông tin chi tiết từng bước kể cả khi giao dịch nghiệp vụ chính bị rollback.
        """
        try:
            engine = engines.get(site.upper())
            if not engine:
                print(f"CRITICAL: Engine not found for site {site}")
                return

            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                query = text("""
                    INSERT INTO "NhatKyThaoTac" 
                    ("MaGiaoTac", "MaLopHP", "MaSV", "MaCoSo", "Buoc", "ChiTiet", "TrangThai", "ThoiGian")
                    VALUES (:txn, :ma_lop, :ma_sv, :site, :buoc, :detail, :status, :now)
                """)
                conn.execute(query, {
                    "txn": tx_id,
                    "ma_lop": ma_lop_hp,
                    "ma_sv": str(ma_sv),
                    "site": site,
                    "buoc": buoc,
                    "detail": chi_tiet,
                    "status": trang_thai,
                    "now": datetime.utcnow()
                })
        except Exception as e:
            print(f"CRITICAL: Failed to write log to {site} via Direct Connection: {e}")
            pass

    @staticmethod
    def _fail_current_3pc_step(site: str, txn_id: str, error_detail: str) -> None:
        """
        [Hàm nội bộ] Cập nhật bước đang chạy gần nhất (MAX ID) của txn_id sang trạng thái THAT_BAI.
        Được gọi khi có lỗi phát sinh trong quá trình chạy 3PC để cập nhật vết lỗi chính xác vào log.
        """
        try:
            engine = engines.get(site.upper())
            if not engine:
                return

            with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                conn.execute(
                    text("""
                        UPDATE "NhatKyThaoTac"
                        SET "TrangThai" = 'THAT_BAI',
                            "ChiTiet"   = :detail
                        WHERE "ID" = (
                            SELECT MAX("ID") FROM "NhatKyThaoTac"
                            WHERE "MaGiaoTac" = :txn_id
                        )
                    """),
                    {"txn_id": txn_id, "detail": error_detail},
                )
        except Exception as e:
            print(f"CRITICAL: Failed to update log step to THAT_BAI at {site}: {e}")
