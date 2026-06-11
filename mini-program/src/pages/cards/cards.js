const { getCards, deleteCard } = require('../../services/api.js');

Page({
  data: {
    loading: false,
    cards: [],
  },

  onLoad() {
    this.loadCards();
  },

  loadCards() {
    this.setData({ loading: true });
    getCards().then(res => {
      const code = res.data && res.data.code !== undefined ? res.data.code : (res.code !== undefined ? res.code : 0);
      const cards = code === 0 ? (res.data.data || []) : [];
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