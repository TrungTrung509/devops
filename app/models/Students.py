import enum
from sqlalchemy import Column, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from configs.db import Base
from enums.gender import Genders
from enums.status import StudentStatus

class Student(Base):
    __tablename__ = "SinhVien"

    MaSV = Column(String, primary_key=True, index=True)
    userId = Column(String, ForeignKey("users.userId"), unique=True, nullable=False)
    Ho = Column(String, nullable=False)
    Ten = Column(String, nullable=False)
    NgaySinh = Column(Date)
    GioiTinh = Column(Enum(Genders))
    SDT = Column(String)
    DiaChi = Column(String)
    MaCoSo = Column(String, nullable=False)
    MaKhoa = Column(String)
    TrangThai = Column(Enum(StudentStatus), default=StudentStatus.DangHoc)
    NgayNhapHoc = Column(Date)
    NgayTao = Column(String)

    # Relationship with User
    user = relationship("User", back_populates="student")

    @property
    def username(self):
        return self.user.username if self.user else None

    @property
    def email(self):
        return self.user.email if self.user else None

    @property
    def role(self):
        return self.user.role if self.user else None

    @property
    def status(self):
        return self.user.status if self.user else None

    # Relationships with Campus and Department (reference tables)
    # Note: These use MaCoSo/MaKhoa for distributed DB pattern
    # For distributed setup, this can be managed via site-specific queries
    # Trung
    # def __repr__(self):
    #     return f"<Student(MaSV='{self.MaSV}', Ho='{self.Ho}', Ten='{self.Ten}')>"

    # __tablename__ = "SinhVien"
    # MaSV = Column(String, primary_key=True, index=True)
    # userId = Column(String, ForeignKey("users.userId"), unique=True)
    # Ho = Column(String, nullable=False)
    # Ten = Column(String, nullable=False)
    # NgaySinh = Column(Date)
    # GioiTinh = Column(Enum(Genders), default=Genders.Khac)
    # SDT = Column(String)
    # DiaChi = Column(String)
    # MaCoSo = Column(String, ForeignKey("CoSo.MaCoSo"), default="HADONG")
    # MaKhoa = Column(String, ForeignKey("Khoa.MaKhoa"))
    # TrangThai = Column(Enum(StudentStatus), default=StudentStatus.DangHoc)
    # NgayNhapHoc = Column(Date)
    # NgayTao = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User")
    # # branch = relationship("Branch") # Branch model might need name check
    # # department = relationship("Departments") # Department model might need name check

    # # Remaining Proxies to User model
    # username = association_proxy("user", "username")
    # email = association_proxy("user", "email")
    # status = association_proxy("user", "status")
    # role = association_proxy("user", "role")
