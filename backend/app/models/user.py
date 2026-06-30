from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    nickname = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar = Column(String(255), default="")
    role = Column(String(20), default="member")  # admin / member
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    reading_records = relationship("ReadingRecord", back_populates="user", cascade="all, delete-orphan")
