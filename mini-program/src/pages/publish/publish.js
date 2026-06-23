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
      const cats = res.data?.categories || []
      const allTags = []
      cats.forEach(cat => {
        if (cat.l2_groups) {
          cat.l2_groups.forEach(g => {
            if (g.l3_items) allTags.push(...g.l3_items)
          })
        }
      })
      this.setData({ tags: allTags })
    } catch (e) {}
  },

  selectType(e) {
    this.setData({ supplyType: parseInt(e.currentTarget.dataset.type) })
  },

  toggleTag(e) {
    const id = e.currentTarget.dataset.id
    const arr = this.data.selectedTags
    const idx = arr.indexOf(id)
    if (idx >= 0) arr.splice(idx, 1)
    else arr.push(id)
    this.setData({ selectedTags: arr })
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

    wx.showLoading({ title: '发布中...' })

    try {
      // 先上传图片，获取 URLs
      let imageUrls = []
      if (images.length > 0) {
        this.setData({ uploadingImages: true })
        imageUrls = await Promise.all(images.map(p => this.uploadImage(p).catch(() => null)))
        imageUrls = imageUrls.filter(Boolean)
        this.setData({ uploadingImages: false })
      }

      const payload = {
        supply_type: supplyType,
        title: title.trim(),
        content: content.trim(),
        tags: selectedTags,
        images: imageUrls  // 提交上传后的 URL 数组
      }
      const res = await createSupply(payload)
      wx.hideLoading()
      // createSupply returns res.data (unwrapped by api.js), so check res directly
      if (res && res.uuid) {
        wx.showToast({ title: '发布成功', icon: 'success' })
        setTimeout(() => wx.switchTab({ url: '/pages/supply-demand/supply-demand' }), 1500)
      } else {
        this.setData({ errorMsg: res && res.message || '发布失败' })
      }
    } catch (e) {
      wx.hideLoading()
      this.setData({ uploadingImages: false, errorMsg: e.message || '网络错误，请稍后重试' })
    }
  }
})
