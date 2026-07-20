from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from typing import Optional, List
from datetime import date, datetime
from enums.status import StudentStatus
from enums.gender import Genders

class StudentProfileBase(BaseModel):
    """Thông tin hồ sơ cá nhân của Sinh viên"""
    Ho: str = Field(..., min_length=1, max_length=50, description="Họ")
    Ten: str = Field(..., min_length=1, max_length=50, description="Tên")
    email: Optional[str] = None
    SDT: Optional[str] = Field(None, max_length=20, description="Số điện thoại")
    NgaySinh: Optional[date] = Field(None, description="Ngày sinh")
    GioiTinh: Optional[Genders] = Field(Genders.Khac, description="Giới tính: Nam, Nu, Khac")
    DiaChi: Optional[str] = Field(None, max_length=300, description="Địa chỉ")

class StudentBase(StudentProfileBase):
    """Schema base cho Sinh viên"""
    MaSV: Optional[str] = Field(None, min_length=3, max_length=20, description="Mã sinh viên (Tự sinh nếu để trống)")
    MaCoSo: str = Field(..., description="Mã cơ sở quản lý")
    MaKhoa: Optional[str] = Field(None, description="Mã khoa")
    TrangThai: Optional[StudentStatus] = Field(default=StudentStatus.DangHoc, description="Trạng thái")
    NgayNhapHoc: Optional[date] = Field(None, description="Ngày nhập học")

    @field_validator("MaKhoa", mode="before")
    @classmethod
    def transform_null_string(cls, v):
        if isinstance(v, str) and v.lower() == "null":
            return None
        return v

    @model_validator(mode='after')
    def validate_birth_date(self):
        if self.NgaySinh:
            today = date.today()
            age = today.year - self.NgaySinh.year
            if age < 16 or age > 100:
                raise ValueError("Ngày sinh không hợp lệ (tuổi phải từ 16-100)")
        return self

class StudentCreate(StudentBase):
    """Request body tạo mới sinh viên"""
    pass

class StudentUpdate(BaseModel):
    """Request body cập nhật sinh viên"""
    Ho: Optional[str] = Field(None, min_length=1, max_length=50)
    Ten: Optional[str] = Field(None, min_length=1, max_length=50)
    NgaySinh: Optional[date] = None
    GioiTinh: Optional[Genders] = None
    SDT: Optional[str] = Field(None, max_length=20)
    DiaChi: Optional[str] = Field(None, max_length=300)
    MaKhoa: Optional[str] = None
    TrangThai: Optional[StudentStatus] = None
    NgayNhapHoc: Optional[date] = None

class StudentStatusUpdate(BaseModel):
    """Request body cập nhật trạng thái sinh viên"""
    TrangThai: StudentStatus = Field(..., description="Trạng thái mới")

class StudentResponse(StudentBase):
    """Response sinh viên"""
    userId: str = Field(..., description="User ID (từ bảng users)")
    NgayTao: Optional[datetime] = Field(None, description="Ngày tạo")
    model_config = ConfigDict(from_attributes=True)

class StudentListResponse(BaseModel):
    """Response danh sách sinh viên"""
    items: List[StudentResponse]
    total: int
    page: int = 1
    page_size: int = 20

class StudentFilter(BaseModel):
    """Filter cho danh sách sinh viên"""
    MaCoSo: Optional[str] = None
    MaKhoa: Optional[str] = None
    TrangThai: Optional[StudentStatus] = None
    keyword: Optional[str] = Field(None, description="Tìm kiếm theo mã, họ tên")
