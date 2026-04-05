"""
routers/sources.py — 订阅源管理路由
  GET    /api/sources          获取全部订阅源
  POST   /api/sources          新增订阅源（含有效性校验）
  DELETE /api/sources/{id}     删除订阅源
  PATCH  /api/sources/{id}/toggle  启用/禁用
"""
from __future__ import annotations
import logging

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from database import AsyncSessionLocal, Source
from models import SourceItemResponse, SourceCreateRequest
from services.crawler_service import validate_url

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sources", tags=["sources"])


@router.get("", response_model=list[SourceItemResponse])
async def list_sources():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Source).order_by(Source.created_at.desc())
        )
        return result.scalars().all()


@router.post("", response_model=SourceItemResponse)
async def create_source(req: SourceCreateRequest):
    # 1. 校验 URL 有效性
    valid, msg, _ = await validate_url(req.url, req.type)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    async with AsyncSessionLocal() as session:
        # 2. 检查是否已存在
        dup = await session.execute(select(Source).where(Source.url == req.url))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="该订阅源已存在，请勿重复添加")

        # 3. 入库
        source = Source(
            name=req.name,
            url=req.url,
            type=req.type,
            category=req.category,
        )
        session.add(source)
        await session.commit()
        await session.refresh(source)
        return source


@router.delete("/{source_id}")
async def delete_source(source_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="订阅源不存在")
        await session.delete(source)
        await session.commit()
    return {"message": "删除成功", "id": source_id}


@router.patch("/{source_id}/toggle")
async def toggle_source(source_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Source).where(Source.id == source_id))
        source = result.scalar_one_or_none()
        if not source:
            raise HTTPException(status_code=404, detail="订阅源不存在")
        source.enabled = not source.enabled
        await session.commit()
        return {"id": source_id, "enabled": source.enabled}
