// 燃冰小程序 - 入口文件
App({
  globalData: {
    userInfo: null,
    token: null,
    isLoggedIn: false,
    API_BASE: 'https://www.asiamlhk.com/api/v1'
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      this.globalData.isLoggedIn = true
    }
  },

  // 全局错误兜底，避免白屏
  onError(err) {
    console.error('[AppError]', err)
  },
  // 未捕获的 Promise 拒绝
  onUnhandledRejection(err) {
    console.error('[AppRejection]', err && (err.reason || err.message || err))
  },
  // 找不到页面时回首页
  onPageNotFound(res) {
    console.warn('[PageNotFound]', res)
    wx.switchTab({ url: '/pages/home/home' })
  }
})