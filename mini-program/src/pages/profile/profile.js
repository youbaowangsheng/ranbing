// pages/profile/profile.js
const { getProfile, request } = require('../../services/api.js')

Page({
  data: {
    userInfo: null,
    stats: { supply_count: 0, conn_count: 0, match_count: 0, community_count: 0 }
  },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.navigateTo({ url: '/pages/login/login' }); return }
    const userInfo = wx.getStorageSync('userInfo')
    this.setData({ userInfo: this._prepUser(userInfo) })
    this.loadProfile()
  },

  _prepUser(u) {
    if (!u) return null
    return {
      ...u,
      real_name_first: u.real_name ? u.real_name.slice(0, 1) : '',
      nickname_first: u.nickname ? u.nickname.slice(0, 1) : ''
    }
  },

  async loadProfile() {
    try {
      const res = await getProfile()
      const userInfo = this._prepUser(res.data)
      this.setData({ userInfo })
      wx.setStorageSync('userInfo', res.data)
    } catch (e) {}
    try {
      const res2 = await request('/profiles/me/stats/')
      this.setData({ stats: res2.data || {} })
    } catch (e2) {}
  },

  toMessages() { wx.navigateTo({ url: '/pages/messages/messages' }) },
  toContacts() { wx.navigateTo({ url: '/pages/contacts/contacts' }) },
  toMyConnections() { wx.navigateTo({ url: '/pages/contacts/contacts' }) },
  toMyMatches() { wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' }) },
  toCardTags() { wx.navigateTo({ url: '/pages/contact-tags/contact-tags' }) },
  toMyCards() { wx.navigateTo({ url: '/pages/cards/cards' }) },
  toEditProfile() { wx.navigateTo({ url: '/pages/profile-edit/profile-edit' }) },
  toMyCommunities() { wx.switchTab({ url: '/pages/community/community' }) },
  toActivities() { wx.showToast({ title: '功能开发中', icon: 'none' }) },
  toCert() { wx.showToast({ title: '功能开发中', icon: 'none' }) },
  toSettings() { wx.showToast({ title: '功能开发中', icon: 'none' }) },
  toAiAssistant() { wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' }) },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: res => {
        if (res.confirm) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('refresh_token')
          wx.removeStorageSync('userInfo')
          wx.navigateTo({ url: '/pages/login/login' })
        }
      }
    })
  }
})