"""
图书元数据聚合服务
策略: 豆瓣搜索页 (book.douban.com 反爬严, 但走搜索页 search.douban.com 较松)
       → 拿到 subject_id → 拉详情页 (反爬较严, 加 referer/UA 兜底)
- 完全免费, 不需要任何 key
- 失败时返回 None, 业务侧允许空字段
- 加 SQLite 缓存层: 7 天内命中直接返回, 避免重复请求豆瓣被风控
"""
import re
import json
import httpx
import logging
import asyncio
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schemas import DoubanSearchResult
from app.models.meta_cache import MetaCache

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

DOUBAN_ISBN_REDIRECT = "https://book.douban.com/isbn/{}/"
DOUBAN_SUBJECT = "https://book.douban.com/subject/{}/"

# 缓存有效期: 7 天, 元数据 (评分/封面) 不会变太多
CACHE_TTL = timedelta(days=7)
# "not_found" 状态缓存: 1 天, 防止冷门书反复打豆瓣
NEG_TTL = timedelta(days=1)


# ===== HTML 解析工具 =====

def _match1(text: str, pattern: str, group: int = 1, flags: int = re.S) -> Optional[str]:
    m = re.search(pattern, text, flags)
    if not m:
        return None
    try:
        v = m.group(group)
    except (IndexError, Exception):
        return None
    return v.strip() if v else None


def _parse_search_page(html: str) -> List[dict]:
    """从豆瓣搜索页抽出 (subject_id, title, url) 列表"""
    items = []
    # 搜索结果在 <a href="https://book.douban.com/subject/12345/" ...> 里
    for m in re.finditer(
        r'<a[^>]+href="https?://book\.douban\.com/subject/(\d+)/?"[^>]*>(.*?)</a>',
        html,
        re.S,
    ):
        sid = m.group(1)
        title_html = m.group(2)
        # 标题可能在 <span> 里
        t = re.sub(r"<[^>]+>", " ", title_html)
        t = re.sub(r"\s+", " ", t).strip()
        if t and len(t) < 200:
            items.append({"subject_id": sid, "title": t})
    # 去重
    seen = set()
    unique = []
    for it in items:
        if it["subject_id"] not in seen:
            seen.add(it["subject_id"])
            unique.append(it)
    return unique[:10]


def _parse_subject_page(html: str, subject_id: str) -> Optional[dict]:
    """从豆瓣详情页抽出 (title, author, publisher, pubdate, pages, rating, rating_count, summary, cover)"""
    title = _match1(html, r'<span property="v:title">([^<]+)</span>')
    if not title:
        title = _match1(html, r'<title>([^<]+)</title>')
    if title:
        title = re.sub(r"\s+", " ", title).strip()
        # 详情页 title 里会带 " (豆瓣)" 之类尾巴, 清掉
        title = re.sub(r"\s*[\(（]豆瓣[\)）]\s*$", "", title)

    # 作者: <span class="pl"> 作者</span>: <a class="...">名字</a> 们
    authors = re.findall(
        r'<span class="pl">\s*作者\s*</span>\s*:?\s*([\s\S]*?)(?:<br\s*/?>|<span class="pl">|$)',
        html,
    )
    author = None
    if authors:
        block = authors[0]
        author_list = re.findall(r'<a[^>]*>([^<]+)</a>', block)
        if author_list:
            author = " / ".join(a.strip() for a in author_list if a.strip())
        else:
            # 有些作者用纯文本 (无 a 标签), 直接抓文本
            txt = re.sub(r"<[^>]+>", " ", block)
            txt = re.sub(r"\s+", " ", txt).strip().rstrip(":")
            if txt:
                author = txt

    # 出版社: <span class="pl">出版社:</span>  <a>...</a>
    # 注: 豆瓣 HTML 里 pl 后的 : 是中文冒号, 紧贴 </span>, \s* 不匹配
    publisher = _match1(
        html,
        r'<span class="pl">出版社[:：]?</span>\s*<a[^>]*>([^<]+)</a>',
    )
    if not publisher:
        # 备选: 不带 a 标签
        publisher = _match1(
            html,
            r'<span class="pl">出版社[:：]?</span>\s*([\s\S]+?)\s*(?:<br|<)',
        )
    if publisher:
        publisher = publisher.strip()

    # 出版日期
    pubdate = _match1(
        html,
        r'<span class="pl">出版年[:：]?</span>\s*([\s\S]+?)(?:<br\s*/?>|<)',
    )
    if pubdate:
        pubdate = pubdate.strip()

    # 页数
    pages_raw = _match1(
        html,
        r'<span class="pl">页数[:：]?</span>\s*(\d+)',
    )
    pages = int(pages_raw) if pages_raw and pages_raw.isdigit() else None

    # 评分
    rating = _match1(html, r'<strong class="ll rating_num"[^>]*>\s*([0-9.]+)\s*</strong>')
    if not rating:
        rating = _match1(html, r'property="v:average">\s*([0-9.]+)\s*<')
    rating_val = float(rating) if rating else None

    votes = _match1(html, r'property="v:votes"[^>]*>\s*(\d+)\s*<')
    if not votes:
        votes = _match1(html, r'<span class="rating_people">.*?>([\d]+)\s*人评价')
    rating_count = int(votes) if votes and votes.isdigit() else None

    # 简介: <div class="intro"> <p>...</p> </div>  (全角冒号也兼容)
    summary = _match1(html, r'<div class="intro">\s*<p>([\s\S]*?)</p>', re.S)
    if summary:
        summary = re.sub(r"<[^>]+>", "", summary)
        summary = re.sub(r"\s+", " ", summary).strip()[:2000] or None

    # 封面: <img src="https://img1.doubanio.com/...jpg" />
    cover = _match1(html, r'<img[^>]+src="(https://img\d+\.doubanio\.com/[^"]+\.(?:jpg|jpeg|png))"')
    if not cover:
        cover = _match1(html, r'"image"\s*:\s*"(https?://img\d+\.doubanio\.com/[^"]+)"')
    if cover and "/spic" in cover:
        cover = cover.replace("/spic", "/lpic")
    if cover and "s/public" in cover and "/l/" not in cover and "/lpic" not in cover:
        # /view/subject/s/public/sxxx.jpg → /view/subject/l/public/sxxx.jpg
        cover = cover.replace("/s/public", "/l/public")

    if not title:
        return None
    return {
        "subject_id": subject_id,
        "title": title,
        "author": author,
        "publisher": publisher,
        "pubdate": pubdate,
        "pages": pages,
        "rating": rating_val,
        "rating_count": rating_count,
        "summary": summary,
        "cover_url": cover,
    }


def _parse_tags(html: str) -> List[str]:
    """从详情页抽出常用标签"""
    tags_block = _match1(
        html,
        r'<div class="indent" id="db-tags-section">[\s\S]*?<div class="tags">([\s\S]*?)</div>',
    )
    if not tags_block:
        return []
    return [t.strip() for t in re.findall(r'<span>\s*<a[^>]*>([^<]+)</a>', tags_block)][:8]


class BookMetaService:
    """豆瓣爬虫版: 搜索页 → 详情页 (反爬宽松, 真实数据) + SQLite 缓存"""

    def __init__(self):
        self._sem = asyncio.Semaphore(2)  # 限流: 同时最多 2 个请求
        # 用一个固定 bid cookie, 避免豆瓣风控 (不存在的 cookie 比不传 cookie 更稳)
        self._headers = {
            "User-Agent": USER_AGENT,
            "Referer": "https://book.douban.com/",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": "bid=family-library-app",
        }

    # ===== 缓存层 =====

    @staticmethod
    def _cache_to_result(row: MetaCache) -> Optional[DoubanSearchResult]:
        if not row.title:  # 失败记录, title 为空
            return None
        try:
            tags = json.loads(row.tags_json) if row.tags_json else []
        except (json.JSONDecodeError, TypeError):
            tags = []
        return DoubanSearchResult(
            douban_id=row.douban_id,
            title=row.title,
            author=row.author,
            publisher=row.publisher,
            pubdate=row.pubdate,
            pages=row.pages,
            cover_url=row.cover_url,
            summary=row.summary,
            rating=float(row.rating) if row.rating else None,
            rating_count=row.rating_count,
            tags=tags,
            source=row.source or "douban",
        )

    async def _cache_get(self, db: AsyncSession, isbn: str) -> Optional[DoubanSearchResult]:
        """查缓存, 返回 (result, hit_kind): hit_kind ∈ {fresh, negative, miss, expired}"""
        row = (await db.execute(select(MetaCache).where(MetaCache.isbn == isbn))).scalar_one_or_none()
        if not row:
            return None
        now = datetime.utcnow()
        # 失败 (not_found) 走 1 天短 TTL
        ttl = NEG_TTL if row.last_status == "not_found" else CACHE_TTL
        if now - row.last_fetched_at < ttl:
            if row.last_status == "ok":
                logger.info(f"meta cache HIT (fresh) isbn={isbn}")
                return self._cache_to_result(row)
            else:
                # 负缓存: 告诉调用方"已知没数据", 让它走空字段 + 手动录入
                logger.info(f"meta cache HIT (negative) isbn={isbn}")
                return None
        return None

    async def _cache_put(self, db: AsyncSession, isbn: str, result: Optional[DoubanSearchResult]):
        """写入缓存: result=None 记 not_found, 否则记全字段"""
        row = (await db.execute(select(MetaCache).where(MetaCache.isbn == isbn))).scalar_one_or_none()
        if not row:
            row = MetaCache(isbn=isbn)
            db.add(row)
        row.last_fetched_at = datetime.utcnow()
        if result is None:
            row.last_status = "not_found"
            row.fail_count = (row.fail_count or 0) + 1
        else:
            row.last_status = "ok"
            row.fail_count = 0
            row.douban_id = result.douban_id
            row.title = result.title
            row.author = result.author
            row.publisher = result.publisher
            row.pubdate = result.pubdate
            row.pages = result.pages
            row.cover_url = result.cover_url
            row.summary = result.summary
            row.rating = str(result.rating) if result.rating is not None else None
            row.rating_count = result.rating_count
            row.tags_json = json.dumps(result.tags or [], ensure_ascii=False)
            row.source = result.source or "douban"
        await db.commit()

    async def _get_html(self, url: str, params: Optional[dict] = None) -> Optional[str]:
        async with self._sem:
            try:
                async with httpx.AsyncClient(timeout=12, headers=self._headers) as client:
                    r = await client.get(url, params=params, follow_redirects=True)
                    if r.status_code != 200:
                        logger.warning(f"douban get 失败 {r.status_code}: {url[:60]}")
                        return None
                    return r.text
            except Exception as e:
                logger.warning(f"douban 请求异常: {e}")
                return None

    async def _isbn_to_subject_id(self, isbn: str) -> Optional[str]:
        """ISBN → subject_id: 走 /isbn/{isbn}/ 的 301 重定向"""
        url = DOUBAN_ISBN_REDIRECT.format(isbn)
        async with self._sem:
            try:
                async with httpx.AsyncClient(
                    timeout=12,
                    headers={**self._headers, "Cookie": ""},  # 不带 cookie
                    follow_redirects=False,
                ) as client:
                    r = await client.get(url)
                    if r.status_code in (301, 302):
                        loc = r.headers.get("location", "")
                        m = re.search(r"subject/(\d+)", loc)
                        if m:
                            return m.group(1)
            except Exception as e:
                logger.warning(f"isbn→subject_id 失败: {e}")
        return None

    async def _fetch_subject(self, subject_id: str) -> Optional[DoubanSearchResult]:
        html = await self._get_html(DOUBAN_SUBJECT.format(subject_id))
        if not html:
            return None
        data = _parse_subject_page(html, subject_id)
        if not data:
            return None
        return DoubanSearchResult(
            douban_id=data["subject_id"],
            title=data["title"],
            author=data["author"],
            publisher=data["publisher"],
            pubdate=data["pubdate"],
            pages=data["pages"],
            cover_url=data["cover_url"],
            summary=data["summary"],
            rating=data["rating"],
            rating_count=data["rating_count"],
            tags=_parse_tags(html),
            source="douban",
        )

    async def get_by_isbn(self, isbn: str, db: Optional[AsyncSession] = None) -> Optional[DoubanSearchResult]:
        """ISBN 精确查询: 走缓存 → 走豆瓣爬虫
        返回 None 时业务侧应走"空字段 + 手动录入"兜底.
        """
        isbn = isbn.strip().replace("-", "").replace(" ", "")
        if not isbn:
            return None

        # 1) 缓存优先 (7 天 / 1 天)
        if db is not None:
            cached = await self._cache_get(db, isbn)
            if cached is not None:
                return cached

        # 2) 抓豆瓣
        sid = await self._isbn_to_subject_id(isbn)
        if not sid:
            logger.info(f"douban: isbn→subject_id 失败 isbn={isbn}")
            if db is not None:
                await self._cache_put(db, isbn, None)
            return None

        result = await self._fetch_subject(sid)
        if db is not None:
            await self._cache_put(db, isbn, result)
        if result:
            logger.info(f"douban: 抓取成功 isbn={isbn} title={result.title!r}")
        return result

    async def get_by_douban_id(self, douban_id: str, db: Optional[AsyncSession] = None) -> Optional[DoubanSearchResult]:
        """根据豆瓣 subject_id 抓详情 (用于无 ISBN 的书, 走缓存 → 抓豆瓣)

        缓存策略: 按 subject_id 当作 key, 但 _cache_get 用的 isbn 字段, 所以直接抓
        """
        if not douban_id:
            return None
        sid = str(douban_id).strip()
        result = await self._fetch_subject(sid)
        if result and db is not None:
            # 顺手缓存 (用 douban_id 当 isbn key 写, 避免下次重复抓)
            await self._cache_put(db, sid, result)
        return result

    async def search(self, query: str, count: int = 10) -> List[DoubanSearchResult]:
        """书名搜索: search.douban.com 是 SPA 拿不到结果, 走 book.douban.com 的搜索页兜底
        (豆瓣对 book 搜索页的 HTML 抓取同样风控严, 这里直接走 isbn 路径并提示用户用 ISBN 搜)
        """
        # 实际上 book.douban.com 的搜索结果页 (https://book.douban.com/subject_search?)
        # 也是 JS 渲染, 拿不到列表. 给一个友好的空结果, 引导用户用 ISBN.
        query = query.strip()
        if not query:
            return []
        return []


# 保留原变量名, 避免改动 books.py / seed.py
douban_service = BookMetaService()
