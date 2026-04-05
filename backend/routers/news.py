"""
routers/news.py — 新闻相关路由
  GET  /api/news              分页查询新闻列表
  POST /api/news/refresh      触发后台异步刷新
  GET  /api/news/refresh/status 查询刷新状态
  GET  /api/news/export       导出 JSON / HTML
  GET  /api/news/categories   获取所有类别
"""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Query
from fastapi.responses import Response, HTMLResponse

from models import NewsItemResponse
from services.news_service import (
    get_news,
    get_all_enabled_sources,
    save_news_items,
    get_distinct_categories,
    get_category_counts,
)
from services.rss_service import fetch_rss
from services.crawler_service import try_parse_url, fetch_sjtu

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news", tags=["news"])

# ──────────────────────────────────────────
# 刷新状态（单进程内共享）
# ──────────────────────────────────────────

_refresh: dict = {
    "status": "idle",          # idle | refreshing | error
    "last_refresh": None,
    "added": 0,
    "error": None,
    "total": 0,
    "done": 0,
}


async def _do_refresh() -> None:
    """后台任务：遍历所有启用的订阅源并入库"""
    _refresh.update({"status": "refreshing", "error": None, "added": 0, "done": 0})
    total_added = 0
    try:
        sources = await get_all_enabled_sources()
        _refresh["total"] = len(sources)
        for source in sources:
            try:
                if source.type == "rss":
                    items = await fetch_rss(source.url, source.category, source.id)
                elif "sjtu.edu.cn" in source.url:
                    items = await fetch_sjtu(source.id)
                else:
                    items = await try_parse_url(
                        source.url, source.id, source.category, source.type
                    )
                added = await save_news_items(items)
                total_added += added
            except Exception as exc:
                logger.warning("Source [%s] failed: %s", source.url, exc)
            finally:
                _refresh["done"] += 1

        _refresh.update(
            {
                "status": "idle",
                "last_refresh": datetime.utcnow().isoformat() + "Z",
                "added": total_added,
            }
        )
        logger.info("Refresh complete. New items: %d", total_added)
    except Exception as exc:
        _refresh.update({"status": "error", "error": str(exc)})
        logger.error("Refresh failed: %s", exc)


# ──────────────────────────────────────────
# 路由
# ──────────────────────────────────────────

@router.get("/refresh/status")
async def get_refresh_status():
    return _refresh


@router.post("/refresh")
async def trigger_refresh(background_tasks: BackgroundTasks):
    if _refresh["status"] == "refreshing":
        return {"status": "already_refreshing", "message": "刷新已在进行中"}
    background_tasks.add_task(_do_refresh)
    return {"status": "refreshing", "message": "后台刷新任务已启动"}


@router.get("/categories")
async def list_categories():
    cats = await get_distinct_categories()
    return cats


@router.get("/category-counts")
async def category_counts_endpoint():
    """返回各类别新闻数量，格式 {category: count, all: total}"""
    return await get_category_counts()


@router.get("/export")
async def export_news(
    category: Optional[str] = Query(None),
    format: str = Query("json", pattern="^(json|html)$"),
):
    items = await get_news(category=category, limit=1000)

    if format == "json":
        data = [
            {
                "id": n.id,
                "title": n.title,
                "link": n.link,
                "category": n.category,
                "description": n.description,
                "published_at": n.published_at.isoformat() if n.published_at else None,
            }
            for n in items
        ]
        content = json.dumps(data, ensure_ascii=False, indent=2)
        return Response(
            content=content.encode("utf-8"),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=news_export.json"},
        )

    # HTML 格式
    rows = "".join(
        f"<tr>"
        f"<td><a href='{n.link}' target='_blank'>{n.title}</a></td>"
        f"<td>{n.category}</td>"
        f"<td>{n.published_at.strftime('%Y-%m-%d') if n.published_at else ''}</td>"
        f"</tr>"
        for n in items
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>新闻导出</title>
<style>
  body {{ font-family: sans-serif; padding: 20px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ddd; padding: 8px 12px; text-align: left; }}
  th {{ background: #f5f5f5; }}
  a {{ color: #1976D2; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>
</head>
<body>
<h1>新闻导出（共 {len(items)} 条）</h1>
<table>
  <thead><tr><th>标题</th><th>类别</th><th>发布时间</th></tr></thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": "attachment; filename=news_export.html"},
    )


@router.get("", response_model=list[NewsItemResponse])
async def list_news(
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return await get_news(category=category, skip=skip, limit=limit)
