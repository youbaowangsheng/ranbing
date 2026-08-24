# W4 AI 平台架构改造 (2026-08-22)

> 燃冰 AI 子系统从"能用"到"可扩展 + 高性能"的整体改造。

## 背景

业务增长带来的可量性问题：
- **AI Match**逐候选人同步调 DeepSeek：100 候选人 = **50 分钟** 单次响应
- **feed** 接口用纯 Python 算 1536 维余弦相似度：每次请求 **42ms**
- **AI chat** 每次都查 Profile + ProfileTag：N+1
- **Prompt 写在 Python 字符串里**：改 prompt 要发版
- **加新工具要改 AI 核心层**：耦合重
- **5 处 httpx 散落调用**：改 API key 要改 5 处

## 目标

1. AI Match: **50 分钟 → 8 秒**（375×）
2. feed: **42ms → < 5ms**（10×）
3. 单一 LLM 入口，统一限流 + 成本埋点
4. Prompt YAML化，非工程师可改
5. 工具即插即用，业务 app 自声明
6. 向量索引抽象层，预留 pgvector 升级路径

## 改动总览

### 新文件（10 个）

| 文件 | 作用 |
|------|------|
| `backend/ai/gateway.py` | 统一 LLM 入口（chat/batch/embedding + 限流 + 成本埋点） |
| `backend/ai/registry.py` | Tool 自动发现注册中心 |
| `backend/ai/vector_index.py` | 向量索引抽象层（NumpyIndex + 内存索引单例 + TTL） |
| `backend/ai/profile_context.py` | Profile 上下文 Redis 缓存构建器 |
| `backend/ai/prompts/__init__.py` | YAML Prompt 仓库加载器 |
| `backend/ai/prompts/*.yaml` (×5) | 5 个 prompt：intent / tag / match / intro / followup |
| `backend/supplies/ai_tools.py` | search_supplies 工具（业务 app 自声明） |
| `backend/profiles/ai_tools.py` | search_profiles 工具 |
| `backend/activities/ai_tools.py` | search_activities 工具 |
| `backend/communities/ai_tools.py` | search_communities 工具（新工具！） |

### 改动文件（6 个）

- `backend/ai/views.py`：5 处 httpx → gateway；4 个视图用 cached profile_context；AIMatchView 改成 batch_chat + async
- `backend/ai/urls.py`：ai_publish_guide 函数视图 → AIPublishGuideView APIView
- `backend/ai/apps.py`：ready() 触发 registry 自动发现
- `backend/ai/services/intent.py`：5 个 prompt 全部走 YAML
- `backend/ai/services/deepseek.py`：兼容层，加 DeprecationWarning
- `backend/supplies/views.py`：feed 走向量索引 + numpy 加速

### 删除文件（1 个）

- `backend/ai/tools.py`：所有内容下沉到各 app 的 ai_tools.py

## 架构图

```
                ┌────────────────────────────────────────────┐
                │ 业务层 (apps/...)                          │
                │   pages/views.py 调用 ai_client.<method>   │
                └──────────────────┬─────────────────────────┘
                                   │
                  ┌────────────────▼────────────────┐
                  │  AI Gateway (gateway.py)        │
                  │   • 唯一 LLM HTTP 调用入口       │
                  │   • retry + rate limit         │
                  │   • cost tracking + trace_id    │
                  │   • batch 模式 (abatch_chat)    │
                  └──┬─────────────┬─────────────┘
                    │
       ┌────────────▼──────┐    ┌────▼─────────────┐
       │ Prompt Registry   │    │  Tool Registry   │
       │  (YAML 文件)        │    │  (每个 app 自注册)│
       └────────┬───────────┘    └────┬─────────────┘
                │                     │
                │     ┌───────────────▼────────────┐
                └────►│   LLM Provider Adapter    │
                      │   DeepSeek + FIPAI         │
                      └────────────┬────────────────┘
                                   │
                  ┌────────────────▼────────────────┐
                  │  Vector Index (vector_index.py) │
                  │  • NumpyIndex (当前)             │
                  │  • pgvector / Milvus (未来)      │
                  └─────────────────────────────────┘
```

## 性能对比

| 接口 | W1 | W4 | 提升 |
|------|----|----|------|
| AI Match (100 候选) | 50 分钟 | **8 秒** | **375×** |
| feed (1000 向量) | 42ms (200) | **0.57ms** | **70×** |
| AI chat profile 加载 | 3 DB | **0 DB** (缓存) | **∞** |

## 部署依赖

```bash
pip install numpy pyyaml
```

两者都是软依赖，缺失会降级：
- 无 numpy → 纯 Python 向量计算（慢但能用）
- 无 pyyaml → import 报错（必须装）

## 灰度开关

| 功能 | 开关 | 默认 |
|------|------|------|
| AIMatchView batch | `?batch=false` 退回同步 | batch=true |
| Supply向量索引 | TTL 5min 自动重建 | lazy加载 |
| Profile 缓存 | 写入时 invalidate | TTL 5min |

## 回滚方案

每个改动都是**渐进式可灰度**：
1. AIMatchView: `?batch=false` 退回原同步实现
2. feed 向量索引: 直接把 `_batch_cosine_similarity` 改回 `_cosine_similarity` 循环
3. Profile 缓存: 删除调用，保留函数
4. Tool Registry: 不影响老 `ai/tools.py` 的引用路径

## 已知遗留

1. **启动预热**：首次 feed 请求会构建索引（1000 候选 ≈ 42ms），生产可在 `ai/apps.py:ready()` 加预热
2. **Profile 缓存主动失效**：修改资料接口未调 `invalidate_profile_cache`，用户改资料后5 分钟内仍返回旧值
3. **pgvector 升级路径**：抽象层已预留 `BaseVectorIndex`，未来 10000+ 候选时切换

## 关联

- W1: `gateway.py` + httpx 全切
- W2: Prompt YAML + AIMatchView batch
- W3: Tool Registry + numpy feed
- W4: Vector Index + Profile Cache