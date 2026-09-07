// pages/ai-assistant/ai-assistant.js - AI对话助手
const { request } = require('../../services/api.js')

Page({
  data: {
    messages: [],
    inputText: '',
    matchResults: [],
    quickQuestions: ['找投资', '找客户', '找渠道资源', '找技术合伙人', '找专家人脉', '消费行业机会'],
    aiTyping: false,
    scrollTop: 0,
    isLogin: false,
  },

  onLoad(query) {
    const token = wx.getStorageSync('token')
    this.setData({ isLogin: !!token })
    this.fromPage = query.from || ''
    // 初始欢迎语
    this.setData({
      messages: [{
        id: 'welcome',
        role: 'ai',
        content: '你好！我是燃冰AI助手。你可以问我任何问题，比如"帮我找消费行业的投资机会"或"有哪些技术合作的供需"。\n\n⚠ 内容由 AI 生成，仅供参考'
      }]
    })
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  async sendMessage() {
    const text = this.data.inputText.trim()
    if (!text || this.data.aiTyping) return
    if (!this.data.isLogin) { wx.navigateTo({ url: '/pages/login/login' }); return }

    this.setData({ inputText: '', aiTyping: true, matchResults: [] })
    this._appendMessage('user', text)

    try {
      // AI 对话生成慢，放宽超时到 60 秒
      const res = await request('/ai/chat/', 'POST', { message: text }, { timeout: 60000 })
      this.setData({ aiTyping: false })
      // 兼容：不用可选链 ?.，改用 && 短路，避免低版本基础库编译问题
      const content = res && res.data && res.data.content
      if (res && res.code === 0 && content) {
        this._appendMessage('ai', content)
      } else {
        const fallback = (res && res.message) || '抱歉，AI暂时无法回复，请稍后重试'
        this._appendMessage('ai', fallback)
      }
    } catch (e) {
      console.error('AI 请求失败', e)
      this.setData({ aiTyping: false })
      this._appendMessage('ai', '网络连接失败，请检查网络后重试')
    }
  },

  _appendMessage(role, content) {
    // 每条消息带唯一 id，供 wx:key 使用
    const messages = [...this.data.messages, { id: Date.now() + '_' + Math.random(), role, content }]
    // scrollTop 直接设一个足够大的值滚到底部，避免累加导致视图滚出内容区显示空白
    this.setData({ messages, scrollTop: 99999 })
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