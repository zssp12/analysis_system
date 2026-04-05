"""
llm_service.py — 统一大模型调用封装
  · call_llm(model_name, prompt)  → str
  · 使用 openai SDK（兼容所有 OpenAI 格式接口：智谱、Qwen、Ollama 等）
  · tenacity 仅对网络/连接错误重试，超时和配置错误不重试
  · 单次超时 120s，适配 Qwen 等推理模型
"""
from __future__ import annotations
import logging

from openai import (
    AsyncOpenAI,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    APIError,
)
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from config import get_model

logger = logging.getLogger(__name__)

# 单次请求超时（秒）：推理模型（Qwen/o1 等）耗时较长，设为 120s
LLM_TIMEOUT = 120.0


def _should_retry(exc: BaseException) -> bool:
    """
    重试判断：
    - 连接失败（网络波动）→ 重试
    - 服务端 5xx 错误     → 重试
    - 超时（模型慢）       → 不重试，直接报错（避免超时叠加）
    - 配置错误 / 4xx      → 不重试
    """
    if isinstance(exc, APIConnectionError):
        return True
    if isinstance(exc, APIStatusError) and exc.status_code >= 500:
        return True
    return False


# ──────────────────────────────────────────
# 核心调用函数
# ──────────────────────────────────────────

@retry(
    stop=stop_after_attempt(2),                          # 最多重试 1 次（共 2 次调用）
    wait=wait_exponential(multiplier=1, min=2, max=8),   # 重试间隔 2-8s
    retry=retry_if_exception(_should_retry),             # 仅网络/5xx 才重试
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
async def call_llm(model_name: str, prompt: str) -> str:
    """
    调用指定模型生成回复
    model_name: 对应 .env 中 MODEL_<NAME> 的小写标识，如 'qwen' / 'zhipu' / 'gpt35'
    """
    cfg = get_model(model_name)          # 配置不存在立即抛 ValueError，不重试

    client = AsyncOpenAI(
        base_url=cfg.base_url,
        api_key=cfg.api_key,
        timeout=LLM_TIMEOUT,
    )

    try:
        response = await client.chat.completions.create(
            model=cfg.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.7,
        )
    except APITimeoutError:
        raise APITimeoutError(
            request=None,
            message=f"大模型请求超时（>{LLM_TIMEOUT}s），请稍后重试或换用其他模型"
        )
    except APIStatusError as exc:
        status = exc.status_code
        body = exc.body or {}
        detail = body.get("message") or body.get("error", {}).get("message") or str(exc)
        raise APIStatusError(
            message=f"API 返回错误 HTTP {status}：{detail}",
            response=exc.response,
            body=body,
        )

    content = response.choices[0].message.content
    if not content:
        logger.warning("LLM [%s] returned empty content", cfg.model_id)
        return "（模型返回了空内容，请重试或调整 Prompt）"

    logger.info("LLM [%s] usage=%s", cfg.model_id, response.usage)
    return content


# ──────────────────────────────────────────
# Prompt 模板
# ──────────────────────────────────────────

def build_analyze_prompt(title: str, content: str) -> str:
    """单条新闻详细解读"""
    return (
        "请用中文详细解读以下新闻，从背景、核心事件、意义与影响、个人观点四个维度进行分析，"
        "输出格式使用 Markdown（含标题层级和要点列表）：\n\n"
        f"**标题**：{title}\n\n"
        f"**内容**：{content}"
    )


def build_category_prompt(category: str, titles: list[str]) -> str:
    """类别新闻综合摘要 — 要求深度分析，篇幅充足"""
    numbered = "\n".join(f"{i + 1}. {t}" for i, t in enumerate(titles))
    return (
        f"以下是【{category}】领域最新的 {len(titles)} 条新闻标题，"
        "请用中文撰写一篇 600-900 字的深度综合报告，要求：\n"
        "1. **热点概览**：提炼本批新闻的 3-5 个核心主题\n"
        "2. **趋势分析**：从宏观视角分析当前领域的发展走向与潜在影响\n"
        "3. **重点事件**：逐条点评其中最值得关注的 3 条新闻\n"
        "4. **前景展望**：结合上述分析，给出对未来短期走势的判断\n"
        "输出使用完整的 Markdown 格式（含 ## 二级标题、要点列表、加粗关键词）：\n\n"
        f"{numbered}"
    )


def build_tweet_prompt(content: str) -> str:
    """生成社交媒体推文"""
    return (
        "请根据以下新闻内容，生成一条适合中文社交平台（微博/微信朋友圈）发布的推文。"
        "要求：200 字以内，语言生动，包含 2-3 个相关话题标签（#话题#），"
        "使用 Markdown 格式（加粗重点词汇）：\n\n"
        f"{content}"
    )
