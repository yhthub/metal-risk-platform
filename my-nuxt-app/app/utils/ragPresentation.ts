/** Presentation-only helpers: no synthetic citations, medical labels or HTML execution. */
export interface EvidenceCard {
  chunk_id: string
  title: string
  text: string
  source?: string | Record<string, any>
  standard_no_or_doi?: string
  doi?: string
  pmid?: string
  priority_label?: string
  section_title?: string
  score?: number
  channel?: string
  retrieval_channel?: string
  retrieval_channels?: string[]
  bm25_rank?: number
  dense_rank?: number
  rrf_score?: number
  citation_id?: string
  is_cited: boolean
  [key: string]: any
}
export interface RagMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  loading: boolean
  error: string
  status: string
  answerMode: string
  evidenceSupport: string
  evidenceCards: EvidenceCard[]
  boundaries: EvidenceCard[]
  sparseHits: EvidenceCard[]
  denseHits: EvidenceCard[]
  warnings: string[]
  corpusName: string
  model: Record<string, any>
  retrieval: Record<string, any>
  dualPathSummary: Record<string, any>
  timings: Record<string, any>
}
/** Generation may remain available without retrieval; never call that successful RAG. */
export const chatAvailability = (runtime: Record<string, any> | null | undefined, selectedModelReady: boolean, retrievalReady: boolean): boolean => {
  if (!runtime || !selectedModelReady || runtime.model?.ready !== true) return false
  if (typeof runtime.can_chat === 'boolean') return runtime.can_chat
  // Compatibility with older backends: fallback must be explicitly reported.
  return (runtime.corpus?.ready === true && retrievalReady) || runtime.general_fallback_enabled === true
}
export const isGeneralKnowledgeAnswer = (response: Record<string, any>): boolean => response.answer_mode === 'general_knowledge' || response.answerMode === 'general_knowledge' || response.status === 'general_answer'
export const generalKnowledgeNotice = '检索信息不足，以下为模型一般知识回答，未获检索文献支持。'
/** Defensive UI normalization: fallback candidates are never rendered as citations. */
export const responseEvidence = (response: Record<string, any>) => {
  const general = isGeneralKnowledgeAnswer(response)
  const citations = general ? [] : response.citations
  const candidates = (cards: unknown) => normalizeEvidenceCards(cards, citations).map(card => general ? { ...card, citation_id: undefined, is_cited: false, context_excerpt: undefined, excerpt_truncated: undefined } : card)
  return {
    evidenceCards: general ? [] : normalizeEvidenceCards(response.evidence_cards, citations),
    sparseHits: candidates(response.sparse_hits),
    denseHits: candidates(response.dense_hits),
    boundaries: candidates(response.p0_p1_boundaries)
  }
}
export const normalizeEvidenceCards = (cards: unknown, citations: unknown = []): EvidenceCard[] => {
  if (!Array.isArray(cards)) return []
  const actualCitations = (Array.isArray(citations) ? citations : []).filter(item => item && typeof item === 'object' && item.chunk_id)
  const citedIds = new Set(actualCitations.map(item => String(item.chunk_id)))
  const citationNames = new Map(actualCitations.map(item => [String(item.chunk_id), String(item.id || '')]))
  return cards.filter(card => card && typeof card === 'object').map(card => ({
    ...card,
    chunk_id: String(card.chunk_id || ''),
    title: String(card.title || ''),
    text: String(card.text || card.content || ''),
    citation_id: card.citation_id || citationNames.get(String(card.chunk_id || '')) || undefined,
    retrieval_channels: Array.isArray(card.retrieval_channels) ? card.retrieval_channels.map(String) : [],
    is_cited: card.is_cited === true || citedIds.has(String(card.chunk_id || ''))
  }))
}

/** Keep execution/preflight facts separate from filenames, ranks, and hit counts. */
export const retrievalPresentation = (retrieval: Record<string, any> | null | undefined, actualCounts?: { bm25: number; medcpt: number }) => {
  const data = retrieval || {}
  const diagnostics = data.diagnostics || {}
  const channels = data.channels || diagnostics.channels || {}
  const channel = (name: 'bm25' | 'medcpt') => {
    const info = channels[name] || (name === 'medcpt' ? data.dense : data.sparse) || {}
    const actual = info.count ?? actualCounts?.[name]
    return {
      ready: typeof info.ready === 'boolean' ? info.ready : null,
      count: typeof actual === 'number' && Number.isFinite(actual) && actual >= 0 ? actual : null,
      scope: typeof info.scope === 'string' ? info.scope : '',
      error: typeof info.error === 'string' ? info.error : ''
    }
  }
  const bm25 = channel('bm25')
  const medcpt = channel('medcpt')
  const mode = typeof data.mode === 'string' ? data.mode : ''
  // status reports configured `hybrid`; query responses report executed mode.
  const hybrid = mode === 'hybrid' || mode === 'hybrid_medcpt_bm25'
  const degraded = data.degraded === true || diagnostics.degraded === true || (hybrid && (bm25.ready === false || medcpt.ready === false))
  const dualRouteExecuted = data.dual_route_executed ?? diagnostics.dual_route_executed
  const hybridConfirmed = hybrid && bm25.ready === true && medcpt.ready === true && !degraded && dualRouteExecuted !== false
  let warning = ''
  if (degraded) warning = '当前检索为降级或通路未就绪状态，不是双路已跑通。请查看各路状态与后端告警。'
  else if (hybrid && dualRouteExecuted === false) warning = '本次未执行完整独立双路检索，不是双路已跑通。'
  else if (!mode || (hybrid && (bm25.ready === null || medcpt.ready === null))) warning = '后端未提供完整的双路状态；不能确认 BM25 与 MedCPT 独立检索均已执行。'
  const labels: Record<string, string> = { bm25: 'BM25 单路', bm25_medcpt_rerank: 'BM25 候选 + MedCPT 重排（非双路）', hybrid: '独立双路尚未确认', hybrid_medcpt_bm25: '独立双路尚未确认', unavailable: '检索不可用' }
  return {
    mode, bm25, medcpt, hybridConfirmed, degraded,
    ready: data.ready === true && bm25.ready === true && (!hybrid || hybridConfirmed),
    label: hybridConfirmed ? 'BM25 + MedCPT 独立双路' : (labels[mode] || mode || '执行信息未提供'),
    warning
  }
}

export const retrievalChannelLabel = (card: EvidenceCard): string => {
  const channels = card.retrieval_channels?.length ? card.retrieval_channels : (card.retrieval_channel ? [card.retrieval_channel] : [])
  const labels: Record<string, string> = { bm25: 'BM25 词法', sparse: 'BM25 词法', medcpt: 'MedCPT 向量', dense: 'MedCPT 向量' }
  return channels.length ? channels.map(channel => labels[channel] || channel).join(' + ') : '召回通路未提供'
}
export const sourceLabel = (card: EvidenceCard): string => {
  if (typeof card.source === 'string' && card.source.trim()) return card.source
  if (card.source && typeof card.source === 'object') return String(card.source.name || card.source.label || card.source.corpus || card.source.source || '来源名称未提供')
  return '来源名称未提供'
}
export const sourceUrl = (card: EvidenceCard): string => {
  const explicit = card.url || (typeof card.source === 'object' ? card.source?.url : '')
  if (typeof explicit === 'string') {
    try { const url = new URL(explicit); if (url.protocol === 'https:' || url.protocol === 'http:') return url.href }
    catch { /* Malformed/untrusted links remain text, not clickable links. */ }
  }
  const doi = card.doi || card.standard_no_or_doi
  if (typeof doi === 'string' && /^10\.\d{4,9}\/\S+$/i.test(doi)) return `https://doi.org/${encodeURI(doi)}`
  if (typeof card.pmid === 'string' && /^\d+$/.test(card.pmid)) return `https://pubmed.ncbi.nlm.nih.gov/${card.pmid}/`
  return ''
}
export const plainAnswer = (response: Record<string, any>): string => {
  if (typeof response.answer === 'string') return response.answer
  // Compatibility only: never render legacy HTML directly into the DOM.
  if (typeof response.message !== 'string') return ''
  if (typeof DOMParser !== 'undefined') {
    const doc = new DOMParser().parseFromString(response.message, 'text/html')
    doc.querySelectorAll('script, style, iframe, object').forEach(node => node.remove())
    return doc.body.textContent || ''
  }
  return response.message.replace(/<[^>]*>/g, '')
}
