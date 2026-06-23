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
  }
})