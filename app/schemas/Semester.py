from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator
from enums.status import SemesterStatus

class SemesterBase(BaseModel):
    MaHocKy: str = Field(..., min_length=3, max_length=20)
    NamHoc: str = Field(..., min_length=4, max_length=10)
    KySo: int = Field(..., ge=1, le=3)
    NgayBatDau: Optional[date] = None
    NgayKetThuc: Optional[date] = None
    TrangThaiHocKy: SemesterStatus = Field(default=SemesterStatus.SapMo)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.NgayBatDau and self.NgayKetThuc and self.NgayKetThuc <= self.NgayBatDau:
            raise ValueError("NgayKetThuc phai lon hon NgayBatDau")
        return self


class SemesterCreate(SemesterBase):
    pass


class SemesterUpdate(BaseModel):
    NamHoc: Optional[str] = Field(default=None, min_length=4, max_length=10)
    KySo: Optional[int] = Field(default=None, ge=1, le=3)
    NgayBatDau: Optional[date] = None
    NgayKetThuc: Optional[date] = None
    TrangThaiHocKy: Optional[SemesterStatus] = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.NgayBatDau and self.NgayKetThuc and self.NgayKetThuc <= self.NgayBatDau:
            raise ValueError("NgayKetThuc phai lon hon NgayBatDau")
        return self


class SemesterResponse(SemesterBase):
    model_config = ConfigDict(from_attributes=True)
