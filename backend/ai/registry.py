"""
工具注册中心 - 自动从每个 app 收集 AI 工具

设计原则：
1. 每个业务 app 自己声明 ai_tools.py（含 SCHEMA + handler）
2. AI 子系统启动时自动 import + 注册
3. 加新工具 = 在某个 app 加一个 ai_tools.py，零改动 AI 层

每个 ai_tools.py 必须暴露：
  SCHEMA: dict - OpenAI 兼容的工具定义
  handler: callable - 工具执行函数

可选暴露：
  PERMISSIONS: list[str] - 需要的权限，默认 IsAuthenticated
  DESCRIPTION_EXTRA: str - 给 LLM 的额外说明
"""
import importlib
import logging
import threading
from typing import Dict, Callable, List

logger = logging.getLogger(__name__)

# 注册表（运行时填充）
TOOL_SCHEMAS: List[dict] = []
TOOL_HANDLERS: Dict[str, Callable] = {}
TOOL_PERMISSIONS: Dict[str, List[str]] = {}

_lock = threading.Lock()
_discovered = False

# 配置：哪些 app 可能声明 AI 工具
APPS_WITH_AI_TOOLS = [
    'supplies',
    'profiles',
    'activities',
    'communities',
]


def register_tool(name: str, schema: dict, handler: Callable, permissions: List[str] = None):
    """
    手动注册一个工具（一般用 discover_tools 自动发现即可）

    用法：
        from ai.registry import register_tool
        register_tool('search_supplies', SCHEMA, handler)
    """
    with _lock:
        if name in TOOL_HANDLERS:
            logger.warning(f"[ai-registry] 工具 {name} 重复注册，已覆盖")
        TOOL_HANDLERS[name] = handler
        # SCHEMA 列表去重
        TOOL_SCHEMAS[:] = [s for s in TOOL_SCHEMAS if s.get('function', {}).get('name') != name]
        TOOL_SCHEMAS.append(schema)
        TOOL_PERMISSIONS[name] = permissions or []


def discover_tools():
    """
    自动发现并注册所有 app 的 AI 工具

    每个 app 提供 ai_tools.py，导出 SCHEMA + handler
    """
    global _discovered
    if _discovered:
        return

    with _lock:
        if _discovered:
            return

        for app_name in APPS_WITH_AI_TOOLS:
            try:
                module = importlib.import_module(f'{app_name}.ai_tools')
                if hasattr(module, 'SCHEMA') and hasattr(module, 'handler'):
                    name = module.SCHEMA.get('function', {}).get('name')
                    if not name:
                        logger.warning(f"[ai-registry] {app_name}.ai_tools SCHEMA 缺少 function.name")
                        continue
                    register_tool(
                        name,
                        module.SCHEMA,
                        module.handler,
                        getattr(module, 'PERMISSIONS', None),
                    )
                    logger.info(f"[ai-registry] registered tool: {name} (from {app_name})")
                else:
                    logger.debug(f"[ai-registry] {app_name}.ai_tools 缺 SCHEMA/handler，跳过")
            except ImportError:
                logger.debug(f"[ai-registry] {app_name} 无 ai_tools 模块")
            except Exception as e:
                logger.exception(f"[ai-registry] 发现 {app_name} 工具失败: {e}")

        _discovered = True
        logger.info(f"[ai-registry] 共注册 {len(TOOL_SCHEMAS)} 个 AI 工具")


def execute_tool(tool_call: dict) -> dict:
    """
    根据 tool_call 执行对应的本地工具
    tool_call 格式: {"name": "search_supplies", "arguments": {"keyword": "投资", "limit": 5}}
    返回 {"result": <执行结果>} 或 {"result": {"error": "..."}}
    """
    import json

    name = tool_call.get("name", "")
    raw_args = tool_call.get("arguments", {})

    # arguments 可能是字符串 JSON
    if isinstance(raw_args, str):
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            return {"result": {"error": f"无法解析参数: {raw_args}"}}
    else:
        args = raw_args

    handler = TOOL_HANDLERS.get(name)
    if not handler:
        return {"result": {"error": f"未知工具: {name}"}}

    try:
        result = handler(**args)
        return {"result": result}
    except Exception as e:
        logger.exception(f"[ai-registry] execute_tool {name} error: {e}")
        return {"result": {"error": str(e)}}


def ready():
    """Django AppConfig.ready() 调用入口"""
    discover_tools()


def clear():
    """测试用：清空注册表"""
    global _discovered
    with _lock:
        TOOL_SCHEMAS.clear()
        TOOL_HANDLERS.clear()
        TOOL_PERMISSIONS.clear()
        _discovered = False