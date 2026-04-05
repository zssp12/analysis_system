"""
models.py — Pydantic 请求/响应模型（Pydantic v2 语法）
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


# ──────────────────────────────────────────
# 新闻
# ──────────────────────────────────────────

class NewsItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    link: str
    source_id: Optional[int] = None
    category: str
    description: Optional[str] = None
    content: Optional[str] = None
    thumbnail: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime


# ──────────────────────────────────────────
# 订阅源
# ──────────────────────────────────────────

class SourceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    url: str
    type: str
    category: str
    enabled: bool
    created_at: datetime


class SourceCreateRequest(BaseModel):
    name: str
    url: str
    type: str = "rss"       # rss | crawler
    category: str


# ──────────────────────────────────────────
# LLM
# ──────────────────────────────────────────

class LLMAnalyzeRequest(BaseModel):
    news_id: int
    model_name: str


class LLMCategoryRequest(BaseModel):
    category: str
    model_name: str


class LLMTweetRequest(BaseModel):
    news_id: Optional[int] = None
    content: Optional[str] = None
    model_name: str


class LLMResponse(BaseModel):
    result: str
    model_name: str
