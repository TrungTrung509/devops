from sqlalchemy import Column, String, Date, Enum

from configs.db import Base
from enums.status import GeneralStatus


class Departments(Base):
    __tablename__ = 'Khoa'
    MaKhoa = Column(String, primary_key=True, index=True)
    TenKhoa = Column(String, nullable=False, unique=True)
    MoTa = Column(String, nullable=True)
    NgayThanhLap = Column(Date)
    TrangThai = Column(Enum(GeneralStatus), default=GeneralStatus.HoatDong)