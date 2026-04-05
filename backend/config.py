"""
config.py — 读取 .env，动态构建多模型注册表
新增模型只需在 .env 中按命名规则添加三行配置即可
"""
import os
import re
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    name: str       # 小写标识符，如 "gpt35"
    base_url: str
    api_key: str
    model_id: str   # 传给 API 的模型名，如 "gpt-3.5-turbo"


def _load_models() -> dict[str, ModelConfig]:
    """
    扫描所有 MODEL_*_BASE_URL 环境变量，构建模型注册表。
    每次调用前先用 override=True 重读 .env，支持运行时热更新。
    """
    load_dotenv(override=True)          # 热重读：覆盖已有环境变量
    models: dict[str, ModelConfig] = {}
    pattern = re.compile(r"^MODEL_([A-Z0-9]+)_BASE_URL$")
    for key, value in os.environ.items():
        m = pattern.match(key)
        if not m:
            continue
        tag = m.group(1)                             # e.g. "QWEN"
        name = tag.lower()                           # e.g. "qwen"
        api_key = os.environ.get(f"MODEL_{tag}_KEY", "")
        model_id = os.environ.get(f"MODEL_{tag}_ID", name)
        models[name] = ModelConfig(
            name=name,
            base_url=value,
            api_key=api_key,
            model_id=model_id,
        )
    return models


# 启动时初始化一次（供直接 import MODELS 的地方兜底）
MODELS: dict[str, ModelConfig] = _load_models()


def get_all_models() -> dict[str, ModelConfig]:
    """每次调用都热重读 .env，返回最新模型注册表（供 API 端点调用）"""
    return _load_models()


def get_model(name: str) -> ModelConfig:
    """按名称获取模型配置，每次热重读以支持不重启添加新模型"""
    models = _load_models()
    key = name.lower()
    if key not in models:
        available = list(models.keys())
        raise ValueError(
            f"模型 '{name}' 未配置。可用模型：{available}。"
            f"请在 backend/.env 中添加对应的 MODEL_{name.upper()}_* 配置。"
        )
    return models[key]
