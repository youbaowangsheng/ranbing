const { getCommunityDetail, getCommunityMembers, getCommunityMessages, postCommunityMessage, joinCommunity, leaveCommunity, getProfile } = require('../../services/api');

Page({
  data: {
    uuid: '',
    community: {},
    activeTab: 'members',
    members: [],
    messages: [],
    postContent: '',
    isJoined: false,
    membersLoading: false,
    msgLoading: false,
    posting: false,
  },

  onLoad(options) {
    const uuid = options.uuid;
    if (!uuid) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      return wx.navigateBack();
    }
    this.setData({ uuid });
    this.loadDetail();
    this.checkJoinStatus();
  },

  loadDetail() {
    getCommunityDetail(this.data.uuid).then(res => {
      const d = res.data || res;
      if (d.code === 0) {
        const c = d.data;
        const typeMap = {1:'行业社群',2:'地域社群',3:'校友群',4:'兴趣社群'};
        c.community_type_name = typeMap[c.community_type] || '社群';
        this.setData({ community: c });
      }
    }).catch(()=>{});
  },

  checkJoinStatus() {
    getCommunityMembers(this.data.uuid).then(res => {
      const d = res.data || res;
      if (d.code === 0) {
        getProfile().then(res => {
          const me = res.data || res;
          const myUuid = me.uuid;
          const members = d.results || d.data || [];
          const found = members.find(m => m.profile.uuid === myUuid);
          this.setData({ isJoined: !!found });
        }).catch(()=>{});
      }
    }).catch(()=>{});
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
    if (tab === 'members') this.loadMembers();
    if (tab === 'messages') this.loadMessages();
  },

  loadMembers() {
    this.setData({ membersLoading: true });
    getCommunityMembers(this.data.uuid).then(res => {
      const d = res.data || res;
      this.setData({ members: d.results || d.data || [], membersLoading: false });
    }).catch(() => this.setData({ membersLoading: false }));
  },

  loadMessages() {
    this.setData({ msgLoading: true });
    getCommunityMessages(this.data.uuid).then(res => {
      const d = res.data || res;
      const msgs = (d.results || d.data || []).map(m => ({
        ...m,
        created_at_fmt: this.fmtTime(m.created_at),
      }));
      this.setData({ messages: msgs, msgLoading: false });
    }).catch(() => this.setData({ msgLoading: false }));
  },

  onContentInput(e) {
    this.setData({ postContent: e.detail.value });
  },

  doPost() {
    const content = this.data.postContent.trim();
    if (!content) return wx.showToast({ title: '内容不能为空', icon: 'none' });
    this.setData({ posting: true });
    postCommunityMessage({ community_uuid: this.data.uuid, content }).then(res => {
      const d = res.data || res;
      this.setData({ posting: false, postContent: '' });
      if (d.code === 0) {
        wx.showToast({ title: '发布成功', icon: 'success' });
        this.setData({ activeTab: 'messages' });
        this.loadMessages();
      } else {
        wx.showToast({ title: d.message || '发布失败', icon: 'none' });
      }
    }).catch(() => this.setData({ posting: false }));
  },

  toggleJoin() {
    const wasJoined = this.data.isJoined;
    const action = wasJoined ? leaveCommunity(this.data.uuid) : joinCommunity(this.data.uuid);
    action.then(res => {
      const d = res.data || res;
      if (d.code === 0) {
        this.setData({ isJoined: !wasJoined });
        wx.showToast({ title: wasJoined ? '已退出' : '已加入', icon: 'success' });
        this.loadDetail();
      } else {
        wx.showToast({ title: d.message || '操作失败', icon: 'none' });
      }
    }).catch(() => wx.showToast({ title: '操作失败', icon: 'none' }));
  },

  viewProfile(e) {
    const uuid = e.currentTarget.dataset.uuid;
    wx.navigateTo({ url: '/pages/profile-view/profile-view?uuid=' + uuid });
  },

  fmtTime(ts) {
    if (!ts) return '';
    const d = new Date(ts);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return '刚刚';
    if (diff < 3600) return Math.floor(diff / 60) + '分钟前';
    if (diff < 86400) return Math.floor(diff / 3600) + '小时前';
    if (diff < 604800) return Math.floor(diff / 86400) + '天前';
    return d.toLocaleDateString('zh-CN');
  },
});