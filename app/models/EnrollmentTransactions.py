from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, UniqueConstraint

from configs.db import Base
from enums.status import EnrollmentAction, EnrollmentTransactionState


class EnrollmentTransaction(Base):
    __tablename__ = "DangKy_3PC"
    __table_args__ = (
        UniqueConstraint("TxnId", "SiteId", name="uq_dk_3pc_txn_site"),
    )

    RecordId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    TxnId = Column(String(64), nullable=False, index=True)
    CoordinatorSite = Column(String(20), nullable=False)
    SiteId = Column(String(20), nullable=False, index=True)
    UserId = Column(String, nullable=False, index=True)
    Action = Column(Enum(EnrollmentAction), nullable=False)
    State = Column(Enum(EnrollmentTransactionState), nullable=False, default=EnrollmentTransactionState.INIT)
    TargetMaLopHP = Column(String, nullable=False)
    TargetMaHP = Column(String, nullable=False)
    TargetMaHocKy = Column(String, nullable=False)
    OldMaLopHP = Column(String, nullable=True)
    Payload = Column(Text, nullable=False)
    Message = Column(Text, nullable=True)
    CreatedAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    UpdatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
