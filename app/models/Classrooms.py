from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from configs.db import Base
from enums.types import RoomType
from enums.status import RoomStatus


class Classroom(Base):
    __tablename__ = "PhongHoc"

    MaPhong = Column(String, primary_key=True, index=True)
    TenPhong = Column(String, nullable=False)
    ToaNha = Column(String, nullable=True)
    Tang = Column(Integer, nullable=True)
    SucChua = Column(Integer, nullable=False)
    LoaiPhong = Column(Enum(RoomType), nullable=False, default=RoomType.LyThuyet)
    MaCoSo = Column(String, ForeignKey("CoSo.MaCoSo"), nullable=False)
    TrangThai = Column(Enum(RoomStatus), nullable=False, default=RoomStatus.HoatDong)
    NgayTao = Column(DateTime, default=datetime.utcnow, nullable=False)
