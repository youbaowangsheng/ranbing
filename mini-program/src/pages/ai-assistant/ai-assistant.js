// pages/ai-assistant/ai-assistant.js - AI对话助手
const { request } = require('../../services/api.js')

Page({
  data: {
    messages: [],
    inputText: '',
    matchResults: [],
    quickQuestions: ['找投资', '找客户', '找渠道资源', '找技术合伙人', '找专家人脉', '消费行业机会'],
    aiTyping: false,
    scrollTop: 0
  },

  onLoad(query) {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.fromPage = query.from || ''
    // 初始欢迎语
    this.setData({
      messages: [{
        role: 'ai',
        content: '你好！我是燃冰AI助手。你可以问我任何问题，比如"帮我找消费行业的投资机会"或"有哪些技术合作的供需"'
      }]
    })
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  async sendMessage() {
    const text = this.data.inputText.trim()
    if (!text || this.data.aiTyping) return

    this.setData({ inputText: '', aiTyping: true, matchResults: [] })
    this._appendMessage('user', text)

    try {
      const res = await request('/ai/chat/', 'POST', { message: text })
      this.setData({ aiTyping: false })
      if (res.code === 0 && res.data?.content) {
        this._appendMessage('ai', res.data.content)
      } else {
        this._appendMessage('ai', res.message || '抱歉，AI暂时无法回复，请稍后重试')
      }
    } catch (e) {
      this.setData({ aiTyping: false })
      this._appendMessage('ai', '网络连接失败，请检查网络后重试')
    }
  },

  _appendMessage(role, content) {
    const messages = [...this.data.messages, { role, content }]
    this.setData({ messages, scrollTop: this.data.scrollTop + 1000 })
  },

  quickAsk(e) {
    const q = e.currentTarget.dataset.q
    this.setData({ inputText: q })
    setTimeout(() => this.sendMessage(), 50)
  },

  goBack() {
    wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/home/home' }) })
  },

  toDetail(e) {
    wx.navigateTo({ url: `/pages/supply-detail/supply-detail?uuid=${e.currentTarget.dataset.uuid}` })
  }
})