# W4 AI 架构改造 — 分阶段安全上线计划

> 背景：2026-08-23 曾一次性全量上线导致生产 500（依赖断裂）。
> 教训：W4 的 4 个新模块不能一起上，必须按依赖顺序、每步验证、可回滚。

## 当前生产状态（2026-08-24）

- ✅ 生产用 `_call_deepseek` 直接调 DeepSeek（4 处），稳定工作
- ✅ 4 个 API 错误已修（Hermes 移交）
- ✅ 小程序准备提交审核
- 📦 W4 架构代码已归档在 `w4-architecture` 分支（未上生产）

## 依赖关系图

```
gateway.py（独立，只依赖 settings）
    ↑
    ├── registry.py（依赖 gateway）
    ├── prompts/（独立，只依赖 PyYAML）
    ├── profile_context.py（独立，依赖 Redis）
    └── vector_index.py（独立，依赖 numpy）
```

## 上线顺序（每个阶段独立可验证、可回滚）

### 阶段 1：gateway.py 上线（最低风险）

**做什么**：只上传 `ai/gateway.py` 到生产，**不改任何现有代码**。
`_call_deepseek` 继续工作，gateway.py 作为独立模块存在。

**验证**：`python3.11 -c "from ai.gateway import gateway; print('OK')"`

**回滚**：`rm /www/ranbing/ai/gateway.py`

**风险**：几乎为零（新文件，无引用）

---

### 阶段 2：gateway 接管 _call_deepseek（低风险）

**做什么**：让 `_call_deepseek` 内部委托给 `gateway.chat()`，获得限流+埋点。

```python
# 在 views.py 里改 _call_deepseek：
def _call_deepseek(messages, *, temperature=0.7, max_tokens=1000, timeout=30):
    from ai.gateway import gateway
    try:
        content = gateway.chat(messages, temperature=temperature,
                               max_tokens=max_tokens, prompt_id='ai_chat')
        return True, content
    except Exception as e:
        return False, f'DeepSeek 调用异常: {str(e)[:200]}'
```

**验证**：3 个 AI 接口仍 200

**回滚**：git checkout 恢复 `_call_deepseek` 旧版

**收益**：用户级限流（20次/分钟）、成本埋点（Redis `ai:cost:日期`）

---

### 阶段 3：Prompt YAML 化（中风险）

**做什么**：上传 `ai/prompts/` 目录 + 改 `intent.py` 读 YAML。

**前置**：`pip install pyyaml`（已装）

**验证**：意图识别/标签提取/匹配理由接口仍正常

**回滚**：恢复 `intent.py` 的字符串 prompt 版本

**收益**：非工程师可改 prompt，改 prompt 不用发版

---

### 阶段 4：Tool 注册中心（中风险）

**做什么**：上传 `ai/registry.py` + 各 app `ai_tools.py` + 改 `apps.py` 的 `ready()`。

**前置**：确认 `INSTALLED_APPS` 里 `ai` 在业务 app 之后

**验证**：`journalctl -u ranbing | grep ai-registry` 看到 4 个工具注册

**回滚**：恢复 `ai/tools.py`（backup 里有）

**收益**：加新工具零改 AI 层

---

### 阶段 5：向量索引 + Profile 缓存（高收益但需谨慎）

**做什么**：上传 `vector_index.py` + `profile_context.py` + 改 `supplies/views.py`（feed 用向量检索）。

**前置**：`pip install numpy`（已装）

**验证**：feed 接口 < 100ms（之前 500ms）

**回滚**：恢复 `supplies/views.py` 的 `_batch_cosine_similarity` 版本

**收益**：feed 70x 加速 + Profile 缓存消除 N+1

---

## 推荐节奏

- **今天**：只做阶段 1（上传 gateway.py 一个文件，零风险）
- **提交审核后 1-2 天**：阶段 2（gateway 接管，获得限流埋点）
- **下周**：阶段 3-4（prompt YAML + tool 注册）
- **下下周**：阶段 5（向量索引 + 缓存）

## 关键原则

1. **每次只动一个阶段**，验证通过再下一个
2. **每个阶段都有明确的回滚命令**
3. **生产分支 `agent/backend` 永远保持"已验证可跑"状态**
4. **W4 完整代码在 `w4-architecture` 分支，可随时查阅对照**
