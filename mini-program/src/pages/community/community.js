// pages/community/community.js
const { getCommunities, joinCommunity } = require('../../services/api.js')

Page({
  data: {
    items: [],       // 社群列表，join_status 区分已加入/未加入
    loading: true,
    keyword: '',
    activeTab: 'all', // all=全部 / joined=我加入的
    statusBarHeight: 20,
    menuBtnTop: 24,
    menuBtnHeight: 32,
  },

  onLoad(options) {
    const app = getApp()
    this.setData({
      statusBarHeight: app.globalData.statusBarHeight || 20,
      menuBtnTop: app.globalData.menuBtnTop || 24,
      menuBtnHeight: app.globalData.menuBtnHeight || 32,
    })
    // 从「我的-我的社群」进入：profile 页用 storage 传 tab=joined
    // （switchTab 不支持带参数，只能用 storage 中转）
    const wanted = (options && options.tab) || wx.getStorageSync('community_tab')
    if (wanted === 'joined') {
      this.setData({ activeTab: 'joined' })
      wx.removeStorageSync('community_tab')  // 用完即清
    }
  },

  onPullDownRefresh() {
    this.setData({ keyword: '' })
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  onShow() {
    this.loadData()
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab
    if (tab === this.data.activeTab) return
    this.setData({ activeTab: tab, items: [], loading: true })
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
      if (this.data.activeTab === 'joined') params.joined = 1
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
    // 注意：async 函数中 `e` 是 asyncGenerator step 对象，不是 DOM 事件
    // 防冒泡通过 WXML 中的 `catchtap` 实现，不需要 stopPropagation
    const token = wx.getStorageSync('token')
    if (!token) { wx.navigateTo({ url: '/pages/login/login' }); return }
    const uuid = (e && e.currentTarget && e.currentTarget.dataset) ? e.currentTarget.dataset.uuid : null
    // 容错：如果 e 是 step 对象，尝试从 dataset 拿
    if (!uuid) {
      // 没办法从事件拿 uuid，放弃
      wx.showToast({ title: '参数错误', icon: 'none' })
      return
    }
    try {
      await joinCommunity(uuid)
      wx.showToast({ title: '加入成功', icon: 'success' })
      this.loadData()
    } catch (err) {
      wx.showToast({ title: err.message || '加入失败', icon: 'none' })
    }
  }
})
