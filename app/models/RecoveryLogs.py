from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Enum, Text
from configs.db import Base
from enums.status import RecoveryAction, LogStatus

class RecoveryLog(Base):
    __tablename__ = "NhatKyPhucHoi"

    LogId = Column(Integer, primary_key=True, index=True, autoincrement=True)
    TxnId = Column(String(64), nullable=False, index=True)
    userId = Column(String, nullable=True, index=True)
    MaLopHP = Column(String(20), nullable=True)
    Action = Column(Enum(RecoveryAction), nullable=False)

    MaCoSo = Column(String(20), nullable=True)
    Status = Column(Enum(LogStatus), default=LogStatus.SUCCESS)

    Message = Column(Text, nullable=True)
    Timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)