// pages/supply-detail/supply-detail.js
const api = require('../../services/api.js')
Page({
  data: { item: null, loading: true, uuid: '' },
  onLoad(opts) { this.setData({ uuid: opts.uuid }); this.loadDetail() },
  async loadDetail() {
    try {
      const res = await api.request(`/supplies/${this.data.uuid}/`)
      const item = res.data || res
      if (item && item.profile) {
        item.avatar_char = item.profile.real_name ? item.profile.real_name.charAt(0) : '?'
      }
      this.setData({ item, loading: false })
    } catch (e) { this.setData({ loading: false }) }
  },
  connectUser() {
    // 直接跳转私信聊天页
    const profile = this.data.item && this.data.item.profile
    if (!profile) { wx.showToast({ title: '无法获取联系人', icon: 'none' }); return }
    if (profile.user === wx.getStorageSync('userInfo').id) {
      wx.showToast({ title: '不能给自己发私信', icon: 'none' }); return
    }
    const peer_name = profile.real_name || profile.nickname || 'Ta'
    wx.navigateTo({
      url: `/pages/chat/chat?peer_uuid=${profile.uuid}&peer_name=${encodeURIComponent(peer_name)}`
    })
  }
})