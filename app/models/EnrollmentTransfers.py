from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, UniqueConstraint
from configs.db import Base

class EnrollmentTransfer(Base):
    __tablename__ = "DangKy_ChuyenCoSo"

    Id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    userId = Column(String, ForeignKey("users.userId"), nullable=False)
    MaLopHP = Column(String, nullable=False) 
    MaHP = Column(String, nullable=False)
    TargetSite = Column(String, nullable=False)
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('userId', 'MaLopHP', name='_user_class_link_uc'),
    )
