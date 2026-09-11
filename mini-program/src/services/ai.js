// services/ai.js - 云开发 AI 统一封装
//
// 所有 AI 调用走这里，便于集中调整参数/换模型。
// 依赖：微信云开发 + 基础库 >= 3.15.1
//
// 【重要】createModel(provider) 的参数是「模型组名」，不是模型名，只能是：
//   'hunyuan-exp'  —— AI 小程序成长计划专属组（当前使用，走赠送的 10 亿 Token）
//   'cloudbase'    —— 主托管组（默认只启用 deepseek-v4-flash）
//   'custom-<名称>' —— 自定义组
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
 * @param {Object} options - { maxTokens, temperature, retries }
 * @returns {Promise<string>} 模型回复文本
 */
async function generateText(messages, options = {}) {
  const maxTokens = options.maxTokens || 600
  const temperature = options.temperature !== undefined ? options.temperature : 0.5
  const retries = options.retries !== undefined ? options.retries : 1

  if (!isCloudReady()) {
    throw new Error('云开发未初始化或基础库版本过低（需 >= 3.15.1）')
  }

  const model = wx.cloud.extend.AI.createModel(PROVIDER)

  let lastErr = null
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await model.generateText({
        model: MODEL,
        messages,
        max_tokens: maxTokens,
        temperature,
      })

      const choice = res && res.choices && res.choices[0]
      const content = choice && choice.message ? choice.message.content : ''
      if (!content) {
        // 限流等情况下 SDK 可能不抛异常，而是返回空 choices
        const detail = (res && (res.error || res.message || res.errMsg)) || '无错误信息'
        throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail))
      }
      return content
    } catch (e) {
      lastErr = e
      const msg = (e && (e.message || e.errMsg)) || ''
      // 限流/网络类错误：退避后重试一次
      if (attempt < retries && /429|Too Many Requests|timeout|超时|网络|空/i.test(msg)) {
        await new Promise(r => setTimeout(r, 1500))
        continue
      }
      break
    }
  }

  // 统一成用户可读的错误
  const raw = (lastErr && (lastErr.message || lastErr.errMsg)) || ''
  if (/429|Too Many Requests/i.test(raw)) {
    throw new Error('AI 使用人数较多，请稍后重试')
  }
  if (/not found|不存在|未开通|not enabled|ModelNotEnabled/i.test(raw)) {
    throw new Error('AI 模型未启用，请在云开发控制台开启模型')
  }
  throw new Error(raw || 'AI 服务暂时不可用')
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
    console.error('[ai] JSON 解析失败', e)
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
