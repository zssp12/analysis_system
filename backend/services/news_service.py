"""
news_service.py — 新闻数据库操作（去重入库、分页查询）
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from database import AsyncSessionLocal, News, Source

logger = logging.getLogger(__name__)


async def save_news_items(items: list[dict]) -> int:
    """
    批量入库，以 link 为唯一键去重（INSERT OR IGNORE）
    返回实际新增条数
    """
    if not items:
        return 0

    saved = 0
    async with AsyncSessionLocal() as session:
        for item in items:
            stmt = (
                sqlite_insert(News)
                .values(
                    title=(item.get("title") or "")[:400],
                    link=(item.get("link") or "").strip(),
                    source_id=item.get("source_id"),
                    category=item.get("category") or "综合",
                    description=item.get("description") or "",
                    content=item.get("content") or "",
                    thumbnail=item.get("thumbnail"),
                    published_at=item.get("published_at"),
                    created_at=datetime.utcnow(),
                )
                .on_conflict_do_nothing(index_elements=["link"])
            )
            result = await session.execute(stmt)
            saved += result.rowcount
        await session.commit()

    logger.info("save_news_items: %d new records saved (out of %d)", saved, len(items))
    return saved


async def get_news(
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[News]:
    """分页查询新闻，按发布时间倒序"""
    async with AsyncSessionLocal() as session:
        q = select(News).order_by(
            News.published_at.desc().nullslast(),
            News.created_at.desc(),
        )
        if category and category != "all":
            q = q.where(News.category == category)
        q = q.offset(skip).limit(limit)
        result = await session.execute(q)
        return result.scalars().all()


async def get_news_by_id(news_id: int) -> Optional[News]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(News).where(News.id == news_id))
        return result.scalar_one_or_none()


async def get_all_enabled_sources() -> list[Source]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Source).where(Source.enabled == True)
        )
        return result.scalars().all()


async def get_distinct_categories() -> list[str]:
    """获取数据库中所有出现过的类别"""
    from sqlalchemy import distinct
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(distinct(News.category)).order_by(News.category)
        )
        return [row[0] for row in result.all()]


async def get_category_counts() -> dict:
    """统计各类别新闻数量，结果含 'all' 总数键"""
    from sqlalchemy import func
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(News.category, func.count(News.id).label("cnt"))
            .group_by(News.category)
        )
        counts: dict = {row[0]: row[1] for row in result.all()}
        counts["all"] = sum(counts.values())
        return counts
