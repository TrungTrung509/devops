from sqlalchemy.orm import Session
from sqlalchemy import text
from models.models import CourseSection, Enrollment, EnrollmentTransfer

class ClassSectionRepo:
    @staticmethod
    def get_by_id(db: Session, ma_lop_hp: str) -> CourseSection | None:
        return db.query(CourseSection).filter(CourseSection.MaLopHP == ma_lop_hp).first()

    @staticmethod
    def get_by_id_for_update(db: Session, ma_lop_hp: str) -> CourseSection | None:
        result = db.execute(
            text('SELECT * FROM "LopHocPhan" WHERE "MaLopHP" = :id FOR UPDATE'),
            {"id": ma_lop_hp}
        ).mappings().first()
        if not result:
            return None
        sec = db.query(CourseSection).filter(CourseSection.MaLopHP == ma_lop_hp).first()
        return sec

class EnrollmentRepo:
    @staticmethod
    def get_student_enrollments(db: Session, user_id: str):
        return db.query(Enrollment).filter(Enrollment.userId == user_id).all()

    @staticmethod
    def get_student_transfers(db: Session, user_id: str):
        return db.query(EnrollmentTransfer).filter(EnrollmentTransfer.userId == user_id).all()
