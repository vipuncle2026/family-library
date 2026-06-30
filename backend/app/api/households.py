from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user, require_admin
from app.models.user import User
from app.models.book import Book
from app.models.household import Household, HouseholdMember
from app.schemas.schemas import (
    HouseholdOut,
    HouseholdMemberCreate,
    HouseholdMemberUpdate,
    HouseholdMemberOut,
)

router = APIRouter(prefix="/api/households", tags=["household"])


async def _ensure_user_household(db: AsyncSession, user: User) -> Household:
    """确保用户有家庭: 第一个用户自动建「我的家」, 之后默认加入第一个家"""
    # 优先: 自己创建的
    result = await db.execute(select(Household).order_by(Household.id).limit(1))
    hh = result.scalar_one_or_none()
    if not hh:
        hh = Household(name=f"{user.nickname}的家")
        db.add(hh)
        await db.flush()
    return hh


def _member_to_out(m: HouseholdMember) -> HouseholdMemberOut:
    """把 ORM 转成 out, 补一个 bound_username 方便前端展示"""
    return HouseholdMemberOut(
        id=m.id,
        household_id=m.household_id,
        user_id=m.user_id,
        display_name=m.display_name,
        relation=m.relation,
        avatar_color=m.avatar_color,
        created_at=m.created_at,
        bound_username=m.user.username if m.user else None,
    )


@router.get("/me", response_model=HouseholdOut)
async def get_my_household(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户的家庭 (含所有成员)"""
    hh = await _ensure_user_household(db, current_user)
    await db.commit()

    result = await db.execute(
        select(HouseholdMember)
        .where(HouseholdMember.household_id == hh.id)
        .options(selectinload(HouseholdMember.user))
        .order_by(HouseholdMember.id)
    )
    members = result.scalars().all()

    return HouseholdOut(
        id=hh.id,
        name=hh.name,
        created_at=hh.created_at,
        members=[_member_to_out(m) for m in members],
    )


@router.get("/users/available")
async def list_available_users(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """admin 看所有可绑定的用户 (未绑定的优先)"""
    result = await db.execute(select(User).order_by(User.id))
    users = result.scalars().all()
    # 同时拿所有已有 member.user_id
    bound = await db.execute(
        select(HouseholdMember.user_id).where(HouseholdMember.user_id.isnot(None))
    )
    bound_ids = {row[0] for row in bound.all()}
    return [
        {
            "id": u.id,
            "username": u.username,
            "nickname": u.nickname,
            "role": u.role,
            "is_bound": u.id in bound_ids,
        }
        for u in users
    ]


@router.post("/me/members", response_model=HouseholdMemberOut)
async def add_member(
    data: HouseholdMemberCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """admin 添加一个家庭成员"""
    hh = await _ensure_user_household(db, admin)
    await db.flush()

    member = HouseholdMember(
        household_id=hh.id,
        display_name=data.display_name,
        relation=data.relation,
        avatar_color=data.avatar_color or "#7C3AED",
        user_id=data.user_id,
    )
    db.add(member)
    await db.commit()
    # 重新拉一次并 eager load user, 避免序列化时 lazy-load
    result = await db.execute(
        select(HouseholdMember)
        .where(HouseholdMember.id == member.id)
        .options(selectinload(HouseholdMember.user))
    )
    return _member_to_out(result.scalar_one())


@router.patch("/me/members/{member_id}", response_model=HouseholdMemberOut)
async def update_member(
    member_id: int,
    data: HouseholdMemberUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(HouseholdMember)
        .where(HouseholdMember.id == member_id)
        .options(selectinload(HouseholdMember.user))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")

    # 用 model_fields_set 区分"未提供"和"显式设值（包括 null=解绑）"
    fields_set = data.model_fields_set

    if "display_name" in fields_set and data.display_name is not None:
        member.display_name = data.display_name
    if "relation" in fields_set and data.relation is not None:
        member.relation = data.relation
    if "avatar_color" in fields_set and data.avatar_color is not None:
        member.avatar_color = data.avatar_color
    if "user_id" in fields_set:
        # 字段在请求里出现过 (即使是 null, 也表示"显式解绑")
        if data.user_id is None:
            member.user_id = None
        else:
            u = await db.execute(select(User).where(User.id == data.user_id))
            if not u.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="绑定的用户不存在")
            member.user_id = data.user_id

    await db.commit()
    # 重新查一次以触发 selectinload
    result = await db.execute(
        select(HouseholdMember)
        .where(HouseholdMember.id == member_id)
        .options(selectinload(HouseholdMember.user))
    )
    return _member_to_out(result.scalar_one())


@router.delete("/me/members/{member_id}")
async def delete_member(
    member_id: int,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(HouseholdMember).where(HouseholdMember.id == member_id)
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="成员不存在")
    # 不删账号, 只删成员关系, 关联的书清空 owner_member_id
    await db.execute(
        Book.__table__.update()
        .where(Book.owner_member_id == member_id)
        .values(owner_member_id=None)
    )
    await db.delete(member)
    await db.commit()
    return {"ok": True}
