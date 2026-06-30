from typing import List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.book import Book
from app.models.reading_record import ReadingRecord
from app.schemas.schemas import ReadingRecordCreate, ReadingRecordOut

router = APIRouter(prefix="/api/reading", tags=["reading"])


@router.post("/records", response_model=ReadingRecordOut)
async def create_record(
    data: ReadingRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    book = await db.get(Book, data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="图书不存在")

    record = ReadingRecord(
        book_id=data.book_id,
        user_id=current_user.id,
        progress=data.progress,
        duration_minutes=data.duration_minutes,
        current_page=data.current_page,
        note=data.note,
        read_at=datetime.utcnow(),
    )
    db.add(record)

    # 自动更新书的阅读状态
    if data.progress >= 100:
        book.read_status = "finished"
    elif data.progress > 0:
        book.read_status = "reading"

    await db.commit()
    await db.refresh(record)
    return record


@router.get("/records", response_model=List[ReadingRecordOut])
async def list_records(
    book_id: int | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(ReadingRecord).where(ReadingRecord.user_id == current_user.id)
    if book_id:
        stmt = stmt.where(ReadingRecord.book_id == book_id)
    stmt = stmt.order_by(ReadingRecord.read_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats")
async def reading_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户阅读统计: 总时长/天数/最近 N 天"""
    since = datetime.utcnow() - timedelta(days=days)

    total_minutes = await db.scalar(
        select(func.coalesce(func.sum(ReadingRecord.duration_minutes), 0))
        .where(ReadingRecord.user_id == current_user.id)
        .where(ReadingRecord.read_at >= since)
    )
    record_count = await db.scalar(
        select(func.count(ReadingRecord.id))
        .where(ReadingRecord.user_id == current_user.id)
        .where(ReadingRecord.read_at >= since)
    )
    finished_books = await db.scalar(
        select(func.count(Book.id))
        .where(Book.owner_id == current_user.id)
        .where(Book.read_status == "finished")
    )
    return {
        "total_minutes": int(total_minutes or 0),
        "record_count": int(record_count or 0),
        "finished_books": int(finished_books or 0),
        "days": days,
    }
