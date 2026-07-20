from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from enums.status import EnrollmentStatus


class EnrollmentCreate(BaseModel):
    MaLopHP: str = Field(..., description="Mã lớp học phần đăng ký")

class SwapEnrollmentRequest(BaseModel):
    old_ma_lop_hp: str = Field(..., description="Mã lớp học phần muốn đổi đi")
    new_ma_lop_hp: str = Field(..., description="Mã lớp học phần muốn đổi sang")

class EligibilityResponse(BaseModel):
    is_eligible: bool
    reasons: List[str] = Field(default_factory=list, description="Lý do nếu không đủ điều kiện")


class RegistrationResult(BaseModel):
    MaLopHP: str
    status: str 
    message: Optional[str] = None
    error_code: Optional[str] = None
    reasons: List[str] = Field(default_factory=list)
    enrollment_id: Optional[int] = None
    action: Optional[str] = None # 
    old_ma_lop_hp: Optional[str] = None

class EnrollmentHistoryResponse(BaseModel):
    MaDangKy: int
    MaSV: str
    MaLopHP: str
    TenLopHP: Optional[str] = None
    TenHocPhan: Optional[str] = None
    MaHocKy: str
    NgayDangKy: datetime
    TrangThaiDangKy: EnrollmentStatus
    MaCoSo: str

class ScheduleResponse(BaseModel):
    MaLich: str
    MaLopHP: str
    TenLopHP: Optional[str] = None
    MaHP: str
    TenHocPhan: Optional[str] = None
    MaPhong: str
    ThuTrongTuan: int
    TietBatDau: int
    SoTiet: int
    NgayBatDau: Optional[datetime] = None
    NgayKetThuc: Optional[datetime] = None
    GhiChu: Optional[str] = None

class StudentTimetableLichHoc(BaseModel):
    MaLich: str
    ThuTrongTuan: int
    TietBatDau: int
    SoTiet: int
    MaPhong: Optional[str] = None
    TenPhong: Optional[str] = None
    ToaNha: Optional[str] = None
    NgayBatDau: Optional[datetime] = None
    NgayKetThuc: Optional[datetime] = None
    GhiChu: Optional[str] = None

class StudentTimetableItem(BaseModel):
    MaLopHP: str
    TenLopHP: Optional[str] = None
    MaHP: str
    TenHP: Optional[str] = None
    SoTinChi: Optional[int] = None
    MaHocKy: str
    MaCoSo: str
    TenCoSo: Optional[str] = None
    MaGV: Optional[str] = None
    TenGiangVien: Optional[str] = None
    TrangThaiDangKy: str
    HinhThucHoc: Optional[str] = None
    LichHoc: List[StudentTimetableLichHoc] = Field(default_factory=list)

class StudentTimetableResponse(BaseModel):
    maHocKy: Optional[str] = None
    items: List[StudentTimetableItem] = Field(default_factory=list)

class StudentInClassResponse(BaseModel):
    MaSV: str
    Ho: str
    Ten: str
    NgaySinh: Optional[datetime] = None
    GioiTinh: Optional[str] = None
    MaLop: Optional[str] = None
    NgayDangKy: datetime
    TrangThaiDangKy: EnrollmentStatus
