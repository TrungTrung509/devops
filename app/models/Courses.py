from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from configs.db import Base
from enums.types import CourseType
from enums.status import CourseStatus


class Course(Base):
    __tablename__ = "HocPhan"

    MaHocPhan = Column("MaHP", String, primary_key=True, index=True)
    TenHocPhan = Column("TenHP", String, nullable=False)
    SoTinChi = Column(Integer, nullable=False)
    SoTietLyThuyet = Column(Integer, nullable=False, default=0)
    SoTietThucHanh = Column(Integer, nullable=False, default=0)
    LoaiHocPhan = Column(Enum(CourseType), nullable=False, default=CourseType.BatBuoc)
    MaKhoa = Column(String, ForeignKey("Khoa.MaKhoa"), nullable=False)
    MoTa = Column(String, nullable=True)
    TrangThai = Column(Enum(CourseStatus), nullable=False, default=CourseStatus.HoatDong)
    NgayTao = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Course(MaHocPhan='{self.MaHocPhan}', TenHocPhan='{self.TenHocPhan}')>"
