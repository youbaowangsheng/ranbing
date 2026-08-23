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
    errorMsg: '',
    agreeProtocol: false
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onCodeInput(e) { this.setData({ smsCode: e.detail.value }) },
  onNicknameInput(e) { this.setData({ nickname: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) },
  onConfirmPwdInput(e) { this.setData({ confirmPwd: e.detail.value }) },

  goBack() { wx.navigateBack() },

  toggleAgree() {
    this.setData({ agreeProtocol: !this.data.agreeProtocol })
  },

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
    if (this._timer) clearInterval(this._timer)
    this._timer = setInterval(() => {
      const c = this.data.countdown - 1
      if (c <= 0) { clearInterval(this._timer); this._timer = null; this.setData({ countdown: 0 }) }
      else this.setData({ countdown: c })
    }, 1000)
  },

  onUnload() {
    if (this._timer) { clearInterval(this._timer); this._timer = null }
  },

  async nextStep() {
    const { phone, smsCode, agreeProtocol } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!smsCode || smsCode.length < 4) { this.setData({ errorMsg: '请输入验证码' }); return }
    if (!agreeProtocol) { this.setData({ errorMsg: '请先阅读并同意《用户协议》和《隐私政策》' }); return }
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
    wx.navigateTo({ url: '/pages/agreement/service' })
  },
  openPrivacy() {
    wx.navigateTo({ url: '/pages/agreement/privacy' })
  },

  backToStep1() { this.setData({ step: 1 }) }
})