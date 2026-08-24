# 今天提交小程序 — 立即行动清单

> 时间：2026-08-24（现在）
> 状态：后端全部修复完毕，可以提交

---

## 后端状态（已全部就绪 ✅）

| 接口 | 状态 |
|------|------|
| GET /supplies/（匿名） | 200 ✅ |
| GET /communities/（匿名） | 200 ✅ |
| GET /activities/（匿名） | 200 ✅ |
| POST /ai/chat/（匿名） | 200 ✅ DeepSeek |
| POST /auth/login/ | 200 ✅ |
| GET /me/ /profiles/me/ /profiles/me/stats/ | 200 ✅ |
| POST /ai/chat/（登录） | 200 ✅ DeepSeek |
| GET /ai/activity-recommend/ | **200 ✅ DeepSeek（今天刚修）** |
| GET /ai/supply-matches/ | **200 ✅ DeepSeek（今天刚修）** |
| POST /ai/chat-v2/ | **200 ✅ DeepSeek（今天刚修）** |
| GET /communities/{uuid}/members/ | **200 ✅（今天刚修）** |
| POST /communities/post_message/ | **201 ✅（今天刚修）** |

**今天修复的 4 个 API 错误**（Hermes 移交）全部搞定，且 **fipai.cn 已用 DeepSeek 替代**。

---

## 测试账号

```
账号1: 13900000009 / test123456 (testuser)
账号2: 13900000099 / test123456 (测试用户)
```

---

## 立刻要做（按顺序）

### 1. 微信开发者工具打开项目（5 分钟）

```bash
# 项目路径
/Users/wangsheng/ranbing/mini-program/
```

- ☐ 打开微信开发者工具 → 导入项目 → 选 `~/ranbing/mini-program/`
- ☐ AppID: `wx38afcc7832ded761`（已配置在 project.config.json）
- ☐ 编译通过（应该无报错）

### 2. 真机预览核心流程（15 分钟）

用**测试账号1**（13900000009 / test123456）：

- ☐ **启动** → 出现用户协议勾选（`agreeProtocol`）
- ☐ **登录** → 勾协议 → 输手机号 13900000009 → 密码 test123456 → 进首页
- ☐ **首页瀑布流** → 能看到供需/活动/社群卡片（匿名也可见）
- ☐ **AI 对话** → 首页点 ✨AI → 发消息 → 收到 DeepSeek 回复（1-5秒）
- ☐ **活动页** → 能看到 AI 活动推荐（今天刚修的接口）
- ☐ **社群详情** → 进入社群 → 成员列表正常 → 发帖成功（今天刚修的）
- ☐ **退出登录** → 左滑回不到 profile 页

### 3. 微信公众平台配置（10 分钟）

登录 https://mp.weixin.qq.com（用小程序账号）

- ☐ **开发管理 → 开发设置 → 服务器域名**
  - request 合法域名：`https://www.asiamlhk.com`
  - uploadFile 合法域名：`https://www.asiamlhk.com`
  - downloadFile 合法域名：`https://www.asiamlhk.com`

- ☐ **设置 → 第三方设置 → 用户隐私保护指引**
  - 采集项勾选：手机号、设备信息、微信OpenID/UnionID、用户发布内容
  - 处理目的：商务社交平台的账号注册、AI 智能匹配、内容审核
  - 隐私政策链接：`https://www.asiamlhk.com/pages/agreement/privacy` 或小程序内 `/pages/agreement/privacy`

### 4. 上传 + 提交审核（5 分钟）

- ☐ 微信开发者工具 → 右上角「上传」
- ☐ 版本号：**1.0.1**
- ☐ 项目备注：`修复：AI接口DeepSeek替代、社群成员/发帖、活动推荐；新增用户协议隐私政策`
- ☐ 提交审核
- ☐ 测试账号：填 `13900000009 / test123456`
- ☐ 测试说明：填"测试账号可登录，AI对话、社群发帖、活动推荐均可正常使用"

---

## 审核员测试路径（写进备注）

1. 打开小程序 → 勾选协议 → 手机号 13900000009 密码 test123456 登录
2. 首页可看到供需/活动/社群
3. 点 AI 助手可对话
4. 进入社群可查看成员并发言
5. 活动页可看到 AI 推荐

---

## 如果审核被拒

常见原因 + 对应：

| 被拒原因 | 处理 |
|---------|------|
| 隐私协议缺失 | 已在 `pages/agreement/` 内置，登录强制勾选 |
| 类目不符 | 类目选「工具→效率」或「商业服务」 |
| AI 内容无免责 | 用户协议第六章有 AI 免责声明 |
| 测试账号登录失败 | 密码 test123456 已重置，找我重新生成 |
| 域名未配置 | 检查第3步服务器域名 |

---

## 紧急联系

- 后端服务：`systemctl status ranbing`（active = 正常）
- 服务器：root@8.138.90.48
- 代码已 push：`origin/agent/backend`（commit `f7a0e95`）
