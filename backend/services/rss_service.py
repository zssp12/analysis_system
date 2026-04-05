"""
rss_service.py — 使用 feedparser 异步抓取 RSS 订阅源
"""
from __future__ import annotations
import asyncio
import logging
from datetime import datetime
from typing import Optional

import feedparser
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _extract_thumbnail(entry) -> Optional[str]:
    """从 enclosure / media_thumbnail / media_content 中提取缩略图 URL"""
    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image"):
                return enc.get("href") or enc.get("url")

    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        return entry.media_thumbnail[0].get("url")

    if hasattr(entry, "media_content") and entry.media_content:
        for m in entry.media_content:
            t = m.get("type", "")
            if m.get("medium") == "image" or t.startswith("image"):
                return m.get("url")

    return None


def _extract_date(entry) -> Optional[datetime]:
    """将 feedparser 的 time_struct 转为 datetime"""
    for attr in ("published_parsed", "updated_parsed"):
        ts = getattr(entry, attr, None)
        if ts:
            try:
                return datetime(*ts[:6])
            except Exception:
                pass
    return None


def _strip_html(text: str) -> str:
    """去除 HTML 标签，保留纯文本"""
    return BeautifulSoup(text, "lxml").get_text(separator=" ", strip=True)


async def fetch_rss(source_url: str, category: str, source_id: int) -> list[dict]:
    """
    异步抓取并解析 RSS 源，返回新闻字典列表
    （feedparser 是同步库，通过 run_in_executor 避免阻塞事件循环）
    单次抓取超时 20 秒，超时后跳过该源继续处理下一个。
    """
    loop = asyncio.get_running_loop()
    try:
        feed = await asyncio.wait_for(
            loop.run_in_executor(None, feedparser.parse, source_url),
            timeout=20.0,
        )
    except asyncio.TimeoutError:
        logger.warning("RSS fetch timeout >20s, skipped [%s]", source_url)
        return []
    except Exception as exc:
        logger.error("RSS fetch error [%s]: %s", source_url, exc)
        return []

    if feed.bozo and not feed.entries:
        logger.warning("RSS parse warning [%s]: %s", source_url, feed.bozo_exception)

    items: list[dict] = []
    for entry in feed.entries:
        link = getattr(entry, "link", None)
        title = getattr(entry, "title", None)
        if not link or not title:
            continue

        raw_desc = (
            getattr(entry, "summary", None)
            or getattr(entry, "description", None)
            or ""
        )
        description = _strip_html(raw_desc)[:800] if raw_desc else ""

        items.append(
            {
                "title": title.strip()[:400],
                "link": link.strip(),
                "source_id": source_id,
                "category": category,
                "description": description,
                "content": description,
                "thumbnail": _extract_thumbnail(entry),
                "published_at": _extract_date(entry),
            }
        )

    logger.info("RSS [%s] → %d entries", source_url, len(items))
    return items
