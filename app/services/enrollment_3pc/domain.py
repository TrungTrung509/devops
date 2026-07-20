from datetime import datetime
from dataclasses import replace
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from enums.status import ClassSectionStatus, EnrollmentAction, EnrollmentTransactionState
from models.CourseSections import CourseSection
from models.Enrollments import Enrollment
from models.Schedules import Schedule
from repositories.ClassSectionRepo import ClassSectionRepo
from repositories.EnrollmentRepo import EnrollmentRepo
from repositories.EnrollmentTransactionRepo import EnrollmentTransactionRepo
from services.ClassSectionService import ClassSectionService

from .context import Enrollment3PCContext
from .db import Enrollment3PCDB
from models.EnrollmentTransfers import EnrollmentTransfer

class Enrollment3PCDomain:
    @staticmethod
    def snapshot_check_eligibility(ctx: Enrollment3PCContext, sessions: dict[str, Session]) -> None:
        if Enrollment3PCDomain._is_same_section_switch(ctx):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Sinh viên đã đăng ký lớp học phần này",
            )

        target_session = sessions[ctx.site_new]
        target_section = target_session.query(CourseSection).filter(CourseSection.MaLopHP == ctx.target_ma_lop_hp).first()
        if target_section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lớp học phần: {ctx.target_ma_lop_hp}",
            )
        if target_section.TrangThaiLop != ClassSectionStatus.Mo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lớp đang ở trạng thái: {target_section.TrangThaiLop}",
            )

        # Kiểm tra sĩ số sơ bộ (sử dụng thuộc tính SiSoHienTai trực tiếp trên LopHocPhan)
        active_count = target_section.SiSoHienTai
        if active_count >= target_section.SiSoToiDa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lớp đã đầy",
            )

        # Kiểm tra trùng học phần trong học kỳ
        if Enrollment3PCDomain._has_other_course_enrollment(ctx, sessions):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sinh viên đã đăng ký học phần {ctx.target_ma_hp} trong học kỳ {ctx.target_ma_hoc_ky}",
            )

        # Kiểm tra trùng lịch học
        conflicts = Enrollment3PCDomain._check_schedule_conflict(
            sessions,
            ctx.user_id,
            target_section,
            ctx.old_ma_lop_hp,
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Trùng lịch học: " + "; ".join(conflicts),
            )

    @staticmethod
    def prepare_lock_rows(ctx: Enrollment3PCContext, sessions: dict[str, Session]) -> CourseSection:
        """
        Bước 1 của pha Prepare: Row Lock (SELECT FOR UPDATE).
        """
        target_db = sessions[ctx.site_new]

        # Lock lớp mới — sẽ BLOCK nếu transaction khác đang giữ lock này
        target_section = Enrollment3PCDomain._get_section_for_update(
            target_db, ctx.target_ma_lop_hp
        )
        if target_section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay lop hoc phan: {ctx.target_ma_lop_hp}",
            )

        # Refresh sau khi acquire lock — đảm bảo đọc SiSoHienTai mới nhất từ DB
        target_db.refresh(target_section)

        # Lock lớp cũ + kiểm tra bản ghi đăng ký cũ (khi đổi lớp)
        if ctx.site_old and ctx.old_ma_lop_hp:
            old_section = Enrollment3PCDomain._get_section_for_update(
                sessions[ctx.site_old], ctx.old_ma_lop_hp
            )
            if old_section is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay lop hoc phan: {ctx.old_ma_lop_hp}",
                )
        return target_section

    @staticmethod
    def prepare_validate(target_section: CourseSection) -> None:
       
        if target_section.TrangThaiLop != ClassSectionStatus.Mo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lớp đang ở trạng thái: {target_section.TrangThaiLop}",
            )

        if target_section.SiSoHienTai >= target_section.SiSoToiDa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lớp đã đầy",
            )

    @staticmethod
    def prepare_cancel(ctx: Enrollment3PCContext, sessions: dict[str, Session]) -> None:
        target_session = sessions[ctx.site_new]
        target_section = Enrollment3PCDomain._get_section_for_update(target_session, ctx.target_ma_lop_hp)
        if target_section is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay lop hoc phan: {ctx.target_ma_lop_hp}",
            )

        return

    @staticmethod
    def commit_site(ctx: Enrollment3PCContext, session: Session, site_name: str) -> int | None:
        site = site_name.upper()
        tx_row = EnrollmentTransactionRepo.get_by_txn_and_site(
            session,
            ctx.txn_id,
            site,
            for_update=True,
        )
        if tx_row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay giao dich 3PC: {ctx.txn_id}",
            )
        if tx_row.State == EnrollmentTransactionState.COMMITTED:
            return Enrollment3PCDomain._existing_enrollment_id(session, ctx)
        if tx_row.State == EnrollmentTransactionState.ABORTED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Giao dich {ctx.txn_id} da bi abort",
            )

        enrollment_id: int | None = None

        if ctx.action == EnrollmentAction.CANCEL:
            # Site quản lý lớp: Xóa bản ghi gốc
            if site == ctx.site_new:
                Enrollment3PCDomain._delete_enrollment_if_exists(session, ctx.user_id, ctx.target_ma_lop_hp)
                Enrollment3PCDomain._update_section_capacity(session, ctx.target_ma_lop_hp, -1)
            
            # Site nhà của SV: Cập nhật liên kết chéo cơ sở khi hủy
            if site == ctx.site_home and site != ctx.site_new:
                Enrollment3PCDomain._sync_cross_site_link(session, ctx)
        else:
            # 1. Nếu đổi lớp 
            if ctx.old_ma_lop_hp:
                # Site quản lý lớp cũ: Xóa bản ghi gốc
                if site == ctx.site_old:
                    Enrollment3PCDomain._delete_enrollment_if_exists(session, ctx.user_id, ctx.old_ma_lop_hp)
                    Enrollment3PCDomain._update_section_capacity(session, ctx.old_ma_lop_hp, -1)
                
                # Site SV: Cập nhật liên kết chéo cơ sở lớp cũ
                if site == ctx.site_home and site != ctx.site_old:
                    # Tạo context tạm để sync CANCEL cho lớp cũ
                    old_ctx = replace(ctx, action=EnrollmentAction.CANCEL, target_ma_lop_hp=ctx.old_ma_lop_hp)
                    Enrollment3PCDomain._sync_cross_site_link(session, old_ctx)

            # 2. Xử lý lớp mới
            # Site quản lý lớp mới: Ghi bản ghi gốc
            if site == ctx.site_new:
                current_id = Enrollment3PCDomain._ensure_enrollment_exists(
                    session,
                    ctx.user_id,
                    ctx.target_ma_lop_hp,
                    ctx.target_ma_hp,
                    ctx.target_ma_hoc_ky,
                    ctx.ma_sv,
                    ctx.ghi_chu,
                )
                enrollment_id = current_id
                Enrollment3PCDomain._update_section_capacity(session, ctx.target_ma_lop_hp, 1)
            
            # Site SV: Cập nhật liên kết chéo cơ sở
            if site == ctx.site_home and site != ctx.site_new:
                Enrollment3PCDomain._sync_cross_site_link(session, ctx)

        tx_row.State = EnrollmentTransactionState.COMMITTED
        tx_row.Message = "Local participant da commit thanh cong"
        session.commit()
        return enrollment_id

    @staticmethod
    def find_section_context(
        sessions: dict[str, Session],
        ma_lop_hp: str,
    ) -> tuple[str, Session, CourseSection]:
        section_code = ma_lop_hp.upper()
        for site, session in sessions.items():
            section = session.query(CourseSection).filter(CourseSection.MaLopHP == section_code).first()
            if section:
                return site, session, section
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Khong tim thay lop hoc phan: {section_code}",
        )

    @staticmethod
    def find_existing_enrollment(
        sessions: dict[str, Session],
        user_id: str,
        ma_hp: str,
        ma_hoc_ky: str,
    ) -> tuple[Enrollment | None, str | None]:
        for site, session in sessions.items():
            enrollment = EnrollmentRepo.find_active_enrollment(session, user_id, ma_hp, ma_hoc_ky)
            if enrollment:
                return enrollment, site
        return None, None

    @staticmethod
    def find_enrollment_by_class(
        sessions: dict[str, Session],
        user_id: str,
        ma_lop_hp: str,
    ) -> tuple[Enrollment | None, str | None]:
        section_code = ma_lop_hp.upper()
        for site, session in sessions.items():
            enrollment = session.query(Enrollment).filter(
                Enrollment.userId == user_id,
                Enrollment.MaLopHP == section_code,
            ).first()
            if enrollment is not None:
                return enrollment, site
        return None, None

    @staticmethod
    def _check_schedule_conflict(
        sessions: dict[str, Session],
        user_id: str,
        section: CourseSection,
        exclude_ma_lop_hp: str | None = None,
    ) -> list[str]:
        """Kiểm tra trùng lịch (Sinh viên và Giảng viên) trên tất cả các cơ sở."""
        conflicts = []
        target_schedules = ClassSectionRepo.list_schedules(sessions[section.MaCoSo], section.MaLopHP)
        if not target_schedules:
            return []

        for site, db in sessions.items():
            # Gom cả Đăng ký của sinh viên và Lớp dạy của giảng viên để kiểm tra 1 lượt
            enrollments = EnrollmentRepo.get_student_enrollments(db, user_id, section.MaHocKy)
            teacher_sections = db.query(CourseSection).filter(
                CourseSection.MaGV == section.MaGV,
                CourseSection.MaHocKy == section.MaHocKy,
            ).all()

            for item in (enrollments + teacher_sections):
                other_ma_lop = getattr(item, "MaLopHP")
                if other_ma_lop in {section.MaLopHP, exclude_ma_lop_hp}:
                    continue

                for s2 in ClassSectionRepo.list_schedules(db, other_ma_lop):
                    for s1 in target_schedules:
                        # Kiểm tra trùng: Cùng thứ + Giao thoa ngày + Giao thoa tiết học
                        is_overlap = (
                            s1.ThuTrongTuan == s2.ThuTrongTuan and
                            not (s1.NgayKetThuc < s2.NgayBatDau or s1.NgayBatDau > s2.NgayKetThuc) and
                            not (s1.TietBatDau + s1.SoTiet - 1 < s2.TietBatDau or s1.TietBatDau > s2.TietBatDau + s2.SoTiet - 1)
                        )
                        if is_overlap:
                            role = "Sinh viên" if hasattr(item, "MaDangKy") else "Giảng viên"
                            conflicts.append(f"{role} bị trùng lịch với lớp {other_ma_lop} tại {site}")

        return list(dict.fromkeys(conflicts))


    @staticmethod
    def _has_other_course_enrollment(
        ctx: Enrollment3PCContext,
        sessions: dict[str, Session],
    ) -> bool:
        for session in sessions.values():
            enrollments = session.query(Enrollment).filter(
                Enrollment.userId == ctx.user_id,
                Enrollment.MaHP == ctx.target_ma_hp,
                Enrollment.MaHocKy == ctx.target_ma_hoc_ky,
            ).all()
            for enrollment in enrollments:
                if enrollment.MaLopHP != ctx.old_ma_lop_hp:
                    return True
        return False

    @staticmethod
    def _is_same_section_switch(ctx: Enrollment3PCContext) -> bool:
        return bool(ctx.old_ma_lop_hp) and ctx.old_ma_lop_hp == ctx.target_ma_lop_hp

    @staticmethod
    def _get_section_for_update(session: Session, ma_lop_hp: str) -> CourseSection | None:
        return (
            session.query(CourseSection)
            .filter(CourseSection.MaLopHP == ma_lop_hp)
            .with_for_update()
            .first()
        )

    @staticmethod
    def _ensure_enrollment_exists(
        session: Session,
        user_id: str,
        ma_lop_hp: str,
        ma_hp: str,
        ma_hoc_ky: str,
        ma_sv: str | None,
        ghi_chu: str | None,
    ) -> int | None:
        enrollment = session.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.MaLopHP == ma_lop_hp,
        ).first()
        if enrollment is None:
            enrollment = Enrollment(
                userId=user_id,
                MaSV=ma_sv,
                MaLopHP=ma_lop_hp,
                MaHP=ma_hp,
                MaHocKy=ma_hoc_ky,
                GhiChu=ghi_chu,
            )
            session.add(enrollment)
            session.flush()
        else:
            enrollment.MaHP = ma_hp
            enrollment.MaHocKy = ma_hoc_ky
            enrollment.GhiChu = ghi_chu
        return enrollment.MaDangKy

    @staticmethod
    def _delete_enrollment_if_exists(session: Session, user_id: str, ma_lop_hp: str) -> None:
        enrollment = session.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.MaLopHP == ma_lop_hp,
        ).first()
        if enrollment is not None:
            session.delete(enrollment)
            session.flush()

    @staticmethod
    def _update_section_capacity(session: Session, ma_lop_hp: str, delta: int) -> None:
        """Cập nhật sĩ số bằng cách cộng/trừ trực tiếp (nhanh và an toàn vì đã có Row Lock)."""
        section = Enrollment3PCDomain._get_section_for_update(session, ma_lop_hp)
        if section is not None:
            section.SiSoHienTai += delta
            # Đảm bảo sĩ số không âm (phòng trường hợp hy hữu)
            if section.SiSoHienTai < 0:
                section.SiSoHienTai = 0

    @staticmethod
    def _existing_enrollment_id(session: Session, ctx: Enrollment3PCContext) -> int | None:
        enrollment = session.query(Enrollment).filter(
            Enrollment.userId == ctx.user_id,
            Enrollment.MaLopHP == ctx.target_ma_lop_hp,
        ).first()
        return enrollment.MaDangKy if enrollment else None

    @staticmethod
    def _sync_cross_site_link(
        session: Session,
        ctx: Enrollment3PCContext,
    ) -> None:
        """Đồng bộ bản ghi liên kết tại site của sinh viên."""
        
        if ctx.action == EnrollmentAction.CANCEL:
            # hủy đăng ký
            session.query(EnrollmentTransfer).filter(
                EnrollmentTransfer.userId == ctx.user_id,
                EnrollmentTransfer.MaLopHP == ctx.target_ma_lop_hp
            ).delete()
        else:
            # Upsert liên kết khi đăng ký mới hoặc đổi lớp
            link = session.query(EnrollmentTransfer).filter(
                EnrollmentTransfer.userId == ctx.user_id,
                EnrollmentTransfer.MaLopHP == ctx.target_ma_lop_hp
            ).first()
            
            if not link:
                link = EnrollmentTransfer(
                    userId=ctx.user_id,
                    MaLopHP=ctx.target_ma_lop_hp,
                    MaHP=ctx.target_ma_hp,
                    TargetSite=ctx.site_new
                )
                session.add(link)
            else:
                link.MaHP = ctx.target_ma_hp
                link.TargetSite = ctx.site_new
                link.Timestamp = datetime.utcnow()
        
        session.flush()
