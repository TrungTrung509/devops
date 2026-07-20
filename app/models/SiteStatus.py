from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from configs.db import Base


class SiteStatus(Base):
    __tablename__ = "SiteStatus"

    SiteId = Column(String(20), primary_key=True, index=True)
    Role = Column(String(20), nullable=False)
    Status = Column(String(20), nullable=False, default="UNKNOWN")
    LastHeartbeat = Column(DateTime, nullable=True)
    LastSuccessAt = Column(DateTime, nullable=True)
    LastError = Column(Text, nullable=True)
    UpdatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
