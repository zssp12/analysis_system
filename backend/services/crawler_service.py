"""
crawler_service.py — BeautifulSoup 爬虫
  · fetch_sjtu()       上海交通大学新闻网（示例学校爬虫）
  · generic_crawl()    通用启发式爬取（提取页面所有 <a> 链接+标题）
  · try_parse_url()    先尝试 RSS，失败则 fallback 到通用爬虫
  · validate_url()     校验 URL 有效性，供添加订阅源时调用
"""
from __future__ import annotations
import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urljoin, urlparse

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

SJTU_BASE = "https://news.sjtu.edu.cn"


# ──────────────────────────────────────────
# 上海交通大学新闻网爬虫（示例）
# ──────────────────────────────────────────

def _fetch_sjtu_sync() -> list[dict]:
    """同步爬取 SJTU 新闻列表（在 executor 中运行）"""
    url = f"{SJTU_BASE}/jdyw/index.html"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = "utf-8"
    except Exception as exc:
        logger.error("SJTU fetch error: %s", exc)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    items: list[dict] = []

    # SJTU 新闻列表结构：<ul class="news-list"> 或含 date/time 子元素的 <li>
    # 选择器尽量宽泛，以应对网页改版
    selectors = [
        "ul.news-list li",
        "ul.list-news li",
        ".news-list li",
        ".article-list li",
        "li.news-item",
    ]
    list_items = []
    for sel in selectors:
        list_items = soup.select(sel)
        if list_items:
            break

    # fallback：找所有含有日期文字的 <li>
    if not list_items:
        date_pat = re.compile(r"\d{4}[-./]\d{2}[-./]\d{2}")
        list_items = [li for li in soup.find_all("li") if date_pat.search(li.get_text())]

    for li in list_items[:40]:
        a_tag = li.find("a", href=True)
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        href = a_tag["href"]
        if not title or len(title) < 4:
            continue
        if not href.startswith("http"):
            href = urljoin(SJTU_BASE, href)

        # 提取日期
        published_at: Optional[datetime] = None
        date_el = li.find(class_=re.compile(r"date|time|pub", re.I))
        raw_date = date_el.get_text(strip=True) if date_el else ""
        if not raw_date:
            m = re.search(r"(\d{4})[-./年](\d{1,2})[-./月](\d{1,2})", li.get_text())
            if m:
                raw_date = f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                published_at = datetime.strptime(raw_date[:10], fmt)
                break
            except ValueError:
                pass

        items.append(
            {
                "title": title[:400],
                "link": href,
                "source_id": None,
                "category": "高校资讯",
                "description": "",
                "content": "",
                "thumbnail": None,
                "published_at": published_at or datetime.now(),
            }
        )

    logger.info("SJTU crawler → %d entries", len(items))
    return items


async def fetch_sjtu(source_id: int) -> list[dict]:
    loop = asyncio.get_running_loop()
    items = await loop.run_in_executor(None, _fetch_sjtu_sync)
    for item in items:
        item["source_id"] = source_id
    return items


# ──────────────────────────────────────────
# 通用爬虫（启发式提取超链接）
# ──────────────────────────────────────────

def _generic_crawl_sync(url: str, category: str, source_id: int) -> list[dict]:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.encoding = resp.apparent_encoding or "utf-8"
    except Exception as exc:
        logger.error("Generic crawl error [%s]: %s", url, exc)
        return []

    soup = BeautifulSoup(resp.text, "lxml")
    base_domain = urlparse(url).netloc
    items: list[dict] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        title = a.get_text(strip=True)
        href: str = a["href"]
        if not title or len(title) < 8 or href in seen:
            continue
        if not href.startswith("http"):
            href = urljoin(url, href)
        # 只保留同域名链接
        if urlparse(href).netloc != base_domain:
            continue
        seen.add(href)
        items.append(
            {
                "title": title[:400],
                "link": href,
                "source_id": source_id,
                "category": category,
                "description": "",
                "content": "",
                "thumbnail": None,
                "published_at": datetime.now(),
            }
        )
        if len(items) >= 30:
            break

    return items


# ──────────────────────────────────────────
# 统一入口：先试 RSS，再 fallback 通用爬虫
# ──────────────────────────────────────────

async def try_parse_url(
    url: str,
    source_id: int,
    category: str,
    source_type: str = "rss",
) -> list[dict]:
    """
    source_type='rss'    → feedparser 解析；失败则 fallback 到通用爬虫
    source_type='crawler' → 直接用通用爬虫（或 SJTU 专用爬虫）
    """
    if source_type == "rss":
        loop = asyncio.get_running_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)
        if feed.entries:
            from services.rss_service import fetch_rss
            return await fetch_rss(url, category, source_id)
        logger.info("RSS fallback to crawler for: %s", url)

    # crawler 专用或 fallback
    if "sjtu.edu.cn" in url:
        return await fetch_sjtu(source_id)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _generic_crawl_sync, url, category, source_id
    )


# ──────────────────────────────────────────
# URL 校验（添加订阅源时调用）
# ──────────────────────────────────────────

async def validate_url(
    url: str, source_type: str
) -> tuple[bool, str, list[dict]]:
    """
    返回 (is_valid, message, sample_items)
    sample_items 最多 3 条，供前端预览
    """
    try:
        items = await try_parse_url(url, source_id=-1, category="test", source_type=source_type)
        if items:
            return True, f"校验成功，共抓取到 {len(items)} 条内容", items[:3]
        return False, "未能从该 URL 提取到任何新闻条目，请检查链接或类型设置", []
    except Exception as exc:
        return False, f"抓取失败：{exc}", []
