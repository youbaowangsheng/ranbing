// pages/chat/chat.js - 私信聊天
const api = require('../../services/api.js')

Page({
  data: {
    peer_uuid: '',
    peer_name: '聊天',
    messages: [],
    inputText: '',
    page: 1,
    hasMore: true,
    loadingMore: false,
    scrollTop: 0
  },

  onLoad(options) {
    const { peer_uuid, peer_name } = options
    this.setData({
      peer_uuid: peer_uuid || '',
      peer_name: peer_name ? decodeURIComponent(peer_name) : '聊天'
    })
    if (peer_uuid) this.loadMessages()
  },

  async loadMessages() {
    this.setData({ loadingMore: true })
    try {
      const res = await api.getMessagesWith(this.data.peer_uuid, this.data.page)
      const msgs = (res.data || []).map(item => ({
        id: item.uuid,
        content: item.content,
        is_mine: item.is_mine,
        created_at: item.created_at
      }))
      // 分页：第1页是最新的，需要反转显示
      const allMsgs = this.data.page === 1 ? msgs.reverse() : [...msgs.reverse(), ...this.data.messages]
      this.setData({
        messages: allMsgs,
        hasMore: msgs.length >= 20,
        loadingMore: false,
        scrollTop: this.data.page === 1 ? 1 : this.data.scrollTop
      })
    } catch (e) {
      console.error('加载消息失败', e)
      this.setData({ loadingMore: false })
    }
  },

  loadMore() {
    if (!this.data.hasMore || this.data.loadingMore) return
    this.setData({ page: this.data.page + 1 }, () => this.loadMessages())
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  async send() {
    const content = this.data.inputText.trim()
    if (!content) return
    this.setData({ inputText: '', loadingMore: false })
    try {
      await api.sendPrivateMessage(this.data.peer_uuid, content)
      // 发完后直接加一条本地消息
      const newMsg = { id: Date.now(), content, is_mine: true, created_at: new Date().toISOString() }
      this.setData({ messages: [...this.data.messages, newMsg], page: 1 })
      wx.pageScrollTo({ scrollTop: 99999 })
    } catch (e) {
      console.error('发送失败', e)
      wx.showToast({ title: '发送失败', icon: 'none' })
    }
  },

  goBack() {
    wx.navigateBack()
  }
})