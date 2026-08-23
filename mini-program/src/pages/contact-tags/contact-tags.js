const { getContactTags, getContactTagsFor, addContactTag, removeContactTag, request, extractData } = require('../../services/api.js');

Page({
  data: {
    profileUuid: '',
    allTags: [],
    myTagIds: [],
    loading: false,
    saving: false,  // 防连点
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
      const list = extractData(res) || [];
      const tags = list.map(t => ({ id: t.id, name: t.name, selected: false }));
      this.setData({ allTags: tags, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  loadMyTagIds(profileUuid) {
    getContactTagsFor(profileUuid).then(res => {
      const list = extractData(res) || [];
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
    if (this.data.saving) return  // 防连点
    wx.showModal({
      title: '新建标签',
      inputs: [{ name: 'tag', placeholder: '标签名称' }],
      success: res => {
        if (res.confirm && res.value && res.value.tag) {
          this.setData({ saving: true })
          request('/contact-tags/', 'POST', { name: res.value.tag })
            .then(() => {
              wx.showToast({ title: '标签已创建', icon: 'success' });
              this.loadAllTags();
            })
            .catch(() => wx.showToast({ title: '创建失败', icon: 'none' }))
            .finally(() => this.setData({ saving: false }));
        }
      },
    });
  },

  saveTags() {
    if (this.data.saving) return
    this.setData({ saving: true })
    const { profileUuid, allTags } = this.data;
    const selectedIds = allTags.filter(t => t.selected).map(t => t.id);
    const promises = [];

    for (const id of selectedIds) {
      if (this.data.myTagIds.indexOf(id) < 0 && profileUuid) {
        promises.push(addContactTag(profileUuid, id));
      }
    }
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
    }).finally(() => this.setData({ saving: false }));
  },

  goBack() {
    wx.navigateBack();
  },
});