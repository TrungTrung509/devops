from datetime import date
from typing import Dict, Iterable, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.user_role import UserRole
from models.Classrooms import Classroom
from models.Courses import Course
from models.CourseSections import CourseSection
from models.Enrollments import Enrollment
from models.Schedules import Schedule
from models.Semesters import Semester
from models.Students import Student
from models.Teachers import Teacher
from models.Users import User
from models.Branches import Branch
from enums.types import StudyForm
from enums.status import (
    ClassSectionStatus, 
    CourseStatus, 
    SemesterStatus, 
    TeacherStatus, 
    RoomStatus, 
    EnrollmentStatus
)
from repositories.ClassSectionRepo import ClassSectionRepo
from schemas.ClassSection import (
    CourseSectionCreate,
    CourseSectionDetailResponse,
    CourseSectionListResponse,
    CourseSectionUpdate,
    EnrollmentResponse,
    ScheduleCreate,
    ScheduleResponse,
    ScheduleUpdate,
)


class ClassSectionService:
    @staticmethod
    def get_all_sections(
        keyword: Optional[str] = None,
        MaCoSo: Optional[str] = None,
        HinhThucHoc: Optional[str] = None,
        TrangThaiLop: Optional[str] = None,
    ) -> tuple[list[CourseSectionListResponse], int]:
        sessions = ClassSectionService._open_all_sessions()

        try:
            all_sections: list[tuple[str, Session, CourseSection]] = []
            for site, session in sessions.items():
                # If MaCoSo filter is set, only query that site
                if MaCoSo is not None and site.upper() != MaCoSo.upper():
                    continue

                query = ClassSectionRepo.base_query(session)

                # Keyword filter: search in MaLopHP or TenLopHP
                if keyword:
                    kw = keyword.strip()
                    if kw:
                        query = query.filter(
                            (CourseSection.MaLopHP.ilike(f"%{kw}%"))
                            | (CourseSection.TenLopHP.ilike(f"%{kw}%"))
                        )

                if HinhThucHoc:
                    query = query.filter(CourseSection.HinhThucHoc == HinhThucHoc)
   
                if TrangThaiLop:
                    query = query.filter(CourseSection.TrangThaiLop == TrangThaiLop)

                sections = query.order_by(CourseSection.MaLopHP.asc()).all()
                for section in sections:
                    all_sections.append((site, session, section))

            if not all_sections:
                return [], 0

            # Batch pre-load schedules per site to avoid N+1
            schedules_by_site: dict[str, dict[str, list[Schedule]]] = {}
            for site, session in sessions.items():
                site_section_ids = [s.MaLopHP for _, _, s in all_sections if s.MaCoSo == site]
                if site_section_ids:
                    schedules_by_site[site] = {}
                    rows = (
                        session.query(Schedule)
                        .filter(Schedule.MaLopHP.in_(site_section_ids))
                        .order_by(Schedule.ThuTrongTuan.asc(), Schedule.TietBatDau.asc())
                        .all()
                    )
                    for row in rows:
                        schedules_by_site[site].setdefault(row.MaLopHP, []).append(row)

            # Batch pre-load enrollments per site
            enrollments_by_site: dict[str, dict[str, list[Enrollment]]] = {}
            for site, session in sessions.items():
                site_section_ids = [s.MaLopHP for _, _, s in all_sections if s.MaCoSo == site]
                if site_section_ids:
                    enrollments_by_site[site] = {}
                    rows = (
                        session.query(Enrollment)
                        .filter(Enrollment.MaLopHP.in_(site_section_ids))
                        .all()
                    )
                    for row in rows:
                        enrollments_by_site[site].setdefault(row.MaLopHP, []).append(row)

            items = [
                ClassSectionService._build_section_response_batch(
                    session,
                    section,
                    schedules_by_site.get(site, {}).get(section.MaLopHP, []),
                    enrollments_by_site.get(site, {}).get(section.MaLopHP, []),
                )
                for site, session, section in all_sections
            ]

            items.sort(key=lambda item: item.MaLopHP)
            return items, len(items)
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    def get_section_by_id(ma_lop_hp: str) -> CourseSectionDetailResponse:
        sessions = ClassSectionService._open_all_sessions()

        try:
            site, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            return ClassSectionService._build_section_response(
                session,
                section,
                include_schedules=True,
                include_enrollments=True,
            )
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    def get_my_teaching_sections(current_user: User) -> tuple[list[CourseSectionListResponse], int]:
        ClassSectionService._ensure_roles(current_user, UserRole.GiangVien)
        site = ClassSectionService._normalize_site(current_user.MaCoSo)
        session = ClassSectionService._open_session_for_site(site)

        try:
            teacher = ClassSectionService._get_teacher_by_user(session, current_user.userId)
            sections = (
                ClassSectionRepo.base_query(session)
                .filter(CourseSection.MaGV == teacher.MaGV)
                .order_by(CourseSection.MaLopHP.asc())
                .all()
            )

            # Batch pre-load schedules and enrollments
            section_ids = [s.MaLopHP for s in sections]
            schedules_by_lop = {}
            if section_ids:
                rows = (
                    session.query(Schedule)
                    .filter(Schedule.MaLopHP.in_(section_ids))
                    .order_by(Schedule.ThuTrongTuan.asc(), Schedule.TietBatDau.asc())
                    .all()
                )
                for row in rows:
                    schedules_by_lop.setdefault(row.MaLopHP, []).append(row)

            enrollments_by_lop = {}
            if section_ids:
                rows = session.query(Enrollment).filter(Enrollment.MaLopHP.in_(section_ids)).all()
                for row in rows:
                    enrollments_by_lop.setdefault(row.MaLopHP, []).append(row)

            items = [
                ClassSectionService._build_section_response_batch(
                    session,
                    section,
                    schedules_by_lop.get(section.MaLopHP, []),
                    enrollments_by_lop.get(section.MaLopHP, []),
                )
                for section in sections
            ]
            return items, len(items)
        finally:
            session.close()

    @staticmethod
    def get_my_teaching_schedules(current_user: User) -> list[dict]:
        """
        Lấy tất cả lịch học của các lớp giảng viên đang phụ trách.
        Trả về danh sách schedule đã flatten (mỗi lịch 1 bản ghi) kèm thông tin lớp.
        """
        ClassSectionService._ensure_roles(current_user, UserRole.GiangVien)
        site = ClassSectionService._normalize_site(current_user.MaCoSo)
        session = ClassSectionService._open_session_for_site(site)

        try:
            teacher = ClassSectionService._get_teacher_by_user(session, current_user.userId)
            sections = (
                ClassSectionRepo.base_query(session)
                .filter(CourseSection.MaGV == teacher.MaGV)
                .all()
            )

            section_ids = [s.MaLopHP for s in sections]
            if not section_ids:
                return []

            # Batch load schedules + rooms + course info
            rows = (
                session.query(Schedule, Classroom, CourseSection, Course, Teacher, Branch)
                .join(Classroom, Schedule.MaPhong == Classroom.MaPhong, isouter=True)
                .join(CourseSection, Schedule.MaLopHP == CourseSection.MaLopHP)
                .join(Course, CourseSection.MaHP == Course.MaHocPhan)
                .join(Teacher, CourseSection.MaGV == Teacher.MaGV, isouter=True)
                .join(Branch, CourseSection.MaCoSo == Branch.MaCoSo, isouter=True)
                .filter(Schedule.MaLopHP.in_(section_ids))
                .order_by(Schedule.ThuTrongTuan.asc(), Schedule.TietBatDau.asc())
                .all()
            )

            result = []
            for schedule, room, section, course, teacher_obj, branch in rows:
                ten_gv = ClassSectionService._format_teacher_name(teacher_obj) if teacher_obj else None
                result.append({
                    "MaLich": schedule.MaLich,
                    "MaLopHP": schedule.MaLopHP,
                    "TenLopHP": section.TenLopHP,
                    "MaHP": course.MaHocPhan,
                    "TenHP": course.TenHocPhan,
                    "SoTinChi": course.SoTinChi,
                    "MaHocKy": section.MaHocKy,
                    "MaCoSo": section.MaCoSo,
                    "TenCoSo": branch.TenCoSo if branch else section.MaCoSo,
                    "HinhThucHoc": section.HinhThucHoc.value if hasattr(section.HinhThucHoc, 'value') else str(section.HinhThucHoc),
                    "MaGV": section.MaGV,
                    "TenGiangVien": ten_gv,
                    "MaPhong": schedule.MaPhong,
                    "TenPhong": room.TenPhong if room else None,
                    "ToaNha": room.ToaNha if room else None,
                    "ThuTrongTuan": schedule.ThuTrongTuan,
                    "TietBatDau": schedule.TietBatDau,
                    "SoTiet": schedule.SoTiet,
                    "NgayBatDau": schedule.NgayBatDau,
                    "NgayKetThuc": schedule.NgayKetThuc,
                    "GhiChu": schedule.GhiChu,
                })
            return result
        finally:
            session.close()

    @staticmethod
    def get_section_schedules(ma_lop_hp: str) -> list[ScheduleResponse]:
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            return ClassSectionService._build_schedule_responses(
                session,
                ClassSectionRepo.list_schedules(session, section.MaLopHP),
            )
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    def get_section_enrollments(ma_lop_hp: str, current_user: User) -> list[EnrollmentResponse]:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin, UserRole.GiangVien)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            ClassSectionService._ensure_can_view_enrollments(session, section, current_user)
            return ClassSectionService._build_enrollment_responses(
                session,
                ClassSectionRepo.list_enrollments(session, section.MaLopHP),
            )
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    async def create_section(section_in: CourseSectionCreate, current_user: User) -> CourseSectionDetailResponse:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        site = ClassSectionService._normalize_site(section_in.MaCoSo)
        session = ClassSectionService._open_session_for_site(site)

        try:
            input_code = section_in.MaLopHP.upper()
            # Tự động thêm tiền tố site nếu chưa có để tối ưu định tuyến DB
            if not input_code.startswith(f"{site}_"):
                section_code = f"{site}_{input_code}"
            else:
                section_code = input_code

            if ClassSectionRepo.get_by_id(session, section_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ma lop hoc phan '{section_code}' da ton tai",
                )

            course = ClassSectionService._ensure_course_exists(session, section_in.MaHocPhan)
            semester = ClassSectionService._ensure_semester_exists(session, section_in.MaHocKy)
            teacher = ClassSectionService._ensure_teacher_exists(session, section_in.MaGV)
            ClassSectionService._validate_section_payload(
                semester=semester,
                teacher=teacher,
                site=site,
                si_so_toi_da=section_in.SiSoToiDa,
                si_so_hien_tai=0,
                hinh_thuc_hoc=section_in.HinhThucHoc,
                trang_thai_lop=section_in.TrangThaiLop,
            )

            section = CourseSection(
                MaLopHP=section_code,
                MaHP=course.MaHocPhan,
                MaHocKy=semester.MaHocKy,
                MaCoSo=site,
                MaGV=teacher.MaGV,
                TenLopHP=section_in.TenLopHP or section_code,
                SiSoToiDa=section_in.SiSoToiDa,
                SiSoHienTai=0,
                HinhThucHoc=section_in.HinhThucHoc,
                TrangThaiLop=section_in.TrangThaiLop,
            )
            session.add(section)
            session.commit()
            session.refresh(section)
            return ClassSectionService._build_section_response(
                session,
                section,
                include_schedules=True,
                include_enrollments=True,
            )
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @staticmethod
    async def update_section(
        ma_lop_hp: str,
        section_in: CourseSectionUpdate,
        current_user: User,
    ) -> CourseSectionDetailResponse:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            update_data = section_in.model_dump(exclude_unset=True)
            if not update_data:
                return ClassSectionService._build_section_response(
                    session,
                    section,
                    include_schedules=True,
                    include_enrollments=True,
                )

            new_teacher = None
            if update_data.get("MaGV"):
                new_teacher = ClassSectionService._ensure_teacher_exists(session, update_data["MaGV"])
                update_data["MaGV"] = new_teacher.MaGV

            active_count = ClassSectionRepo.count_active_enrollments(session, section.MaLopHP)
            new_capacity = update_data.get("SiSoToiDa", section.SiSoToiDa)
            new_form = update_data.get("HinhThucHoc", section.HinhThucHoc)
            new_status = update_data.get("TrangThaiLop", section.TrangThaiLop)
            ClassSectionService._validate_section_payload(
                semester=ClassSectionService._ensure_semester_exists(session, section.MaHocKy),
                teacher=new_teacher or ClassSectionService._ensure_teacher_exists(session, section.MaGV),
                site=section.MaCoSo,
                si_so_toi_da=new_capacity,
                si_so_hien_tai=active_count,
                hinh_thuc_hoc=new_form,
                trang_thai_lop=new_status,
            )
            ClassSectionService._ensure_capacity_matches_existing_rooms(session, section, new_capacity)

            for field, value in update_data.items():
                setattr(section, field, value)

            ClassSectionService._ensure_teacher_schedule_available(session, section)
            session.commit()
            session.refresh(section)
            return ClassSectionService._build_section_response(
                session,
                section,
                include_schedules=True,
                include_enrollments=True,
            )
        except Exception:
            for current_session in sessions.values():
                current_session.rollback()
            raise
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    async def delete_section(ma_lop_hp: str, current_user: User) -> None:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            enrollments = ClassSectionRepo.list_enrollments(session, section.MaLopHP)
            if enrollments:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Khong the xoa lop hoc phan da co du lieu dang ky",
                )

            session.delete(section)
            session.commit()
        except Exception:
            for current_session in sessions.values():
                current_session.rollback()
            raise
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    async def add_schedule(
        ma_lop_hp: str,
        schedule_in: ScheduleCreate,
        current_user: User,
    ) -> ScheduleResponse:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            if ClassSectionRepo.get_schedule(session, section.MaLopHP, schedule_in.MaLich.upper()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Ma lich '{schedule_in.MaLich.upper()}' da ton tai trong lop",
                )

            room = ClassSectionService._ensure_room_exists(session, schedule_in.MaPhong)
            semester = ClassSectionService._ensure_semester_exists(session, section.MaHocKy)
            ClassSectionService._validate_schedule_payload(
                semester=semester,
                room=room,
                section=section,
                thu_trong_tuan=schedule_in.ThuTrongTuan,
                tiet_bat_dau=schedule_in.TietBatDau,
                so_tiet=schedule_in.SoTiet,
                ngay_bat_dau=schedule_in.NgayBatDau,
                ngay_ket_thuc=schedule_in.NgayKetThuc,
            )
            ClassSectionService._ensure_schedule_conflicts(
                session=session,
                section=section,
                ma_lich=None,
                ma_phong=room.MaPhong,
                thu_trong_tuan=schedule_in.ThuTrongTuan,
                tiet_bat_dau=schedule_in.TietBatDau,
                so_tiet=schedule_in.SoTiet,
                ngay_bat_dau=schedule_in.NgayBatDau,
                ngay_ket_thuc=schedule_in.NgayKetThuc,
            )

            schedule = Schedule(
                MaLich=schedule_in.MaLich.upper(),
                MaLopHP=section.MaLopHP,
                MaPhong=room.MaPhong,
                ThuTrongTuan=schedule_in.ThuTrongTuan,
                TietBatDau=schedule_in.TietBatDau,
                SoTiet=schedule_in.SoTiet,
                NgayBatDau=schedule_in.NgayBatDau,
                NgayKetThuc=schedule_in.NgayKetThuc,
                GhiChu=schedule_in.GhiChu,
            )
            session.add(schedule)
            session.commit()
            session.refresh(schedule)
            return ClassSectionService._build_schedule_response(session, schedule)
        except Exception:
            for current_session in sessions.values():
                current_session.rollback()
            raise
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    async def update_schedule(
        ma_lop_hp: str,
        ma_lich: str,
        schedule_in: ScheduleUpdate,
        current_user: User,
    ) -> ScheduleResponse:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            schedule = ClassSectionRepo.get_schedule(session, section.MaLopHP, ma_lich.upper())
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay lich hoc voi ma: {ma_lich.upper()}",
                )

            update_data = schedule_in.model_dump(exclude_unset=True)
            room = ClassSectionService._ensure_room_exists(
                session,
                update_data.get("MaPhong", schedule.MaPhong),
            )
            semester = ClassSectionService._ensure_semester_exists(session, section.MaHocKy)
            thu_trong_tuan = update_data.get("ThuTrongTuan", schedule.ThuTrongTuan)
            tiet_bat_dau = update_data.get("TietBatDau", schedule.TietBatDau)
            so_tiet = update_data.get("SoTiet", schedule.SoTiet)
            ngay_bat_dau = update_data.get("NgayBatDau", schedule.NgayBatDau)
            ngay_ket_thuc = update_data.get("NgayKetThuc", schedule.NgayKetThuc)

            ClassSectionService._validate_schedule_payload(
                semester=semester,
                room=room,
                section=section,
                thu_trong_tuan=thu_trong_tuan,
                tiet_bat_dau=tiet_bat_dau,
                so_tiet=so_tiet,
                ngay_bat_dau=ngay_bat_dau,
                ngay_ket_thuc=ngay_ket_thuc,
            )
            ClassSectionService._ensure_schedule_conflicts(
                session=session,
                section=section,
                ma_lich=schedule.MaLich,
                ma_phong=room.MaPhong,
                thu_trong_tuan=thu_trong_tuan,
                tiet_bat_dau=tiet_bat_dau,
                so_tiet=so_tiet,
                ngay_bat_dau=ngay_bat_dau,
                ngay_ket_thuc=ngay_ket_thuc,
            )

            for field, value in update_data.items():
                setattr(schedule, field, value)

            session.commit()
            session.refresh(schedule)
            return ClassSectionService._build_schedule_response(session, schedule)
        except Exception:
            for current_session in sessions.values():
                current_session.rollback()
            raise
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    async def delete_schedule(ma_lop_hp: str, ma_lich: str, current_user: User) -> None:
        ClassSectionService._ensure_roles(current_user, UserRole.Admin)
        sessions = ClassSectionService._open_all_sessions()

        try:
            _, session, section = ClassSectionService._find_section_context(sessions, ma_lop_hp)
            schedule = ClassSectionRepo.get_schedule(session, section.MaLopHP, ma_lich.upper())
            if not schedule:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Khong tim thay lich hoc voi ma: {ma_lich.upper()}",
                )

            session.delete(schedule)
            session.commit()
        except Exception:
            for current_session in sessions.values():
                current_session.rollback()
            raise
        finally:
            ClassSectionService._close_sessions(sessions)

    @staticmethod
    def _build_section_response(
        db: Session,
        section: CourseSection,
        include_schedules: bool = False,
        include_enrollments: bool = False,
    ) -> CourseSectionDetailResponse:
        course = ClassSectionService._ensure_course_exists(db, section.MaHP)
        semester = ClassSectionService._ensure_semester_exists(db, section.MaHocKy)
        teacher = ClassSectionService._ensure_teacher_exists(db, section.MaGV)
        schedules = ClassSectionRepo.list_schedules(db, section.MaLopHP) if include_schedules else []
        enrollments = ClassSectionRepo.list_enrollments(db, section.MaLopHP) if include_enrollments else []
        active_count = sum(1 for enrollment in enrollments if enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy)

        return CourseSectionDetailResponse(
            MaLopHP=section.MaLopHP,
            MaHocPhan=section.MaHP,
            TenHocPhan=course.TenHocPhan,
            MaHocKy=section.MaHocKy,
            NamHoc=semester.NamHoc,
            KySo=semester.KySo,
            MaCoSo=section.MaCoSo,
            MaGV=section.MaGV,
            TenGiangVien=ClassSectionService._format_teacher_name(teacher),
            TenLopHP=section.TenLopHP,
            SiSoToiDa=section.SiSoToiDa,
            SiSoHienTai=active_count,
            SoChoConLai=max(section.SiSoToiDa - active_count, 0),
            HinhThucHoc=section.HinhThucHoc,
            TrangThaiLop=section.TrangThaiLop,
            SoLuongLichHoc=len(schedules),
            NgayTao=section.NgayTao,
            LichHoc=ClassSectionService._build_schedule_responses(db, schedules),
            DanhSachDangKy=ClassSectionService._build_enrollment_responses(db, enrollments) if include_enrollments else [],
        )

    @staticmethod
    def _build_section_response_batch(
        db: Session,
        section: CourseSection,
        schedules: list[Schedule],
        enrollments: list[Enrollment],
    ) -> CourseSectionListResponse:
        course = ClassSectionService._ensure_course_exists(db, section.MaHP)
        semester = ClassSectionService._ensure_semester_exists(db, section.MaHocKy)
        teacher = ClassSectionService._ensure_teacher_exists(db, section.MaGV)
        active_count = sum(1 for enrollment in enrollments if enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy)

        return CourseSectionListResponse(
            MaLopHP=section.MaLopHP,
            MaHocPhan=section.MaHP,
            TenHocPhan=course.TenHocPhan,
            MaHocKy=section.MaHocKy,
            NamHoc=semester.NamHoc,
            KySo=semester.KySo,
            MaCoSo=section.MaCoSo,
            MaGV=section.MaGV,
            TenGiangVien=ClassSectionService._format_teacher_name(teacher),
            TenLopHP=section.TenLopHP,
            SiSoToiDa=section.SiSoToiDa,
            SiSoHienTai=active_count,
            SoChoConLai=max(section.SiSoToiDa - active_count, 0),
            HinhThucHoc=section.HinhThucHoc,
            TrangThaiLop=section.TrangThaiLop,
            SoLuongLichHoc=len(schedules),
            NgayTao=section.NgayTao,
            LichHoc=ClassSectionService._build_schedule_responses(db, schedules),
        )

    @staticmethod
    def _build_schedule_responses(db: Session, schedules: Iterable[Schedule]) -> list[ScheduleResponse]:
        return [ClassSectionService._build_schedule_response(db, schedule) for schedule in schedules]

    @staticmethod
    def _build_schedule_response(db: Session, schedule: Schedule) -> ScheduleResponse:
        room = db.query(Classroom).filter(Classroom.MaPhong == schedule.MaPhong).first()
        return ScheduleResponse(
            MaLich=schedule.MaLich,
            MaLopHP=schedule.MaLopHP,
            MaPhong=schedule.MaPhong,
            TenPhong=room.TenPhong if room else None,
            ToaNha=room.ToaNha if room else None,
            ThuTrongTuan=schedule.ThuTrongTuan,
            TietBatDau=schedule.TietBatDau,
            SoTiet=schedule.SoTiet,
            NgayBatDau=schedule.NgayBatDau,
            NgayKetThuc=schedule.NgayKetThuc,
            GhiChu=schedule.GhiChu,
        )

    @staticmethod
    def _build_enrollment_responses(db: Session, enrollments: Iterable[Enrollment]) -> list[EnrollmentResponse]:
        items: list[EnrollmentResponse] = []
        for enrollment in enrollments:
            # Tìm Student qua userId (vì Enrollment giờ dùng userId, không dùng MaSV làm FK)
            student = db.query(Student).filter(Student.userId == enrollment.userId).first()
            items.append(
                EnrollmentResponse(
                    MaDangKy=enrollment.MaDangKy,
                    MaSV=student.MaSV if student else enrollment.MaSV,
                    MaLich=getattr(enrollment, 'MaLich', None),
                    HoTenSinhVien=ClassSectionService._format_student_name(student),
                    TrangThaiDangKy=enrollment.TrangThaiDangKy,
                    LanDangKy=enrollment.LanDangKy,
                    NgayDangKy=enrollment.NgayDangKy,
                    GhiChu=enrollment.GhiChu,
                )
            )
        return items

    @staticmethod
    def _ensure_can_view_enrollments(db: Session, section: CourseSection, current_user: User) -> None:
        role = ClassSectionService._current_role(current_user)
        if role == UserRole.Admin.value:
            return
        teacher = ClassSectionService._get_teacher_by_user(db, current_user.userId)
        if teacher.MaGV != section.MaGV:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chi giang vien phu trach moi duoc xem danh sach dang ky cua lop nay",
            )

    @staticmethod
    def _ensure_course_exists(db: Session, ma_hoc_phan: str) -> Course:
        course = db.query(Course).filter(Course.MaHocPhan == ma_hoc_phan.upper()).first()
        if not course:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ma hoc phan khong hop le: {ma_hoc_phan.upper()}",
            )
        if course.TrangThai != CourseStatus.HoatDong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hoc phan '{course.MaHocPhan}' khong o trang thai hoat dong",
            )
        return course

    @staticmethod
    def _ensure_semester_exists(db: Session, ma_hoc_ky: str) -> Semester:
        semester = db.query(Semester).filter(Semester.MaHocKy == ma_hoc_ky.upper()).first()
        if not semester:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ma hoc ky khong hop le: {ma_hoc_ky.upper()}",
            )
        return semester

    @staticmethod
    def _ensure_teacher_exists(db: Session, ma_gv: str) -> Teacher:
        teacher = db.query(Teacher).filter(Teacher.MaGV == ma_gv.upper()).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ma giang vien khong hop le: {ma_gv.upper()}",
            )
        if teacher.TrangThai != TeacherStatus.DangCongTac:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Giang vien '{teacher.MaGV}' khong o trang thai dang cong tac",
            )
        return teacher

    @staticmethod
    def _get_teacher_by_user(db: Session, user_id: str) -> Teacher:
        teacher = db.query(Teacher).filter(Teacher.userId == user_id).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Khong tim thay thong tin giang vien tu tai khoan hien tai",
            )
        return teacher

    @staticmethod
    def _ensure_room_exists(db: Session, ma_phong: str) -> Classroom:
        room = db.query(Classroom).filter(Classroom.MaPhong == ma_phong.upper()).first()
        if not room:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ma phong khong hop le: {ma_phong.upper()}",
            )
        if room.TrangThai != RoomStatus.HoatDong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phong hoc '{room.MaPhong}' khong san sang de xep lich",
            )
        return room

    @staticmethod
    def _validate_section_payload(
        semester: Semester,
        teacher: Teacher,
        site: str,
        si_so_toi_da: int,
        si_so_hien_tai: int,
        hinh_thuc_hoc: str,
        trang_thai_lop: str,
    ) -> None:
        if teacher.MaCoSo.upper() != site:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Giang vien phai thuoc cung co so voi lop hoc phan",
            )
        if si_so_toi_da <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Si so toi da phai lon hon 0",
            )
        if si_so_hien_tai > si_so_toi_da:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Si so toi da khong duoc nho hon si so hien tai",
            )
        if not isinstance(hinh_thuc_hoc, StudyForm):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"HinhThucHoc khong hop le. Phai la {[e.value for e in StudyForm]}",
            )
        if not isinstance(trang_thai_lop, ClassSectionStatus):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TrangThaiLop khong hop le. Phai la {[e.value for e in ClassSectionStatus]}",
            )
        if semester.TrangThaiHocKy == SemesterStatus.DaKetThuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Hoc ky '{semester.MaHocKy}' da ket thuc, khong the mo lop moi",
            )

    @staticmethod
    def _validate_schedule_payload(
        semester: Semester,
        room: Classroom,
        section: CourseSection,
        thu_trong_tuan: int,
        tiet_bat_dau: int,
        so_tiet: int,
        ngay_bat_dau: date,
        ngay_ket_thuc: date,
    ) -> None:
        if room.MaCoSo.upper() != section.MaCoSo.upper():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phong hoc phai thuoc cung co so voi lop hoc phan",
            )
        if room.SucChua < section.SiSoToiDa:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Phong '{room.MaPhong}' khong du suc chua cho si so toi da cua lop",
            )
        if ngay_bat_dau > ngay_ket_thuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay bat dau lich hoc khong duoc lon hon ngay ket thuc",
            )
        if tiet_bat_dau + so_tiet - 1 > 15:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khung tiet hoc vuot qua so tiet cho phep trong ngay",
            )
        if semester.NgayBatDau and ngay_bat_dau < semester.NgayBatDau:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay bat dau lich hoc phai nam trong hoc ky",
            )
        if semester.NgayKetThuc and ngay_ket_thuc > semester.NgayKetThuc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ngay ket thuc lich hoc phai nam trong hoc ky",
            )
        if section.TrangThaiLop == ClassSectionStatus.Huy:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Khong the xep lich cho lop da bi huy",
            )
        if thu_trong_tuan < 2 or thu_trong_tuan > 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ThuTrongTuan phai nam trong khoang tu 2 den 8",
            )

    @staticmethod
    def _ensure_schedule_conflicts(
        session: Session,
        section: CourseSection,
        ma_lich: str | None,
        ma_phong: str,
        thu_trong_tuan: int,
        tiet_bat_dau: int,
        so_tiet: int,
        ngay_bat_dau: date,
        ngay_ket_thuc: date,
    ) -> None:
        end_period = tiet_bat_dau + so_tiet - 1
        candidate_schedules = session.query(Schedule).filter(Schedule.ThuTrongTuan == thu_trong_tuan).all()
        for schedule in candidate_schedules:
            if ma_lich and schedule.MaLich == ma_lich:
                continue
            if not ClassSectionService._date_ranges_overlap(
                schedule.NgayBatDau,
                schedule.NgayKetThuc,
                ngay_bat_dau,
                ngay_ket_thuc,
            ):
                continue
            schedule_end_period = schedule.TietBatDau + schedule.SoTiet - 1
            if not ClassSectionService._period_ranges_overlap(
                schedule.TietBatDau,
                schedule_end_period,
                tiet_bat_dau,
                end_period,
            ):
                continue

            other_section = ClassSectionRepo.get_by_id(session, schedule.MaLopHP)
            if other_section is None:
                continue

            if schedule.MaLopHP == section.MaLopHP:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lich hoc moi bi trung khung gio voi lich '{schedule.MaLich}' cua cung lop",
                )
            if schedule.MaPhong == ma_phong:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phong '{ma_phong}' da co lop khac su dung trong khung gio nay",
                )
            if other_section.MaGV == section.MaGV:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Giang vien dang bi trung lich voi lop hoc phan khac",
                )

    @staticmethod
    def _ensure_capacity_matches_existing_rooms(
        db: Session,
        section: CourseSection,
        new_capacity: int,
    ) -> None:
        schedules = ClassSectionRepo.list_schedules(db, section.MaLopHP)
        for schedule in schedules:
            room = ClassSectionService._ensure_room_exists(db, schedule.MaPhong)
            if room.SucChua < new_capacity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Phong '{room.MaPhong}' trong lich hien tai khong du suc chua cho si so moi",
                )

    @staticmethod
    def _ensure_teacher_schedule_available(db: Session, section: CourseSection) -> None:
        schedules = ClassSectionRepo.list_schedules(db, section.MaLopHP)
        for schedule in schedules:
            ClassSectionService._ensure_schedule_conflicts(
                session=db,
                section=section,
                ma_lich=schedule.MaLich,
                ma_phong=schedule.MaPhong,
                thu_trong_tuan=schedule.ThuTrongTuan,
                tiet_bat_dau=schedule.TietBatDau,
                so_tiet=schedule.SoTiet,
                ngay_bat_dau=schedule.NgayBatDau,
                ngay_ket_thuc=schedule.NgayKetThuc,
            )

    @staticmethod
    def _find_section_context(
        sessions: Dict[str, Session],
        ma_lop_hp: str,
    ) -> tuple[str, Session, CourseSection]:
        section_code = ma_lop_hp.upper()
        
        # Tối ưu hóa: Nếu mã có chứa prefix [SITE]_, truy cập thẳng site đó
        if "_" in section_code:
            site_prefix = section_code.split("_")[0]
            if site_prefix in sessions:
                session = sessions[site_prefix]
                section = ClassSectionRepo.get_by_id(session, section_code)
                if section:
                    return site_prefix, session, section

        # Fallback: Quét tất cả các site (cho các mã cũ hoặc không đúng định dạng prefix)
        for site, session in sessions.items():
            section = ClassSectionRepo.get_by_id(session, section_code)
            if section:
                return site, session, section
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Khong tim thay lop hoc phan voi ma: {section_code}",
        )

    @staticmethod
    def _open_all_sessions() -> Dict[str, Session]:
        return {site: session_factory() for site, session_factory in SessionLocals.items()}

    @staticmethod
    def _open_session_for_site(site: str) -> Session:
        if site not in SessionLocals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ma co so khong hop le: {site}",
            )
        return SessionLocals[site]()

    @staticmethod
    def _close_sessions(sessions: Dict[str, Session]) -> None:
        for session in sessions.values():
            session.close()

    @staticmethod
    def _ensure_roles(current_user: User, *roles: UserRole) -> None:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {', '.join([r.value for r in roles])}",
            )

    @staticmethod
    def _normalize_site(site: str) -> str:
        return (site or "").upper()

    @staticmethod
    def _current_role(current_user: User) -> str:
        return current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)

    @staticmethod
    def _format_teacher_name(teacher: Teacher | None) -> str | None:
        if teacher is None:
            return None
        return f"{teacher.Ho} {teacher.Ten}".strip()

    @staticmethod
    def _format_student_name(student: Student | None) -> str | None:
        if student is None:
            return None
        return f"{student.Ho} {student.Ten}".strip()

    @staticmethod
    def _date_ranges_overlap(
        first_start: date | None,
        first_end: date | None,
        second_start: date | None,
        second_end: date | None,
    ) -> bool:
        if first_start is None or first_end is None or second_start is None or second_end is None:
            return True
        return max(first_start, second_start) <= min(first_end, second_end)

    @staticmethod
    def _period_ranges_overlap(first_start: int, first_end: int, second_start: int, second_end: int) -> bool:
        return max(first_start, second_start) <= min(first_end, second_end)
