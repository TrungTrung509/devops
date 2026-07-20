from datetime import date, datetime
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session

from configs.db import SessionLocals
from enums.status import UserStatus, TeacherStatus
from enums.user_role import UserRole
from models.Teachers import Teacher
from models.Users import User
from repositories.TeacherRepo import TeacherRepo
from repositories.UserRepo import UserRepo
from schemas.Teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherStatusUpdate,
    TeacherResponse,
    TeacherFilter,
)
from services.AuthService import AuthService
from services.UserService import UserService


class TeacherManagementService:
    """
    Service xử lý nghiệp vụ Giảng viên.
    GiangVien thuộc site theo MaCoSo - đọc/ghi đúng site sở hữu.
    """

    VALID_DEGREES = ["CN", "ThS", "TS", "PGS"]

    @staticmethod
    def get_all_teachers(
        db: Session, filters: Optional[TeacherFilter] = None, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Teacher], int, dict]:
        """Lấy danh sách giảng viên với filter."""
        query = db.query(Teacher)
        if filters:
            if filters.MaCoSo:
                query = query.filter(Teacher.MaCoSo == filters.MaCoSo.upper())
            if filters.MaKhoa:
                query = query.filter(Teacher.MaKhoa == filters.MaKhoa.upper())
            if filters.TrangThai:
                query = query.filter(Teacher.TrangThai == filters.TrangThai)
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                query = query.filter(
                    or_(
                        Teacher.MaGV.ilike(keyword),
                        Teacher.Ho.ilike(keyword),
                        Teacher.Ten.ilike(keyword),
                    )
                )
        offset = skip * limit
        total = query.count()
        teachers = query.offset(offset).limit(limit).all()

        # Calculate stats based on filters, excluding TrangThai filter
        stats_query = db.query(Teacher.TrangThai, func.count(Teacher.MaGV))
        if filters:
            if filters.MaCoSo:
                stats_query = stats_query.filter(Teacher.MaCoSo == filters.MaCoSo.upper())
            if filters.MaKhoa:
                stats_query = stats_query.filter(Teacher.MaKhoa == filters.MaKhoa.upper())
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                stats_query = stats_query.filter(
                    or_(
                        Teacher.MaGV.ilike(keyword),
                        Teacher.Ho.ilike(keyword),
                        Teacher.Ten.ilike(keyword),
                    )
                )
        stats_rows = stats_query.group_by(Teacher.TrangThai).all()
        status_counts = {
            (r[0].value if hasattr(r[0], "value") else str(r[0])): r[1]
            for r in stats_rows
        }

        return teachers, total, status_counts

    @staticmethod
    def get_teacher_by_magv(db: Session, ma_gv: str) -> Optional[Teacher]:
        """Lấy giảng viên theo MaGV"""
        teacher = db.query(Teacher).filter(Teacher.MaGV == ma_gv).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giảng viên với mã: {ma_gv}",
            )
        return teacher

    @staticmethod
    def get_teacher_by_userid(db: Session, user_id: str) -> Optional[Teacher]:
        """Lấy giảng viên theo userId"""
        teacher = db.query(Teacher).filter(Teacher.userId == user_id).first()
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giảng viên với userId: {user_id}",
            )
        return teacher

    @staticmethod
    def get_teachers_by_coso(db: Session, ma_co_so: str) -> List[Teacher]:
        """Lấy danh sách giảng viên theo cơ sở"""
        return db.query(Teacher).filter(Teacher.MaCoSo == ma_co_so.upper()).all()

    @staticmethod
    async def create_teacher(
        teacher_in: TeacherCreate, current_user: User
    ) -> TeacherResponse:
        """
        Tạo mới giảng viên (Distributed).
        Yêu cầu: Admin role
        Logic di chuyển từ UserService để tập trung quản lý.
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admin can create teachers",
            )

        # Validate degree
        if (
            teacher_in.HocVi
            and teacher_in.HocVi not in TeacherManagementService.VALID_DEGREES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Học vị phải là một trong: {', '.join(TeacherManagementService.VALID_DEGREES)}",
            )

        sessions = {
            site: session_factory() for site, session_factory in SessionLocals.items()
        }

        try:
            # Tự sinh mã nếu không cung cấp
            ma_gv = teacher_in.MaGV
            if not ma_gv:
                ma_gv = UserService.generate_id(UserRole.GiangVien, teacher_in.MaCoSo, teacher_in.MaKhoa)

            # Check username on HEAD site
            if UserRepo.get_by_username(sessions["HADONG"], ma_gv):
                raise HTTPException(
                    status_code=400,
                    detail=f"Username '{ma_gv}' đã tồn tại",
                )

            email_to_check = teacher_in.email
            if email_to_check and email_to_check.lower() == "string":
                email_to_check = None

            if email_to_check and UserRepo.get_by_email(
                sessions["HADONG"], email_to_check
            ):
                raise HTTPException(
                    status_code=400, detail=f"Email '{email_to_check}' đã được sử dụng"
                )

            db_local = sessions.get(teacher_in.MaCoSo)
            if not db_local:
                raise HTTPException(
                    status_code=400, detail=f"Cơ sở không hợp lệ: {teacher_in.MaCoSo}"
                )

            if TeacherRepo.get_by_MaGV(db_local, ma_gv):
                raise HTTPException(
                    status_code=400, detail="Mã giảng viên (MaGV) đã tồn tại"
                )

            hashed_password = AuthService.get_password_hash(ma_gv)

            db_user_data = {
                "userId": ma_gv,
                "username": ma_gv,
                "password": hashed_password,
                "role": UserRole.GiangVien,
                "email": email_to_check,
                "MaCoSo": teacher_in.MaCoSo,
                "status": UserStatus.Active,
                "NgayTao": datetime.now().isoformat(),
            }

            for session in sessions.values():
                session.add(User(**db_user_data))

            db_teacher = Teacher(
                MaGV=ma_gv,
                userId=ma_gv,
                Ho=teacher_in.Ho,
                Ten=teacher_in.Ten,
                NgaySinh=teacher_in.NgaySinh,
                GioiTinh=teacher_in.GioiTinh,
                SDT=teacher_in.SDT,
                DiaChi=teacher_in.DiaChi,
                HocVi=teacher_in.HocVi,
                HocHam=teacher_in.HocHam,
                TrangThai=teacher_in.TrangThai or TeacherStatus.DangCongTac,
                MaCoSo=teacher_in.MaCoSo,
                MaKhoa=teacher_in.MaKhoa,
                NgayVaoLam=teacher_in.NgayVaoLam or date.today(),
                NgayTao=datetime.now().isoformat(),
            )
            db_local.add(db_teacher)

            for session in sessions.values():
                session.commit()

            db_local.refresh(db_teacher)
            return TeacherResponse.model_validate(db_teacher)

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
    def update_teacher(
        db: Session, ma_gv: str, teacher_in: TeacherUpdate, current_user: User
    ) -> Teacher:
        """
        Cập nhật thông tin giảng viên.
        Yêu cầu: Admin role
        """
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền cập nhật giảng viên",
            )

        teacher = TeacherManagementService.get_teacher_by_magv(db, ma_gv)

        update_data = teacher_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "MaCoSo" and value:
                value = value.upper()
            if hasattr(teacher, field) and value is not None:
                setattr(teacher, field, value)

        if (
            teacher_in.HocVi
            and teacher_in.HocVi not in TeacherManagementService.VALID_DEGREES
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Học vị phải là một trong: {', '.join(TeacherManagementService.VALID_DEGREES)}",
            )

        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def update_teacher_status(
        db: Session, ma_gv: str, status_update: TeacherStatusUpdate, current_user: User
    ) -> Teacher:
        """Cập nhật trạng thái giảng viên."""
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền cập nhật trạng thái",
            )

        teacher = TeacherManagementService.get_teacher_by_magv(db, ma_gv)
        teacher.TrangThai = status_update.TrangThai

        db.commit()
        db.refresh(teacher)
        return teacher

    @staticmethod
    def delete_teacher(db: Session, ma_gv: str, current_user: User) -> bool:
        """Xóa giảng viên (Admin only)"""
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền xóa giảng viên",
            )

        teacher = TeacherManagementService.get_teacher_by_magv(db, ma_gv)
        db.delete(teacher)
        db.commit()
        return True
