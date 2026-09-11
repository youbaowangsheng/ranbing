// pages/ai-assistant/ai-assistant.js - AI对话助手
const { getProfile, extractData } = require('../../services/api.js')
const { generateText } = require('../../services/ai.js')

// 系统提示语：引导简洁、直接、商务风格的回复
const SYSTEM_PROMPT = (
  '你是「燃冰」AI商务助手，服务商务社交、供需对接、人脉连接场景。'
  + '回复要求：'
  + '1. 简洁直接，开门见山，不要客套寒暄；'
  + '2. 商务风格，专业务实，多用短句和要点；'
  + '3. 控制在 300 字以内，重点突出，不展开无关细节；'
  + '4. 如涉及资源/人脉推荐，给出具体可执行的建议或方向即可。'
)

Page({
  data: {
    messages: [],
    inputText: '',
    matchResults: [],
    quickQuestions: ['找投资', '找客户', '找渠道资源', '找技术合伙人', '找专家人脉', '消费行业机会'],
    aiTyping: false,
    scrollIntoViewId: '',
    isLogin: false,
  },

  onLoad(query) {
    const token = wx.getStorageSync('token')
    this.setData({ isLogin: !!token })
    this.fromPage = (query && query.from) || ''
    // 初始欢迎语
    this.setData({
      messages: [{
        id: 'welcome',
        role: 'ai',
        content: '你好！我是燃冰AI助手。你可以问我任何问题，比如"帮我找消费行业的投资机会"或"有哪些技术合作的供需"。\n\n⚠ 内容由 AI 生成，仅供参考'
      }]
    })
  },

  onShow() {
    // 兜底：如果 messages 意外为空，重新补欢迎语
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
      // 用户背景（姓名/公司/职位/标签）拼进 prompt，让回复更贴合
      const userContext = await this._buildUserContext()
      const content = await generateText([
        { role: 'system', content: SYSTEM_PROMPT },
        { role: 'user', content: text + userContext },
      ], { maxTokens: 600, temperature: 0.5 })

      this.setData({ aiTyping: false })
      this._appendMessage('ai', content)
    } catch (e) {
      console.error('AI 请求失败', e)
      this.setData({ aiTyping: false })
      this._appendMessage('ai', 'AI 服务暂时不可用，请稍后重试')
    }
  },

  // 拉取当前用户资料，拼成 [用户背景] 文本；失败则返回空串
  async _buildUserContext() {
    try {
      const res = await getProfile()
      const p = extractData(res) || {}
      const parts = []
      if (p.real_name) parts.push(`姓名：${p.real_name}`)
      if (p.company) parts.push(`公司：${p.company}`)
      if (p.position) parts.push(`职位：${p.position}`)
      if (p.industry) parts.push(`行业：${p.industry}`)
      if (p.city) parts.push(`城市：${p.city}`)
      if (!parts.length) return ''
      return `\n\n[用户背景] ${parts.join('，')}。`
    } catch (e) {
      return ''
    }
  },

  _appendMessage(role, content) {
    // 用 concat 避免展开运算符对 undefined 的兼容问题，并确保 data.messages 是数组
    const current = Array.isArray(this.data.messages) ? this.data.messages : []
    const id = Date.now() + '_' + Math.random()
    const messages = current.concat([{ id, role, content }])
    // 用 scroll-into-view 定位到最新消息，避免 scroll-top 固定大值导致滚出可视区
    this.setData({ messages, scrollIntoViewId: 'msg-' + id })
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