from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from enums.types import StudyForm
from enums.status import ClassSectionStatus


class ScheduleBase(BaseModel):
    MaLich: str = Field(..., min_length=3, max_length=20)
    MaPhong: str = Field(..., min_length=3, max_length=20)
    ThuTrongTuan: int = Field(..., ge=2, le=8)
    TietBatDau: int = Field(..., ge=1, le=15)
    SoTiet: int = Field(..., ge=1, le=10)
    NgayBatDau: date
    NgayKetThuc: date
    GhiChu: Optional[str] = Field(default=None, max_length=200)


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    MaPhong: Optional[str] = Field(default=None, min_length=3, max_length=20)
    ThuTrongTuan: Optional[int] = Field(default=None, ge=2, le=8)
    TietBatDau: Optional[int] = Field(default=None, ge=1, le=15)
    SoTiet: Optional[int] = Field(default=None, ge=1, le=10)
    NgayBatDau: Optional[date] = None
    NgayKetThuc: Optional[date] = None
    GhiChu: Optional[str] = Field(default=None, max_length=200)


class ScheduleResponse(ScheduleBase):
    MaLopHP: str
    TenPhong: Optional[str] = None
    ToaNha: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EnrollmentResponse(BaseModel):
    MaDangKy: int
    MaSV: str
    MaLich: Optional[str] = None
    HoTenSinhVien: Optional[str] = None
    TrangThaiDangKy: str
    LanDangKy: int
    NgayDangKy: datetime
    GhiChu: Optional[str] = None


class CourseSectionBase(BaseModel):
    MaLopHP: str = Field(..., min_length=5, max_length=50)
    MaHocPhan: str = Field(..., min_length=2, max_length=20)
    MaHocKy: str = Field(..., min_length=2, max_length=20)
    MaCoSo: str = Field(..., min_length=2, max_length=10)
    MaGV: str = Field(..., min_length=2, max_length=20)
    TenLopHP: Optional[str] = Field(default=None, max_length=100)
    SiSoToiDa: int = Field(..., ge=1, le=500)
    HinhThucHoc: StudyForm = Field(default=StudyForm.Offline)
    TrangThaiLop: ClassSectionStatus = Field(default=ClassSectionStatus.Mo)


class CourseSectionCreate(CourseSectionBase):
    pass


class CourseSectionUpdate(BaseModel):
    MaGV: Optional[str] = Field(default=None, min_length=2, max_length=20)
    TenLopHP: Optional[str] = Field(default=None, max_length=100)
    SiSoToiDa: Optional[int] = Field(default=None, ge=1, le=500)
    HinhThucHoc: Optional[StudyForm] = Field(default=None)
    TrangThaiLop: Optional[ClassSectionStatus] = Field(default=None)


class CourseSectionListResponse(BaseModel):
    MaLopHP: str
    MaHocPhan: str
    TenHocPhan: Optional[str] = None
    MaHocKy: str
    NamHoc: Optional[str] = None
    KySo: Optional[int] = None
    MaCoSo: str
    MaGV: str
    TenGiangVien: Optional[str] = None
    TenLopHP: Optional[str] = None
    SiSoToiDa: int
    SiSoHienTai: int
    SoChoConLai: int
    HinhThucHoc: StudyForm
    TrangThaiLop: ClassSectionStatus
    SoLuongLichHoc: int = 0
    NgayTao: datetime
    LichHoc: list[ScheduleResponse] = Field(default_factory=list)


class CourseSectionDetailResponse(CourseSectionListResponse):
    LichHoc: list[ScheduleResponse] = Field(default_factory=list)
    DanhSachDangKy: list[EnrollmentResponse] = Field(default_factory=list)
