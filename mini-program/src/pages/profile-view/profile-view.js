// pages/profile-view/profile-view.js
const { request, getProfile, extractData } = require('../../services/api.js')

Page({
  data: {
    loading: true,
    profile: null,
    myUuid: '',
    is_self: false,
    connected: false,
    avatar_char: '',
    avatar_color: '#1a3a5c'
  },

  onLoad(options) {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this._uuid = options.uuid || ''
    this.loadAll()
  },

  async loadAll() {
    try {
      // Get my profile uuid to check is_self
      const myProfileRes = await getProfile()
      const myProfile = extractData(myProfileRes) || {}
      this._myUuid = myProfile.uuid || ''

      // Get target profile
      const res = await request(`/profiles/${this._uuid}/`, 'GET')
      const profile = extractData(res) || {}

      const avatar_char = profile.real_name ? profile.real_name.charAt(0) : '?'
      const colors = ['#1a3a5c', '#e86a3a', '#7c3aed', '#059669', '#dc2626', '#2563eb']
      const avatar_color = colors[(avatar_char.charCodeAt(0) || 0) % colors.length]

      this.setData({
        profile,
        myUuid: this._myUuid,
        is_self: this._uuid === this._myUuid,
        avatar_char,
        avatar_color,
        loading: false
      })
    } catch (e) {
      console.error('load profile error', e)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  goBack() { wx.navigateBack() },

  async onConnect() {
    if (this.data.connected) return
    try {
      await request('/profiles/connect/', 'POST', { target_uuid: this._uuid, message: '想加你为好友' })
      this.setData({ connected: true })
      wx.showToast({ title: '已发送请求', icon: 'success' })
    } catch (e) {
      wx.showToast({ title: e.message || '连接失败', icon: 'none' })
    }
  },

  onMessage() {
    const profile = this.data.profile
    wx.navigateTo({
      url: `/pages/chat/chat?peer_uuid=${profile.uuid}&peer_name=${profile.real_name}`
    })
  }
})