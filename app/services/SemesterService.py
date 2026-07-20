from typing import Dict, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.user_role import UserRole
from models.CourseSections import CourseSection
from models.Semesters import Semester
from models.Users import User
from repositories.SemesterRepo import SemesterRepo
from enums.status import SemesterStatus
from schemas.Semester import SemesterCreate, SemesterResponse, SemesterUpdate


class SemesterService:
    @staticmethod
    def get_all_semesters(db: Session) -> Tuple[list[Semester], int]:
        query = SemesterRepo.base_query(db)
        total = query.count()
        items = query.order_by(Semester.NamHoc.desc(), Semester.KySo.desc(), Semester.MaHocKy.asc()).all()
        return items, total

    @staticmethod
    def get_semester_by_id(db: Session, ma_hoc_ky: str) -> Semester:
        semester = SemesterRepo.get_by_id(db, ma_hoc_ky)
        if not semester:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Khong tim thay hoc ky voi ma: {ma_hoc_ky}",
            )
        return semester

    @staticmethod
    async def create_semester(semester_in: SemesterCreate, current_user: User) -> SemesterResponse:
        SemesterService._ensure_admin(current_user)
        sessions = SemesterService._open_sessions()
        primary_site, primary_session = SemesterService._get_primary_session(sessions)

        try:
            semester_code = semester_in.MaHocKy.upper()
            SemesterService._validate_payload(
                ky_so=semester_in.KySo,
                ngay_bat_dau=semester_in.NgayBatDau,
                ngay_ket_thuc=semester_in.NgayKetThuc,
                trang_thai=semester_in.TrangThaiHocKy,
            )

            # Chỉ check ở publisher
            if SemesterRepo.get_by_id(primary_session, semester_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ma hoc ky '{semester_code}' da ton tai",
                )

            semester = Semester(
                MaHocKy=semester_code,
                NamHoc=semester_in.NamHoc,
                KySo=semester_in.KySo,
                NgayBatDau=semester_in.NgayBatDau,
                NgayKetThuc=semester_in.NgayKetThuc,
                TrangThaiHocKy=semester_in.TrangThaiHocKy,
            )

            # Chỉ ghi vào publisher
            primary_session.add(semester)
            primary_session.commit()
            primary_session.refresh(semester)

            return SemesterResponse.model_validate(semester)
        except Exception as e:
            primary_session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Create semester failed at publisher {primary_site}: {str(e)}",
            )
        finally:
            SemesterService._close_sessions(sessions)

    @staticmethod
    async def update_semester(ma_hoc_ky: str, semester_in: SemesterUpdate, current_user: User) -> SemesterResponse:
        SemesterService._ensure_admin(current_user)
        sessions = SemesterService._open_sessions()
        primary_site, primary_session = SemesterService._get_primary_session(sessions)

        try:
            semester_code = ma_hoc_ky.upper()
            existing = SemesterRepo.get_by_id(primary_session, semester_code)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay hoc ky voi ma: {semester_code}",
                )

            update_data = semester_in.model_dump(exclude_unset=True)
            SemesterService._validate_payload(
                ky_so=update_data.get("KySo", existing.KySo),
                ngay_bat_dau=update_data.get("NgayBatDau", existing.NgayBatDau),
                ngay_ket_thuc=update_data.get("NgayKetThuc", existing.NgayKetThuc),
                trang_thai=update_data.get("TrangThaiHocKy", existing.TrangThaiHocKy),
            )

            representative = None
            for site_name, session in sessions.items():
                semester = SemesterRepo.get_by_id(session, semester_code)
                if not semester:
                    continue
                for field, value in update_data.items():
                    setattr(semester, field, value)
                if site_name == primary_site:
                    representative = semester

            for session in sessions.values():
                session.commit()

            if representative is None:
                raise HTTPException(status_code=500, detail="Distributed update failed")

            primary_session.refresh(representative)
            return SemesterResponse.model_validate(representative)
        except Exception as e:
            for session in sessions.values():
                session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Distributed update failed: {str(e)}",
            )
        finally:
            SemesterService._close_sessions(sessions)

    @staticmethod
    async def delete_semester(ma_hoc_ky: str, current_user: User) -> None:
        SemesterService._ensure_admin(current_user)
        sessions = SemesterService._open_sessions()
        _, primary_session = SemesterService._get_primary_session(sessions)

        try:
            semester_code = ma_hoc_ky.upper()
            existing = SemesterRepo.get_by_id(primary_session, semester_code)
            if not existing:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay hoc ky voi ma: {semester_code}",
                )

            for session in sessions.values():
                in_use = session.query(CourseSection).filter(CourseSection.MaHocKy == semester_code).first()
                if in_use:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Hoc ky '{semester_code}' da duoc gan cho lop hoc phan '{in_use.MaLopHP}'",
                    )

            for session in sessions.values():
                semester = SemesterRepo.get_by_id(session, semester_code)
                if semester:
                    session.delete(semester)

            for session in sessions.values():
                session.commit()
        except Exception as e:
            for session in sessions.values():
                session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Distributed delete failed: {str(e)}",
            )
        finally:
            SemesterService._close_sessions(sessions)

    @staticmethod
    def _ensure_admin(current_user: User) -> None:
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can manage semesters",
            )

    @staticmethod
    def _validate_payload(ky_so: int, ngay_bat_dau, ngay_ket_thuc, trang_thai: SemesterStatus) -> None:
        if ky_so not in {1, 2, 3}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="KySo phai la 1, 2 hoac 3",
            )
        if not isinstance(trang_thai, SemesterStatus):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TrangThaiHocKy khong hop le. Phai la {[e.value for e in SemesterStatus]}",
            )
        if ngay_bat_dau and ngay_ket_thuc and ngay_ket_thuc <= ngay_bat_dau:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="NgayKetThuc phai lon hon NgayBatDau",
            )

    @staticmethod
    def _open_sessions() -> Dict[str, Session]:
        return {site: session_factory() for site, session_factory in SessionLocals.items()}

    @staticmethod
    def _get_primary_session(sessions: Dict[str, Session]) -> tuple[str, Session]:
        primary_site, primary_session = next(iter(sessions.items()), (None, None))
        if primary_site is None or primary_session is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Khong mo duoc ket noi den bat ky site nao",
            )
        return primary_site, primary_session

    @staticmethod
    def _close_sessions(sessions: Dict[str, Session]) -> None:
        for session in sessions.values():
            session.close()
