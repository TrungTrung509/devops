from sqlalchemy import func
from sqlalchemy.orm import Query, Session

from models.CourseSections import CourseSection
from models.Enrollments import Enrollment
from models.Schedules import Schedule


class ClassSectionRepo:
    @staticmethod
    def base_query(db: Session) -> Query:
        return db.query(CourseSection)

    @staticmethod
    def get_by_id(db: Session, ma_lop_hp: str) -> CourseSection | None:
        return db.query(CourseSection).filter(CourseSection.MaLopHP == ma_lop_hp).first()

    @staticmethod
    def get_by_id_for_update(db: Session, ma_lop_hp: str) -> CourseSection | None:
        from sqlalchemy import text
        sql = text('SELECT * FROM "LopHocPhan" WHERE "MaLopHP" = :ma_lop_hp FOR UPDATE')
        return db.query(CourseSection).from_statement(sql).params(ma_lop_hp=ma_lop_hp).first()

    @staticmethod
    def list_schedules(db: Session, ma_lop_hp: str) -> list[Schedule]:
        return (
            db.query(Schedule)
            .filter(Schedule.MaLopHP == ma_lop_hp)
            .order_by(Schedule.ThuTrongTuan.asc(), Schedule.TietBatDau.asc(), Schedule.MaLich.asc())
            .all()
        )

    @staticmethod
    def get_schedule(db: Session, ma_lop_hp: str, ma_lich: str) -> Schedule | None:
        return (
            db.query(Schedule)
            .filter(Schedule.MaLopHP == ma_lop_hp, Schedule.MaLich == ma_lich)
            .first()
        )

    @staticmethod
    def list_enrollments(db: Session, ma_lop_hp: str) -> list[Enrollment]:
        return (
            db.query(Enrollment)
            .filter(Enrollment.MaLopHP == ma_lop_hp)
            .order_by(Enrollment.NgayDangKy.asc(), Enrollment.MaDangKy.asc())
            .all()
        )

    @staticmethod
    def count_active_enrollments(db: Session, ma_lop_hp: str) -> int:
        return (
            db.query(func.count(Enrollment.MaDangKy))
            .filter(
                Enrollment.MaLopHP == ma_lop_hp,
                Enrollment.TrangThaiDangKy == "DaDangKy",
            )
            .scalar()
            or 0
        )
