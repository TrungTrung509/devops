from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from enums.status import GeneralStatus

class BranchBase(BaseModel):
    MaCoSo: str
    TenCoSo: str
    DiaChi: str
    SoDienThoai: Optional[str] = None
    Email: Optional[str] = None
    NgayThanhLap: Optional[date] = None
    TrangThai: Optional[GeneralStatus] = GeneralStatus.HoatDong

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    TenCoSo: Optional[str] = None
    DiaChi: Optional[str] = None
    SoDienThoai: Optional[str] = None
    Email: Optional[str] = None
    NgayThanhLap: Optional[date] = None
    TrangThai: Optional[GeneralStatus] = None

class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)