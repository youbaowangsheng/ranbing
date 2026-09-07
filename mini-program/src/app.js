// 燃冰小程序 - 入口文件
App({
  globalData: {
    userInfo: null,
    token: null,
    isLoggedIn: false,
    API_BASE: 'https://www.asiamlhk.com/api/v1',
    // 自定义导航栏用：状态栏高度 + 胶囊按钮位置/高度
    statusBarHeight: 20,
    menuBtnTop: 24,
    menuBtnHeight: 32,
  },

  onLaunch() {
    // 获取状态栏高度和胶囊按钮位置，供页面自定义导航栏对齐
    try {
      const sysInfo = wx.getSystemInfoSync()
      const menuBtn = wx.getMenuButtonBoundingClientRect()
      this.globalData.statusBarHeight = sysInfo.statusBarHeight || 20
      this.globalData.menuBtnTop = menuBtn.top || 24
      this.globalData.menuBtnHeight = menuBtn.height || 32
    } catch (e) {
      // 兜底默认值
      this.globalData.statusBarHeight = 20
      this.globalData.menuBtnTop = 24
      this.globalData.menuBtnHeight = 32
    }

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