// pages/community/community.js
const { getCommunities, joinCommunity } = require('../../services/api.js')

Page({
  data: {
    items: [],       // 全部社群，join_status 区分已加入/未加入
    loading: true,
    keyword: ''
  },

  onPullDownRefresh() {
    this.setData({ keyword: '' })
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  onShow() {
    this.loadData()
  },

  onKeywordInput(e) {
    clearTimeout(this._searchTimer)
    this._searchTimer = setTimeout(() => {
      this.setData({ keyword: e.detail.value, loading: true })
      this.loadData()
    }, 400)
  },

  async loadData() {
    this.setData({ loading: true })
    try {
      const params = {}
      if (this.data.keyword) params.search = this.data.keyword
      const res = await getCommunities(params)
      const items = res.results || res.items || []
      this.setData({ items, loading: false })
    } catch (e) {
      console.error('load communities error', e)
      this.setData({ loading: false })
    }
  },

  toDetail(e) {
    wx.navigateTo({ url: `/pages/community-detail/community-detail?uuid=${e.currentTarget.dataset.uuid}` })
  },

  toAiAssistant() { wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' }) },
  toSearch() { wx.navigateTo({ url: '/pages/search/search' }) },

  async joinNow(e) {
    e.stopPropagation()
    const token = wx.getStorageSync('token')
    if (!token) { wx.navigateTo({ url: '/pages/login/login' }); return }
    const uuid = e.currentTarget.dataset.uuid
    try {
      await joinCommunity(uuid)
      wx.showToast({ title: '加入成功', icon: 'success' })
      this.loadData()
    } catch (e) {
      wx.showToast({ title: e.message || '加入失败', icon: 'none' })
    }
  }
})
