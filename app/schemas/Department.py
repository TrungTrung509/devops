from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from enums.status import GeneralStatus

class DepartmentBase(BaseModel):
    MaKhoa: str
    TenKhoa: str
    MoTa: Optional[str] = None
    NgayThanhLap: Optional[date] = None
    TrangThai: Optional[GeneralStatus] = GeneralStatus.HoatDong

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    TenKhoa: Optional[str] = None
    MoTa: Optional[str] = None
    NgayThanhLap: Optional[date] = None
    TrangThai: Optional[GeneralStatus] = None

class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
