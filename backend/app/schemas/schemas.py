from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ===== User Schemas =====
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    nickname: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    avatar: Optional[str] = ""
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ===== Book Schemas =====
class BookBase(BaseModel):
    isbn: Optional[str] = None
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    pages: Optional[int] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    read_status: Optional[str] = "unread"
    owner_member_id: Optional[int] = None


class BookCreate(BookBase):
    # 创建时也允许直接带手动评分 / 豆瓣 ID (从豆瓣搜索结果直接落库)
    douban_id: Optional[str] = None
    douban_rating: Optional[float] = None
    douban_rating_count: Optional[int] = None


class BookUpdate(BaseModel):
    isbn: Optional[str] = None
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    pages: Optional[int] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    read_status: Optional[str] = None
    owner_member_id: Optional[int] = None
    # 手动评分 (豆瓣抓不到时, 管理员/用户可手工录入)
    douban_rating: Optional[float] = None
    douban_rating_count: Optional[int] = None
    douban_id: Optional[str] = None
    clear_manual_rating: Optional[bool] = False  # True 表示清空手动评分


class BookOut(BookBase):
    id: int
    douban_id: Optional[str] = None
    douban_rating: Optional[float] = None
    douban_rating_count: Optional[int] = None
    douban_tags: Optional[str] = None
    last_douban_sync: Optional[datetime] = None
    is_borrowed: bool
    owner_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoubanSearchResult(BaseModel):
    """图书元数据搜索结果 (来源可能是 Open Library / Google Books)"""
    douban_id: str
    title: str
    author: Optional[str] = None
    publisher: Optional[str] = None
    pubdate: Optional[str] = None
    pages: Optional[int] = None
    cover_url: Optional[str] = None
    summary: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    tags: Optional[list] = []
    source: Optional[str] = None  # openlibrary / googlebooks


# ===== Reading Record Schemas =====
class ReadingRecordCreate(BaseModel):
    book_id: int
    progress: int = Field(0, ge=0, le=100)
    duration_minutes: int = 0
    current_page: int = 0
    note: Optional[str] = None
    member_id: Optional[int] = None


class ReadingRecordOut(BaseModel):
    id: int
    book_id: int
    user_id: int
    member_id: Optional[int] = None
    progress: int
    duration_minutes: int
    current_page: int
    note: Optional[str] = None
    read_at: datetime

    class Config:
        from_attributes = True


# ===== Household Schemas =====
class HouseholdMemberCreate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=50)
    relation: str = Field("成员", max_length=20)
    avatar_color: Optional[str] = "#7C3AED"
    user_id: Optional[int] = None  # 绑定已有账号


class HouseholdMemberUpdate(BaseModel):
    display_name: Optional[str] = None
    relation: Optional[str] = None
    avatar_color: Optional[str] = None
    user_id: Optional[int] = None


class HouseholdMemberOut(BaseModel):
    id: int
    household_id: int
    user_id: Optional[int] = None
    display_name: str
    relation: str
    avatar_color: str
    created_at: datetime
    bound_username: Optional[str] = None  # 便利字段: 绑定的账号名

    class Config:
        from_attributes = True


class HouseholdOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    members: list[HouseholdMemberOut] = []

    class Config:
        from_attributes = True
