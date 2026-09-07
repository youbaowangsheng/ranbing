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
    this.fromPage = (query && query.from) || ''
    // 初始欢迎语
    const welcome = [{
      id: 'welcome',
      role: 'ai',
      content: '你好！我是燃冰AI助手。你可以问我任何问题，比如"帮我找消费行业的投资机会"或"有哪些技术合作的供需"。\n\n⚠ 内容由 AI 生成，仅供参考'
    }]
    this.setData({ messages: welcome })
    console.log('[onLoad] messages 初始化完成，长度:', welcome.length)
  },

  onShow() {
    // 兜底：如果 messages 意外为空，重新补欢迎语（避免 data 被清空后无内容）
    if (!this.data.messages || this.data.messages.length === 0) {
      this.setData({ messages: [{
        id: 'welcome',
        role: 'ai',
        content: '你好！我是燃冰AI助手。\n\n⚠ 内容由 AI 生成，仅供参考'
      }] })
    }
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
      console.log('[sendMessage] await 返回:', res, '| 类型:', typeof res)
      this.setData({ aiTyping: false })
      // 兼容：不用可选链 ?.，改用 && 短路，避免低版本基础库编译问题
      const content = res && res.data && res.data.content
      console.log('[sendMessage] content:', content ? content.slice(0, 50) : content)
      if (res && res.code === 0 && content) {
        this._appendMessage('ai', content)
      } else {
        const fallback = (res && res.message) || '抱歉，AI暂时无法回复，请稍后重试'
        this._appendMessage('ai', fallback)
      }
    } catch (e) {
      console.error('[sendMessage] 异常', e)
      this.setData({ aiTyping: false })
      this._appendMessage('ai', '网络连接失败，请检查网络后重试')
    }
  },

  _appendMessage(role, content) {
    // 用 concat 避免展开运算符对 undefined 的兼容问题，并确保 data.messages 是数组
    const current = Array.isArray(this.data.messages) ? this.data.messages : []
    const messages = current.concat([{ id: Date.now() + '_' + Math.random(), role, content }])
    console.log('[_appendMessage] 当前 messages 长度:', messages.length, '| role:', role)
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