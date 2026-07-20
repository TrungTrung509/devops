from sqlalchemy.orm import Session
from models.Enrollments import Enrollment
from enums.status import EnrollmentStatus


class EnrollmentRepo:

    @staticmethod
    def get_student_enrollments(db: Session, user_id: str, ma_hoc_ky: str = None):
        """Danh sách đăng ký active của sinh viên (truy vấn tại Site nhà)"""
        query = db.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy
        )
        if ma_hoc_ky:
            query = query.filter(Enrollment.MaHocKy == ma_hoc_ky)
        return query.all()

    @staticmethod
    def find_active_enrollment(db: Session, user_id: str, ma_hp: str, ma_hk: str):
        """Tìm đăng ký active (để detect switch class)"""
        return db.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.MaHP == ma_hp,
            Enrollment.MaHocKy == ma_hk,
            Enrollment.TrangThaiDangKy == EnrollmentStatus.DaDangKy
        ).first()

    @staticmethod
    def find_any_enrollment(
        db: Session,
        user_id: str,
        ma_hp: str,
        ma_hk: str,
        exclude_ma_lop_hp: str = None
    ):
        """Tìm bất kỳ enrollment (dùng check duplicate)"""
        query = db.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.MaHP == ma_hp,
            Enrollment.MaHocKy == ma_hk
        )
        if exclude_ma_lop_hp:
            query = query.filter(Enrollment.MaLopHP != exclude_ma_lop_hp)
        return query.first()

    @staticmethod
    def is_already_enrolled(
        db: Session,
        user_id: str,
        ma_hp: str,
        ma_hk: str,
        exclude_ma_lop_hp: str = None
    ):
        return EnrollmentRepo.find_any_enrollment(
            db, user_id, ma_hp, ma_hk, exclude_ma_lop_hp
        ) is not None

    @staticmethod
    def get_by_lop_user(db: Session, user_id: str, ma_lop_hp: str):
        return db.query(Enrollment).filter(
            Enrollment.userId == user_id,
            Enrollment.MaLopHP == ma_lop_hp
        ).first()