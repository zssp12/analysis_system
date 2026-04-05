"""
database.py — SQLAlchemy 异步引擎、ORM 模型、数据库初始化
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

DATABASE_URL = "sqlite+aiosqlite:///./news.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# ──────────────────────────────────────────
# ORM 模型
# ──────────────────────────────────────────

class Source(Base):
    """订阅源（RSS 或爬虫）"""
    __tablename__ = "sources"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    name       = Column(String(200), nullable=False)
    url        = Column(String(1000), nullable=False, unique=True)
    type       = Column(String(20), nullable=False, default="rss")   # rss | crawler
    category   = Column(String(50), nullable=False)
    enabled    = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class News(Base):
    """新闻条目，以 link 作为唯一键去重"""
    __tablename__ = "news"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    title        = Column(String(500), nullable=False)
    link         = Column(String(2000), unique=True, nullable=False)
    source_id    = Column(Integer, ForeignKey("sources.id"), nullable=True)
    category     = Column(String(50), nullable=False, default="综合")
    description  = Column(Text, nullable=True)
    content      = Column(Text, nullable=True)
    thumbnail    = Column(String(1000), nullable=True)
    published_at = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, default=datetime.datetime.utcnow)


# ──────────────────────────────────────────
# 默认订阅源（首次启动自动写入）
# ──────────────────────────────────────────

DEFAULT_SOURCES = [
    # ── 科技 ──────────────────────────────────────────────────────────────────
    {"name": "TechCrunch",        "url": "https://techcrunch.com/feed/",                                    "type": "rss",     "category": "科技"},
    {"name": "The Verge",         "url": "https://www.theverge.com/rss/index.xml",                          "type": "rss",     "category": "科技"},
    {"name": "BBC 科技",          "url": "https://feeds.bbci.co.uk/news/technology/rss.xml",                "type": "rss",     "category": "科技"},
    {"name": "阮一峰博客",        "url": "https://www.ruanyifeng.com/blog/atom.xml",                        "type": "rss",     "category": "科技"},

    # ── 国际 ──────────────────────────────────────────────────────────────────
    {"name": "BBC World",         "url": "https://feeds.bbci.co.uk/news/world/rss.xml",                     "type": "rss",     "category": "国际"},
    {"name": "Al Jazeera",        "url": "https://www.aljazeera.com/xml/rss/all.xml",                       "type": "rss",     "category": "国际"},
    {"name": "The Guardian",      "url": "https://www.theguardian.com/world/rss",                           "type": "rss",     "category": "国际"},

    # ── 财经 ──────────────────────────────────────────────────────────────────
    {"name": "Bloomberg Markets", "url": "https://feeds.bloomberg.com/markets/news.rss",                    "type": "rss",     "category": "财经"},
    {"name": "华尔街见闻",        "url": "https://wallstreetcn.com/rss",                                    "type": "rss",     "category": "财经"},

    # ── 体育 ──────────────────────────────────────────────────────────────────
    {"name": "ESPN",              "url": "https://www.espn.com/espn/rss/news",                              "type": "rss",     "category": "体育"},
    {"name": "BBC Sport",         "url": "https://feeds.bbci.co.uk/sport/rss.xml",                          "type": "rss",     "category": "体育"},

    # ── 娱乐 ──────────────────────────────────────────────────────────────────
    {"name": "BBC 娱乐",          "url": "https://feeds.bbci.co.uk/news/entertainment_and_arts/rss.xml",    "type": "rss",     "category": "娱乐"},
    {"name": "Variety",           "url": "https://variety.com/feed/",                                       "type": "rss",     "category": "娱乐"},

    # ── 科学 ──────────────────────────────────────────────────────────────────
    {"name": "BBC 科学",          "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",   "type": "rss",     "category": "科学"},
    {"name": "Science Daily",     "url": "https://www.sciencedaily.com/rss/top/science.xml",               "type": "rss",     "category": "科学"},
    {"name": "NASA",              "url": "https://www.nasa.gov/rss/dyn/breaking_news.rss",                  "type": "rss",     "category": "科学"},

    # ── 健康 ──────────────────────────────────────────────────────────────────
    {"name": "WHO 新闻",          "url": "https://www.who.int/rss-feeds/news-releases.xml",                 "type": "rss",     "category": "健康"},

    # ── 高校资讯 ──────────────────────────────────────────────────────────────
    {"name": "上海交通大学新闻",  "url": "https://news.sjtu.edu.cn/jdyw/index.html",                        "type": "crawler", "category": "高校资讯"},
]


async def init_db() -> None:
    """
    创建所有表，并按 URL 去重补充写入默认订阅源。
    每次启动均执行检查：新增的默认源自动入库，已存在的不重复插入。
    """
    import logging as _log
    from sqlalchemy import select
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        added = 0
        for s in DEFAULT_SOURCES:
            exists = await session.execute(select(Source).where(Source.url == s["url"]))
            if exists.scalar_one_or_none() is None:
                session.add(Source(**s))
                added += 1
        if added:
            await session.commit()
            _log.getLogger(__name__).info("init_db: 补充写入 %d 个默认订阅源", added)
