// pages/my-posts/my-posts.js
const { getMySupplies, deleteSupply } = require('../../services/api.js')

Page({
  data: { items: [], page: 1, pageSize: 20, hasMore: true, loading: false, loadingMore: false },

  onShow() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.navigateTo({ url: '/pages/login/login' }); return }
    this.setData({ page: 1, items: [], hasMore: true })
    this.loadData()
  },

  async loadData(append = false) {
    if (this.data.loading) return
    this.setData({ loading: !append, loadingMore: append })
    try {
      const res = await getMySupplies({ page: this.data.page, page_size: this.data.pageSize })
      const items = res.data || []
      this.setData({ items: append ? [...this.data.items, ...items] : items, hasMore: items.length >= this.data.pageSize, loading: false, loadingMore: false })
    } catch (e) { this.setData({ loading: false, loadingMore: false }) }
  },

  toDetail(e) { wx.navigateTo({ url: `/pages/supply-detail/supply-detail?uuid=${e.currentTarget.dataset.uuid}` }) },
  toEdit(e) { wx.navigateTo({ url: `/pages/publish/publish?uuid=${e.currentTarget.dataset.uuid}` }) },

  confirmDelete(e) {
    wx.showModal({
      title: '确认删除',
      content: '删除后无法恢复，确定要删除吗？',
      success: res => {
        if (res.confirm) this.doDelete(e.currentTarget.dataset.uuid)
      }
    })
  },

  async doDelete(uuid) {
    try {
      await deleteSupply(uuid)
      const items = this.data.items.filter(i => i.uuid !== uuid)
      this.setData({ items })
      wx.showToast({ title: '已删除', icon: 'success' })
    } catch (e) { wx.showToast({ title: '删除失败', icon: 'none' }) }
  },

  loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadData(true)
  },

  goBack() { wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/profile/profile' }) }) }
})