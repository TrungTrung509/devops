from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Enum
from configs.db import Base
from enums.types import StudyForm
from enums.status import ClassSectionStatus


class CourseSection(Base):
    __tablename__ = "LopHocPhan"

    MaLopHP = Column(String, primary_key=True, index=True)
    MaHP = Column(String, ForeignKey("HocPhan.MaHP"), nullable=False)
    MaHocKy = Column(String, ForeignKey("HocKy.MaHocKy"), nullable=False)
    MaCoSo = Column(String, ForeignKey("CoSo.MaCoSo"), nullable=False)
    MaGV = Column(String, ForeignKey("GiangVien.MaGV"), nullable=False)
    TenLopHP = Column(String, nullable=True)
    SiSoToiDa = Column(Integer, nullable=False)
    SiSoHienTai = Column(Integer, nullable=False, default=0)
    HinhThucHoc = Column(Enum(StudyForm), nullable=False, default=StudyForm.Offline)
    TrangThaiLop = Column(Enum(ClassSectionStatus), nullable=False, default=ClassSectionStatus.Mo)
    NgayTao = Column(DateTime, default=datetime.utcnow, nullable=False)
