# W4 AI 平台改造 - 文件清单

> 按文件路径列出所有本次改动的文件，方便对照源代码。
> 归档时间：2026-08-23

## 新建文件

### AI 核心（4 个）
- `backend/ai/gateway.py` - LLM 统一入口（11.6 KB）
- `backend/ai/registry.py` - Tool 自动注册中心（4.5 KB）
- `backend/ai/vector_index.py` - 向量索引抽象层（7.5 KB）
- `backend/ai/profile_context.py` - Profile 上下文 Redis 缓存（4.2 KB）

### Prompt 仓库（6 个）
- `backend/ai/prompts/__init__.py` - YAML 加载器
- `backend/ai/prompts/intent_recognition.yaml` - 意图识别
- `backend/ai/prompts/tag_extract.yaml` - 标签提取
- `backend/ai/prompts/match_reason.yaml` - 匹配理由（批量用）
- `backend/ai/prompts/intro_script.yaml` - 初次话术
- `backend/ai/prompts/followup_script.yaml` - 跟进话术

### 业务 app 自声明工具（4 个）
- `backend/supplies/ai_tools.py` - search_supplies
- `backend/profiles/ai_tools.py` - search_profiles
- `backend/activities/ai_tools.py` - search_activities
- `backend/communities/ai_tools.py` - search_communities（新工具！）

## 改动文件

- `backend/ai/views.py` - 5 处 httpx → gateway；4 个视图用 cached profile_context；AIMatchView 改成 batch + async
- `backend/ai/urls.py` - ai_publish_guide 函数视图 → DRF APIView
- `backend/ai/apps.py` - ready() 触发 registry + **新增向量索引异步预热**
- `backend/ai/services/intent.py` - 5 个 prompt 全部走 YAML
- `backend/ai/services/deepseek.py` - 改为兼容层（gateway 转发）
- `backend/supplies/views.py` - feed 走向量索引 + numpy 加速
- `backend/profiles/views.py` - **profile 修改后调 `invalidate_profile_cache`**（me / cert / update_tags）

## 删除文件

- `backend/ai/tools.py` - 内容下沉到各 app 的 ai_tools.py

## 部署脚本

- `backend/deploy-w4-ai-platform.sh` - 一键部署脚本（备份→上传→装依赖→重启→验证）

## 一致性验证

```
✓ backend/ai/views.py 不再 import ai.tools
✓ backend/ai/registry.py 暴露 TOOL_SCHEMAS/execute_tool
✓ backend/ai/views.py 改 import registry
✓ backend/supplies/views.py 暴露 _batch_cosine_similarity
✓ backend/ai/apps.py:ready() → registry.ready()
```

## 部署 checklist

1. pip install numpy pyyaml
2. git pull / scp 上传所有新建+改动文件
3. 删除 backend/ai/tools.py（如果服务器上还有）
4. systemctl restart ranbing
5. 检查日志：[ai-registry] 共注册 4 个 AI 工具
6. 检查日志：[vector-index:supply] loaded N vectors
7. curl /api/v1/ai/chat/ 验证 200
8. curl /api/v1/supplies/feed/ 验证 < 100ms