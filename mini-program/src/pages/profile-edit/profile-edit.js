// pages/profile-edit/profile-edit.js
const { getProfile, updateProfile, getTags } = require('../../services/api.js')

Page({
  data: {
    loading: true,
    formData: {},
    allTags: [],
    selectedTagIds: [],
    sections: [
      {
        name: '基本信息',
        icon: '👤',
        fields: [
          { key: 'real_name', label: '姓名', type: 'text', required: true, placeholder: '请输入真实姓名' },
          { key: 'city', label: '城市', type: 'text', placeholder: '如：北京、上海' },
          { key: 'industry', label: '行业', type: 'select', placeholder: '请选择行业', options: [] }
        ]
      },
      {
        name: '职业信息',
        icon: '💼',
        fields: [
          { key: 'company', label: '公司', type: 'text', placeholder: '当前任职公司' },
          { key: 'position', label: '职位', type: 'text', placeholder: '当前职位' },
          { key: 'education_school', label: '学校', type: 'text', placeholder: '毕业院校' },
          { key: 'education_year', label: '届数', type: 'text', placeholder: '如：2018' }
        ]
      },
      {
        name: '个人简介',
        icon: '✍️',
        fields: [
          { key: 'bio', label: '简介', type: 'textarea', placeholder: '简单介绍一下自己…', maxlength: 200 }
        ]
      }
    ]
  },

  onLoad() {
    this.loadAll()
  },

  async loadAll() {
    try {
      const [profileRes, tagsRes] = await Promise.all([getProfile(), getTags()])
      const profile = profileRes.data?.profile || profileRes.data || {}

      // Build industry options
      const industryOptions = [
        { label: '请选择行业', value: '' },
        { label: '互联网/IT', value: '互联网/IT' },
        { label: '金融', value: '金融' },
        { label: '教育', value: '教育' },
        { label: '医疗健康', value: '医疗健康' },
        { label: '制造/生产', value: '制造/生产' },
        { label: '房地产/建筑', value: '房地产/建筑' },
        { label: '零售/消费', value: '零售/消费' },
        { label: '媒体/广告', value: '媒体/广告' },
        { label: '政府/非营利', value: '政府/非营利' },
        { label: '其他', value: '其他' }
      ]

      const allTags = (tagsRes.results || tagsRes || []).map(t => ({ ...t, selected: false }))

      this.setData({
        loading: false,
        formData: {
          real_name: profile.real_name || '',
          city: profile.city || '',
          industry: profile.industry || '',
          company: profile.company || '',
          position: profile.position || '',
          education_school: profile.education_school || '',
          education_year: profile.education_year || '',
          bio: profile.bio || ''
        },
        allTags,
        sections: this.data.sections.map(s => ({
          ...s,
          fields: s.fields.map(f =>
            f.key === 'industry' ? { ...f, options: industryOptions, value: profile.industry || '' } : f
          )
        }))
      })
    } catch (e) {
      console.error('load profile error', e)
      this.setData({ loading: false })
      wx.showToast({ title: '加载失败', icon: 'none' })
    }
  },

  onFieldInput(e) {
    const key = e.currentTarget.dataset.key
    this.setData({ [`formData.${key}`]: e.detail.value })
  },

  onSelectChange(e) {
    const key = e.currentTarget.dataset.key
    const options = this.data.sections.find(s => s.fields.some(f => f.key === key))?.fields.find(f => f.key === key)?.options || []
    const value = options[e.detail.value]?.value || ''
    this.setData({ [`formData.${key}`]: value })
  },

  toggleTag(e) {
    const id = e.currentTarget.dataset.id
    const allTags = this.data.allTags.map(t =>
      t.id === id ? { ...t, selected: !t.selected } : t
    )
    const selectedTagIds = allTags.filter(t => t.selected).map(t => t.id)
    if (selectedTagIds.length > 10) {
      wx.showToast({ title: '最多选择10个标签', icon: 'none' })
      return
    }
    this.setData({ allTags, selectedTagIds })
  },

  goBack() { wx.navigateBack() },

  async doSave() {
    const fd = this.data.formData
    if (!fd.real_name?.trim()) {
      wx.showToast({ title: '请填写姓名', icon: 'none' })
      return
    }
    try {
      await updateProfile({
        real_name: fd.real_name,
        city: fd.city || '',
        industry: fd.industry || '',
        company: fd.company || '',
        position: fd.position || '',
        education_school: fd.education_school || '',
        education_year: fd.education_year || '',
        bio: fd.bio || ''
      })

      // Update tags separately
      if (this.data.selectedTagIds.length > 0) {
        const { request } = require('../../services/api.js')
        await request('/profiles/update_tags/', 'POST', {
          tags: this.data.selectedTagIds.map(id => ({ id, tag_type: 1 }))
        })
      }

      wx.showToast({ title: '保存成功', icon: 'success' })
      setTimeout(() => wx.navigateBack(), 1500)
    } catch (e) {
      console.error('save error', e)
      wx.showToast({ title: e.message || '保存失败', icon: 'none' })
    }
  }
})