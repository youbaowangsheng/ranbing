// pages/supply-demand/supply-demand.js
const { getSupplies, extractData } = require('../../services/api.js')

Page({
  data: { items: [], page: 1, pageSize: 20, hasMore: true, loading: false, loadingMore: false, typeTab: 'all', keyword: '' },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], hasMore: true })
    this.loadData().finally(() => wx.stopPullDownRefresh())
  },

  onShow() {
    this.loadData()
  },

  async loadData(append = false) {
    if (this.data.loading) return
    this.setData({ loading: !append, loadingMore: append })
    try {
      const params = { page: this.data.page, page_size: this.data.pageSize }
      if (this.data.typeTab === 'supply') params.type = 1
      if (this.data.typeTab === 'demand') params.type = 2
      if (this.data.keyword) params.search = this.data.keyword
      const res = await getSupplies(params)
      const rawItems = extractData(res) || []
      const items = rawItems.map(item => ({
        ...item,
        avatar_char: item.profile?.real_name ? item.profile.real_name.charAt(0) : '?',
        created_at_fmt: item.created_at ? item.created_at.replace('T', ' ').slice(0, 16) : ''
      }))
      this.setData({ items: append ? [...this.data.items, ...items] : items, hasMore: items.length >= this.data.pageSize, loading: false, loadingMore: false })
    } catch (e) {
      this.setData({ loading: false, loadingMore: false })
    }
  },

  switchType(e) {
    this.setData({ typeTab: e.currentTarget.dataset.tab, page: 1, items: [], hasMore: true })
    this.loadData()
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value, page: 1, items: [], hasMore: true })
    this.loadData()
  },

  toDetail(e) { wx.navigateTo({ url: `/pages/supply-detail/supply-detail?uuid=${e.currentTarget.dataset.uuid}` }) },
  toPublish() {
    if (!wx.getStorageSync('token')) { wx.navigateTo({ url: '/pages/login/login' }); return }
    wx.navigateTo({ url: '/pages/publish/publish' })
  },
  toAiAssistant() { wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' }) },
  toSearch() { wx.navigateTo({ url: '/pages/search/search' }) },
  loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadData(true)
  }
})