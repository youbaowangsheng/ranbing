// pages/publish/publish.js
const { createSupply, getTags } = require('../../services/api.js')

Page({
  data: {
    supplyType: 1,
    tags: [],
    selectedTags: [],
    title: '',
    content: '',
    images: [],       // 最多9张，存本地临时路径
    uploadingImages: false,
    errorMsg: ''
  },

  onLoad() {
    const token = wx.getStorageSync('token')
    if (!token) { wx.redirectTo({ url: '/pages/landing/landing' }); return }
    this.loadTags()
  },

  async loadTags() {
    try {
      const res = await getTags()
      // 后端 /tags/ 返回扁平数组 [{id, name, l1_category, tag_type}, ...]
      const list = Array.isArray(res) ? res : (res.results || res.data || [])
      // 每个标签自带 selected 状态：WXML 不支持数组方法调用（如 includes），
      // 必须在 JS 里算好。
      const tags = list
        .filter(t => t && t.id != null)
        .map(t => ({ id: t.id, name: t.name, selected: false }))
      this.setData({ tags })
    } catch (e) {
      console.error('[publish] 标签加载失败', e)
    }
  },

  selectType(e) {
    this.setData({ supplyType: parseInt(e.currentTarget.dataset.type) })
  },

  toggleTag(e) {
    // 用索引定位（比 data-id 更可靠，避免取不到值）
    const idx = Number(e.currentTarget.dataset.idx)
    const tags = (this.data.tags || []).slice()
    if (!tags[idx]) return
    tags[idx] = { ...tags[idx], selected: !tags[idx].selected }
    this.setData({
      tags,
      selectedTags: tags.filter(t => t.selected).map(t => t.id),
    })
  },

  onTitleInput(e) { this.setData({ title: e.detail.value }) },
  onContentInput(e) { this.setData({ content: e.detail.value }) },

  // 选择图片，最多9张
  chooseImages() {
    const remain = 9 - this.data.images.length
    if (remain <= 0) {
      wx.showToast({ title: '最多9张图片', icon: 'none' })
      return
    }
    wx.chooseMedia({
      count: remain,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: res => {
        const newPaths = res.tempFiles.map(f => f.tempFilePath)
        this.setData({ images: [...this.data.images, ...newPaths].slice(0, 9) })
      }
    })
  },

  // 删除已选图片
  removeImage(e) {
    const idx = e.currentTarget.dataset.idx
    const arr = this.data.images
    arr.splice(idx, 1)
    this.setData({ images: arr })
  },

  goBack() { wx.navigateBack({ fail: () => wx.switchTab({ url: '/pages/home/home' }) }) },

  // 上传单张图片，返回 URL
  uploadImage(tempFilePath) {
    return new Promise((resolve, reject) => {
      const token = wx.getStorageSync('token')
      wx.uploadFile({
        url: 'https://www.asiamlhk.com/api/v1/upload/image/',
        filePath: tempFilePath,
        name: 'file',
        header: { 'Authorization': token ? `Bearer ${token}` : '' },
        success: res => {
          try {
            const data = JSON.parse(res.data)
            if (data.url || data.data?.url) {
              resolve(data.url || data.data.url)
            } else {
              reject(new Error(data.message || '上传失败'))
            }
          } catch (e) {
            reject(new Error('上传响应解析失败'))
          }
        },
        fail: err => reject(new Error(err.errMsg || '上传失败'))
      })
    })
  },

  async submit() {
    const { supplyType, selectedTags, title, content, images } = this.data
    if (!title.trim()) { this.setData({ errorMsg: '请填写标题' }); return }
    if (!content.trim()) { this.setData({ errorMsg: '请填写详细内容' }); return }
    this.setData({ errorMsg: '' })

    wx.showLoading({ title: '发布中...', mask: true })

    try {
      // 先上传图片，获取 URLs
      let imageUrls = []
      if (images.length > 0) {
        this.setData({ uploadingImages: true })
        wx.showLoading({ title: '上传图片中...', mask: true })
        const results = await Promise.all(
          images.map(p => this.uploadImage(p).then(url => ({ ok: true, url })).catch(err => ({ ok: false, err })))
        )
        this.setData({ uploadingImages: false })
        const failed = results.filter(r => !r.ok)
        imageUrls = results.filter(r => r.ok).map(r => r.url)

        // 图片全部失败时明确告知，避免"以为发了其实没发"
        if (failed.length === images.length) {
          wx.hideLoading()
          const reason = (failed[0].err && failed[0].err.message) || '未知原因'
          this.setData({ errorMsg: `图片上传失败（${reason}），可去掉图片后直接发布` })
          return
        }
        if (failed.length > 0) {
          wx.showToast({ title: `${failed.length} 张图片上传失败，已跳过`, icon: 'none' })
        }
      }

      wx.showLoading({ title: '发布中...', mask: true })
      // tags 兜底过滤：剔除 null/undefined/非数字，避免后端返回
      // "该字段不能为 null" 的 400
      const safeTags = (selectedTags || [])
        .map(t => Number(t))
        .filter(t => Number.isInteger(t) && t > 0)

      const payload = {
        supply_type: supplyType,
        title: title.trim(),
        content: content.trim(),
        tags: safeTags,
        images: imageUrls  // 提交上传后的 URL 数组
      }
      const res = await createSupply(payload)
      wx.hideLoading()

      if (res && res.uuid) {
        // 跳「我的发布」而非首页：首页只显示已审核通过的内容，
        // 新发布的是待审核状态，跳首页会让用户以为发布失败
        wx.showToast({ title: '发布成功，待审核', icon: 'success' })
        setTimeout(() => wx.navigateTo({ url: '/pages/my-posts/my-posts' }), 1500)
      } else {
        // 后端返回但无 uuid：透传后端 message
        this.setData({ errorMsg: (res && res.message) || '发布失败，请稍后重试' })
      }
    } catch (e) {
      wx.hideLoading()
      this.setData({ uploadingImages: false, errorMsg: (e && e.message) || '网络异常，请稍后重试' })
    }
  }
})
