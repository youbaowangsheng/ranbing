"""
Prompt 仓库 - 所有 prompt 从 YAML 加载

设计原则：
1. prompt 与代码分离：非工程师可改，无需懂 Python
2. 模板用 str.format 而非 jinja2（避免模板注入且无依赖）
3. lru_cache 避免每次调用都读盘
4. 必填变量校验：少传变量直接报错

目录结构：
  ai/prompts/
    __init__.py            ← 本文件（loader）
    intent.yaml            ← 意图识别
    tag_extract.yaml       ← 标签提取
    match_reason.yaml      ← 匹配理由
    intro_script.yaml      ← 初次话术
    followup_script.yaml   ← 跟进话术
"""
import logging
import threading
from functools import lru_cache
from pathlib import Path

import yaml
from django.conf import settings

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent
_lock = threading.Lock()


class PromptNotFound(Exception):
    """找不到 prompt 文件"""
    pass


class PromptRenderError(Exception):
    """prompt 渲染失败（通常是变量缺失）"""
    pass


def _load_yaml(name: str) -> dict:
    """读 YAML 文件，线程安全"""
    path = PROMPTS_DIR / f"{name}.yaml"
    if not path.exists():
        raise PromptNotFound(f"prompt {name!r} 不存在: {path}")
    with _lock:
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise PromptRenderError(f"prompt {name} YAML 顶层必须是 dict")
    return data


@lru_cache(maxsize=32)
def load_prompt(name: str) -> dict:
    """
    加载 prompt 定义（带 lru_cache）

    返回 dict: {
        'id': 'intent_recognition',
        'version': 1,
        'description': '...',
        'variables': ['text'],
        'template': '...',
        'system': '...',   # 可选：system prompt
        'examples': [...], # 可选：few-shot
    }
    """
    return _load_yaml(name)


def render(name: str, /, **vars) -> str:
    """
    加载并渲染 prompt

    用法：
        from ai.prompts import render
        text = render('intent_recognition', text='找投资人')

    必传变量从 YAML 的 `variables` 字段校验；缺失会抛 PromptRenderError。
    """
    p = load_prompt(name)

    # 校验必填变量
    required = p.get('variables', [])
    missing = [v for v in required if v not in vars]
    if missing:
        raise PromptRenderError(
            f"prompt {name!r} 缺少变量: {missing}, 需要: {required}"
        )

    template = p['template']
    try:
        return template.format(**vars)
    except KeyError as e:
        raise PromptRenderError(f"prompt {name!r} 渲染失败，缺少变量 {e}") from e


def get_system(name: str) -> str:
    """获取 prompt 的 system 部分，没有则返回空"""
    p = load_prompt(name)
    return p.get('system', '')


def clear_cache():
    """清缓存（开发时改 YAML 热加载用，生产不用调）"""
    load_prompt.cache_clear()
    logger.info("[prompts] cache cleared")