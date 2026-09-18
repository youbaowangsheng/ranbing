const { getContactTags, request, extractData } = require('../../services/api.js');

Page({
  data: {
    tags: [],        // 我的联系人标签 [{id, name}]
    loading: false,
    saving: false,   // 防连点
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadTags();
  },

  loadTags() {
    this.setData({ loading: true });
    getContactTags().then(res => {
      // 后端返回 {code:0, data:[{id, name, created_at}]}
      const list = extractData(res) || [];
      const tags = list.map(t => ({ id: t.id, name: t.name }));
      this.setData({ tags, loading: false });
    }).catch((e) => {
      console.error('[contact-tags] 加载失败', e);
      this.setData({ loading: false });
    });
  },

  // 新建标签
  addTag() {
    if (this.data.saving) return;
    wx.showModal({
      title: '新建标签',
      editable: true,
      placeholderText: '输入标签名称，如：投资人',
      success: res => {
        if (!res.confirm) return;
        const name = (res.content || '').trim();
        if (!name) {
          wx.showToast({ title: '名称不能为空', icon: 'none' });
          return;
        }
        this.setData({ saving: true });
        request('/contact-tags/', 'POST', { name })
          .then(() => {
            wx.showToast({ title: '标签已创建', icon: 'success' });
            this.loadTags();
          })
          .catch((e) => wx.showToast({ title: (e && e.message) || '创建失败', icon: 'none' }))
          .finally(() => this.setData({ saving: false }));
      },
    });
  },

  // 长按删除标签
  deleteTag(e) {
    const { id, name } = e.currentTarget.dataset;
    wx.showModal({
      title: '删除标签',
      content: `确定删除「${name}」吗？`,
      success: res => {
        if (!res.confirm) return;
        request(`/contact-tags/${id}/`, 'DELETE')
          .then(() => {
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadTags();
          })
          .catch(() => wx.showToast({ title: '删除失败', icon: 'none' }));
      },
    });
  },

  goBack() {
    wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/profile/profile' }) });
  },
});
