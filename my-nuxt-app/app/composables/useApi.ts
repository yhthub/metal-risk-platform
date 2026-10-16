/**
 * API 调用 composable
 * 用于前后端通信
 */

// 仅保存在当前浏览器运行内存中，不写入存储、URL 或构建配置。
let sessionApiKey = ''
// 通知整站访问入口，不重放请求，也不把密钥放入响应式/序列化状态。
const accessRequiredListeners = new Set<() => void>()

export const useApi = () => {
  // 默认同源；本地开发或分离部署时设置 NUXT_PUBLIC_API_BASE。
  const config = useRuntimeConfig()
  const apiBase = String(config.public.apiBase || '').replace(/\/$/, '')
  const setApiKey = (key: string) => { sessionApiKey = key.trim() }
  const onAccessRequired = (listener: () => void) => {
    accessRequiredListeners.add(listener)
    return () => { accessRequiredListeners.delete(listener) }
  }
  /**
   * 通用请求方法
   */
  const request = async (url: string, options: any = {}, apiKey: string = sessionApiKey) => {
    try {
      const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
      const response = await $fetch(`${apiBase}${url}`, {
        retry: 0,
        ...options,
        headers: {
          ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
          ...options.headers
        }
      })
      return { success: true, data: response }
    } catch (error: any) {
      // A CSV download requests Blob responses, including HTTP error responses.
      // Recover the same JSON error contract without saving credentials or files.
      let errorData = error?.data
      if (typeof Blob !== 'undefined' && errorData instanceof Blob && errorData.size <= 1024 * 1024) {
        try { errorData = JSON.parse(await errorData.text()) } catch { /* keep generic error */ }
      }
      const detail = errorData?.detail
      const detailMessage = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map(item => `${(item.loc || []).filter((part: string) => part !== 'body').join('.')}: ${item.msg}`).join('；')
          : detail?.message
      const statusCode = Number(error?.response?.status || error?.statusCode || error?.status || 0) || null
      if (statusCode === 401) {
        for (const listener of accessRequiredListeners) {
          try { listener() } catch { /* a UI listener cannot turn a failed request into success */ }
        }
      }
      return {
        success: false,
        statusCode,
        error: statusCode === 401
          ? '访问密钥无效或未提供（401）。请填写有效密钥后刷新状态。'
          : statusCode === 403
            ? '服务拒绝访问（403）。请确认部署访问权限与密钥配置。'
            : detailMessage || error.message || '请求失败',
        data: null,
        details: detail || null
      }
    }
  }

  // 轻量只读预检；候选密钥验证成功前不会替换当前会话密钥。
  const getApiInfo = async (candidateKey?: string) => await request(
    '/api/info', { method: 'GET', timeout: 10000 },
    candidateKey === undefined ? sessionApiKey : candidateKey.trim()
  )

  /**
   * 获取群体数据可选择的预测结局及字段要求
   */
  const getOutcomeConfigs = async () => {
    return await request('/api/datainput/outcomes')
  }

  const getGroupDemo = async () => await request('/api/datainput/demo')
  const importGroupDemo = async () => await request('/api/datainput/demo/import', { method: 'POST' })

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

  const getCleaningSchema = async (outcomeId: string = 'blood_pressure') => {
    return await request(`/api/datainput/cleaning/schema?outcome_id=${encodeURIComponent(outcomeId)}`)
  }

  const cleaningBody = (file: File, options?: any) => {
    const body = new FormData()
    body.append('file', file)
    if (options !== undefined) body.append('options', JSON.stringify(options))
    return body
  }
  const inspectCleaningFile = async (file: File) => {
    return await request('/api/datainput/cleaning/inspect', { method: 'POST', body: cleaningBody(file) })
  }
  const previewCleanedData = async (file: File, options: any) => {
    return await request('/api/datainput/cleaning/preview', { method: 'POST', body: cleaningBody(file, options) })
  }
  const downloadCleanedData = async (file: File, options: any) => {
    return await request('/api/datainput/cleaning/export', {
      method: 'POST', body: cleaningBody(file, options), responseType: 'blob'
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

  const getAgentStatus = async () => {
    return await request('/api/agent/status')
  }

  // Independent of the RAG generator: local saved CPU regression models.
  const getPredictionStatus = async () => await request('/api/risk/status', { timeout: 20000 })
  const getPredictionDemo = async () => await request('/api/risk/demo')
  // Fixed, provenance-verified public NHANES records; this does not run inference itself.
  const importPredictionBatchDemo = async () => await request('/api/risk/demo-batch/import', { method: 'POST', timeout: 60000 })
  const predictIndividual = async (body: any) => await request('/api/risk/predict', { method: 'POST', body, timeout: 60000 })
  const predictBatch = async (body: any) => await request('/api/risk/predict-batch', { method: 'POST', body, timeout: 120000 })
  const predictCohort = async (body: any) => await request('/api/risk/predict-cohort', { method: 'POST', body, timeout: 600000 })
  const getPredictionDashboard = async (body: any) => await request('/api/risk/dashboard', { method: 'POST', body, timeout: 120000 })

  /**
   * 发送智能问答消息给 Agent (集成双通路真实循证检索)
   */
  const agentChat = async (message: string, options: {
    model?: string
    knowledgeBases?: string[]
    enableDeepThink?: boolean
    history?: { role: 'user' | 'assistant'; content: string }[]
  } = {}) => {
    return await request('/api/agent/chat', {
      method: 'POST',
      body: {
        message,
        model: options.model || undefined,
        knowledge_bases: options.knowledgeBases || [],
        enable_deep_think: options.enableDeepThink !== false,
        history: (options.history || []).slice(-12).map(item => ({ role: item.role, content: item.content.slice(0, 8000) }))
      }
    })
  }

  /**
   * 真实语料检索。后端返回 hits/mode/diagnostics，不承诺独立稠密召回。
   */
  const searchEvidence = async (query: string, topK: number = 8) => {
    return await request('/api/agent/evidence-search', {
      method: 'POST',
      body: {
        query,
        top_k: Number.isFinite(topK) ? Math.max(1, Math.min(12, Math.trunc(topK))) : 8
      }
    })
  }
  // 保留旧调用名称兼容，但请求采用新的真实检索契约。
  const searchDualPathEvidence = searchEvidence

  return {
    setApiKey,
    onAccessRequired,
    getApiInfo,
    getOutcomeConfigs,
    getGroupDemo,
    importGroupDemo,
    uploadBatchData,
    getDatasetAnalysis,
    getCleaningSchema,
    inspectCleaningFile,
    previewCleanedData,
    downloadCleanedData,
    agentChat,
    searchEvidence,
    searchDualPathEvidence,
    getKnowledgeBases,
    getModels,
    getAgentStatus,
    getPredictionStatus,
    getPredictionDemo,
    importPredictionBatchDemo,
    predictIndividual,
    predictBatch,
    predictCohort,
    getPredictionDashboard
  }
}

