// services/ai.js - 云开发 AI（混元）统一封装
//
// 所有 AI 调用走这里，便于集中调整参数/换模型。
// 依赖：微信云开发 + 基础库 >= 3.15.1
//
// 注意 createModel() 的参数不是模型名，只能是以下之一：
//   'hunyuan-exp'  —— 小程序成长计划专属（免费额度，当前使用）
//   'cloudbase'    —— 主托管组
//   'custom-<名称>' —— 自定义分组
// 具体模型 ID 放在请求参数的 model 字段里。

const PROVIDER = 'hunyuan-exp'
const MODEL = 'hy3'

// 云开发 AI 是否可用
function isCloudReady() {
  return !!(wx.cloud && wx.cloud.extend && wx.cloud.extend.AI)
}

/**
 * 非流式文本生成
 * @param {Array} messages - [{role, content}, ...]，支持 system/user/assistant
 * @param {Object} options - { maxTokens, temperature }
 * @returns {Promise<string>} 模型回复文本
 */
async function generateText(messages, options = {}) {
  const maxTokens = options.maxTokens || 600
  const temperature = options.temperature !== undefined ? options.temperature : 0.5

  if (!isCloudReady()) {
    throw new Error('云开发未初始化或基础库版本过低（需 >= 3.15.1）')
  }

  const model = wx.cloud.extend.AI.createModel(PROVIDER)
  const res = await model.generateText({
    model: MODEL,
    messages,
    max_tokens: maxTokens,
    temperature,
  })

  const choice = res && res.choices && res.choices[0]
  const content = choice && choice.message ? choice.message.content : ''
  if (!content) {
    throw new Error('AI 返回内容为空')
  }
  return content
}

/**
 * 让模型返回 JSON 并解析（容错：从回复里抠出第一个 {...}）
 * @returns {Promise<Object|null>} 解析失败返回 null
 */
async function generateJSON(messages, options = {}) {
  const text = await generateText(messages, options)
  try {
    const match = text.match(/\{[\s\S]*\}/)
    if (!match) return null
    return JSON.parse(match[0])
  } catch (e) {
    console.warn('[ai] JSON 解析失败:', text.slice(0, 100))
    return null
  }
}

module.exports = {
  generateText,
  generateJSON,
  isCloudReady,
  PROVIDER,
  MODEL,
}
