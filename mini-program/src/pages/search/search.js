// pages/search/search.js
const { request, extractData } = require('../../services/api.js')

Page({
  data: {
    q: '',
    hasSearched: false,
    loading: false,
    profiles: [],
    supplies: [],
    activities: [],
    communities: []
  },

  onLoad(options) {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    if (options.q) {
      this.setData({ q: options.q })
      this.doSearch()
    }
  },

  onPullDownRefresh() {
    if (this.data.q) {
      this.doSearch()
    } else {
      wx.stopPullDownRefresh()
    }
  },

  onInput(e) {
    this.setData({ q: e.detail.value })
  },

  doSearch() {
    const q = this.data.q.trim()
    if (!q) return
    this.setData({ loading: true, hasSearched: true })
    this._search(q)
  },

  async _search(q) {
    try {
      const res = await request(`/supplies/search/?q=${encodeURIComponent(q)}`, 'GET')
      const data = extractData(res) || {}

      const profiles = (data.profiles || []).map(p => ({
        ...p,
        avatar_color: this._avatarColor(p.real_name)
      }))

      const supplies = (data.supplies || []).map(s => ({
        ...s,
        tags: s.tag_names || []
      }))

      const activities = (data.activities || []).map(a => ({
        ...a,
        start_time_fmt: a.start_time ? a.start_time.replace('T', ' ').slice(0, 16) : ''
      }))

      const communities = data.communities || []

      this.setData({ profiles, supplies, activities, communities, loading: false })
      wx.stopPullDownRefresh()
    } catch (e) {
      console.error('search error', e)
      this.setData({ loading: false })
      wx.stopPullDownRefresh()
    }
  },

  goBack() { wx.navigateBack() },
  toAiAssistant() { wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' }) },

  toProfile(e) {
    const uuid = e.currentTarget.dataset.uuid
    wx.navigateTo({ url: `/pages/profile-view/profile-view?uuid=${uuid}` })
  },
  toSupply(e) {
    const uuid = e.currentTarget.dataset.uuid
    wx.navigateTo({ url: `/pages/supply-detail/supply-detail?uuid=${uuid}` })
  },
  toActivity(e) {
    const uuid = e.currentTarget.dataset.uuid
    wx.navigateTo({ url: `/pages/activity-detail/activity-detail?uuid=${uuid}` })
  },
  toCommunity(e) {
    const uuid = e.currentTarget.dataset.uuid
    wx.navigateTo({ url: `/pages/community-detail/community-detail?uuid=${uuid}` })
  },

  _avatarColor(name) {
    const colors = ['#1a3a5c', '#e86a3a', '#7c3aed', '#059669', '#dc2626', '#2563eb']
    if (!name) return colors[0]
    const idx = name.charCodeAt(0) % colors.length
    return colors[idx]
  }
})
