from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from enums.types import CourseType
from enums.status import CourseStatus


class CourseBase(BaseModel):
    MaHocPhan: str = Field(..., min_length=2, max_length=20)
    TenHocPhan: str = Field(..., min_length=3, max_length=255)
    SoTinChi: int = Field(..., ge=1, le=10)
    SoTietLyThuyet: int = Field(default=0, ge=0, le=120)
    SoTietThucHanh: int = Field(default=0, ge=0, le=120)
    LoaiHocPhan: CourseType = Field(default=CourseType.BatBuoc)
    MaKhoa: str = Field(..., min_length=2, max_length=20)
    MoTa: Optional[str] = Field(default=None, max_length=1000)
    TrangThai: CourseStatus = Field(default=CourseStatus.HoatDong)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    TenHocPhan: Optional[str] = Field(default=None, min_length=3, max_length=255)
    SoTinChi: Optional[int] = Field(default=None, ge=1, le=10)
    SoTietLyThuyet: Optional[int] = Field(default=None, ge=0, le=120)
    SoTietThucHanh: Optional[int] = Field(default=None, ge=0, le=120)
    LoaiHocPhan: Optional[CourseType] = Field(default=None)
    MaKhoa: Optional[str] = Field(default=None, min_length=2, max_length=20)
    MoTa: Optional[str] = Field(default=None, max_length=1000)
    TrangThai: Optional[CourseStatus] = Field(default=None)


class CourseFilter(BaseModel):
    MaKhoa: Optional[str] = None
    TrangThai: Optional[CourseStatus] = None
    keyword: Optional[str] = None
    so_tin_chi_from: Optional[int] = Field(default=None, ge=0, le=10)
    so_tin_chi_to: Optional[int] = Field(default=None, ge=0, le=10)


class CourseResponse(CourseBase):
    NgayTao: datetime

    model_config = ConfigDict(from_attributes=True)
