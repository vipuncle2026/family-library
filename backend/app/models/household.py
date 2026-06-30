from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Household(Base):
    """一个家"""

    __tablename__ = "households"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, default="我的家")
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship(
        "HouseholdMember", back_populates="household", cascade="all, delete-orphan"
    )


class HouseholdMember(Base):
    """家庭成员 (可绑定也可不绑定账号)"""

    __tablename__ = "household_members"

    id = Column(Integer, primary_key=True, index=True)
    household_id = Column(Integer, ForeignKey("households.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 可空: 小孩/未注册
    display_name = Column(String(50), nullable=False)
    relation = Column(String(20), nullable=False, default="成员")  # 自己/配偶/子女/父母/其他
    avatar_color = Column(String(20), default="#7C3AED")
    created_at = Column(DateTime, default=datetime.utcnow)

    household = relationship("Household", back_populates="members")
    user = relationship("User", backref="member_profile")
    reading_records = relationship(
        "ReadingRecord", back_populates="member", cascade="all, delete-orphan"
    )
    owned_books = relationship("Book", back_populates="owner_member")
