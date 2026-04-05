"""
main.py — FastAPI 应用入口
启动命令：
  cd backend
  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from routers import news, sources, llm

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database …")
    await init_db()
    logger.info("Database ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="新闻聚合与推送系统",
    description="基于大模型的新闻聚合、分析与推文生成平台",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS（允许本地前端开发服务器）──────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由挂载 ───────────────────────────────────
app.include_router(news.router)
app.include_router(sources.router)
app.include_router(llm.router)


@app.get("/", tags=["health"])
async def root():
    return {
        "message": "新闻聚合与推送系统 API 运行中",
        "docs": "/docs",
        "redoc": "/redoc",
    }
