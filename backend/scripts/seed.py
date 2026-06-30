"""
初始化演示数据: 默认管理员 + 一个家庭 + 几张参考截图里的图书
运行: python -m scripts.seed
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import init_db, AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.book import Book
from app.models.household import Household, HouseholdMember
from app.services.douban import douban_service


DEFAULT_CATEGORIES = [
    {"name": "小说", "color": "blue"},
    {"name": "历史", "color": "amber"},
    {"name": "文学", "color": "purple"},
    {"name": "传记", "color": "pink"},
    {"name": "科技", "color": "teal"},
    {"name": "心理", "color": "coral"},
    {"name": "经管", "color": "green"},
    {"name": "计算机", "color": "gray"},
    {"name": "科学", "color": "teal"},
    {"name": "艺术", "color": "pink"},
    {"name": "教育", "color": "amber"},
]


SEED_BOOKS = [
    {"isbn": "9787122326751", "title": "历史穿越报·元朝卷", "author": "彭凡", "category": "历史", "location": "儿童房书架第二层", "for": "女儿"},
    {"isbn": "9787122326744", "title": "历史穿越报·秦汉", "author": "彭凡", "category": "历史", "location": "儿童房书架第二层", "for": "女儿"},
    {"isbn": "9787122326737", "title": "历史穿越报·夏商西周", "author": "彭凡", "category": "历史", "location": "儿童房书架第二层", "for": "女儿"},
    {"isbn": "9787020002207", "title": "红楼梦", "author": "曹雪芹", "category": "文学", "location": "客厅书柜上层", "for": "夫人"},
    {"isbn": "9787020043439", "title": "百年孤独", "author": "加西亚·马尔克斯", "category": "文学", "location": "客厅书柜上层", "for": "夫人"},
    {"isbn": "9787544253994", "title": "霍乱时期的爱情", "author": "加西亚·马尔克斯", "category": "文学", "location": "客厅书柜上层", "for": "夫人"},
    {"isbn": "9787108036091", "title": "万历十五年", "author": "黄仁宇", "category": "历史", "location": "书房书架A3", "for": "书管"},
    {"isbn": "9787213025945", "title": "人类简史", "author": "尤瓦尔·赫拉利", "category": "历史", "location": "书房书架B1", "for": "书管"},
    {"isbn": "9787508649170", "title": "未来简史", "author": "尤瓦尔·赫拉利", "category": "历史", "location": "书房书架B1", "for": "书管"},
    {"isbn": "9787508672062", "title": "今日简史", "author": "尤瓦尔·赫拉利", "category": "历史", "location": "书房书架B1", "for": "书管"},
    {"isbn": "9787115428028", "title": "深入理解计算机系统", "author": "Randal E. Bryant", "category": "计算机", "location": "书房书架C2", "for": "书管"},
    {"isbn": "9787121362460", "title": "算法导论", "author": "Thomas H. Cormen", "category": "计算机", "location": "书房书架C2", "for": "书管"},
    {"isbn": "9787111545140", "title": "设计模式", "author": "Erich Gamma", "category": "计算机", "location": "书房书架C2", "for": "书管"},
    {"isbn": "9787121362477", "title": "代码大全", "author": "Steve McConnell", "category": "计算机", "location": "书房书架C2", "for": "书管"},
    {"isbn": "9787508653444", "title": "小王子", "author": "圣埃克苏佩里", "category": "小说", "location": "儿童房书架第一层", "for": "儿子"},
]


# 默认家庭结构
DEFAULT_FAMILY = [
    {"key": "self",    "display_name": "书管",     "relation": "自己", "avatar_color": "#8B6914", "bind_admin": True},
    {"key": "wife",    "display_name": "夫人",     "relation": "配偶", "avatar_color": "#C45C3F", "bind_admin": False},
    {"key": "daughter","display_name": "女儿",     "relation": "子女", "avatar_color": "#D4943B", "bind_admin": False},
    {"key": "son",     "display_name": "儿子",     "relation": "子女", "avatar_color": "#3F6B5A", "bind_admin": False},
]


async def main():
    print(">> 初始化数据库表...")
    await init_db()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # ===== 1. 默认管理员 =====
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = User(
                username="admin",
                nickname="书管",
                hashed_password=get_password_hash("admin123"),
                role="admin",
            )
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            print(">> 创建默认管理员: admin / admin123")
        else:
            print(">> 管理员已存在, 跳过")
        # 同步旧数据: 已存在的 admin 昵称若还是旧值, 一并更新
        if admin and admin.nickname == "菜鸡":
            admin.nickname = "书管"
            await db.commit()
            print(">> 已将管理员昵称 '菜鸡' 升级为 '书管'")

        # ===== 2. 默认家庭 =====
        hh = (await db.execute(select(Household).order_by(Household.id).limit(1))).scalar_one_or_none()
        if not hh:
            hh = Household(name="书管的小家")
            db.add(hh)
            await db.flush()
            print(">> 创建默认家庭: 书管的小家")
        else:
            print(">> 家庭已存在, 跳过")
        # 同步旧家庭名
        if hh and hh.name == "菜鸡家":
            hh.name = "书管的小家"
            await db.commit()
            print(">> 已将家庭名 '菜鸡家' 升级为 '书管的小家'")

        # ===== 3. 默认家庭成员 =====
        existing_members = await db.execute(
            select(HouseholdMember).where(HouseholdMember.household_id == hh.id)
        )
        members_list = existing_members.scalars().all()
        if not members_list:
            for fm in DEFAULT_FAMILY:
                m = HouseholdMember(
                    household_id=hh.id,
                    user_id=admin.id if fm["bind_admin"] else None,
                    display_name=fm["display_name"],
                    relation=fm["relation"],
                    avatar_color=fm["avatar_color"],
                )
                db.add(m)
            await db.flush()
            print(f">> 创建 {len(DEFAULT_FAMILY)} 个家庭成员")
        else:
            print(f">> 家庭成员已存在 ({len(members_list)}), 跳过")

        # 重新拉一次成员 (拿 id 用)
        members_result = await db.execute(
            select(HouseholdMember).where(HouseholdMember.household_id == hh.id)
        )
        members_map = {m.display_name: m for m in members_result.scalars().all()}

        # 同步旧成员 display_name: '菜鸡' → '书管'
        for m in members_map.values():
            if m.display_name == "菜鸡":
                m.display_name = "书管"
        await db.commit()
        # 重建 map (因为 display_name 是 key)
        members_map = {m.display_name: m for m in members_map.values()}

        # ===== 4. 图书 =====
        existing_books = await db.execute(select(Book))
        if existing_books.scalars().all():
            print(">> 图书数据已存在, 跳过 seed")
            print(f">> 默认账户: admin / admin123")
            print(f">> 家庭: {hh.name} (书管/夫人/女儿/儿子)")
            return

        print(f">> 写入 {len(SEED_BOOKS)} 本演示书...")
        created = 0
        for item in SEED_BOOKS:
            # 归属成员
            target_key = item.get("for")
            target_member = members_map.get(target_key) if target_key else None
            owner_member_id = target_member.id if target_member else None

            book = Book(
                isbn=item["isbn"],
                title=item["title"],
                author=item["author"],
                category=item["category"],
                location=item["location"],
                owner_id=admin.id,
                owner_member_id=owner_member_id,
                read_status="unread",
            )
            # 尝试同步元数据 (Open Library / Google Books)
            try:
                d = await douban_service.get_by_isbn(item["isbn"])
                if d:
                    book.douban_id = d.douban_id
                    book.douban_rating = d.rating
                    book.douban_rating_count = d.rating_count
                    book.cover_url = d.cover_url
                    book.summary = d.summary
                    book.publisher = d.publisher
                    book.pages = d.pages
                    book.last_douban_sync = __import__("datetime").datetime.utcnow()
                    print(f"   [元数据 OK · {d.source}] {item['title']} 评分: {d.rating or '无'}")
                else:
                    print(f"   [元数据 MISS] {item['title']} (将用占位图)")
            except Exception as e:
                print(f"   [元数据异常] {item['title']}: {e}")

            db.add(book)
            created += 1

        await db.commit()
        print(f">> 完成, 共写入 {created} 本图书")
        print(f">> 默认账户: admin / admin123")
        print(f">> 家庭: {hh.name} (书管/夫人/女儿/儿子)")


if __name__ == "__main__":
    asyncio.run(main())
