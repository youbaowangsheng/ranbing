// 认证服务
const WX_APPID = 'wx5c3b0ab31ced45fa'
const WX_APPSECRET = 'b8a595334354f2291c51551d485a1ed1'
const API_BASE = 'https://www.asiamlhk.com/api/v1'

function request(path, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    const token = wx.getStorageSync('token')
    if (token) header['Authorization'] = `Bearer ${token}`
    wx.request({
      url: API_BASE + path,
      method,
      data,
      header,
      timeout: 15000,
      success: res => {
        if ((res.statusCode === 200 || res.statusCode === 201) && res.data) {
          resolve(res.data)
        } else if (res.statusCode === 401) {
          wx.removeStorageSync('token')
          wx.removeStorageSync('userInfo')
          wx.navigateTo({ url: '/pages/login/login' })
          reject(new Error('未登录'))
        } else {
          const errMsg = res.data && (res.data.message || (res.data.errors && JSON.stringify(res.data.errors)) || (res.data.detail) || res.statusCode)
          console.error('[请求失败]', path, res.statusCode, res.data)
          reject(new Error(errMsg || '请求失败'))
        }
      },
      fail: err => reject(new Error(err.errMsg || '网络错误'))
    })
  })
}

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