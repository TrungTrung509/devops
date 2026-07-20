from sqlalchemy import Column, String, Enum
from sqlalchemy.orm import relationship
from configs.db import Base
from enums.status import UserStatus
from enums.user_role import UserRole

class User(Base):
    __tablename__ = "users"

    userId = Column(String, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(Enum(UserRole), nullable=False)  
    MaCoSo = Column(String, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.Active) 
    NgayTao = Column(String)

    # Relationship with Student
    student = relationship("Student", back_populates="user", uselist=False)
    # # Trung
    # email = Column(String, nullable=True)
    # MaCoSo = Column(String, nullable=False)
    # status = Column(Enum(UserStatus), default=UserStatus.Active)
