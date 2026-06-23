// pages/messages/messages.js
const { getConversations, extractData } = require('../../services/api.js')

Page({
  data: {
    loading: true,
    conversations: []
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadConversations()
  },

  onShow() {
    this.loadConversations()
  },

  async loadConversations() {
    this.setData({ loading: true })
    try {
      const res = await getConversations()
      // getConversations returns {code:0, data:[...]} which api.js unwraps to {code:0, data:[...]}
      // So res here is the unwrapped response = {code:0, data:[...]}
      const list = extractData(res) || []
      const conversations = list.map(item => {
        const avatar_char = (item.peer_name || '匿名').charAt(0)
        const time_ago = this.computeTimeAgo(item.last_message_time)
        return {
          peer_uuid: item.peer_uuid,
          peer_name: item.peer_name || '匿名',
          avatar_char,
          avatar_color: '#1a3a5c',
          last_message: item.last_message || '',
          last_message_time: item.last_message_time || '',
          time_ago,
          unread_count: item.unread_count || 0
        }
      })
      this.setData({ conversations, loading: false })
    } catch (e) {
      console.error('加载私信列表失败', e)
      this.setData({ loading: false })
    }
  },

  toChat(e) {
    const { peer, name } = e.currentTarget.dataset
    wx.navigateTo({ url: `/pages/chat/chat?peer_uuid=${peer}&peer_name=${encodeURIComponent(name)}` })
  },

  goBack() {
    wx.navigateBack()
  },

  computeTimeAgo(timeStr) {
    if (!timeStr) return ''
    const diff = Date.now() - new Date(timeStr).getTime()
    if (diff < 60000) return '刚刚'
    if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
    if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
    return Math.floor(diff / 86400000) + '天前'
  }
})