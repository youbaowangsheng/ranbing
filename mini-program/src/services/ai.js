// services/ai.js - 云开发 AI 统一封装
//
// 所有 AI 调用走这里，便于集中调整参数/换模型。
// 依赖：微信云开发 + 基础库 >= 3.15.1
//
// 【重要】createModel(provider) 的参数是「模型组名」，不是模型名，只能是：
//   'hunyuan-exp'  —— 成长计划旧组（可能已随 Hy3 升级迁移）
//   'hunyuan-v3'   —— 成长计划 Hy3 组
//   'cloudbase'    —— 主托管组（默认只启用 deepseek-v4-flash）
//   'custom-<名称>' —— 自定义组
// 具体模型 ID 放在请求参数的 model 字段里。
//
// 由于成长计划升级后渠道名有变动，这里采用「候选组合依次尝试」策略：
// 第一个成功的组合会被缓存，后续请求直接用，避免每次都试错。

const CANDIDATES = [
  { provider: 'hunyuan-exp', model: 'hy3' },
  { provider: 'hunyuan-exp', model: 'hunyuan-2.0-instruct-20251111' },
  { provider: 'hunyuan-v3', model: 'hy3-preview' },
  { provider: 'cloudbase', model: 'hy3' },
  { provider: 'cloudbase', model: 'deepseek-v4-flash' },
]

// 记住第一个成功的组合，后续直接用
let resolved = null

// 云开发 AI 是否可用
function isCloudReady() {
  return !!(wx.cloud && wx.cloud.extend && wx.cloud.extend.AI)
}

// 单次调用（指定 provider + model）
async function _once(provider, model, messages, opts) {
  const m = wx.cloud.extend.AI.createModel(provider)
  const res = await m.generateText({
    model,
    messages,
    max_tokens: opts.maxTokens,
    temperature: opts.temperature,
  })
  const choice = res && res.choices && res.choices[0]
  const content = choice && choice.message ? choice.message.content : ''
  if (!content) throw new Error('AI 返回内容为空')
  return content
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
  const opts = { maxTokens, temperature }

  if (!isCloudReady()) {
    throw new Error('云开发未初始化或基础库版本过低（需 >= 3.15.1）')
  }

  // 1) 已确定可用组合，直接调
  if (resolved) {
    try {
      return await _once(resolved.provider, resolved.model, messages, opts)
    } catch (e) {
      console.warn('[ai] 已缓存组合失效，重新探测：', e && e.message)
      resolved = null
      // 继续走下面的探测流程
    }
  }

  // 2) 依次尝试候选组合
  let lastErr = null
  for (const c of CANDIDATES) {
    try {
      const content = await _once(c.provider, c.model, messages, opts)
      resolved = c
      console.log(`[ai] 使用 ${c.provider} / ${c.model}`)
      return content
    } catch (e) {
      lastErr = e
      const msg = (e && (e.message || e.errMsg)) || ''
      // 配置类错误（渠道/模型不存在、无权限）→ 换下一个候选
      // 429/超时类错误 → 也换下一个候选试试（不同模型资源池独立）
      console.warn(`[ai] ${c.provider}/${c.model} 失败：${msg}`)
    }
  }

  // 3) 全部失败，给出可读错误
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
    console.warn('[ai] JSON 解析失败:', text.slice(0, 100))
    return null
  }
}

module.exports = {
  generateText,
  generateJSON,
  isCloudReady,
  CANDIDATES,
}
