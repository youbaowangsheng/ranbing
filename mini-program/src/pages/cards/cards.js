const { getProfile, extractData } = require('../../services/api.js');

Page({
  data: {
    loading: true,
    profile: null,      // 我的资料
    card: null,         // 名片数据（可能为空）
    avatarChar: '',
    tags: [],
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadAll();
  },

  onShow() {
    // 从资料编辑页返回时刷新
    if (this.data.profile) this.loadAll();
  },

  async loadAll() {
    this.setData({ loading: true });
    try {
      const res = await getProfile();
      const data = extractData(res) || {};
      // /profiles/me/ 返回 {code:0, data:{uuid, real_name, company, ...}}
      const profile = data.profile || data;
      const name = profile.real_name || '';
      const tags = (profile.tags || []).map(t => t.name || t).filter(Boolean);

      this.setData({
        profile,
        avatarChar: name ? name.charAt(0) : '?',
        tags,
        loading: false,
      });
    } catch (e) {
      console.error('[cards] 加载资料失败', e);
      this.setData({ loading: false });
    }
  },

  // 编辑 → 跳转资料编辑页（名片内容就是个人资料）
  editCard() {
    wx.navigateTo({ url: '/pages/profile-edit/profile-edit' });
  },

  goBack() {
    wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/profile/profile' }) });
  },
});
