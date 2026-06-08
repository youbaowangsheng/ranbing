// pages/activity/activity.js
const { getActivities, getActivityRecommend, getMyEnrollments } = require('../../services/api.js')

Page({
  data: {
    activeTab: 'recommend',
    activeCat: '全部',
    // activity_type: 1=沙龙 2=路演 3=培训班 4=社交聚会 5=线上讲座
    categories: ['全部', '沙龙', '路演', '培训班', '社交聚会', '线上讲座'],
    catMap: { '全部': 0, '沙龙': 1, '路演': 2, '培训班': 3, '社交聚会': 4, '线上讲座': 5 },
    keyword: '',
    aiItem: null,
    aiLoading: false,
    items: [],
    page: 1,
    pageSize: 20,
    hasMore: true,
    loading: false,
    loadingMore: false
  },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], hasMore: true, aiItem: null })
    Promise.all([this.loadData(), this.loadAiRecommend()])
      .finally(() => wx.stopPullDownRefresh())
  },

  onShow() {
    this.loadAiRecommend()
    this.loadData()
  },

  async loadAiRecommend() {
    this.setData({ aiLoading: true })
    try {
      const res = await getActivityRecommend()
      const ai = res.data
      if (ai) {
        ai.start_time_fmt = ai.start_time ? ai.start_time.replace('T', ' ').slice(0, 16) : ''
      }
      this.setData({ aiItem: ai, aiLoading: false })
    } catch (e) {
      this.setData({ aiItem: null, aiLoading: false })
    }
  },

  async loadData(append = false) {
    if (this.data.loading) return
    this.setData({ loading: !append, loadingMore: append })
    try {
      let res
      if (this.data.activeTab === 'mine') {
        // 我报名的活动，调用专用接口
        res = await getMyEnrollments()
        const rawItems = Array.isArray(res) ? res : (res.data || [])
        const items = rawItems.map(item => ({
          ...item,
          attendee_count: item.current_attendees || 0,
          start_time_fmt: item.start_time ? item.start_time.replace('T', ' ').slice(0, 16) : ''
        }))
        this.setData({ items, hasMore: false, loading: false, loadingMore: false })
        return
      }
      const params = { page: this.data.page, page_size: this.data.pageSize }
      if (this.data.activeTab === 'upcoming') params.status = 1
      if (this.data.activeTab === 'past') params.status = 2
      const catVal = this.data.catMap[this.data.activeCat] || 0
      if (catVal > 0) params.type = catVal
      if (this.data.keyword) params.search = this.data.keyword
      res = await getActivities(params)
      const rawItems = res.results || res.items || (typeof res.count === 'number' ? [] : res) || []
      const items = rawItems.map(item => ({
        ...item,
        attendee_count: item.current_attendees || 0,
        start_time_fmt: item.start_time ? item.start_time.replace('T', ' ').slice(0, 16) : ''
      }))
      this.setData({
        items: append ? [...this.data.items, ...items] : items,
        hasMore: items.length >= this.data.pageSize,
        loading: false,
        loadingMore: false
      })
    } catch (e) {
      this.setData({ loading: false, loadingMore: false })
    }
  },

  toAiAssistant() {
    wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' })
  },
  toSearch() {
    wx.navigateTo({ url: '/pages/search/search' })
  },

  switchTab(e) {
    this.setData({
      activeTab: e.currentTarget.dataset.tab,
      page: 1,
      items: [],
      hasMore: true,
      activeCat: '全部'   // 切到非mine tab时重置分类
    })
    this.loadData()
  },

  selectCat(e) {
    this.setData({ activeCat: e.currentTarget.dataset.cat, page: 1, items: [], hasMore: true })
    this.loadData()
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value, page: 1, items: [], hasMore: true })
    this.loadData()
  },

  toDetail(e) { wx.navigateTo({ url: `/pages/activity-detail/activity-detail?uuid=${e.currentTarget.dataset.uuid}` }) },
  toPublish() { wx.navigateTo({ url: '/pages/publish/publish' }) },
  loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadData(true)
  }
})
