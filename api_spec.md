# 燃冰 · API接口文档 v1.0

> 版本：v1.0 · 2026-05-04
> Base URL: `/api/v1`
> 认证方式：JWT（`Authorization: Bearer <token>`）

---

## 一、通用规范

### 1.1 请求格式

```
Content-Type: application/json
Authorization: Bearer <jwt_token>
```

### 1.2 响应格式

**成功：**
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

**错误：**
```json
{
  "code": 1001,
  "message": "登录已过期，请重新登录",
  "data": null
}
```

### 1.3 错误码定义

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1001 | 认证失败（token无效/过期） |
| 1002 | 无权限访问 |
| 2001 | 资源不存在 |
| 2002 | 参数校验失败 |
| 2003 | 重复操作（如已报名） |
| 3001 | 系统繁忙 |
| 3002 | AI服务不可用 |

### 1.4 分页规范

```
GET /api/v1/supplies?page=1&page_size=20&sort=created_at:desc
```

**响应包含：**
```json
{
  "data": { ... },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 152,
    "total_pages": 8
  }
}
```

---

## 二、认证相关 API

### 2.1 POST /auth/login

手机号 + 验证码登录

**请求：**
```json
{
  "phone": "13812345678",
  "code": "847293"
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2026-05-11T10:00:00Z",
    "user": {
      "id": 10001,
      "uuid": "550e8400-e29b-41d4-a716-446655440000",
      "phone": "138****5678",
      "nickname": "张三",
      "avatar_url": "https://cdn.example.com/avatar/xxx.jpg",
      "is_verified": true
    }
  }
}
```

---

### 2.2 POST /auth/register

注册账号

**请求：**
```json
{
  "phone": "13812345678",
  "code": "847293",
  "nickname": "张三",
  "wx_openid": "oXXXXX"
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "token": "...",
    "user": { ... }
  }
}
```

---

### 2.3 POST /auth/send-code

发送验证码

**请求：**
```json
{
  "phone": "13812345678",
  "type": "login"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "验证码已发送"
}
```

---

### 2.4 GET /auth/profile

获取当前用户信息

**响应：**
```json
{
  "code": 0,
  "data": {
    "id": 10001,
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "138****5678",
    "wx_openid": "oXXXXX",
    "nickname": "张三",
    "avatar_url": "https://cdn.example.com/avatar/xxx.jpg",
    "is_verified": true,
    "last_login_at": "2026-05-04T08:30:00Z"
  }
}
```

---

## 三、Profile 相关 API

### 3.1 GET /profiles/:uuid

查看他人Profile

**路径参数：** `uuid` — 用户UUID

**响应：**
```json
{
  "code": 0,
  "data": {
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "real_name": "李四",
    "gender": 1,
    "company": "鼎晖投资",
    "position": "合伙人",
    "industry": "投资",
    "city": "北京",
    "bio": "专注早期消费和科技投资",
    "education_year": "2010",
    "education_major": "MBA",
    "education_school": "中欧国际工商学院",
    "cert_level": 3,
    "conn_count": 128,
    "tags": [
      { "id": 5, "name": "天使投资", "tag_type": 1, "weight": 1.0 },
      { "id": 12, "name": "消费行业", "tag_type": 1, "weight": 0.8 },
      { "id": 23, "name": "找早期项目", "tag_type": 2, "weight": 1.0 }
    ],
    "active_score": 92.5,
    "last_active_at": "2026-05-04T09:00:00Z"
  }
}
```

---

### 3.2 PUT /profiles/me

编辑我的Profile

**请求：**
```json
{
  "nickname": "张三",
  "avatar_url": "https://cdn.example.com/avatar/new.jpg",
  "real_name": "张伟",
  "gender": 1,
  "company": "华润集团",
  "position": "战略总监",
  "industry": "企业服务",
  "city": "深圳",
  "bio": "专注企业数字化转型"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "更新成功"
}
```

---

### 3.3 POST /profiles/me/cert

提交认证

**请求：**
```json
{
  "cert_level": 2,
  "education_year": "2015",
  "education_school": "长江商学院",
  "education_major": "EMBA",
  "cert_document_url": "https://cdn.example.com/cert/xxx.jpg"
}
```

**响应：**
```json
{
  "code": 0,
  "message": "认证申请已提交，审核结果将在24小时内通知"
}
```

---

### 3.4 GET /profiles/me/stats

我的Profile统计

**响应：**
```json
{
  "code": 0,
  "data": {
    "conn_count": 45,
    "supply_count": 3,
    "demand_count": 2,
    "match_count": 28,
    "active_score": 78.5,
    "active_rank": 128
  }
}
```

---

## 四、标签相关 API

### 4.1 GET /tags

获取全部标签（L1~L5层级）

**响应：**
```json
{
  "code": 0,
  "data": {
    "categories": [
      {
        "l1": "供给资源",
        "l2_groups": [
          {
            "l2": "资金资源",
            "l3_items": [
              { "id": 1, "name": "天使投资", "l4_attrs": [] },
              { "id": 2, "name": "VC投资", "l4_attrs": [] }
            ]
          },
          {
            "l2": "人脉资源",
            "l3_items": [
              { "id": 10, "name": "行业专家", "l4_attrs": [] }
            ]
          }
        ]
      },
      {
        "l1": "需求帮助",
        "l2_groups": [...]
      }
    ]
  }
}
```

---

### 4.2 POST /profiles/me/tags

更新我的标签

**请求：**
```json
{
  "tags": [
    { "id": 5, "tag_type": 1, "weight": 1.0 },
    { "id": 12, "tag_type": 1, "weight": 0.8 },
    { "id": 23, "tag_type": 2, "weight": 1.0 }
  ]
}
```

**响应：**
```json
{
  "code": 0,
  "message": "标签已更新"
}
```

---

### 4.3 POST /profiles/me/tags/ai-extend

AI扩展标签（分析Profile后推荐新标签）

**响应：**
```json
{
  "code": 0,
  "data": {
    "suggested_tags": [
      { "id": 45, "name": "企业服务", "confidence": 0.92, "reason": "您的工作经历和公司业务高度相关" },
      { "id": 67, "name": "SaaS", "confidence": 0.85, "reason": "您关注的行业方向" }
    ]
  }
}
```

---

## 五、供需相关 API

### 5.1 GET /supplies

供需广场列表

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| page_size | int | 每页数量，默认20 |
| type | int | 1=供给 2=需求 |
| tag_ids | string | 标签ID，逗号分隔，如 "5,12,23" |
| sort | string | created_at:desc / match_score:desc / hot:desc |
| school | string | 按学校筛选 |
| keyword | string | 关键词搜索（标题+内容） |

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "uuid": "660e8400-e29b-41d4-a716-446655440001",
        "profile": {
          "uuid": "550e8400-e29b-41d4-a716-446655440000",
          "real_name": "李四",
          "company": "鼎晖投资",
          "position": "合伙人",
          "cert_level": 3,
          "avatar_url": "https://cdn.example.com/avatar/xxx.jpg"
        },
        "supply_type": 1,
        "title": "专注消费赛道的天使投资，寻找早期项目",
        "content": "我们团队专注消费行业投资，单笔投资100-500万...",
        "tags": [
          { "id": 5, "name": "天使投资" },
          { "id": 12, "name": "消费行业" }
        ],
        "match_count": 28,
        "view_count": 1523,
        "quality_score": 92.5,
        "created_at": "2026-05-03T14:30:00Z",
        "is_mine": false
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 152,
      "total_pages": 8
    }
  }
}
```

---

### 5.2 POST /supplies

发布供需

**请求：**
```json
{
  "supply_type": 2,
  "title": "寻找消费行业的销售渠道",
  "content": "我们在做一个新消费品牌，需要找到线下渠道合伙人...",
  "tags": [15, 28, 33]
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "uuid": "660e8400-e29b-41d4-a716-446655440001",
    "quality_score": 88.0,
    "ai_suggestions": [
      "建议补充具体需要的渠道类型（KA/便利店/电商）",
      "建议添加'消费品'标签以提高曝光"
    ]
  }
}
```

---

### 5.3 GET /supplies/feed

AI推荐Feed（个性化供需流）

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| page_size | int | 每页数量，默认10 |
| type | int | 过滤类型（可选） |

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "uuid": "660e8400-e29b-41d4-a716-446655440001",
        "profile": { ... },
        "supply_type": 1,
        "title": "专注消费赛道的天使投资，寻找早期项目",
        "tags": [ ... ],
        "match_score": 0.94,
        "match_reason": "您的标签'找早期项目'与此供给'天使投资'高度匹配",
        "created_at": "2026-05-03T14:30:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 5.4 GET /supplies/:uuid

供需详情

**响应：**
```json
{
  "code": 0,
  "data": {
    "uuid": "660e8400-e29b-41d4-a716-446655440001",
    "profile": { ... },
    "supply_type": 1,
    "title": "专注消费赛道的天使投资，寻找早期项目",
    "content": "我们团队专注消费行业投资...",
    "tags": [ ... ],
    "view_count": 1523,
    "match_count": 28,
    "quality_score": 92.5,
    "status": 1,
    "created_at": "2026-05-03T14:30:00Z",
    "expires_at": "2026-06-02T14:30:00Z"
  }
}
```

---

### 5.5 PUT /supplies/:uuid

编辑我的供需

**请求：**
```json
{
  "title": "更新后的标题",
  "content": "更新后的内容",
  "tags": [15, 28, 33, 45],
  "status": 1
}
```

---

### 5.6 DELETE /supplies/:uuid

删除/下架供需

---

## 六、AI 相关 API

### 6.1 POST /ai/recognize-intent

意图识别（对话入口）

**请求：**
```json
{
  "text": "我想找一些消费行业的投资人",
  "context": {
    "conversation_id": "conv_xxx",
    "history": []
  }
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "intent": "find_investors",
    "entities": {
      "industry": "消费",
      "stage": null,
      "amount": null
    },
    "suggested_action": {
      "type": "redirect",
      "target": "/pages/supplies?type=1&tag_ids=5,12&keyword=消费"
    },
    "reply_text": "为您找到一批专注消费行业的投资人，他们都在找好项目"
  }
}
```

**意图类型说明：**

| intent | 说明 | 推荐动作 |
|--------|------|---------|
| find_investors | 找投资人 | 跳转供给列表 |
| find_partners | 找合伙人 | 跳转人脉推荐 |
| publish_supply | 发布供需 | 跳转发布页 |
| find_activity | 找活动 | 跳转活动列表 |
| find_community | 找社群 | 跳转社群列表 |
| general_chat | 闲聊 | AI直接回复 |

---

### 6.2 POST /ai/extract-tags

标签提取（发布时AI辅助）

**请求：**
```json
{
  "text": "我在找一个懂医疗健康的CTO，技术要过硬的",
  "supply_type": 2
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "tags": [
      { "id": 45, "name": "技术合伙人", "confidence": 0.95, "is_demand": true },
      { "id": 78, "name": "医疗健康", "confidence": 0.88, "is_demand": false }
    ],
    "title_suggestion": "寻找医疗健康行业CTO合伙人",
    "quality_tips": [
      "建议补充技术栈要求（如Python/AI方向）",
      "建议说明合作形式（全职/兼职/顾问）"
    ]
  }
}
```

---

### 6.3 POST /ai/match

AI匹配（批量匹配引擎）

**请求：**
```json
{
  "supply_id": 10001,
  "limit": 20,
  "min_score": 0.6
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "matches": [
      {
        "profile": { ... },
        "match_score": 0.94,
        "ai_reason": "该用户的供给标签'找早期项目'与您的需求'天使投资'高度匹配，且同为消费行业",
        "signal_tags": ["找早期项目", "消费行业", "天使投资"]
      }
    ],
    "total_candidates": 156,
    "matched_count": 20
  }
}
```

---

### 6.4 POST /ai/generate-script

AI生成话术

**请求：**
```json
{
  "type": "introduction",
  "from_profile": {
    "real_name": "张伟",
    "company": "华润集团",
    "position": "战略总监"
  },
  "to_profile": {
    "real_name": "李四",
    "company": "鼎晖投资",
    "position": "合伙人"
  },
  "context": {
    "match_reason": "都在消费行业，有潜在合作机会",
    "supply_title": "专注消费赛道的天使投资"
  }
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "script": "李总好，我是华润集团战略总监张伟。我们团队最近在关注消费行业的早期项目，听说您也在看这个方向，不知道有没有机会交流一下？",
    "variants": [
      "张伟：您好李总，我是华润的张伟，关注到您在找消费行业的好项目，我们这边也有一些资源可以对接。",
      "李总好，我是经朋友介绍找到您的。张伟，在华润做战略工作。我们正在看消费赛道的一些机会，想请教一下您的看法。"
    ]
  }
}
```

---

### 6.5 POST /ai/followup-suggest

AI跟进建议

**请求：**
```json
{
  "from_profile_uuid": "uuid_a",
  "to_profile_uuid": "uuid_b",
  "trigger_event": 1
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "scheduled_at": "2026-05-05T10:00:00Z",
    "suggested_message": "李总，上次发的项目资料有没有机会看一下？创始团队是消费行业老兵，之前在XX品牌做到过分管销售的VP。",
    "alternatives": [ ... ]
  }
}
```

---

## 七、人脉相关 API

### 7.1 GET /connections

我的关系链

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| type | int | 关系类型 1~5 |
| sort | string | recent:desc / strength:desc |

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "uuid": "...",
        "profile": { ... },
        "conn_type": 5,
        "relation_strength": 0.75,
        "last_interact_at": "2026-05-03T14:30:00Z",
        "interact_count": 3,
        "is_mutual": true
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 7.2 POST /connections

发起连接/牵线请求

**请求：**
```json
{
  "target_profile_uuid": "uuid_b",
  "conn_type": 5,
  "message": "您好，我是张伟，在华润做战略工作..."
}
```

**响应：**
```json
{
  "code": 0,
  "data": {
    "uuid": "conn_xxx",
    "ai_script": "李总好，我是张伟...",
    "status": "pending"
  }
}
```

---

### 7.3 PUT /connections/:uuid/accept

接受连接请求

---

### 7.4 DELETE /connections/:uuid

删除连接

---

## 八、活动相关 API

### 8.1 GET /activities

活动列表

**查询参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码 |
| type | int | 活动类型 1~5 |
| school | string | 学校筛选 |
| nearby | string | lat,lng,distance(km) |
| upcoming | bool | 仅 upcoming |

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "uuid": "act_xxx",
        "title": "消费行业创始人交流会",
        "cover_url": "https://cdn.example.com/cover/xxx.jpg",
        "activity_type": 1,
        "host_school": "中欧国际工商学院",
        "location": "北京市朝阳区建国路88号",
        "start_time": "2026-05-15T14:00:00Z",
        "max_attendees": 50,
        "current_attendees": 38,
        "enrollment_mode": 1,
        "status": 1,
        "organizer": {
          "real_name": "王五",
          "company": "中欧校友会",
          "avatar_url": "..."
        },
        "ai_match_score": 0.88
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 8.2 POST /activities/:uuid/enroll

报名活动

**请求：**
```json
{
  "ai_recommended": true
}
```

---

### 8.3 GET /activities/:uuid/attendees

活动参与者列表（AI推荐排序）

---

## 九、社群相关 API

### 9.1 GET /communities

社群列表

**查询参数：** `type`（1~4）, `school`, `page`, `page_size`

---

### 9.2 POST /communities/:uuid/join

加入社群

---

### 9.3 GET /communities/:uuid/messages

社群消息列表（App内发布的内容）

**查询参数：** `page`, `signal_type`（AI信号过滤）

---

## 十、跟进相关 API

### 10.1 GET /followups

我的AI跟进列表

**查询参数：** `status`（0=待处理 1=已计划 2=已发送 3=已完成）

**响应：**
```json
{
  "code": 0,
  "data": {
    "items": [
      {
        "uuid": "fu_xxx",
        "to_profile": { ... },
        "trigger_event": 1,
        "ai_script": "李总，上次发的项目资料有没有机会看一下？...",
        "followup_type": 1,
        "scheduled_at": "2026-05-05T10:00:00Z",
        "status": 1
      }
    ],
    "pagination": { ... }
  }
}
```

---

### 10.2 PUT /followups/:uuid

更新跟进状态

**请求：**
```json
{
  "status": 2,
  "result": 1,
  "result_text": "已成功约到见面"
}
```

---

## 十一、Webhook 事件（可选）

用于推送通知到用户侧（如微信服务号）

**事件类型：**
- `match.new` — 新匹配推荐
- `followup.remind` — 跟进提醒
- `activity.upcoming` — 活动开始提醒
- `connection.accepted` — 连接被接受

---

## 附录：Apifox导入格式

```json
{
  "info": {
    "name": "燃冰API",
    "version": "1.0.0"
  },
  "item": [
    {
      "name": "认证",
      "item": [
        { "name": "登录", "request": { "method": "POST", "url": "/auth/login" } },
        { "name": "发送验证码", "request": { "method": "POST", "url": "/auth/send-code" } }
      ]
    }
  ]
}
```
