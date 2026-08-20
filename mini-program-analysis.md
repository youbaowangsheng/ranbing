# 燃冰小程序全面分析报告

## 一、页面完整性

### app.json pages 注册 (23个页面)
| # | 页面路径 | 状态 |
|---|---------|------|
| 1 | pages/login/login | OK |
| 2 | pages/login/register | OK |
| 3 | pages/home/home | OK |
| 4 | pages/supply-demand/supply-demand | OK |
| 5 | pages/publish/publish | OK |
| 6 | pages/my-posts/my-posts | OK |
| 7 | pages/ai-assistant/ai-assistant | OK |
| 8 | pages/activity/activity | OK |
| 9 | pages/community/community | OK |
| 10 | pages/profile/profile | OK |
| 11 | pages/supply-detail/supply-detail | OK |
| 12 | pages/activity-detail/activity-detail | OK |
| 13 | pages/community-detail/community-detail | OK |
| 14 | pages/messages/messages | OK |
| 15 | pages/chat/chat | OK |
| 16 | pages/search/search | OK |
| 17 | pages/profile-edit/profile-edit | OK |
| 18 | pages/profile-view/profile-view | OK |
| 19 | pages/contacts/contacts | OK |
| 20 | pages/contact-tags/contact-tags | OK |
| 21 | pages/cards/cards | OK |
| 22 | pages/card-edit/card-edit | OK |

### services/api.js 接口层 (已实现 41 个函数)
```
request, getSupplies, getFeed, createSupply, deleteSupply,
getActivities, getMyEnrollments, getActivityRecommend, getActivityDetail,
getCommunities, getCommunityDetail, getCommunityMembers,
joinCommunity, leaveCommunity, getMySupplies,
aiMatch, getProfile, getMe, updateProfile, getTags,
getConnections, getFriendRequests, sendFriendRequest,
acceptFriendRequest, rejectFriendRequest, getSentFriendRequests,
getContactTags, getCards, createCard, updateCard, deleteCard, setDefaultCard,
getContactTagsFor, addContactTag, removeContactTag,
sendMessage, getConversations, getMessages, getMessagesWith, sendPrivateMessage
```

---

## 二、API 对齐分析

### 后端已有 API vs 小程序已调用

| 后端 API | 小程序调用 | 状态 |
|---------|-----------|------|
| **认证 auth/** | | |
| POST /api/v1/auth/login/ | loginByPassword, loginByCode | OK |
| POST /api/v1/auth/register/ | register | OK |
| POST /api/v1/auth/send_code/ | sendCode | OK |
| POST /api/v1/auth/wx_login/ | loginByWechat | OK |
| POST /api/v1/auth/refresh/ | refreshToken (auth.js) | OK |
| **用户 me/** | | |
| GET /api/v1/me/ | getMe (api.js), getProfile (auth.js) | OK |
| **Profile profiles/** | | |
| GET /api/v1/profiles/me/ | getProfile | OK |
| PUT /api/v1/profiles/me/ | updateProfile | OK |
| GET /api/v1/profiles/{uuid}/ | profile-view.js (手动request) | OK |
| POST /api/v1/profiles/send_message/ | sendMessage, sendPrivateMessage | OK |
| GET /api/v1/profiles/conversations/ | getConversations | OK |
| GET /api/v1/profiles/messages_with/ | getMessages, getMessagesWith | OK |
| GET /api/v1/profiles/me/stats/ | profile.js 手动 request | OK |
| POST /api/v1/profiles/connect/ | profile-view.js 硬编码 | OK |
| POST /api/v1/profiles/update_tags/ | profile-edit.js 硬编码 | OK |
| **Tags** | | |
| GET /api/v1/tags/ | getTags | OK |
| **Supplies** | | |
| GET /api/v1/supplies/ | getSupplies | OK |
| POST /api/v1/supplies/ | createSupply | OK |
| DELETE /api/v1/supplies/{uuid}/ | deleteSupply | OK |
| GET /api/v1/supplies/mine/ | getMySupplies | OK |
| GET /api/v1/supplies/feed/ | getFeed | OK |
| GET /api/v1/supplies/{uuid}/ | supply-detail.js 手动request | OK |
| **Activities** | | |
| GET /api/v1/activities/ | getActivities | OK |
| GET /api/v1/activities/mine/ | getMyEnrollments | OK |
| GET /api/v1/activities/{uuid}/ | getActivityDetail | OK |
| POST /api/v1/activities/{uuid}/enroll/ | activity-detail.js 手动request | OK |
| GET /api/v1/ai/activity-recommend/ | getActivityRecommend | OK |
| **Communities** | | |
| GET /api/v1/communities/ | getCommunities | OK |
| GET /api/v1/communities/{uuid}/ | getCommunityDetail | OK |
| GET /api/v1/communities/{uuid}/members/ | getCommunityMembers | OK |
| POST /api/v1/communities/{uuid}/join/ | joinCommunity | OK |
| POST /api/v1/communities/{uuid}/leave/ | leaveCommunity | OK |
| **Connections** | | |
| GET /api/v1/connections/ | getConnections | OK |
| **Friend Requests** | | |
| GET /api/v1/friend-requests/ | getFriendRequests | OK |
| POST /api/v1/friend-requests/send/ | sendFriendRequest | OK |
| POST /api/v1/friend-requests/{uuid}/accept/ | acceptFriendRequest | OK |
| POST /api/v1/friend-requests/{uuid}/reject/ | rejectFriendRequest | OK |
| GET /api/v1/friend-requests/sent/ | getSentFriendRequests | OK |
| **Cards** | | |
| GET /api/v1/cards/ | getCards | OK |
| POST /api/v1/cards/ | createCard | OK |
| PATCH /api/v1/cards/{uuid}/ | updateCard | OK |
| DELETE /api/v1/cards/{uuid}/ | deleteCard | OK |
| POST /api/v1/cards/{uuid}/set_default/ | setDefaultCard | OK |
| **Contact Tags** | | |
| GET /api/v1/contact-tags/ | getContactTags | OK |
| GET /api/v1/contacts/{profileUuid}/tags/ | getContactTagsFor | OK |
| POST /api/v1/contacts/{profileUuid}/tags/add/ | addContactTag | OK |
| DELETE /api/v1/contacts/{profileUuid}/tags/{tagId}/ | removeContactTag | OK |
| **AI** | | |
| POST /api/v1/ai/match/ | aiMatch | OK |
| POST /api/v1/ai/chat/ | ai-assistant.js 手动request | OK |

### API 缺失/未实现

| API | 说明 | 影响 |
|-----|------|------|
| GET /api/v1/communities/{uuid}/messages/ | 社群消息列表 | community-detail.js 引用但未定义 |
| POST /api/v1/communities/{uuid}/messages/ | 社群发帖 | community-detail.js 引用但未定义 |
| GET /api/v1/search/?q= | 全局搜索 | search.js 有调用但api.js未导出 |
| GET /api/v1/profiles/me/stats/ | 个人统计 | profile.js 硬编码 |
| POST /api/v1/profiles/connect/ | 发起连接 | profile-view.js 硬编码 |
| POST /api/v1/profiles/update_tags/ | 更新标签 | profile-edit.js 硬编码 |
| POST /api/v1/activities/{uuid}/cancel/ | 取消报名 | 未实现 |
| GET /api/v1/tags/?category= | 按分类获取标签 | 未实现 |

---

## 三、功能一致性对照

### Web端 vs 小程序端

| Web页面 (TemplateView) | 小程序页面 | 功能对齐 | 说明 |
|----------------------|----------|---------|------|
| /pages/home/ | pages/home/home | 部分 | 小程序是瀑布流混合信息流，Web是单列表 |
| /pages/supply/demand/ | pages/supply-demand/supply-demand | OK | 功能基本一致 |
| /pages/supply/publish/ | pages/publish/publish | OK | 功能基本一致 |
| /pages/supply/<uuid>/ | pages/supply-detail/supply-detail | OK | 功能基本一致 |
| /pages/messages/ | pages/messages/messages | OK | 功能一致 |
| /pages/messages/<uuid>/ | pages/chat/chat | OK | 功能一致 |
| /pages/profile/ | pages/profile/profile | OK | 功能一致 |
| /pages/profile/<uuid>/ | pages/profile-view/profile-view | OK | 功能一致 |
| /pages/profile/edit/ | pages/profile-edit/profile-edit | OK | 功能一致 |
| /pages/activities/ | pages/activity/activity | OK | 功能一致 |
| /pages/activities/<id>/ | pages/activity-detail/activity-detail | OK | 功能一致 |
| /pages/community/ | pages/community/community | OK | 功能一致 |
| /pages/community/<id>/ | pages/community-detail/community-detail | 部分 | 社群消息功能API缺失 |
| /pages/ai/ | pages/ai-assistant/ai-assistant | OK | AI对话功能基本一致 |
| /pages/network/ | ❌ 无 | 缺失 | **Web有人脉图，小程序无** |
| /pages/search/ | pages/search/search | OK | 功能一致 |
| /pages/followup/ | ❌ 无 | 缺失 | **Web有跟进记录，小程序无** |
| /pages/certification/ | ❌ 无 | 缺失 | **Web有认证功能，小程序无** |

### 通讯录与人脉功能 (Phase1 & Phase2)

| PRD功能 | 小程序实现 | 说明 |
|--------|----------|------|
| 通讯录列表 | pages/contacts/contacts | OK - 好友列表+好友申请 |
| 好友申请接受/拒绝 | contacts/contacts.js | OK |
| 联系人标签 | pages/contact-tags/contact-tags | OK |
| 名片管理 | pages/cards/cards + card-edit | OK |
| 标签增删 | contact-tags/contact-tags.js | OK |
| 默认名片设置 | card-edit/card-edit.js | OK |
| 人脉统计 (Phase2) | ❌ 无 | **缺失 - profile.js只有stub** |
| 可见权限 (Phase2) | ❌ 无 | **缺失** |

---

## 四、代码质量问题

### 1. 严重问题：错误的方法引用

**问题1: contacts.js 引用不存在的方法**
```javascript
// contacts.js line 2
const { getMyProfile } = require('../../services/auth.js');
// auth.js 导出: { sendCode, loginByPassword, loginByCode, loginByWechat, register, refreshToken, getProfile, logout }
// 根本没有 getMyProfile！
```
正确应该是 `getProfile` from api.js 或 `getProfile` from auth.js

**问题2: community-detail.js 引用不存在的方法**
```javascript
// community-detail.js line 1
const { getCommunityMessages, postCommunityMessage } = require('../../services/api');
// api.js 根本没有导出这两个方法！
```

**问题3: search.js 使用 request 但未导出**
```javascript
// search.js line 43
const res = await request(`/search/?q=...`, 'GET')
// api.js 导出了 request，但这个调用未经过封装，直接裸用
```

### 2. 中等问题：硬编码的 API 路径

| 文件 | 硬编码路径 | 应改为 |
|-----|----------|-------|
| profile.js | `request('/profiles/me/stats/')` | 封装为 `getProfileStats()` |
| profile-view.js | `request('/profiles/connect/', 'POST', ...)` | 封装为 `connectProfile()` |
| profile-edit.js | `request('/profiles/update_tags/', 'POST', ...)` | 封装为 `updateProfileTags()` |
| supply-detail.js | `api.request(...)` | 通过 api.js 的 request |

### 3. 认证相关问题

**问题: contacts.js 引用 getMyProfile 但 auth.js 没有这个函数**
```javascript
// contacts.js line 2
const { getMyProfile } = require('../../services/auth.js');  // 不存在！
```

正确方法：
- 如果要获取当前用户profile，用 `getProfile()` from api.js
- auth.js 有 `getProfile()` 函数但逻辑是调用 `/me/`

### 4. 潜在空指针问题

```javascript
// home.js line 40 - 可选链使用不当
me.nickname || profile.real_name || me.phone?.replace(...) || '用户'
// me.phone 是 string，string没有 ?. 方法（小程序基础库2.8+才支持）

// contacts.js line 36
this.initials((c.other_profile && c.other_profile.real_name) || c.real_name || '未知')
// this.initials 方法名冲突（定义在line 67），但调用时写法奇怪

// 所有 pages 的错误处理基本是空的 catch(e) {}
```

### 5. WXS 语法问题
未发现 .wxs 文件，无此问题。

### 6. API响应格式不一致
多处代码对响应的处理不一致：
```javascript
// contacts.js 处理 res.code === 0 判断
// community-detail.js 处理 res.data.code === 0 判断
// home.js 直接取 res.data 或 res.results
```
后端返回格式可能是 `{code: 0, data: {...}}` 或直接 `{...}`，代码中多处手动处理。

---

## 五、登录/认证流程

### 当前流程
```
wx.login() → /auth/wx_login/ → 获取 token → 存储 → 跳转首页
```

### 发现的问题

1. **app.js 和 auth.js API_BASE 不一致**
   - app.js: `'https://asiamlhk.com/api/v1'` (无www)
   - auth.js: `'https://www.asiamlhk.com/api/v1'` (有www)
   - api.js: `'https://www.asiamlhk.com/api/v1'` (有www)

2. **401 处理会中断用户操作**
   ```javascript
   // api.js line 19-23
   } else if (res.statusCode === 401) {
     wx.removeStorageSync('token')
     wx.removeStorageSync('userInfo')
     wx.navigateTo({ url: '/pages/login/login' })
     reject(new Error('未登录'))
   }
   ```
   在某些页面（如 messages）自动跳转会中断用户操作。

3. **refresh_token 未被使用**
   - auth.js 有 `refreshToken()` 函数
   - 但 token 过期时没有自动刷新机制
   - 直接跳转到 login 页面

4. **token 存储位置**
   - token 存储在 `wx.storageSync('token')`
   - refresh_token 存储在 `wx.storageSync('refresh_token')`
   - 没有使用 `userInfo` 作为主数据源

---

## 六、已有页面和功能清单

### 小程序页面清单 (22个)

| 页面 | 主要功能 |
|------|---------|
| login/login | 密码登录/短信登录/微信登录 |
| login/register | 手机号注册 |
| home/home | 瀑布流信息流(供需+活动+社群混合) |
| supply-demand/supply-demand | 供需列表(筛选+搜索) |
| publish/publish | 发布供需(标签+图片) |
| my-posts/my-posts | 我的发布(管理+删除) |
| ai-assistant/ai-assistant | AI对话助手 |
| activity/activity | 活动列表(分类+推荐) |
| activity-detail/activity-detail | 活动详情+报名 |
| community/community | 社群列表+搜索+加入 |
| community-detail/community-detail | 社群详情+成员+消息(API缺失) |
| profile/profile | 个人中心+统计 |
| profile-edit/profile-edit | 编辑个人信息+标签 |
| profile-view/profile-view | 查看他人 profile + 发消息 |
| messages/messages | 会话列表 |
| chat/chat | 私信聊天 |
| search/search | 全局搜索(人+供需+活动+社群) |
| contacts/contacts | 通讯录(好友列表+申请管理) |
| contact-tags/contact-tags | 联系人标签管理 |
| cards/cards | 名片列表 |
| card-edit/card-edit | 创建/编辑名片 |

### 缺失功能

| 功能 | Web有 | 小程序无 |
|------|------|---------|
| 人脉图/网络图 | /pages/network/ | ❌ |
| 跟进记录 | /pages/followup/ | ❌ |
| 认证中心 | /pages/certification/ | ❌ |
| 活动报名取消 | POST /activities/<id>/cancel/ | ❌ |
| 人脉统计 | profiles/me/stats/ | stub (profile.js) |
| 社群消息功能 | 有 | API缺失 |

---

## 七、问题优先级

### P0 - 严重（影响功能）
1. `contacts.js` 引用不存在的 `getMyProfile` - 会导致页面崩溃
2. `community-detail.js` 引用不存在的 `getCommunityMessages`, `postCommunityMessage` - 会导致页面崩溃
3. `app.js` 和 `auth.js` API_BASE 不一致 (asiamlhk.com vs www.asiamlhk.com)
4. 社群消息功能的 API 未定义

### P1 - 高优先级
5. `profile.js` 的 `/profiles/me/stats/` 硬编码应封装
6. `profile-view.js` 的 `/profiles/connect/` 硬编码应封装
7. `profile-edit.js` 的 `/profiles/update_tags/` 硬编码应封装
8. `search.js` 的 `/search/` 路径应封装

### P2 - 中优先级
9. 错误处理普遍为空 `catch(e) {}`
10. API响应格式处理不一致 (code===0判断混乱)
11. 401 自动跳转可能中断用户操作

### P3 - 低优先级
12. `publish.js` 提交图片仍是本地路径，后端可能不支持
13. `ai-assistant.js` 调用 `/ai/chat/` 但后端有 `/ai/chat/` 和 `/ai/chat-v2/`
14. `profile-edit.js` 的行业选择是硬编码的，未从后端获取