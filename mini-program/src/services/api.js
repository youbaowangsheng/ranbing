// services/api.js - 通用 API 服务
const API_BASE = 'https://www.asiamlhk.com/api/v1'

function request(path, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    const token = wx.getStorageSync('token')
    if (token) header['Authorization'] = `Bearer ${token}`

    wx.request({
      url: API_BASE + path,
      method,
      data,
      header,
      timeout: 15000,
      success: res => {
        if ((res.statusCode === 200 || res.statusCode === 201) && res.data) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.navigateTo({ url: '/pages/login/login' })
          reject(new Error('未登录'))
        } else {
          const errMsg = res.data && (res.data.message || (res.data.errors && JSON.stringify(res.data.errors)) || res.data.detail || res.statusCode)
          console.error('[API请求失败]', path, res.statusCode, res.data)
          reject(new Error(errMsg || '请求失败'))
        }
      },
      fail: err => reject(new Error(err.errMsg || '网络错误'))
    })
  })
}

// 微信小程序的 URLSearchParams polyfill
function buildQuery(params) {
  if (!params || Object.keys(params).length === 0) return ''
  return Object.keys(params).map(k => `${encodeURIComponent(k)}=${encodeURIComponent(params[k])}`).join('&')
}

// 供需列表
function getSupplies(params = {}) {
  const q = buildQuery(params)
  return request(`/supplies/${q ? '?' + q : ''}`)
}

// AI推荐Feed
function getFeed(params = {}) {
  const q = buildQuery(params)
  return request(`/supplies/feed/${q ? '?' + q : ''}`)
}

// 发布供需
function createSupply(data) {
  return request('/supplies/', 'POST', data)
}

// 删除供需
function deleteSupply(uuid) {
  return request(`/supplies/${uuid}/`, 'DELETE')
}

// 获取活动列表
function getActivities(params = {}) {
  const q = buildQuery(params)
  return request(`/activities/${q ? '?' + q : ''}`)
}

// 我报名的活动
function getMyEnrollments() {
  return request('/activities/mine/')
}

// 获取活动详情
function getActivityDetail(uuid) {
  return request(`/activities/${uuid}/`)
}

// AI活动推荐
function getActivityRecommend() {
  return request('/ai/activity-recommend/', 'GET')
}

// 获取社群列表
function getCommunities(params = {}) {
  const q = buildQuery(params)
  return request(`/communities/${q ? '?' + q : ''}`)
}

// 获取社群详情
function getCommunityDetail(uuid) {
  return request(`/communities/${uuid}/`)
}

// 社群成员
function getCommunityMembers(uuid, page = 1) {
  return request(`/communities/${uuid}/members/?page=${page}`)
}

// 加入社群
function joinCommunity(uuid) {
  return request(`/communities/${uuid}/join/`, 'POST')
}

// 退出社群
function leaveCommunity(uuid) {
  return request(`/communities/${uuid}/leave/`, 'POST')
}

// 社群消息列表
function getCommunityMessages(uuid, page = 1) {
  return request(`/communities/${uuid}/messages/?page=${page}`)
}

// 社群发消息
function postCommunityMessage(data) {
  return request('/communities/post_message/', 'POST', data)
}

// 我的发布（当前用户）
function getMySupplies(params = {}) {
  const q = buildQuery(params)
  return request(`/supplies/mine/${q ? '?' + q : ''}`)
}

// AI匹配
function aiMatch(data) {
  return request('/ai/match/', 'POST', data)
}

// 获取个人Profile（/profiles/me/返回完整profile，含company/position/cert_level）
function getProfile() {
  return request('/profiles/me/', 'GET')
}

// 更新个人Profile
function updateProfile(data) {
  return request('/profiles/me/', 'PUT', data)
}

// 获取当前登录用户信息（/me/返回User基本信息含phone/nickname）
function getMe() {
  return request('/me/', 'GET')
}

// 获取标签
function getTags() {
  return request('/tags/')
}

// 获取通讯录好友列表
function getConnections() {
  return request('/connections/')
}

// 获取收到的好友申请
function getFriendRequests() {
  return request('/friend-requests/')
}

// 发送好友申请
function sendFriendRequest(toProfileUuid, message) {
  return request('/friend-requests/send/', 'POST', { to_profile_uuid: toProfileUuid, message: message || '' })
}

// 接受好友申请
function acceptFriendRequest(uuid) {
  return request(`/friend-requests/${uuid}/accept/`, 'POST')
}

// 拒绝好友申请
function rejectFriendRequest(uuid) {
  return request(`/friend-requests/${uuid}/reject/`, 'POST')
}

// 获取发出的好友申请
function getSentFriendRequests() {
  return request('/friend-requests/sent/')
}

// 获取联系人标签
function getContactTags() {
  return request('/contact-tags/')
}

// 获取名片列表（当前用户只有一张名片，用 /cards/me/）
function getCards() {
  return request('/cards/me/')
}

// 创建名片（使用 /cards/me/ POST）
function createCard(cardData) {
  return request('/cards/me/', 'POST', cardData)
}

// 更新名片（使用 /cards/me/ PUT）
function updateCard(uuid, cardData) {
  return request('/cards/me/', 'PUT', cardData)
}

// 删除名片
function deleteCard(uuid) {
  return request(`/cards/${uuid}/`, 'DELETE')
}

// 设置默认名片
function setDefaultCard(uuid) {
  return request(`/cards/${uuid}/set_default/`, 'POST')
}

// 获取某人的联系人标签
function getContactTagsFor(profileUuid) {
  return request(`/contact-tags/contacts/${profileUuid}/tags/`)
}

// 添加联系人标签
function addContactTag(profileUuid, tagId) {
  return request(`/contact-tags/contacts/${profileUuid}/tags/add/`, 'POST', { tag_id: tagId })
}

// 删除联系人标签
function removeContactTag(profileUuid, tagId) {
  return request(`/contact-tags/contacts/${profileUuid}/tags/${tagId}/`, 'DELETE')
}

// 私信
function sendMessage(targetUuid, content) {
  return request('/profiles/send_message/', 'POST', { target_uuid: targetUuid, content })
}

function getConversations() {
  return request('/profiles/conversations/', 'GET')
}

function getMessages(targetUuid, page = 1) {
  return request(`/profiles/messages_with/?target_uuid=${targetUuid}&page=${page}`)
}

function getMessagesWith(targetUuid, page = 1) {
  return request(`/profiles/messages_with/?target_uuid=${targetUuid}&page=${page}`)
}

function sendPrivateMessage(targetUuid, content) {
  return request('/profiles/send_message/', 'POST', { target_uuid: targetUuid, content })
}

// 统一提取响应数据，处理 DRF 分页和非分页两种格式
// DRF分页: {results: [...], count: N}  -> 返回 results
// 非分页: {code: 0, data: {...}} -> 返回 data
// 两者都不是 -> 返回原始 res
function extractData(res) {
  if (Array.isArray(res)) return res
  if (res.results !== undefined) return res.results
  if (res.data !== undefined) return res.data
  return res
}

// 获取总数（分页响应）
function extractCount(res) {
  if (res.count !== undefined) return res.count
  return null
}

module.exports = {
  request,
  extractData,
  extractCount,
  getSupplies,
  getFeed,
  createSupply,
  deleteSupply,
  getActivities,
  getMyEnrollments,
  getActivityRecommend,
  getActivityDetail,
  getCommunities,
  getCommunityDetail,
  getCommunityMembers,
  getCommunityMessages,
  postCommunityMessage,
  getMySupplies,
  joinCommunity,
  leaveCommunity,
  aiMatch,
  getProfile,
  getMe,
  updateProfile,
  getTags,
  getConnections,
  getFriendRequests,
  sendFriendRequest,
  acceptFriendRequest,
  rejectFriendRequest,
  getSentFriendRequests,
  getContactTags,
  getCards,
  createCard,
  updateCard,
  deleteCard,
  setDefaultCard,
  getContactTagsFor,
  addContactTag,
  removeContactTag,
  sendMessage,
  getConversations,
  getMessages,
  getMessagesWith,
  sendPrivateMessage
}