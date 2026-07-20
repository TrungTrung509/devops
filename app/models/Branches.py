from sqlalchemy import Column, String, Date, Enum
from configs.db import Base
from enums.status import GeneralStatus

class Branch(Base):
    # Viet
    __tablename__ = 'CoSo'

    MaCoSo = Column(String, primary_key=True, index=True)
    TenCoSo = Column(String, nullable=False)
    DiaChi = Column(String, nullable=True)
    SoDienThoai = Column(String, nullable=True)
    Email = Column(String, nullable=True)
    NgayThanhLap = Column(Date, nullable=True)
    TrangThai = Column(Enum(GeneralStatus), nullable=True, default=GeneralStatus.HoatDong)
    def __repr__(self):
        return f"<Branch(MaCoSo='{self.MaCoSo}', TenCoSo='{self.TenCoSo}')>"
    # Trung
    # __tablename__ = 'CoSo'
    # MaCoSo = Column(String, primary_key=True, index=True)
    # TenCoSo = Column(String, nullable=False, unique=True)
    # DiaChi = Column(String, nullable=False)
    # SoDienThoai = Column(String, nullable=True)
    # Email = Column(String, nullable=True)
    # NgayThanhLap = Column(Date)
    # TrangThai = Column(String, default='HoatDong')
