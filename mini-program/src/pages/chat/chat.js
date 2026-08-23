// pages/chat/chat.js - 私信聊天
const { getMessagesWith, sendPrivateMessage, extractData } = require('../../services/api.js')

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
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
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
      const res = await getMessagesWith(this.data.peer_uuid, this.data.page)
      const msgs = (extractData(res) || []).map(item => ({
        id: item.uuid,
        content: item.content,
        is_mine: item.is_mine,
        created_at: item.created_at
      }))
      // 假设服务端按 created_at DESC 返回（最新在前）：
      //   page=1 → 取最新，反转成时间正序，并滚到底部
      //   page>1 → 取更早的页，反转后追加到列表末尾（更早的在最底部）
      const ordered = msgs.reverse()
      const messages = this.data.page === 1
        ? ordered
        : [...this.data.messages, ...ordered]
      this.setData({
        messages,
        hasMore: msgs.length >= 20,
        loadingMore: false,
        scrollTop: this.data.page === 1 ? 99999 : this.data.scrollTop
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
      await sendPrivateMessage(this.data.peer_uuid, content)
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