from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    isbn = Column(String(20), index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255))
    publisher = Column(String(255))
    pubdate = Column(String(50))
    pages = Column(Integer)
    cover_url = Column(String(500))
    summary = Column(Text)
    category = Column(String(50), index=True)  # 小说/历史/科技/...
    location = Column(String(100))  # 家中存放位置
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner_member_id = Column(Integer, ForeignKey("household_members.id"))  # 归属家庭成员

    # 豆瓣元数据
    douban_id = Column(String(50))
    douban_rating = Column(Float)  # 豆瓣评分 0-10
    douban_rating_count = Column(Integer)  # 评分人数
    douban_tags = Column(String(500))  # JSON string
    last_douban_sync = Column(DateTime)  # 上次同步时间

    # 阅读状态
    read_status = Column(String(20), default="unread")  # unread / reading / finished
    is_borrowed = Column(Boolean, default=False)
    borrower_id = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reading_records = relationship("ReadingRecord", back_populates="book", cascade="all, delete-orphan")
    owner = relationship("User", foreign_keys=[owner_id])
    owner_member = relationship("HouseholdMember", back_populates="owned_books")
