import enum
from sqlalchemy import Column, String, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime

from configs.db import Base
from enums.status import TeacherStatus
from enums.gender import Genders

class Teacher(Base):
    __tablename__ = "GiangVien"

    MaGV = Column(String, primary_key=True, index=True)
    userId = Column(String, ForeignKey("users.userId"), unique=True, nullable=False)
    Ho = Column(String, nullable=False)
    Ten = Column(String, nullable=False)
    NgaySinh = Column(Date)
    GioiTinh = Column(Enum(Genders))
    HocVi = Column(String)
    HocHam = Column(String)
    SDT = Column(String)
    DiaChi = Column(String)
    MaCoSo = Column(String, nullable=False)
    MaKhoa = Column(String)
    TrangThai = Column(Enum(TeacherStatus), default=TeacherStatus.DangCongTac)
    NgayVaoLam = Column(Date)
    NgayTao = Column(String)

    # Relationship with User
    user = relationship("User")

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
    # Trung
    # __tablename__ = "GiangVien"
    # MaGV = Column(String, primary_key=True, index=True)
    # userId = Column(String, ForeignKey("users.userId"), unique=True)
    # Ho = Column(String, nullable=False)
    # Ten = Column(String, nullable=False)
    # NgaySinh = Column(Date)
    # GioiTinh = Column(Enum(Genders), default=Genders.Khac)
    # SDT = Column(String)
    # DiaChi = Column(String)
    # HocVi = Column(String, nullable=True)
    # HocHam = Column(String, nullable=True)
    # MaCoSo = Column(String, ForeignKey("CoSo.MaCoSo"), default="HADONG")
    # MaKhoa = Column(String, ForeignKey("Khoa.MaKhoa"))
    # TrangThai = Column(Enum(TeacherStatus), default=TeacherStatus.DangCongTac)
    # NgayVaoLam = Column(Date)
    # NgayTao = Column(DateTime, default=datetime.utcnow)

    # user = relationship("User")
    # # branch = relationship("Branch")
    # # department = relationship("Departments")

    # # Remaining Proxies to User model
    # username = association_proxy("user", "username")
    # email = association_proxy("user", "email")
    # status = association_proxy("user", "status")
    # role = association_proxy("user", "role")
