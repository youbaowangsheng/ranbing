// pages/landing/landing.js
Page({
  data: {},

  onShow() {
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/home/home' })
    }
  },

  toLogin() {
    wx.navigateTo({ url: '/pages/login/login' })
  },

  toRegister() {
    wx.navigateTo({ url: '/pages/login/register' })
  },

  toActivities() {
    wx.switchTab({ url: '/pages/activity/activity' })
  },

  toCommunities() {
    wx.switchTab({ url: '/pages/community/community' })
  }
})
