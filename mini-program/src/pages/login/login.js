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

  async doSendCode() {
    const { phone } = this.data
    if (!phone || phone.length !== 11) {
      this.setData({ errorMsg: '请输入11位手机号' })
      return
    }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '发送中...' })
    try {
      await sendCode(phone, 'login')
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

  async doPasswordLogin() {
    const { phone, password } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!password) { this.setData({ errorMsg: '请输入密码' }); return }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '登录中...' })
    try {
      const res = await loginByPassword(phone, password)
      wx.hideLoading()
      // res = {code: 0, data: {token, user, refresh_token}} from api.js request()
      if (res && res.code === 0 && res.data && res.data.token) {
        this.saveAndRedirect(res.data)
      } else {
        this.setData({ errorMsg: res && res.message || res && res.data && res.data.message || '登录失败，请稍后重试' })
      }
    } catch (e) {
      wx.hideLoading()
      this.setData({ errorMsg: e.message || '网络错误，请检查网络后重试' })
    }
  },

  async doSmsLogin() {
    const { phone, smsCode } = this.data
    if (!phone || phone.length !== 11) { this.setData({ errorMsg: '请输入11位手机号' }); return }
    if (!smsCode || smsCode.length < 4) { this.setData({ errorMsg: '请输入验证码' }); return }
    this.setData({ errorMsg: '' })
    wx.showLoading({ title: '登录中...' })
    try {
      const res = await loginByCode(phone, smsCode)
      wx.hideLoading()
      if (res && res.code === 0 && res.data && res.data.token) {
        this.saveAndRedirect(res.data)
      } else {
        this.setData({ errorMsg: res && res.message || res && res.data && res.data.message || '登录失败，请稍后重试' })
      }
    } catch (e) {
      wx.hideLoading()
      this.setData({ errorMsg: e.message || '网络错误，请检查网络后重试' })
    }
  },

  async doWechatLogin() {
    this.setData({ wechatLoading: true, errorMsg: '' })
    try {
      const res = await loginByWechat()
      this.setData({ wechatLoading: false })
      if (res && res.code === 0 && res.data && res.data.token) {
        this.saveAndRedirect(res.data)
      } else {
        this.setData({ errorMsg: res && res.message || '微信登录失败' })
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