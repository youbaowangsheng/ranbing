// pages/activity-detail/activity-detail.js
const { getActivityDetail, enrollActivity, unenrollActivity, getMyEnrollmentStatus, extractData } = require('../../services/api.js')

Page({
  data: { item: null, loading: true, joined: false, uuid: '', joined_count: 0, isLogin: false },
  onLoad(opts) {
    const isLogin = !!wx.getStorageSync('token')
    this.setData({ uuid: opts.uuid, isLogin })
    this.loadDetail()
    if (isLogin) this.checkEnrollment()
  },
  async loadDetail() {
    try {
      const res = await getActivityDetail(this.data.uuid)
      const item = extractData(res) || res || null
      this.setData({ item, loading: false, joined_count: item && item.current_attendees ? item.current_attendees : 0 })
    } catch (e) { this.setData({ loading: false }) }
  },
  async checkEnrollment() {
    try {
      const res = await getMyEnrollmentStatus(this.data.uuid)
      const data = extractData(res) || res || {}
      this.setData({ joined: !!data.enrolled })
    } catch (e) { /* 忽略，保持默认未报名 */ }
  },
  async joinActivity() {
    if (!wx.getStorageSync('token')) { wx.navigateTo({ url: '/pages/login/login' }); return }
    try {
      await enrollActivity(this.data.uuid)
      this.setData({ joined: true, joined_count: (this.data.joined_count || 0) + 1 })
      wx.showToast({ title: '报名成功', icon: 'success' })
    } catch (e) {
      const msg = (e && e.message) || '报名失败'
      wx.showToast({ title: msg, icon: 'none' })
    }
  },
  async cancelActivity() {
    const that = this
    wx.showModal({
      title: '取消报名',
      content: '确定要取消报名该活动吗？',
      success: async (res) => {
        if (!res.confirm) return
        try {
          await unenrollActivity(that.data.uuid)
          that.setData({ joined: false, joined_count: Math.max(0, (that.data.joined_count || 0) - 1) })
          wx.showToast({ title: '已取消报名', icon: 'success' })
        } catch (e) {
          wx.showToast({ title: (e && e.message) || '取消失败', icon: 'none' })
        }
      }
    })
  },
  onShareAppMessage() {
    const item = this.data.item || {}
    return {
      title: item.title || '燃冰活动',
      path: `/pages/activity-detail/activity-detail?uuid=${this.data.uuid}`,
    }
  },
  goBack() { wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/home/home' }) }) }
})
