// pages/login/register.js
const { sendCode, register } = require('../../services/auth.js')
const { updateProfile } = require('../../services/api.js')

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
    const { phone } = this.data
    if (!phone || phone.length !== 11) {
      this.setData({ errorMsg: '请输入11位手机号' })
      return
    }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '发送中...' })
    try {
      await sendCode(phone, 'register')
      wx.hideLoading()
      this.startCountdown()
      wx.showToast({ title: '验证码已发送', icon: 'success' })
    } catch (e) {
      wx.hideLoading()
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

  async doRegister() {
    const { phone, smsCode, nickname, password, confirmPwd } = this.data
    if (!password || password.length < 6) { this.setData({ errorMsg: '密码至少6位' }); return }
    if (password !== confirmPwd) { this.setData({ errorMsg: '两次密码输入不一致' }); return }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '注册中...' })
    try {
      const res = await register(phone, smsCode, nickname || `用户${phone.slice(-4)}`)
      wx.hideLoading()
      // res = {code: 0, data: {token, user, refresh_token}} from api.js request()
      if (res && res.code === 0 && res.data && res.data.token) {
        const tokenData = res.data
        // 立即设置密码（注册时可能没设）
        if (password) {
          try {
            const { request } = require('../../services/api.js')
            await request('/profiles/me/', 'PUT', { password })
          } catch (e2) { console.warn('setPassword failed', e2) }
        }
        wx.setStorageSync('token', tokenData.token)
        if (tokenData.refresh_token) wx.setStorageSync('refresh_token', tokenData.refresh_token)
        if (tokenData.user) wx.setStorageSync('userInfo', tokenData.user)
        wx.switchTab({ url: '/pages/home/home' })
      } else {
        this.setData({ errorMsg: res && res.message || res && res.data && res.data.message || '注册失败' })
      }
    } catch (e) {
      wx.hideLoading()
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