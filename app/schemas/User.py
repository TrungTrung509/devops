from enums.status import UserStatus
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional
from enums.user_role import UserRole

class UserBase(BaseModel):
    """Thông tin định danh dùng chung"""
    username: str
    email: Optional[str] = None
    role: UserRole
    MaCoSo: str
    status: UserStatus = UserStatus.Active

class UserResponse(UserBase):
    userId: str
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    status: UserStatus = UserStatus.Active

class UserSelfUpdate(BaseModel):
    """Người dùng tự cập nhật thông tin cá nhân"""
    SDT: Optional[str] = None
    DiaChi: Optional[str] = None
    password: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode='after')
    def check_passwords_match(self) -> 'ChangePasswordRequest':
        if self.new_password != self.confirm_password:
            raise ValueError("Mật khẩu mới và mật khẩu xác nhận không khớp")
        return self
