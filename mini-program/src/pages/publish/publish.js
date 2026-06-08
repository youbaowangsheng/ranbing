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
    errorMsg: ''
  },

  onLoad() {
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

  async submit() {
    const { supplyType, selectedTags, title, content, images } = this.data
    if (!title.trim()) { this.setData({ errorMsg: '请填写标题' }); return }
    if (!content.trim()) { this.setData({ errorMsg: '请填写详细内容' }); return }
    this.setData({ errorMsg: '' })

    wx.showLoading({ title: '发布中...' })

    try {
      const payload = {
        supply_type: supplyType,
        title: title.trim(),
        content: content.trim(),
        tags: selectedTags,
        images: images  // 提交时传本地路径数组，后端只存储URL字符串
      }
      const res = await createSupply(payload)
      wx.hideLoading()
      if (res.code === 0) {
        wx.showToast({ title: '发布成功', icon: 'success' })
        setTimeout(() => wx.switchTab({ url: '/pages/supply-demand/supply-demand' }), 1500)
      } else {
        this.setData({ errorMsg: res.message || '发布失败' })
      }
    } catch (e) {
      wx.hideLoading()
      this.setData({ errorMsg: '网络错误，请稍后重试' })
    }
  }
})
