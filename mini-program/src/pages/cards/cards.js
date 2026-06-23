const { getCards, deleteCard } = require('../../services/api.js');

Page({
  data: {
    loading: false,
    cards: [],
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadCards();
  },

  loadCards() {
    this.setData({ loading: true });
    getCards().then(res => {
      // /cards/me/ 返回单张名片 {code:0, data:{uuid,...}}
      // 如果 data 是对象而非数组，则包装成数组
      let cards = [];
      if (res.data && typeof res.data === 'object' && !Array.isArray(res.data)) {
        if (res.data.uuid) {
          cards = [res.data];
        }
      } else if (Array.isArray(res.data)) {
        cards = res.data;
      } else if (Array.isArray(res)) {
        cards = res;
      }
      this.setData({ cards, loading: false });
    }).catch(() => this.setData({ loading: false }));
  },

  createCard() {
    wx.navigateTo({ url: '/pages/card-edit/card-edit' });
  },

  editCard(e) {
    const card = e.currentTarget.dataset.card;
    const str = encodeURIComponent(JSON.stringify(card));
    wx.navigateTo({ url: '/pages/card-edit/card-edit?card=' + str });
  },

  deleteCard(e) {
    const uuid = e.currentTarget.dataset.uuid;
    wx.showModal({
      title: '确认删除',
      content: '确定要删除这张名片吗？',
      success: res => {
        if (res.confirm) {
          deleteCard(uuid).then(() => {
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadCards();
          }).catch(() => wx.showToast({ title: '删除失败', icon: 'none' }));
        }
      },
    });
  },

  goBack() {
    wx.navigateBack();
  },
});