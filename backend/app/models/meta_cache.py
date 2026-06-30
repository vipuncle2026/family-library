"""
豆瓣元数据缓存表
- 主键: isbn
- 命中: 7 天内直接返回, 不打豆瓣
- 失败不写缓存, 允许下次重试
- 内存 LRU 不需要, SQLite 够用
"""
from sqlalchemy import Column, String, DateTime, Integer, Text
from datetime import datetime
from app.core.database import Base


class MetaCache(Base):
    __tablename__ = "meta_cache"

    isbn = Column(String(20), primary_key=True)  # 13 位 ISBN
    douban_id = Column(String(50))  # 豆瓣 subject_id, 没拿到时为 None
    title = Column(String(255))
    author = Column(String(255))
    publisher = Column(String(255))
    pubdate = Column(String(50))
    pages = Column(Integer)
    cover_url = Column(String(500))
    summary = Column(Text)
    rating = Column(String(20))  # 字符串存 float, 避免 NULL 比较
    rating_count = Column(Integer)
    tags_json = Column(Text)  # JSON list
    source = Column(String(20), default="douban")

    last_fetched_at = Column(DateTime, default=datetime.utcnow)
    last_status = Column(String(20))  # "ok" / "not_found" - 失败也记, 避免反复打
    fail_count = Column(Integer, default=0)
