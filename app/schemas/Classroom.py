from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from enums.types import RoomType
from enums.status import RoomStatus


class ClassroomFilter(BaseModel):
    keyword: Optional[str] = Field(default=None, description="Tìm kiếm theo mã phòng hoặc tên phòng")
    MaCoSo: Optional[str] = Field(default=None, description="Lọc theo mã cơ sở")
    LoaiPhong: Optional[RoomType] = Field(default=None, description="Lọc theo loại phòng")
    TrangThai: Optional[RoomStatus] = Field(default=None, description="Lọc theo trạng thái")


class ClassroomBase(BaseModel):
    MaPhong: str = Field(..., min_length=3, max_length=20)
    TenPhong: str = Field(..., min_length=2, max_length=100)
    ToaNha: Optional[str] = Field(default=None, max_length=50)
    Tang: Optional[int] = Field(default=None, ge=0, le=100)
    SucChua: int = Field(..., ge=1, le=1000)
    LoaiPhong: RoomType = Field(default=RoomType.LyThuyet)
    MaCoSo: str = Field(..., min_length=2, max_length=10)
    TrangThai: RoomStatus = Field(default=RoomStatus.HoatDong)


class ClassroomCreate(ClassroomBase):
    pass


class ClassroomUpdate(BaseModel):
    TenPhong: Optional[str] = Field(default=None, min_length=2, max_length=100)
    ToaNha: Optional[str] = Field(default=None, max_length=50)
    Tang: Optional[int] = Field(default=None, ge=0, le=100)
    SucChua: Optional[int] = Field(default=None, ge=1, le=1000)
    LoaiPhong: Optional[RoomType] = Field(default=None)
    TrangThai: Optional[RoomStatus] = Field(default=None)


class ClassroomResponse(ClassroomBase):
    NgayTao: datetime

    model_config = ConfigDict(from_attributes=True)
