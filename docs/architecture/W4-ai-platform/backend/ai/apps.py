"""
AI 子系统 AppConfig

启动时自动发现并注册所有业务 app 暴露的 AI 工具
"""
from django.apps import AppConfig


class AiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai'
    verbose_name = 'AI子系统'

    def ready(self):
        # 自动发现 + 注册所有 app 的 ai_tools
        from .registry import ready as registry_ready
        registry_ready()
        # registry_ready() 内部有日志，确认看到 [ai-registry] 日志说明启动成功