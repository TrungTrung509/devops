from datetime import date, datetime
import uuid

from fastapi import HTTPException, status

from configs.db import SessionLocals
from enums.status import UserStatus
from enums.user_role import UserRole
from models.Students import Student
from models.Teachers import Teacher
from models.Users import User
from repositories.StudentRepo import StudentRepo
from repositories.TeacherRepo import TeacherRepo
from repositories.UserRepo import UserRepo
from sqlalchemy import text
from sqlalchemy.orm import Session
from schemas.User import UserCreate
from schemas.Student import StudentResponse
from schemas.Teacher import TeacherResponse
from schemas.User import ChangePasswordRequest
from services.AuthService import AuthService
class UserService:
    @staticmethod
    def generate_id(role: UserRole, ma_co_so: str = None, ma_khoa: str = None) -> str:
        """
        Tự sinh mã theo quy tắc:
        - Sinh viên: SV + Cơ sở (HD/NT/HL) + Năm (26) + Mã Khoa (CNTT) + STT (001) -> SVHD26CNTT001
        - Giảng viên: GV + Cơ sở (HD/NT/HL) + Năm (26) + Mã Khoa (CNTT) + STT (001) -> GVHD26CNTT001
        - Admin: AD + STT -> AD1
        """
        # Ánh xạ mã cơ sở
        site_map = {
            "HADONG": "HD",
            "NGOCTRUC": "NT",
            "HOALAC": "HL"
        }
        
        # Mở session trên site HADONG (site chính để quản lý ID toàn hệ thống)
        db = SessionLocals["HADONG"]()
        try:
            year_prefix = str(datetime.now().year)[2:]
            
            if role == UserRole.Admin:
                prefix = "AD"
                # Tìm STT lớn nhất của Admin
                query = text('SELECT "userId" FROM users WHERE "userId" LIKE :prefix || \'%\' ORDER BY "userId" DESC LIMIT 1')
                result = db.execute(query, {"prefix": prefix}).fetchone()
                if result:
                    last_id = result[0]
                    last_num = int(last_id[2:])
                    return f"AD{last_num + 1}"
                return "AD1"
            
            # SV hoặc GV
            role_prefix = "SV" if role == UserRole.SinhVien else "GV"
            site_code = site_map.get(ma_co_so.upper(), "XX")
            khoa_code = ma_khoa.upper() if ma_khoa else ""
            prefix = f"{role_prefix}{site_code}{year_prefix}{khoa_code}"
            
            query = text('SELECT "userId" FROM users WHERE "userId" LIKE :prefix || \'%\' ORDER BY "userId" DESC LIMIT 1')
            result = db.execute(query, {"prefix": prefix}).fetchone()
            
            if result:
                last_id = result[0]
                # Tìm phần số cuối cùng (giả sử là 3 chữ số)
                # Vì độ dài prefix có thể thay đổi do mã khoa, ta lấy 3 ký tự cuối
                try:
                    last_num = int(last_id[-3:])
                    new_num = str(last_num + 1).zfill(3)
                    return f"{prefix}{new_num}"
                except ValueError:
                    return f"{prefix}001"
            
            return f"{prefix}001"
        finally:
            db.close()

    @staticmethod
    async def create_admin(admin_in: UserCreate, current_user: User):
        """Tạo tài khoản Admin mới (chỉ Admin mới được tạo Admin)"""
        if current_user.role != UserRole.Admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Chỉ Admin mới có quyền tạo tài khoản Admin"
            )

        sessions = {site: session_factory() for site, session_factory in SessionLocals.items()}
        
        try:
            # Check if username or email exists
            if UserRepo.get_by_username(sessions["HADONG"], admin_in.username):
                raise HTTPException(status_code=400, detail="Username đã tồn tại")
            
            if admin_in.email and UserRepo.get_by_email(sessions["HADONG"], admin_in.email):
                raise HTTPException(status_code=400, detail="Email đã tồn tại")

            admin_id = UserService.generate_id(UserRole.Admin)
            hashed_password = AuthService.get_password_hash(admin_in.password)

            db_user_data = {
                "userId": admin_id,
                "username": admin_in.username,
                "password": hashed_password,
                "role": UserRole.Admin,
                "email": admin_in.email,
                "MaCoSo": "HADONG", # Admin mặc định ở site chính
                "status": UserStatus.Active,
                "NgayTao": datetime.now().isoformat(),
            }

            for session in sessions.values():
                session.add(User(**db_user_data))
                session.commit()

            return {"message": f"Admin created successfully with ID: {admin_id}", "userId": admin_id}
        except Exception as e:
            for session in sessions.values():
                session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            for session in sessions.values():
                session.close()

    @staticmethod
    async def get_user_profile(user: User):

        db_site = SessionLocals[user.MaCoSo]()
        try:
            if user.role == UserRole.SinhVien:
                profile = StudentRepo.get_by_userId(db_site, user.userId)
                if profile:
                    return StudentResponse.model_validate(profile)
            elif user.role == UserRole.GiangVien:
                profile = TeacherRepo.get_by_userId(db_site, user.userId)
                if profile:
                    return TeacherResponse.model_validate(profile)
            return user
        finally:
            db_site.close()

    @staticmethod
    async def change_password(user: User, request: ChangePasswordRequest):
        sessions = {site: Session() for site, Session in SessionLocals.items()}

        try:
            if not AuthService.verify_password(request.old_password, user.password):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Mat khau cu khong chinh xac",
                )

            new_hashed_password = AuthService.get_password_hash(request.new_password)

            for session in sessions.values():
                db_user = UserRepo.get_by_id(session, user.userId)
                if db_user:
                    db_user.password = new_hashed_password
                    session.commit()

            return {"message": "Password changed successfully across all sites"}
        except Exception as e:
            for session in sessions.values():
                session.rollback()
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Distributed update failed: {str(e)}")
        finally:
            for session in sessions.values():
                session.close()
