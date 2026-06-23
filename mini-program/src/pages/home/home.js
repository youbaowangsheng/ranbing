// pages/home/home.js - 瀑布流首页
const { getMe, getProfile, getSupplies, getActivities, getCommunities } = require('../../services/api.js')

Page({
  data: {
    userInfo: {},
    loggedIn: false,
    items: [],
    leftItems: [],
    rightItems: [],
    page: 1,
    pageSize: 20,
    hasMore: false,
    loading: false,
    loadingMore: false
  },

  onShow() {
    const token = wx.getStorageSync('token')
    this.setData({ loggedIn: !!token })
    this.loadAll()
    if (token) this.loadUserInfo()
  },

  onPullDownRefresh() {
    this.setData({ page: 1, items: [], leftItems: [], rightItems: [], hasMore: true })
    const token = wx.getStorageSync('token')
    if (token) this.loadUserInfo()
    this.loadAll().finally(() => wx.stopPullDownRefresh())
  },

  async loadUserInfo() {
    try {
      const [meRes, profileRes] = await Promise.all([getMe(), getProfile()])
      const me = meRes.data || meRes
      const profile = profileRes.data?.profile || profileRes.data || profileRes
      this.setData({
        userInfo: {
          nickname: me.nickname || profile.real_name || me.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') || '用户',
          company: profile.company || '',
          position: profile.position || ''
        }
      })
    } catch (e) {}
  },

  async loadAll(append = false) {
    if (this.data.loading) return
    this.setData({ loading: !append, loadingMore: append })
    try {
      const [supplyRes, activityRes, communityRes] = await Promise.all([
        getSupplies({ page: this.data.page, page_size: this.data.pageSize }),
        getActivities({ page: this.data.page, page_size: 6 }),
        getCommunities({ page: this.data.page, page_size: 6 })
      ])

      const supplies = Array.isArray(supplyRes) ? supplyRes
        : supplyRes.results || supplyRes.items || []
      const activities = Array.isArray(activityRes) ? activityRes
        : activityRes.results || activityRes.items || []
      const communities = Array.isArray(communityRes) ? communityRes
        : communityRes.results || communityRes.items || []

      const supplyItems = supplies.map(item => ({
        ...item,
        card_type: 'supply',
        avatar_char: item.profile?.real_name ? item.profile.real_name.charAt(0) : '?',
        avatar_color: item.profile?.avatar_color || '#1a3a5c',
        created_at_fmt: item.created_at ? item.created_at.replace('T', ' ').slice(0, 16) : '',
        supply_type: item.supply_type || item.type || 1
      }))

      const activityItems = activities.map(item => ({
        ...item,
        card_type: 'activity',
        attendee_count: item.current_attendees || item.attendee_count || 0,
        start_time_fmt: item.start_time ? item.start_time.replace('T', ' ').slice(0, 16) : '',
        created_at_fmt: item.created_at ? item.created_at.replace('T', ' ').slice(0, 16) : ''
      }))

      const communityItems = communities.map(item => ({
        ...item,
        card_type: 'community',
        created_at_fmt: item.created_at ? item.created_at.replace('T', ' ').slice(0, 16) : ''
      }))

      // 混合所有类型，打散插入两列
      const mixed = [...supplyItems, ...activityItems, ...communityItems]
        .sort(() => Math.random() - 0.5)

      const left = []
      const right = []
      mixed.forEach((item, i) => {
        if (i % 2 === 0) left.push(item)
        else right.push(item)
      })

      this.setData({
        items: append ? [...this.data.items, ...mixed] : mixed,
        leftItems: append ? [...this.data.leftItems, ...left] : left,
        rightItems: append ? [...this.data.rightItems, ...right] : right,
        hasMore: supplyRes.count ? this.data.page * this.data.pageSize < supplyRes.count : false,
        loading: false,
        loadingMore: false
      })
    } catch (e) {
      console.error('loadAll error', e)
      this.setData({ loading: false, loadingMore: false })
    }
  },

  onItemTap(e) {
    const item = e.currentTarget.dataset.item
    if (!item) return
    if (item.card_type === 'supply') {
      wx.navigateTo({ url: `/pages/supply-detail/supply-detail?uuid=${item.uuid}` })
    } else if (item.card_type === 'activity') {
      wx.navigateTo({ url: `/pages/activity-detail/activity-detail?uuid=${item.uuid}` })
    } else if (item.card_type === 'community') {
      wx.navigateTo({ url: `/pages/community-detail/community-detail?uuid=${item.uuid}` })
    }
  },

  toSearch() { wx.navigateTo({ url: '/pages/search/search' }) },

  toAiAssistant() {
    wx.navigateTo({ url: '/pages/ai-assistant/ai-assistant' })
  },

  toPublish() {
    if (!wx.getStorageSync('token')) { wx.navigateTo({ url: '/pages/login/login' }); return }
    wx.navigateTo({ url: '/pages/publish/publish' })
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  loadMore() {
    if (this.data.loadingMore || !this.data.hasMore) return
    this.setData({ page: this.data.page + 1 })
    this.loadAll(true)
  }
})