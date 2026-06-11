// pages/login/register.js
const { sendCode, register, loginByPassword } = require('../../services/auth.js')

Page({
  data: {
    step: 1,
    phone: '',
    smsCode: '',
    nickname: '',
    password: '',
    confirmPwd: '',
    countdown: 0,
    errorMsg: ''
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onCodeInput(e) { this.setData({ smsCode: e.detail.value }) },
  onNicknameInput(e) { this.setData({ nickname: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) },
  onConfirmPwdInput(e) { this.setData({ confirmPwd: e.detail.value }) },

  goBack() { wx.navigateBack() },

  async sendCode() {
    console.log('[register] sendCode called, phone:', this.data.phone)
    const { phone } = this.data
    if (!phone || phone.length !== 11) {
      this.setData({ errorMsg: '请输入11位手机号' })
      return
    }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '发送中...' })
    try {
      const res = await sendCode(phone, 'register')
      wx.hideLoading()
      console.log('[register] sendCode resp:', res)
      this.startCountdown()
      wx.showToast({ title: '验证码已发送', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
      console.error('[register] sendCode error:', e)
      this.setData({ errorMsg: e.message || '发送失败' })
    }
  },

  startCountdown() {
    this.setData({ countdown: 60 })
    const t = setInterval(() => {
      const c = this.data.countdown - 1
      if (c <= 0) { clearInterval(t); this.setData({ countdown: 0 }) }
      else this.setData({ countdown: c })
    }, 1000)
  },

  async nextStep() {
    const { phone, smsCode } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!smsCode || smsCode.length < 4) { this.setData({ errorMsg: '请输入验证码' }); return }
    this.setData({ errorMsg: '' })
    this.setData({ step: 2 })
  },

  async setPassword(password) {
    const token = wx.getStorageSync('token')
    if (!token) return
    return new Promise((resolve, reject) => {
      wx.request({
        url: 'https://www.asiamlhk.com/api/v1/profiles/me/',
        method: 'PUT',
        data: { password },
        header: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        success: res => resolve(res.data),
        fail: reject
      })
    })
  },

  async doRegister() {
    const { phone, smsCode, nickname, password, confirmPwd } = this.data
    if (!password || password.length < 6) { this.setData({ errorMsg: '密码至少6位' }); return }
    if (password !== confirmPwd) { this.setData({ errorMsg: '两次密码输入不一致' }); return }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '注册中...' })
    try {
      const res = await register(phone, smsCode, nickname || phone.slice(-4))
      wx.hideLoading()
      console.log('[register] doRegister resp:', res)
      if (res.code === 0) {
        // 立即设置密码
        try {
          await this.setPassword(password)
        } catch (e2) { console.error('setPassword failed', e2) }
        wx.setStorageSync('token', res.data.token)
        if (res.data.refresh_token) wx.setStorageSync('refresh_token', res.data.refresh_token)
        wx.setStorageSync('userInfo', res.data.user)
        wx.switchTab({ url: '/pages/home/home' })
      } else {
        this.setData({ errorMsg: res.message || '注册失败' })
      }
    } catch (e) {
      wx.hideLoading()
      console.error('[register] doRegister error:', e)
      this.setData({ errorMsg: e.message || '网络错误，请稍后重试' })
    }
  },

  openProtocol() {
    wx.showModal({
      title: '用户协议',
      content: '燃烧吧用户协议：用户在使用本平台服务时，需遵守相关法律法规，不得发布违法、违规内容。平台对用户发布的内容不承担法律责任。',
      showCancel: false,
      confirmText: '我已知晓'
    })
  },
  openPrivacy() {
    wx.showModal({
      title: '隐私政策',
      content: '燃烧吧隐私政策：我们收集您的手机号、设备信息等用于账号安全和个性化服务。未经您同意，我们不会向第三方披露您的个人信息。',
      showCancel: false,
      confirmText: '我已知晓'
    })
  },

  backToStep1() { this.setData({ step: 1 }) }
})