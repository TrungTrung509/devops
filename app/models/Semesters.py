from sqlalchemy import Column, Date, Integer, String, Enum
from configs.db import Base
from enums.status import SemesterStatus


class Semester(Base):
    __tablename__ = "HocKy"

    MaHocKy = Column(String, primary_key=True, index=True)
    NamHoc = Column(String, nullable=False)
    KySo = Column(Integer, nullable=False)
    NgayBatDau = Column(Date, nullable=True)
    NgayKetThuc = Column(Date, nullable=True)
    TrangThaiHocKy = Column(Enum(SemesterStatus), nullable=False, default=SemesterStatus.SapMo)
