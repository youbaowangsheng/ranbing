const { getContactTags, getContactTagsFor, addContactTag, removeContactTag, request } = require('../../services/api.js');

Page({
  data: {
    profileUuid: '',
    allTags: [],
    myTagIds: [],
    loading: false,
  },

  onLoad(options) {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.setData({ profileUuid: options.profile_uuid || '' });
    this.loadAllTags();
    if (options.profile_uuid) {
      this.loadMyTagIds(options.profile_uuid);
    }
  },

  loadAllTags() {
    this.setData({ loading: true });
    getContactTags().then(res => {
      const code = res.data && res.data.code !== undefined ? res.data.code : (res.code !== undefined ? res.code : 0);
      const list = code === 0 ? (res.data.data || []) : [];
      const tags = list.map(t => ({ id: t.id, name: t.name, selected: false }));
      this.setData({ allTags: tags, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  loadMyTagIds(profileUuid) {
    getContactTagsFor(profileUuid).then(res => {
      const code = res.data && res.data.code !== undefined ? res.data.code : (res.code !== undefined ? res.code : 0);
      const list = code === 0 ? (res.data.data || []) : [];
      const myTagIds = list.map(t => t.id);
      const allTags = this.data.allTags.map(t => ({
        ...t,
        selected: myTagIds.indexOf(t.id) >= 0,
      }));
      this.setData({ allTags, myTagIds });
    });
  },

  toggleTag(e) {
    const id = e.currentTarget.dataset.id;
    const allTags = this.data.allTags.map(t => {
      if (t.id === id) {
        return { ...t, selected: !t.selected };
      }
      return t;
    });
    this.setData({ allTags });
  },

  addTag() {
    wx.showModal({
      title: '新建标签',
      inputs: [{ name: 'tag', placeholder: '标签名称' }],
      success: res => {
        if (res.confirm && res.value && res.value.tag) {
          request('/contact-tags/', 'POST', { name: res.value.tag })
            .then(() => {
              wx.showToast({ title: '标签已创建', icon: 'success' });
              this.loadAllTags();
            })
            .catch(() => wx.showToast({ title: '创建失败', icon: 'none' }));
        }
      },
    });
  },

  saveTags() {
    const { profileUuid, allTags } = this.data;
    const selectedIds = allTags.filter(t => t.selected).map(t => t.id);
    const promises = [];
    const allTagsAll = allTags;

    // Add new selections
    for (const id of selectedIds) {
      if (this.data.myTagIds.indexOf(id) < 0 && profileUuid) {
        promises.push(addContactTag(profileUuid, id));
      }
    }
    // Remove unselections
    for (const id of this.data.myTagIds) {
      if (selectedIds.indexOf(id) < 0 && profileUuid) {
        promises.push(removeContactTag(profileUuid, id));
      }
    }
    Promise.all(promises).then(() => {
      wx.showToast({ title: '已保存', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1000);
    }).catch(() => {
      wx.showToast({ title: '保存失败', icon: 'none' });
    });
  },

  goBack() {
    wx.navigateBack();
  },
});