from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text, Enum
from configs.db import Base
from enums.status import TrangThaiGiaoTac, BuocGiaoTac

class NhatKyThaoTac(Base):
    __tablename__ = "NhatKyThaoTac"

    ID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    MaGiaoTac = Column(String(50), nullable=False)
    MaLopHP = Column(String(20), nullable=False)
    MaSV = Column(String(20), nullable=False)
    MaCoSo = Column(String(20), nullable=True)   # Site nguồn của bước giao tác
    Buoc = Column(Enum(BuocGiaoTac), nullable=False)
    ChiTiet = Column(Text, nullable=True)
    ThoiGian = Column(DateTime, default=datetime.utcnow, nullable=False)
    TrangThai = Column(Enum(TrangThaiGiaoTac), nullable=False, default=TrangThaiGiaoTac.DANG_CHAY)
