const { getCommunityDetail, getCommunityMembers, getCommunityMessages, postCommunityMessage, joinCommunity, leaveCommunity, getCommunityMyStatus, extractData } = require('../../services/api.js');

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
    isLogin: false,
  },

  onLoad(options) {
    const uuid = options.uuid;
    if (!uuid) {
      wx.showToast({ title: '参数错误', icon: 'none' });
      return wx.navigateBack();
    }
    this.setData({ uuid })
    this.loadDetail()
    const token = wx.getStorageSync('token')
    this.setData({ isLogin: !!token })
    if (token) this.checkJoinStatus()
  },

  loadDetail() {
    getCommunityDetail(this.data.uuid).then(res => {
      const d = extractData(res);
      if (d && d.uuid) {
        const typeMap = {1:'行业社群',2:'地域社群',3:'校友群',4:'兴趣社群'};
        d.community_type_name = typeMap[d.community_type] || '社群';
        this.setData({ community: d });
      }
    }).catch(()=>{});
  },

  checkJoinStatus() {
    // 用专门的 my_status 接口判断加入状态，避免遍历成员列表
    getCommunityMyStatus(this.data.uuid).then(res => {
      const data = extractData(res) || {};
      this.setData({ isJoined: !!data.joined });
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
      const members = extractData(res) || [];
      this.setData({ members, membersLoading: false });
    }).catch(() => this.setData({ membersLoading: false }));
  },

  loadMessages() {
    this.setData({ msgLoading: true });
    getCommunityMessages(this.data.uuid).then(res => {
      const items = extractData(res) || [];
      const msgs = items.map(m => ({
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
    if (!wx.getStorageSync('token')) { wx.navigateTo({ url: '/pages/login/login' }); return }
    const content = this.data.postContent.trim();
    if (!content) return wx.showToast({ title: '内容不能为空', icon: 'none' });
    this.setData({ posting: true });
    postCommunityMessage({ community_uuid: this.data.uuid, content }).then(res => {
      // 后端返回 {code:0, message:'发布成功，待审核', data:{id:40}}
      // extractData 会剥掉外层，返回内层 {id:40}，所以成功判断要看
      // 原始 res.code 或内层 data.id（不是 uuid）
      const raw = res || {}
      const inner = extractData(res) || {}
      const ok = raw.code === 0 || inner.id || inner.uuid
      this.setData({ posting: false, postContent: '' })
      if (ok) {
        wx.showToast({ title: '发布成功，待审核', icon: 'success' })
        this.setData({ activeTab: 'messages' })
        this.loadMessages()
      } else {
        wx.showToast({ title: raw.message || inner.message || '发布失败', icon: 'none' })
      }
    }).catch((e) => {
      this.setData({ posting: false })
      wx.showToast({ title: (e && e.message) || '发布失败', icon: 'none' })
    });
  },

  toggleJoin() {
    if (!wx.getStorageSync('token')) { wx.navigateTo({ url: '/pages/login/login' }); return }
    const wasJoined = this.data.isJoined;
    const that = this;
    // 退出需要二次确认
    if (wasJoined) {
      wx.showModal({
        title: '退出社群',
        content: '确定要退出该社群吗？',
        success: (r) => {
          if (r.confirm) that._doJoinAction(true);
        }
      });
      return;
    }
    this._doJoinAction(false);
  },

  _doJoinAction(wasJoined) {
    const action = wasJoined ? leaveCommunity(this.data.uuid) : joinCommunity(this.data.uuid);
    action.then(res => {
      // 后端返回 {code:0, message:'加入成功'}，extractData 会剥掉外层；
      // 这里直接看原始 res.code 更明确
      const raw = res || {}
      if (raw.code === 0) {
        this.setData({ isJoined: !wasJoined });
        wx.showToast({ title: wasJoined ? '已退出' : '已加入', icon: 'success' });
        this.loadDetail();
        this.loadMembers();
      } else {
        wx.showToast({ title: raw.message || '操作失败', icon: 'none' });
      }
    }).catch((e) => wx.showToast({ title: (e && e.message) || '操作失败', icon: 'none' }));
  },

  onShareAppMessage() {
    const community = this.data.community || {};
    return {
      title: community.name || '燃冰社群',
      path: `/pages/community-detail/community-detail?uuid=${this.data.uuid}`,
    };
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