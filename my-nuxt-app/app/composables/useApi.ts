/**
 * API 调用 composable
 * 用于前后端通信
 */

// 后端 API 基础地址
const API_BASE = 'http://localhost:8000'

export const useApi = () => {
  /**
   * 通用请求方法
   */
  const request = async (url: string, options: any = {}) => {
    try {
      const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
      const response = await $fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
          ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
          ...options.headers
        }
      })
      return { success: true, data: response }
    } catch (error: any) {
      console.error('API 请求失败:', error)
      const detail = error?.data?.detail
      const detailMessage = typeof detail === 'string'
        ? detail
        : detail?.message
      return {
        success: false,
        error: detailMessage || error.message || '请求失败',
        data: null,
        details: detail || null
      }
    }
  }

  /**
   * 获取群体数据可选择的预测结局及字段要求
   */
  const getOutcomeConfigs = async () => {
    return await request('/api/datainput/outcomes')
  }

  /**
   * 上传群体数据并生成指定结局的统计分析
   */
  const uploadBatchData = async (file: File, outcomeId: string) => {
    const body = new FormData()
    body.append('file', file)
    body.append('outcome_id', outcomeId)
    return await request('/api/datainput/batch', {
      method: 'POST',
      body
    })
  }

  /**
   * 获取群体数据的完整图表数据
   */
  const getDatasetAnalysis = async (fileId: string) => {
    return await request(`/api/datainput/analysis/${fileId}`)
  }

  /**
   * 检查 Ollama 服务状态
   */
  const checkOllamaStatus = async () => {
    return await request('/api/agent/ollama/status')
  }

  /**
   * 获取 Ollama 可用模型
   */
  const getOllamaModels = async () => {
    return await request('/api/agent/ollama/models')
  }

  /**
   * 使用 Ollama 聊天
   */
  const ollamaChat = async (message: string, options: {
    model?: string
    systemPrompt?: string
    temperature?: number
  } = {}) => {
    return await request('/api/agent/ollama/chat', {
      method: 'POST',
      body: {
        message,
        model: options.model,
        system_prompt: options.systemPrompt,
        temperature: options.temperature
      }
    })
  }

  /**
   * 获取知识库列表
   */
  const getKnowledgeBases = async () => {
    return await request('/api/agent/knowledge-bases')
  }

  /**
   * 获取模型列表
   */
  const getModels = async () => {
    return await request('/api/agent/models')
  }

  /**
   * 获取快捷提问
   */
  const getQuickPrompts = async () => {
    return await request('/api/agent/quick-prompts')
  }

  /**
   * 发送智能问答消息给 Agent (集成双通路真实循证检索)
   */
  const agentChat = async (message: string, options: {
    model?: string
    knowledgeBases?: string[]
    enableDeepThink?: boolean
  } = {}) => {
    return await request('/api/agent/chat', {
      method: 'POST',
      body: {
        message,
        model: options.model || 'XGBoost',
        knowledge_bases: options.knowledgeBases || ['职业重金属复合暴露因果库', '职业病临床诊疗指南 (2025版)'],
        knowledge_bases: options.knowledgeBases || [],
        enable_deep_think: options.enableDeepThink !== false
      }
    })
  }

  /**
   * 双通路循证检索 (每通路 Top-32，评分去 fu 指数)
   */
  const searchDualPathEvidence = async (query: string, topKPerChannel: number = 32) => {
    return await request('/api/agent/evidence-search', {
      method: 'POST',
      body: {
        query,
        top_k_per_channel: topKPerChannel
      }
    })
  }

  return {
    getOutcomeConfigs,
    uploadBatchData,
    getDatasetAnalysis,
    checkOllamaStatus,
    getOllamaModels,
    ollamaChat,
    agentChat,
    searchDualPathEvidence,
    getKnowledgeBases,
    getModels,
    getQuickPrompts
  }
}

