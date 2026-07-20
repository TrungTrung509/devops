from datetime import date, datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.status import UserStatus, StudentStatus
from enums.user_role import UserRole
from models.Students import Student
from models.Users import User
from repositories.StudentRepo import StudentRepo
from repositories.UserRepo import UserRepo
from schemas.Student import (
    StudentCreate,
    StudentUpdate,
    StudentStatusUpdate,
    StudentResponse,
    StudentFilter,
)
from services.AuthService import AuthService
from services.UserService import UserService


class StudentManagementService:
    """
    Service xử lý nghiệp vụ Sinh viên.
    SinhVien thuộc site theo MaCoSo - đọc/ghi đúng site sở hữu.
    """

    @staticmethod
    def get_all_students(
        db: Session, filters: Optional[StudentFilter] = None, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Student], int, dict]:
        """
        Lấy danh sách sinh viên với filter.
        """
        query = db.query(Student)

        if filters:
            if filters.MaCoSo:
                query = query.filter(Student.MaCoSo == filters.MaCoSo.upper())
            if filters.MaKhoa:
                query = query.filter(Student.MaKhoa == filters.MaKhoa.upper())
            if filters.TrangThai:
                query = query.filter(Student.TrangThai == filters.TrangThai)
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                query = query.filter(
                    or_(
                        Student.MaSV.ilike(keyword),
                        Student.Ho.ilike(keyword),
                        Student.Ten.ilike(keyword),
                    )
                )

        offset = skip * limit
        total = query.count()
        students = query.offset(offset).limit(limit).all()

        # Calculate stats based on filters, excluding TrangThai filter
        stats_query = db.query(Student.TrangThai, func.count(Student.MaSV))
        if filters:
            if filters.MaCoSo:
                stats_query = stats_query.filter(Student.MaCoSo == filters.MaCoSo.upper())
            if filters.MaKhoa:
                stats_query = stats_query.filter(Student.MaKhoa == filters.MaKhoa.upper())
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                stats_query = stats_query.filter(
                    or_(
                        Student.MaSV.ilike(keyword),
                        Student.Ho.ilike(keyword),
                        Student.Ten.ilike(keyword),
                    )
                )
        stats_rows = stats_query.group_by(Student.TrangThai).all()
        status_counts = {
            (r[0].value if hasattr(r[0], "value") else str(r[0])): r[1]
            for r in stats_rows
        }

        return students, total, status_counts

    @staticmethod
    def get_student_by_masv(db: Session, ma_sv: str) -> Optional[Student]:
        """Lấy sinh viên theo MaSV"""
        student = db.query(Student).filter(Student.MaSV == ma_sv).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sinh viên với mã: {ma_sv}",
            )
        return student

    @staticmethod
    def get_student_by_userid(db: Session, user_id: str) -> Optional[Student]:
        """Lấy sinh viên theo userId"""
        student = db.query(Student).filter(Student.userId == user_id).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sinh viên với userId: {user_id}",
            )
        return student

    @staticmethod
    def get_students_by_coso(db: Session, ma_co_so: str) -> List[Student]:
        """Lấy danh sách sinh viên theo cơ sở"""
        return db.query(Student).filter(Student.MaCoSo == ma_co_so.upper()).all()

    @staticmethod
    async def create_student(
        student_in: StudentCreate, current_user: User
    ) -> StudentResponse:
        """
        Tạo mới sinh viên (Distributed).
        Yêu cầu: Admin role
        Logic di chuyển từ UserService để tập trung quản lý.
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can create students",
            )

        sessions = {
            site: session_factory() for site, session_factory in SessionLocals.items()
        }

        try:
            # Tự sinh mã nếu không cung cấp
            ma_sv = student_in.MaSV
            if not ma_sv:
                ma_sv = UserService.generate_id(UserRole.SinhVien, student_in.MaCoSo, student_in.MaKhoa)

            if UserRepo.get_by_username(sessions["HADONG"], ma_sv):
                raise HTTPException(
                    status_code=400, detail=f"Username '{ma_sv}' đã tồn tại"
                )

            email_to_check = student_in.email
            if email_to_check and email_to_check.lower() == "string":
                email_to_check = None

            if email_to_check and UserRepo.get_by_email(sessions["HADONG"], email_to_check):
                raise HTTPException(
                    status_code=400, detail=f"Email '{email_to_check}' đã được sử dụng"
                )

            db_local = sessions.get(student_in.MaCoSo)
            if not db_local:
                raise HTTPException(
                    status_code=400, detail=f"Cơ sở không hợp lệ: {student_in.MaCoSo}"
                )

            if StudentRepo.get_by_MaSV(db_local, ma_sv):
                raise HTTPException(
                    status_code=400, detail="Mã sinh viên (MaSV) đã tồn tại"
                )

            hashed_password = AuthService.get_password_hash(ma_sv)

            db_user_data = {
                "userId": ma_sv,
                "username": ma_sv,
                "password": hashed_password,
                "role": UserRole.SinhVien,
                "email": email_to_check,
                "MaCoSo": student_in.MaCoSo,
                "status": UserStatus.Active,
                "NgayTao": datetime.now().isoformat(),
            }

            for session in sessions.values():
                session.add(User(**db_user_data))

            db_student = Student(
                MaSV=ma_sv,
                userId=ma_sv,
                Ho=student_in.Ho,
                Ten=student_in.Ten,
                NgaySinh=student_in.NgaySinh,
                GioiTinh=student_in.GioiTinh,
                SDT=student_in.SDT,
                DiaChi=student_in.DiaChi,
                TrangThai=student_in.TrangThai or StudentStatus.DangHoc,
                MaCoSo=student_in.MaCoSo,
                MaKhoa=student_in.MaKhoa,
                NgayNhapHoc=student_in.NgayNhapHoc or date.today(),
                NgayTao=datetime.now().isoformat(),
            )
            db_local.add(db_student)

            for session in sessions.values():
                session.commit()

            db_local.refresh(db_student)
            return StudentResponse.model_validate(db_student)

        except Exception as e:
            for session in sessions.values():
                session.rollback()

            from sqlalchemy.exc import IntegrityError

            if isinstance(e, IntegrityError):
                raise HTTPException(
                    status_code=400, detail=f"Database integrity error: {str(e.orig)}"
                )
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(
                status_code=500, detail=f"Distributed write failed: {str(e)}"
            )
        finally:
            for session in sessions.values():
                session.close()

    @staticmethod
    def update_student(
        db: Session, ma_sv: str, student_in: StudentUpdate, current_user: User
    ) -> Student:
        """
        Cập nhật thông tin sinh viên.
        Yêu cầu: Admin role
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền cập nhật sinh viên",
            )

        student = StudentManagementService.get_student_by_masv(db, ma_sv)

        update_data = student_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "MaCoSo" and value:
                value = value.upper()
            if hasattr(student, field) and value is not None:
                setattr(student, field, value)

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def update_student_status(
        db: Session, ma_sv: str, status_update: StudentStatusUpdate, current_user: User
    ) -> Student:
        """
        Cập nhật trạng thái sinh viên.
        Yêu cầu: Admin role
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền cập nhật trạng thái",
            )

        student = StudentManagementService.get_student_by_masv(db, ma_sv)
        student.TrangThai = status_update.TrangThai

        db.commit()
        db.refresh(student)
        return student

    @staticmethod
    def delete_student(db: Session, ma_sv: str, current_user: User) -> bool:
        """Xóa sinh viên (Admin only)"""
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền xóa sinh viên",
            )

        student = StudentManagementService.get_student_by_masv(db, ma_sv)
        db.delete(student)
        db.commit()
        return True
