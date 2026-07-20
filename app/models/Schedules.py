from sqlalchemy import Column, Date, ForeignKey, Integer, String

from configs.db import Base


class Schedule(Base):
    __tablename__ = "LichHoc"

    MaLich = Column(String, primary_key=True, index=True)
    MaLopHP = Column(String, ForeignKey("LopHocPhan.MaLopHP"), nullable=False)
    MaPhong = Column(String, ForeignKey("PhongHoc.MaPhong"), nullable=False)
    ThuTrongTuan = Column(Integer, nullable=False)
    TietBatDau = Column(Integer, nullable=False)
    SoTiet = Column(Integer, nullable=False)
    NgayBatDau = Column(Date, nullable=True)
    NgayKetThuc = Column(Date, nullable=True)
    GhiChu = Column(String, nullable=True)
