from typing import Optional, List
from datetime import datetime
import json
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func, text
from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_user, require_admin
from app.models.user import User
from app.models.book import Book
from app.models.meta_cache import MetaCache
from app.schemas.schemas import BookCreate, BookUpdate, BookOut, DoubanSearchResult
from app.services.douban import douban_service

router = APIRouter(prefix="/api/books", tags=["books"])

ALLOWED_IMAGE_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}


@router.get("", response_model=List[BookOut])
async def list_books(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    read_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    """图书列表, 公开访问(用于游客浏览), 搜索/筛选"""
    stmt = select(Book)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(
            or_(
                Book.title.like(like),
                Book.author.like(like),
                Book.isbn.like(like),
                Book.publisher.like(like),
            )
        )
    if category and category not in ("全部", "all", ""):
        stmt = stmt.where(Book.category == category)
    if read_status and read_status != "all":
        stmt = stmt.where(Book.read_status == read_status)
    stmt = stmt.order_by(Book.updated_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats")
async def book_stats(
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    """统计: 总数/分类/阅读状态分布"""
    total = await db.scalar(select(func.count(Book.id))) or 0
    by_category = await db.execute(
        select(Book.category, func.count(Book.id)).group_by(Book.category)
    )
    by_status = await db.execute(
        select(Book.read_status, func.count(Book.id)).group_by(Book.read_status)
    )
    return {
        "total": total,
        "categories": [{"name": c, "count": n} for c, n in by_category.all() if c],
        "statuses": [{"name": s or "unread", "count": n} for s, n in by_status.all()],
    }


@router.get("/categories", response_model=List[str])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    """所有用过的分类, 供前端做标签云"""
    result = await db.execute(
        select(Book.category).where(Book.category.isnot(None)).group_by(Book.category)
    )
    return [r[0] for r in result.all()]


# 注意: 下列端点必须放在 /{book_id} 之前, 否则会被泛匹配的 book_id 抢走
@router.delete("/meta-cache")
async def clear_meta_cache(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """清空豆瓣元数据缓存 (管理员), 用于: 评分变了想重新拉 / 缓存错乱时手动修复"""
    result = await db.execute(text("DELETE FROM meta_cache"))
    await db.commit()
    return {"ok": True, "deleted": result.rowcount}


@router.get("/meta-cache/stats")
async def meta_cache_stats(
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    """缓存统计: 数量 / 命中分布, 给管理员看"""
    total = await db.scalar(select(func.count(MetaCache.isbn))) or 0
    ok = await db.scalar(
        select(func.count(MetaCache.isbn)).where(MetaCache.last_status == "ok")
    ) or 0
    not_found = total - ok
    return {"total": total, "hit_ok": ok, "negative_cached": not_found}


@router.get("/{book_id}", response_model=BookOut)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    _: User | None = Depends(get_optional_user),
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    return book


@router.post("", response_model=BookOut)
async def create_book(
    data: BookCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增图书, 需要登录"""
    book = Book(**data.model_dump(), owner_id=current_user.id)
    db.add(book)
    await db.commit()
    await db.refresh(book)
    return book


@router.put("/{book_id}", response_model=BookOut)
async def update_book(
    book_id: int,
    data: BookUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    payload = data.model_dump(exclude_unset=True)
    # 显式清空手动评分
    if payload.pop("clear_manual_rating", False):
        book.douban_rating = None
        book.douban_rating_count = None
    for k, v in payload.items():
        setattr(book, k, v)
    await db.commit()
    await db.refresh(book)
    return book


@router.delete("/{book_id}")
async def delete_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if book.owner_id and book.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除")
    await db.delete(book)
    await db.commit()
    return {"ok": True}


# ===== 豆瓣同步相关 =====

@router.get("/douban/search", response_model=List[DoubanSearchResult])
async def douban_search(q: str = Query(..., min_length=1)):
    """书名/作者搜索豆瓣"""
    return await douban_service.search(q)


@router.get("/douban/isbn/{isbn}", response_model=Optional[DoubanSearchResult])
async def douban_by_isbn(isbn: str, db: AsyncSession = Depends(get_db)):
    """ISBN 精确查豆瓣 (走 7 天缓存, 失败时返回 404 而不是 502, 便于前端走"手动录入"兜底)"""
    result = await douban_service.get_by_isbn(isbn, db=db)
    if result is None:
        # 区分: 缓存负命中 vs ISBN 格式错; 业务侧都让前端走手动录入
        raise HTTPException(status_code=404, detail="豆瓣暂无该 ISBN 数据, 可切到手动录入")
    return result


@router.post("/{book_id}/sync-douban", response_model=BookOut)
async def sync_douban(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据 ISBN 重新拉取豆瓣元数据更新"""
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    if not book.isbn:
        raise HTTPException(status_code=400, detail="该书没有 ISBN, 无法同步豆瓣")

    result = await douban_service.get_by_isbn(book.isbn, db=db)
    if not result:
        # 同步失败不当作系统错误, 让前端知道"豆瓣没数据"并提示手动补
        raise HTTPException(
            status_code=404,
            detail="豆瓣暂无该 ISBN 数据, 可在详情页手动设置评分/封面/简介",
        )

    _apply_douban_to_book(book, result)
    await db.commit()
    await db.refresh(book)
    return book


@router.post("/{book_id}/sync-douban-by-id", response_model=BookOut)
async def sync_douban_by_id(
    book_id: int,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """根据 douban_id 重新拉取豆瓣元数据更新 (用于无 ISBN 的情况, 比如用书名+作者搜到后入库)"""
    book = await db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")
    douban_id = payload.get("douban_id") or book.douban_id
    if not douban_id:
        raise HTTPException(status_code=400, detail="缺少 douban_id, 无法同步")

    result = await douban_service.get_by_douban_id(douban_id, db=db)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="豆瓣暂无该 douban_id 数据, 可在详情页手动设置评分/封面/简介",
        )

    _apply_douban_to_book(book, result)
    await db.commit()
    await db.refresh(book)
    return book


def _apply_douban_to_book(book: Book, result) -> None:
    """把豆瓣搜索结果回填到 Book 对象 (公共逻辑)"""
    book.douban_id = result.douban_id
    book.douban_rating = result.rating
    book.douban_rating_count = result.rating_count
    book.douban_tags = json.dumps(result.tags, ensure_ascii=False)
    book.last_douban_sync = datetime.utcnow()
    # 顺便补全空字段
    if not book.cover_url and result.cover_url:
        book.cover_url = result.cover_url
    if not book.summary and result.summary:
        book.summary = result.summary
    if not book.author and result.author:
        book.author = result.author
    if not book.publisher and result.publisher:
        book.publisher = result.publisher
    if not book.pages and result.pages:
        book.pages = result.pages


@router.post("/upload-cover")
async def upload_cover(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """本地上传图书封面, 保存到 data/uploads/, 返回 /uploads/<filename> 形式的 URL"""
    # 校验类型
    ext = ALLOWED_IMAGE_TYPES.get(file.content_type)
    if not ext:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的图片类型: {file.content_type} (允许 jpg/png/webp/gif)",
        )
    # 读全部内容, 校验大小
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件过大: {len(content)//1024}KB > {settings.MAX_UPLOAD_SIZE//1024//1024}MB",
        )
    # 写盘
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    name = f"cover_{uuid.uuid4().hex}.{ext}"
    dest = upload_dir / name
    dest.write_bytes(content)
    return {"url": f"/uploads/{name}", "filename": name, "size": len(content)}
