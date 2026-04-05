"""
routers/llm.py — 大模型分析路由
  GET  /api/llm/models            已配置模型列表
  POST /api/llm/analyze           单条新闻分析
  POST /api/llm/analyze-category  类别综合摘要
  POST /api/llm/generate-tweet    生成推文
"""
from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException

from config import get_all_models
from models import (
    LLMAnalyzeRequest,
    LLMCategoryRequest,
    LLMTweetRequest,
    LLMResponse,
)
from services.llm_service import (
    call_llm,
    build_analyze_prompt,
    build_category_prompt,
    build_tweet_prompt,
)
from services.news_service import get_news_by_id, get_news

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/models")
async def list_models():
    """返回已配置的模型列表（每次热重读 .env，无需重启后端）"""
    models = get_all_models()
    return [
        {"name": k, "model_id": v.model_id, "base_url": v.base_url}
        for k, v in models.items()
    ]


@router.post("/analyze", response_model=LLMResponse)
async def analyze_single(req: LLMAnalyzeRequest):
    """分析单条新闻，生成详细解读"""
    news = await get_news_by_id(req.news_id)
    if not news:
        raise HTTPException(status_code=404, detail="新闻条目不存在")

    body = news.content or news.description or news.title
    prompt = build_analyze_prompt(news.title, body)
    try:
        result = await call_llm(req.model_name, prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("LLM analyze error: %s", exc)
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}")

    return LLMResponse(result=result, model_name=req.model_name)


@router.post("/analyze-category", response_model=LLMResponse)
async def analyze_category(req: LLMCategoryRequest):
    """对某类别最新 20 条新闻生成综合摘要；category='all' 时分析全部类别"""
    # 'all' / '全部' → 不过滤类别，直接取最新 20 条
    is_all = req.category in ("all", "全部", "全部新闻")
    query_cat = None if is_all else req.category
    display_cat = "全部新闻" if is_all else req.category

    items = await get_news(category=query_cat, limit=50)
    if not items:
        raise HTTPException(status_code=404, detail="暂无新闻数据，请先点击「刷新新闻」")

    titles = [n.title for n in items]
    prompt = build_category_prompt(display_cat, titles)
    try:
        result = await call_llm(req.model_name, prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("LLM category error: %s", exc)
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}")

    return LLMResponse(result=result, model_name=req.model_name)


@router.post("/generate-tweet", response_model=LLMResponse)
async def generate_tweet(req: LLMTweetRequest):
    """根据新闻内容生成社交媒体推文"""
    if req.news_id is not None:
        news = await get_news_by_id(req.news_id)
        if not news:
            raise HTTPException(status_code=404, detail="新闻条目不存在")
        content = f"{news.title}\n\n{news.content or news.description or ''}"
    elif req.content:
        content = req.content
    else:
        raise HTTPException(status_code=400, detail="需要提供 news_id 或 content 字段")

    prompt = build_tweet_prompt(content)
    try:
        result = await call_llm(req.model_name, prompt)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("LLM tweet error: %s", exc)
        raise HTTPException(status_code=502, detail=f"大模型调用失败：{exc}")

    return LLMResponse(result=result, model_name=req.model_name)
