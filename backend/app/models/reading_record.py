from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class ReadingRecord(Base):
    __tablename__ = "reading_records"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("household_members.id"))  # 归属家庭成员
    progress = Column(Integer, default=0)  # 阅读进度 0-100
    duration_minutes = Column(Integer, default=0)  # 本次阅读时长
    current_page = Column(Integer, default=0)
    note = Column(Text)
    read_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="reading_records")
    user = relationship("User", back_populates="reading_records")
    member = relationship("HouseholdMember", back_populates="reading_records")
