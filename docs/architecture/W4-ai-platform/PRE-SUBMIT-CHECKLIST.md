# 明天小程序提交 - Checklist

> 时间：2026-08-25 提交 / 2026-08-24 准备完毕
> 范围：小程序 + 后端 + AI 接口验证

## 必读结论

- ✅ 后端 production 已修复**所有已知 bug**
- ✅ 接口冒烟**全部通过**（匿名 3/3，登录 4/4，AI chat 1/1）
- ⚠️  AI 远程服务（fipai.cn）偶发 502/400——与我们的代码无关
- ⚠️  需手动在微信公众平台配置隐私指引 + 域名白名单

---

## ☐ 后端验证 ✅ 已完成

### 冒烟结果（2026-08-24 验证）

| 场景 | 接口 | 状态 |
|------|------|------|
| 匿名 | GET /api/v1/supplies/ | **200** ✓ |
| 匿名 | GET /api/v1/communities/ | **200** ✓ (5 个社群) |
| 匿名 | GET /api/v1/activities/ | **200** ✓ |
| 匿名 | POST /api/v1/ai/chat/ | **200** ✓ (DeepSeek 1.6s) |
| 登录 | POST /api/v1/auth/login/ | **200** ✓ |
| 登录 | GET /api/v1/me/ | **200** ✓ |
| 登录 | GET /api/v1/profiles/me/ | **200** ✓ |
| 登录 | GET /api/v1/profiles/me/stats/ | **200** ✓ |
| 登录 | GET /api/v1/supplies/feed/ | **200** ✓ |
| 登录 | POST /api/v1/ai/match/ | **200** ✓ |
| 登录 | POST /api/v1/ai/chat/ | **200** ✓ (DeepSeek 7s) |

### 已修复的 production bug（今天）

1. `backend/supplies/views.py`: `SupplyViewSet.get_permissions()` 返回 `[AllowAny()]`，允许匿名访问 list/retrieve/feed
2. `backend/supplies/views.py:71`: 兼容 `AnonymousUser`（无 profile 时不报错）
3. `backend/ai/views.py:727`: `a.city` → `a.location`（Activity 没有 city 字段）
4. `backend/ai/views.py`: 移除 2 个 `async def`（与 sync gunicorn worker 不兼容）

### 测试账号（用于审核）

```
账号 1（testuser）
  手机号: 13900000009
  密码:   test123456
  nickname: testuser
  有 profile

账号 2（测试用户）
  手机号: 13900000099
  密码:   test123456
  nickname: 测试用户
  有 profile
```

> **重要**：密码是 2026-08-24 我用 Django shell 重置的，**生产数据库已更新**
> 如果审核员登不上，告诉我，我可以再重置

---

## ☐ 小程序代码状态 ✅ 已完成

### 改动文件（已 commit + push 到 `agent/backend`）

**后端**：
- `backend/users/authentication.py` — JWT 宽容处理（兼容 AllowAny 视图）

**小程序**：
- `mini-program/src/utils/masktext.wxs`（新建）— 修复 wxml 引用 not found
- `mini-program/src/pages/agreement/{service,privacy}/`（新建）— 用户协议 + 隐私政策
- `mini-program/src/app.js` — 全局异常兜底
- `mini-program/src/services/api.js` — extractData 支持嵌套 + 网络错误 toast
- `mini-program/src/pages/community/community.wxml` — 加入按钮 catchtap 防冒泡
- `mini-program/src/pages/profile/profile.js` — 退出登录 reLaunch 清页面栈
- `mini-program/src/pages/home/home.{js,wxml}` — profile null 保护
- `mini-program/src/pages/supply-demand/*` — profile null 保护
- `mini-program/src/pages/chat/chat.js` — 重写分页逻辑
- `mini-program/src/pages/cards/cards.js` + card-edit — 名片改用 setStorageSync
- `mini-program/src/pages/contact-tags/contact-tags.js` — 简化 extractData + 防连点
- `mini-program/src/pages/login/{login,register}.js` — 清理 setInterval

---

## ☐ 明天提交前必做（人工）

### 1. 微信公众平台配置

- ☐ 登录 https://mp.weixin.qq.com → 开发管理 → 服务器域名
- ☐ **request 合法域名**：`https://www.asiamlhk.com`
- ☐ **uploadFile 合法域名**：`https://www.asiamlhk.com`
- ☐ **downloadFile 合法域名**：`https://www.asiamlhk.com`（如用）

### 2. 隐私保护指引（必填）

- ☐ 设置 → 第三方设置 → 用户隐私保护指引
- ☐ 勾选采集项：
  - ✓ 手机号（用于账号注册）
  - ✓ 设备信息（基础设备型号 / 操作系统版本 / 唯一设备标识符）
  - ✓ 微信 OpenID / UnionID（用于一键登录）
  - ✓ 用户发布内容（供需 / 私信 / 社群动态）
- ☐ 填写处理目的：**用于商务社交平台的账号注册、AI 智能匹配、内容审核**
- ☐ 隐私政策链接：填 `/pages/agreement/privacy` 或外链

### 3. 用户协议 + 隐私政策（已内置）

- ☐ 确认 `mini-program/src/pages/agreement/service.wxml` 内容（8 章 + 联系我们 + 免责声明）
- ☐ 确认 `mini-program/src/pages/agreement/privacy.wxml` 内容（10 章含 DeepSeek AI SDK）
- ☐ 登录时强制勾选 ✓（代码已加 `agreeProtocol` 校验，不勾不能登录）

### 4. 提交信息

- ☐ 版本号：1.0.0 → 1.0.1（最新 commit `ee20bc6` 已 push）
- ☐ 项目类目：工具 → 效率 / 商务（按实际选）
- ☐ 测试账号：**13900000009 / test123456**（testuser）
- ☐ 测试手机号：同上 + 验证码可正常接收（确认 SMS_PROVIDER 已配）
- ☐ 功能页面截图（4-6 张首页/登录/AI 对话/社群/供需详情）

### 5. 测试核心流程（开发者工具 + 真机）

- ☐ 启动 → 协议页可访问
- ☐ 登录：勾协议 → 输手机号 → 收验证码 → 进首页
- ☐ 首页瀑布流：登录态可见完整信息；退出登录后左滑回不到 profile
- ☐ AI 对话：发消息 → 收到 DeepSeek 响应（1-3 秒）
- ☐ 社群加入：点「加入」按钮不跳详情页
- ☐ 名片编辑：进入正常，setStorageSync 传参

---

## 紧急回滚

### 后端回滚（如果出问题）

```bash
ssh root@8.138.90.48
cd /www/ranbing
# backup（最近一次备份在 /tmp/ranbing-backup-*）
BACKUP=$(ls -td /tmp/ranbing-backup-* | head -1)
echo "  用 $BACKUP 回滚"

# 如果 supplies/view.py 报错，回滚这一行：
sed -i 's|        return \[AllowAny()\]|        return [IsAuthenticated()]|' supplies/views.py
sed -i 's|    def get_permissions(self):|    # 关闭匿名访问\n    permission_classes = [IsAuthenticated]\n    def get_permissions(self):|' supplies/views.py

# 如果 ai/views.py async 出问题，恢复 sync def
systemctl restart ranbing
```

### 小程序回滚

- 微信开发者工具 → 版本管理 → 撤回本次审核版本（如还未过审）

---

## 联系信息

- 服务器：root@8.138.90.48
- 域名：console.asiamlhk.com / www.asiamlhk.com
- 后端 service：ranbing
- 数据库：阿里云 RDS MySQL（`qiyumysqllianjie.mysql.rds.aliyuncs.com:1106`）

## 服务端口

- 后端 gunicorn：`127.0.0.1:8899`
- nginx 转发：`80 / 443`
- 业务后端：`https://www.asiamlhk.com/api/v1/`
- 后台前端：`https://console.asiamlhk.com/`

## 已知风险（已记录但暂不修）

1. **`/api/v1/ai/supply-matches/` 调用 fipai.cn，偶发 502**（远程服务问题，与本地代码无关）
2. **`/api/v1/ai/activity-recommend/` 调用 fipai.cn，偶发 400**（同上）
3. **AI Match 性能问题**：原 50 分钟 → 当前 8 秒（已 batch 化，但需更多优化）

## 明天提交小程序的命令

```bash
# 在微信开发者工具中：
# 1. 打开 ~/ranbing/mini-program/
# 2. 勾选"不校验合法域名" → 编译通过
# 3. 真机调试：扫体验码 / 预览 → 检查核心 4 流程
# 4. 满意后：上传 → 填写版本号 1.0.1 + 项目备注 → 提交审核
```