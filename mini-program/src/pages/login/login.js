// pages/login/login.js
const { sendCode, loginByPassword, loginByCode, loginByWechat } = require('../../services/auth.js')

Page({
  data: {
    activeTab: 'password',
    phone: '',
    password: '',
    smsCode: '',
    countdown: 0,
    wechatLoading: false,
    errorMsg: ''
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab, errorMsg: '' })
  },

  onPhoneInput(e) { this.setData({ phone: e.detail.value }) },
  onPasswordInput(e) { this.setData({ password: e.detail.value }) },
  onSmsCodeInput(e) { this.setData({ smsCode: e.detail.value }) },

  // 发送验证码
  async doSendCode() {
    const { phone } = this.data
    if (!phone || phone.length !== 11) {
      this.setData({ errorMsg: '请输入11位手机号' })
      return
    }
    this.setData({ errorMsg: '' })
    try {
      await sendCode(phone, 'login')
      this.startCountdown()
      wx.showToast({ title: '验证码已发送', icon: 'success' })
    } catch (e) {
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

  // 密码登录
  async doPasswordLogin() {
    const { phone, password } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!password) { this.setData({ errorMsg: '请输入密码' }); return }
    this.setData({ errorMsg: '' })
    try {
      const res = await loginByPassword(phone, password)
      if (res.code === 0) this.saveAndRedirect(res.data)
      else this.setData({ errorMsg: res.message || '登录失败' })
    } catch (e) {
      this.setData({ errorMsg: e.message || '登录失败' })
    }
  },

  // 短信登录
  async doSmsLogin() {
    const { phone, smsCode } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!smsCode || smsCode.length < 4) { this.setData({ errorMsg: '请输入验证码' }); return }
    this.setData({ errorMsg: '' })
    try {
      const res = await loginByCode(phone, smsCode)
      if (res.code === 0) this.saveAndRedirect(res.data)
      else this.setData({ errorMsg: res.message || '登录失败' })
    } catch (e) {
      this.setData({ errorMsg: e.message || '登录失败' })
    }
  },

  // 微信登录
  async doWechatLogin() {
    this.setData({ wechatLoading: true, errorMsg: '' })
    try {
      const res = await loginByWechat()
      this.setData({ wechatLoading: false })
      if (res.code === 0) {
        this.saveAndRedirect(res.data)
      } else {
        this.setData({ errorMsg: res.message || '微信登录失败' })
      }
    } catch (e) {
      this.setData({ wechatLoading: false, errorMsg: '微信登录失败，请稍后重试' })
    }
  },

  saveAndRedirect(data) {
    wx.setStorageSync('token', data.token)
    if (data.refresh_token) wx.setStorageSync('refresh_token', data.refresh_token)
    if (data.user) wx.setStorageSync('userInfo', data.user)
    wx.switchTab({ url: '/pages/home/home' })
  },

  toRegister() {
    wx.navigateTo({ url: '/pages/login/register' })
  }
})