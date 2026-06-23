const { getConnections, getFriendRequests, acceptFriendRequest, rejectFriendRequest, extractData } = require('../../services/api.js');

Page({
  data: {
    activeTab: 'friends',
    loading: false,
    items: [],
    requests: [],
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadFriends();
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    if (tab === 'friends') {
      this.loadFriends();
    } else {
      this.loadRequests();
    }
  },

  loadFriends() {
    this.setData({ loading: true });
    getConnections().then(res => {
      const list = extractData(res) || [];
      const items = list.map(c => ({
        uuid: c.other_profile && c.other_profile.uuid ? c.other_profile.uuid : c.uuid || '',
        real_name: c.other_profile && c.other_profile.real_name ? c.other_profile.real_name : (c.real_name || '未知'),
        company: c.other_profile && c.other_profile.company ? c.other_profile.company : (c.company || ''),
        position: c.other_profile && c.other_profile.position ? c.other_profile.position : (c.position || ''),
        initials: this.initials((c.other_profile && c.other_profile.real_name) || c.real_name || '未知'),
      }));
      this.setData({ items, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  loadRequests() {
    this.setData({ loading: true });
    getFriendRequests().then(res => {
      const list = extractData(res) || [];
      const requests = list.map(r => {
        const fp = r.from_profile || {};
        return {
          uuid: r.uuid,
          from_profile: {
            uuid: fp.uuid || '',
            real_name: fp.real_name || '未知',
            company: fp.company || '',
            position: fp.position || '',
            initials: this.initials(fp.real_name || '未知'),
          },
          message: r.message || '',
          status: r.status || 1,
          statusText: ['', '待接受', '已接受', '已拒绝', '已过期'][r.status] || '未知',
        };
      });
      this.setData({ requests, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  initials(name) {
    if (!name) return '?';
    const chars = name.trim().split('');
    return (chars[0] || '?') + (chars[1] || '');
  },

  viewProfile(e) {
    const uuid = e.currentTarget.dataset.uuid;
    if (uuid) wx.navigateTo({ url: '/pages/profile-view/profile-view?uuid=' + uuid });
  },

  accept(e) {
    const uuid = e.currentTarget.dataset.uuid;
    acceptFriendRequest(uuid).then(() => {
      wx.showToast({ title: '已添加', icon: 'success' });
      this.loadRequests();
      this.loadFriends();
    }).catch(() => wx.showToast({ title: '操作失败', icon: 'none' }));
  },

  reject(e) {
    const uuid = e.currentTarget.dataset.uuid;
    rejectFriendRequest(uuid).then(() => {
      wx.showToast({ title: '已拒绝', icon: 'success' });
      this.loadRequests();
    }).catch(() => wx.showToast({ title: '操作失败', icon: 'none' }));
  },

  goBack() {
    wx.navigateBack();
  },
});