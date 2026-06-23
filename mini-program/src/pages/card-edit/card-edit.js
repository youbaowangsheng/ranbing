const { createCard, updateCard, setDefaultCard } = require('../../services/api.js');

Page({
  data: {
    isEdit: false,
    cardUuid: '',
    form: {
      name: '',
      company: '',
      position: '',
      phone: '',
      wechat: '',
      email: '',
      bio: '',
      tags: '',
      is_default: false,
    },
  },

  onLoad(options) {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    if (options.card) {
      try {
        const card = JSON.parse(decodeURIComponent(options.card));
        this.setData({
          isEdit: true,
          cardUuid: card.uuid,
          form: {
            name: card.name || '',
            company: card.company || '',
            position: card.position || '',
            phone: card.phone || '',
            wechat: card.wechat || '',
            email: card.email || '',
            bio: card.bio || '',
            tags: Array.isArray(card.tags) ? card.tags.join(',') : '',
            is_default: !!card.is_default,
          },
        });
      } catch (e) {}
    }
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ ['form.' + field]: e.detail.value });
  },

  onSwitch(e) {
    this.setData({ ['form.is_default']: e.detail.value });
  },

  doSubmit() {
    const { form, isEdit, cardUuid } = this.data;
    const data = {
      name: form.name,
      company: form.company,
      position: form.position,
      phone: form.phone,
      wechat: form.wechat,
      email: form.email,
      bio: form.bio,
      tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      is_default: form.is_default,
    };

    (isEdit ? updateCard(cardUuid, data) : createCard(data)).then(res => {
      // 成功后端返回 {'code': 0, 'message': '更新成功'} 或 {'code': 0, 'data': {...}}
      if (res.code === 0 || (res.data && res.data.code === 0)) {
        wx.showToast({ title: isEdit ? '已保存' : '已创建', icon: 'success' });
        setTimeout(() => wx.navigateBack(), 1000);
      } else {
        wx.showToast({ title: res.message || res.data?.message || '操作失败', icon: 'none' });
      }
    }).catch(() => {
      wx.showToast({ title: '操作失败', icon: 'none' });
    });
  },

  goBack() {
    wx.navigateBack();
  },
});