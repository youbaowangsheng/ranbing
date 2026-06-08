# Ranbing 燃冰

燃冰业务运营平台，包含运营后台 API 和原业务后端。

## 项目结构

```
ranbing/
├── apps/                    # 运营后台 API (Console API, port 8002)
│   ├── accounts/            # 账户管理（UserProfile、quota）
│   ├── agents/              # Agent 业务配置
│   ├── community/           # 社群内容管理
│   ├── core/                # 核心数据模型（MatchingRecord、PublishTask、UsageRecord）
│   ├── matching/            # 匹配队列
│   ├── publish/             # 发布队列
│   ├── stats/               # 运营统计
│   └── users/               # 用户管理
│
├── backend/                 # 原业务后端 (port 8003)
│   ├── activities/          # 活动管理
│   ├── ai/                 # AI 意图识别 / DeepSeek 集成
│   ├── communities/        # 社群 / 帖子管理
│   ├── profiles/           # 用户资料
│   ├── supplies/           # 供需管理
│   └── users/              # 用户认证 / 短信
│
└── config/                 # Django settings
```

## 启动

```bash
# Console API (port 8002)
cd /Users/wangsheng/ranbing
./venv/bin/python manage.py runserver 0.0.0.0:8002

# 业务后端 (port 8003)
cd /Users/wangsheng/ranbing/backend
./venv/bin/python manage.py runserver 0.0.0.0:8003
```

## API 概览

### Console API (8002)

| 端点 | 说明 |
|------|------|
| `GET /api/users/` | 用户列表 |
| `GET/PUT /api/accounts/profile/` | 账户信息 |
| `GET /api/accounts/quota/` | 配额信息 |
| `GET /api/matching/records/` | 匹配队列 |
| `PATCH /api/matching/records/{id}/` | 更新匹配状态 |
| `GET /api/publish/tasks/` | 发布队列 |
| `POST /api/publish/tasks/{id}/retry/` | 重试发布 |
| `GET /api/stats/usage/` | 用量报表 |
| `GET /api/stats/daily/` | 每日趋势 |
| `GET /api/stats/agents_rank/` | Agent 排行 |
| `POST /api/admin/activities/pending/` | 待审核活动 |
| `POST /api/admin/activities/{uuid}/approve/` | 审核通过 |
| `POST /api/admin/communities/pending/` | 待审核社群 |
| `POST /api/admin/supplies/pending/` | 待审核供需 |
| `POST /api/admin/messages/pending/` | 待审核帖子 |

### 业务后端 API (8003)

| 端点 | 说明 |
|------|------|
| `GET /api/v1/activities/` | 活动列表 |
| `GET /api/v1/communities/` | 社群列表 |
| `GET /api/v1/supplies/` | 供需列表 |
| `POST /api/v1/ai/intent/` | 意图识别 |

## 环境变量

```bash
# Aliyun SMS
export ALIYUN_ACCESS_KEY_ID=xxx
export ALIYUN_ACCESS_KEY_SECRET=xxx
export ALIYUN_SMS_SIGN_NAME=湖南器宇
export ALIYUN_SMS_TEMPLATE_CODE=SMS_xxx
export SMS_DEMO_MODE=false

# FIPAI 中台（AI 匹配）
export FIPAI_GATEWAY_URL=http://localhost:8000
```

## 技术栈

- **Console API**: Django + DRF (port 8002)
- **业务后端**: Django + DRF (port 8003)
- **前端**: React (ranbing-console, port 5180)
- **向量检索**: FIPAI Gateway (ChromaDB)