// pages/activity/activity.js
const { getActivities, getMyEnrollments, getProfile, extractData } = require('../../services/api.js')
const { generateJSON } = require('../../services/ai.js')

Page({
  data: {
    activeTab: 'recommend',
    activeCat: '全部',
    loggedIn: false,
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
    loadingMore: false,
    statusBarHeight: 20,
    menuBtnTop: 24,
    menuBtnHeight: 32,
  },

  onLoad() {
    const app = getApp()
    this.setData({
      statusBarHeight: app.globalData.statusBarHeight || 20,
      menuBtnTop: app.globalData.menuBtnTop || 24,
      menuBtnHeight: app.globalData.menuBtnHeight || 32,
    })
  },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], hasMore: true, aiItem: null })
    Promise.all([this.loadData(), this.loadAiRecommend()])
      .finally(() => wx.stopPullDownRefresh())
  },

  onShow() {
    const token = wx.getStorageSync('token')
    this.setData({ loggedIn: !!token })
    this.loadData()
    if (token) this.loadAiRecommend()
  },

  // AI 精选：拉候选活动 → 混元挑最相关的一个并给理由
  async loadAiRecommend() {
    this.setData({ aiLoading: true })
    try {
      const [actRes, profileRes] = await Promise.all([
        getActivities({ page: 1, page_size: 10 }),
        getProfile().catch(() => null),
      ])

      let acts = actRes.results || actRes.items || (typeof actRes.count === 'number' ? [] : actRes) || []
      acts = acts.map(item => ({
        ...item,
        attendee_count: item.current_attendees || 0,
        start_time_fmt: item.start_time ? item.start_time.replace('T', ' ').slice(0, 16) : ''
      }))

      if (!acts.length) {
        this.setData({ aiItem: null, aiLoading: false })
        return
      }

      const p = extractData(profileRes) || {}
      const profileText = [p.real_name, p.company, p.position, p.industry, p.city]
        .filter(Boolean).join('，') || '商务人士'
      const list = acts.map((a, i) => `${i}. ${a.title}（${a.location || ''}）`).join('\n')
      const prompt = (
        `用户背景：${profileText}\n\n可选活动：\n${list}\n\n`
        + '请选出与该用户最相关的一个活动，只返回 JSON：'
        + '{"index": 序号, "reason": "30字以内的推荐理由", "pct": 匹配度0到100的整数}'
      )

      const parsed = await generateJSON(
        [{ role: 'user', content: prompt }],
        { maxTokens: 200, temperature: 0.5 }
      )

      const idx = parsed && Number.isInteger(parsed.index) && acts[parsed.index] ? parsed.index : 0
      const item = { ...acts[idx] }
      item.match_reason = (parsed && parsed.reason) || '根据您的行业背景为您推荐'
      item.pct = (parsed && parsed.pct) || 75

      this.setData({ aiItem: item, aiLoading: false })
    } catch (e) {
      console.error('[AI精选] 失败', e)
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
    if (e.currentTarget.dataset.tab === 'mine' && !wx.getStorageSync('token')) {
      wx.navigateTo({ url: '/pages/login/login' })
      return
    }
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
