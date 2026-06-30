from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.household import Household, HouseholdMember
from app.schemas.schemas import UserCreate, UserLogin, UserOut, Token

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _pick_avatar_color() -> str:
    """新用户默认头像色, 跟 admin 紫区分开"""
    palette = ["#F59E0B", "#10B981", "#EC4899", "#3B82F6", "#8B5CF6", "#EF4444"]
    import random
    return random.choice(palette)


@router.post("/register", response_model=Token)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 看是不是系统里第一个用户
    count_result = await db.execute(select(User))
    is_first = len(count_result.scalars().all()) == 0

    # 看是不是这个家庭第一个注册的用户 (用于决定加入现有家还是新建)
    existing_hh = (await db.execute(select(Household).order_by(Household.id).limit(1))).scalar_one_or_none()

    user = User(
        username=data.username,
        nickname=data.nickname,
        hashed_password=get_password_hash(data.password),
        role="admin" if is_first else "member",
    )
    db.add(user)
    await db.flush()  # 拿 user.id

    if existing_hh is None:
        # 第一个家庭: 拿这个新用户当 admin, 同时建成员
        hh = Household(name=f"{data.nickname}的家")
        db.add(hh)
        await db.flush()
        member = HouseholdMember(
            household_id=hh.id,
            user_id=user.id,
            display_name=data.nickname,
            relation="自己",
            avatar_color="#7C3AED",
        )
        db.add(member)
    else:
        # 已有家庭: 当前用户加入, 但 admin 也会自动绑定; 第二个 member 起按昵称占位
        member = HouseholdMember(
            household_id=existing_hh.id,
            user_id=user.id,
            display_name=data.nickname,
            relation="成员",
            avatar_color=_pick_avatar_color(),
        )
        db.add(member)

    await db.commit()
    await db.refresh(user)

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == data.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="账号已禁用")

    token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
