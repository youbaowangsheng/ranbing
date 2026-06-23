// 认证服务
const { request } = require('./api')

function loginByWechat() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: res => {
        if (!res.code) { reject(new Error('微信code获取失败')); return }
        request('/auth/wx_login/', 'POST', { code: res.code })
          .then(resolve)
          .catch(err => reject(new Error(err.message || '微信登录失败')))
      },
      fail: err => reject(new Error(err.errMsg || '微信登录失败'))
    })
  })
}

function sendCode(phone, type) {
  return request('/auth/send_code/', 'POST', { phone, type })
}

function loginByPassword(phone, password) {
  return request('/auth/login/', 'POST', { phone, password })
}

function loginByCode(phone, code) {
  return request('/auth/login/', 'POST', { phone, code })
}

function register(phone, code, nickname) {
  return request('/auth/register/', 'POST', { phone, code, nickname })
}

function refreshToken() {
  const t = wx.getStorageSync('refresh_token')
  if (!t) return Promise.reject(new Error('无refresh_token'))
  return request('/auth/refresh/', 'POST', { refresh_token: t })
}

function getProfile() {
  return request('/me/', 'GET')
}

function logout() {
  wx.removeStorageSync('token')
  wx.removeStorageSync('refresh_token')
  wx.removeStorageSync('userInfo')
  wx.reLaunch({ url: '/pages/login/login' })
}

module.exports = {
  sendCode, loginByPassword, loginByCode, loginByWechat,
  register, refreshToken, getProfile, logout
}