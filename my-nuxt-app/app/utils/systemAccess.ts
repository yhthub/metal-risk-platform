type AccessResult = {
  success: boolean
  data?: unknown
  statusCode?: number | null
  error?: string
}

// A proxy returning the SPA HTML with HTTP 200 is not an authenticated API check.
export const verifySystemAccessResult = (result: AccessResult) => {
  const data = result.data as Record<string, unknown> | null
  const validInfo = result.success && data !== null && typeof data === 'object'
    && typeof data.title === 'string' && typeof data.version === 'string'
    && data.endpoints !== null && typeof data.endpoints === 'object'
  if (validInfo) return { accepted: true, needsKey: false, error: '' }
  return {
    accepted: false,
    needsKey: result.statusCode === 401,
    error: result.success
      ? '未收到有效的系统 API 信息，请检查网站的 /api 代理配置后重试。'
      : result.error || '暂时无法连接系统 API，请检查服务后重试。'
  }
}
