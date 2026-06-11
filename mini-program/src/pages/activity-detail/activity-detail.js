// pages/activity-detail/activity-detail.js
const { getActivityDetail, request } = require('../../services/api.js')

Page({
  data: { item: null, loading: true, joined: false, uuid: '', joined_count: 0 },
  onLoad(opts) {
    this.setData({ uuid: opts.uuid })
    this.loadDetail()
  },
  async loadDetail() {
    try {
      const res = await getActivityDetail(this.data.uuid)
      const item = res.data
      this.setData({ item, loading: false, joined_count: item.current_attendees || 0 })
    } catch (e) { this.setData({ loading: false }) }
  },
  async joinActivity() {
    try {
      await request(`/activities/${this.data.uuid}/enroll/`, 'POST')
      this.setData({ joined: true, joined_count: (this.data.joined_count || 0) + 1 })
      wx.showToast({ title: '报名成功', icon: 'success' })
    } catch (e) { wx.showToast({ title: '报名失败', icon: 'none' }) }
  },
  goBack() { wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/home/home' }) }) }
})