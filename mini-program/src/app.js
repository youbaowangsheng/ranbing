// 燃冰小程序 - 入口文件
// 微信小程序凭证
const WX_APPID = 'wx5c3b0ab31ced45fa'
const WX_APPSECRET = process.env.WX_APPSECRET || 'YOUR_WX_APPSECRET_HERE' // TODO: set via environment

App({
  globalData: {
    userInfo: null,
    token: null,
    isLoggedIn: false,
    API_BASE: 'https://www.asiamlhk.com/api/v1',
    APPID: WX_APPID
  },

  onLaunch() {
    const token = wx.getStorageSync('token')
    if (token) {
      this.globalData.token = token
      this.globalData.isLoggedIn = true
    }
  }
})