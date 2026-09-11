// 燃冰小程序 - 入口文件

// 云开发环境 ID（在微信开发者工具 → 云开发 中查看，形如 'ranbing-xxxxx'）
// 留空则使用默认环境；建议显式填写，避免多环境时串号
const CLOUD_ENV_ID = ''

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
    // 初始化云开发（AI 能力走云开发混元，需基础库 >= 3.15.1）
    if (!wx.cloud) {
      console.error('[Cloud] 当前基础库不支持云开发，请升级到 3.15.1 及以上')
    } else {
      try {
        wx.cloud.init({
          env: CLOUD_ENV_ID || undefined,
          traceUser: true,
        })
      } catch (e) {
        console.error('[Cloud] 初始化失败', e)
      }
    }

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