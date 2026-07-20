from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from configs.db import Base

class User(Base):
    __tablename__ = "users"
    userId = Column(String, primary_key=True, index=True)
    role = Column(String, nullable=False, default="SinhVien")

class SinhVien(Base):
    __tablename__ = "SinhVien"
    MaSV = Column(String, primary_key=True, index=True)
    userId = Column(String, ForeignKey("users.userId"), unique=True, nullable=False)
    MaCoSo = Column(String, nullable=False)

class CourseSection(Base):
    __tablename__ = "LopHocPhan"
    MaLopHP = Column(String, primary_key=True, index=True)
    MaHP = Column(String, nullable=False)
    MaHocKy = Column(String, nullable=False)
    SiSoToiDa = Column(Integer, nullable=False)
    SiSoHienTai = Column(Integer, nullable=False, default=0)
    ThuTrongTuan = Column(Integer, nullable=False) 
    TietBatDau = Column(Integer, nullable=False)
    SoTiet = Column(Integer, nullable=False)

class Enrollment(Base):
    __tablename__ = "DangKy"
    __table_args__ = (UniqueConstraint("userId", "MaHP", "MaHocKy", name="uq_dk_user_hp_hk"),)

    MaDangKy = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    MaLopHP = Column(String, ForeignKey("LopHocPhan.MaLopHP"), nullable=False)
    MaHP = Column(String, nullable=False)
    MaHocKy = Column(String, nullable=False)
    NgayDangKy = Column(DateTime, default=datetime.utcnow, nullable=False)

class EnrollmentTransfer(Base):
    __tablename__ = "DangKy_ChuyenCoSo"
    __table_args__ = (UniqueConstraint('userId', 'MaLopHP', name='_user_class_link_uc'),)

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    MaLopHP = Column(String, nullable=False) 
    MaHP = Column(String, nullable=False)
    TargetSite = Column(String, nullable=False)
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
