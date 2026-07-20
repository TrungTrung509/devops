from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional, List
from datetime import date, datetime
from enums.status import TeacherStatus
from enums.gender import Genders

class TeacherProfileBase(BaseModel):
    """Thông tin hồ sơ cá nhân của Giảng viên"""
    Ho: str = Field(..., min_length=1, max_length=50, description="Họ")
    Ten: str = Field(..., min_length=1, max_length=50, description="Tên")
    email: Optional[str] = None
    SDT: Optional[str] = Field(None, max_length=20, description="Số điện thoại")
    NgaySinh: Optional[date] = Field(None, description="Ngày sinh")
    GioiTinh: Optional[Genders] = Field(Genders.Khac, description="Giới tính: Nam, Nu, Khac")
    DiaChi: Optional[str] = Field(None, max_length=300, description="Địa chỉ")

class TeacherBase(TeacherProfileBase):
    """Schema base cho Giảng viên"""
    MaGV: Optional[str] = Field(None, min_length=3, max_length=20, description="Mã giảng viên (Tự sinh nếu để trống)")
    HocVi: Optional[str] = Field(None, max_length=50, description="Học vị (CN, ThS, TS, PGS)")
    HocHam: Optional[str] = Field(None, max_length=50, description="Học hàm (GTV, PGS)")
    MaCoSo: str = Field(..., description="Mã cơ sở quản lý")
    MaKhoa: Optional[str] = Field(None, description="Mã khoa")
    TrangThai: Optional[TeacherStatus] = Field(default=TeacherStatus.DangCongTac, description="Trạng thái")
    NgayVaoLam: Optional[date] = Field(None, description="Ngày vào làm")

    @field_validator("MaKhoa", mode="before")
    @classmethod
    def transform_null_string(cls, v):
        if isinstance(v, str) and v.lower() == "null":
            return None
        return v

class TeacherCreate(TeacherBase):
    """Request body tạo mới giảng viên"""
    pass

class TeacherUpdate(BaseModel):
    """Request body cập nhật giảng viên"""
    Ho: Optional[str] = Field(None, min_length=1, max_length=50)
    Ten: Optional[str] = Field(None, min_length=1, max_length=50)
    NgaySinh: Optional[date] = None
    GioiTinh: Optional[Genders] = None
    HocVi: Optional[str] = Field(None, max_length=50)
    HocHam: Optional[str] = Field(None, max_length=50)
    SDT: Optional[str] = Field(None, max_length=20)
    DiaChi: Optional[str] = Field(None, max_length=300)
    MaKhoa: Optional[str] = None
    TrangThai: Optional[TeacherStatus] = None
    NgayVaoLam: Optional[date] = None
    MaCoSo: Optional[str] = Field(None, max_length=50, description="Mã cơ sở (để xác định DB site khi update)")

class TeacherStatusUpdate(BaseModel):
    """Request body cập nhật trạng thái giảng viên"""
    TrangThai: TeacherStatus = Field(..., description="Trạng thái mới")

class TeacherResponse(TeacherBase):
    """Response giảng viên"""
    userId: str = Field(..., description="User ID (từ bảng users)")
    NgayTao: Optional[datetime] = Field(None, description="Ngày tạo")
    model_config = ConfigDict(from_attributes=True)

class TeacherListResponse(BaseModel):
    """Response danh sách giảng viên"""
    items: List[TeacherResponse]
    total: int
    page: int = 1
    page_size: int = 20

class TeacherFilter(BaseModel):
    """Filter cho danh sách giảng viên"""
    MaCoSo: Optional[str] = None
    MaKhoa: Optional[str] = None
    TrangThai: Optional[TeacherStatus] = None
    keyword: Optional[str] = Field(None, description="Tìm kiếm theo mã, họ tên")
