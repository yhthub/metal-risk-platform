<template>
  <div class="system-layout agent-chat-page">
    <Sidebar default-active="6" />
    <main class="main-content">
      <header class="page-header">
        <div class="page-heading">
          <NuxtLink to="/" class="home-link"><el-icon><ArrowLeft /></el-icon> 系统首页</NuxtLink>
          <h1>医学知识问答</h1>
          <p>查阅医学资料，理解职业暴露与健康相关问题。</p>
        </div>
        <div class="header-actions">
          <button class="service-status" :class="{ available: serviceAvailable, checking: checkingStatus }" :disabled="isGenerating || checkingStatus" title="刷新服务状态" @click="refreshStatus">
            <span class="status-dot" />{{ checkingStatus ? '正在连接' : serviceAvailable ? '服务可用' : '暂不可用' }}<el-icon><RefreshRight /></el-icon>
          </button>
          <el-button class="new-chat" plain :disabled="isGenerating || !chatHistory.length" @click="newConversation"><el-icon><Plus /></el-icon><span>新对话</span></el-button>
        </div>
      </header>

      <details v-if="!publicDemo" class="access-settings">
        <summary>访问设置</summary>
        <div class="access-key-row">
          <label for="rag-access-key">访问密钥</label>
          <el-input id="rag-access-key" v-model="accessKey" type="password" autocomplete="off" placeholder="仅在本次访问中使用" :disabled="isGenerating || checkingStatus" @keydown.enter.prevent="applyAccessKey" />
          <el-button :disabled="isGenerating || checkingStatus" @click="applyAccessKey">应用</el-button>
          <el-button text :disabled="isGenerating || checkingStatus" @click="clearAccessKey">清除</el-button>
        </div>
      </details>

      <div v-if="!checkingStatus && !serviceAvailable && !isGenerating" class="service-notice" role="status">
        <el-icon><InfoFilled /></el-icon><span>{{ statusError ? friendlyError(statusError) : '问答服务暂时不可用，请稍后重试。' }}</span><button @click="refreshStatus">重新连接</button>
      </div>

      <div ref="messageListRef" class="conversation-scroll">
        <div class="conversation-content">
          <section v-if="!chatHistory.length" class="welcome-panel">
            <div class="welcome-symbol" aria-hidden="true"><el-icon><Reading /></el-icon></div>
            <span class="welcome-eyebrow">医学知识助手</span>
            <h2>今天想了解什么？</h2>
            <p>从一个具体问题开始，获得清晰解答，并查看回答引用的资料。</p>
            <div class="quick-prompts">
              <button v-for="(prompt, index) in quickPrompts" :key="prompt" :class="`prompt-card-${index}`" :disabled="isGenerating" @click="usePrompt(prompt)">
                <span class="prompt-heading">
                  <span class="prompt-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                      <path v-if="index === 0" d="M3 12h4l3-7 4 14 3-7h4" />
                      <g v-else-if="index === 1"><path d="M14 3H6a1 1 0 0 0-1 1v16a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8Z" /><path d="M14 3v5h5M9 12h6M9 16h4" /></g>
                      <g v-else><path d="m9 7 6 3m-6 7 6-4" /><circle cx="6" cy="5.5" r="3" /><circle cx="18" cy="11.5" r="3" /><circle cx="6" cy="18.5" r="3" /></g>
                    </svg>
                  </span>
                  <span class="prompt-label">{{ ['暴露与健康', '研究证据', '复合暴露'][index] }}</span>
                </span>
                <span class="prompt-question">{{ prompt }}</span><span class="prompt-arrow" aria-hidden="true">↗</span>
              </button>
            </div>
          </section>

          <section v-else class="message-list" aria-label="问答记录" aria-live="polite" aria-relevant="additions text">
            <article v-for="msg in chatHistory" :key="msg.id" :class="['message', msg.role]">
              <div class="message-body">
                <div v-if="msg.role === 'assistant'" class="assistant-heading">
                  <RagAvatar role="assistant" class="assistant-avatar" />
                  <div class="message-label">医学知识助手</div>
                </div>
                <div v-else class="message-label">你</div>
                <RagPending v-if="msg.loading" />
                <div v-else-if="msg.error" class="answer-error" role="alert">
                  <strong>这次回答未能完成</strong><p>{{ friendlyError(msg.error) }}</p><button @click="retryQuestion(msg)">重新提问 <span aria-hidden="true">↗</span></button>
                </div>
                <template v-else-if="msg.role === 'assistant'">
                  <p v-if="isGeneralKnowledgeAnswer(msg)" class="general-answer-notice" role="note"><el-icon><InfoFilled /></el-icon>{{ generalAnswerNotice }}</p>
                  <p v-for="notice in answerNotices(msg)" :key="notice" class="answer-notice" role="note"><el-icon><InfoFilled /></el-icon>{{ notice }}</p>
                  <RagAnswer :content="answerContent(msg)" :citation-ids="citationIds(msg)" @citation="openCitation(msg, $event)" />
                  <div class="answer-actions">
                    <button v-if="referenceCards(msg).length" class="references-button" @click="openEvidenceDrawer(msg)"><el-icon><Collection /></el-icon>参考资料 <span>{{ referenceCards(msg).length }}</span><el-icon><ArrowRight /></el-icon></button>
                    <button class="copy-answer" :disabled="!msg.content" @click="copyText(msg.content)"><el-icon><DocumentCopy /></el-icon>复制</button>
                  </div>
                </template>
                <div v-else class="user-text">{{ msg.content }}</div>
              </div>
              <RagAvatar v-if="msg.role === 'user'" role="user" class="user-avatar" />
            </article>
          </section>
        </div>
      </div>

      <footer class="composer-area">
        <div class="composer-wrap">
          <section class="composer" aria-label="输入问题">
            <textarea ref="inputRef" v-model="userInput" placeholder="例如：铅暴露与高血压" :disabled="isGenerating" :maxlength="2000" rows="2" aria-label="医学问题" @keydown="handleInputKeydown" />
            <div class="composer-actions">
              <small class="keyboard-hint">Enter 发送 · Shift + Enter 换行</small>
              <div class="send-actions"><small v-if="userInput.length">{{ userInput.length }}/2000</small><el-button type="primary" :loading="isGenerating" :disabled="!userInput.trim() || !canSend" @click="sendMessage"><el-icon v-if="!isGenerating"><Position /></el-icon>{{ isGenerating ? '回答中' : '发送' }}</el-button></div>
            </div>
          </section>
          <p class="privacy-note">回答仅供健康信息参考，不替代专业诊疗建议；请勿输入个人敏感信息</p>
        </div>
      </footer>

      <el-drawer v-model="evidenceDrawerVisible" title="参考资料" size="min(600px, 100vw)" destroy-on-close @opened="scrollToReference">
        <div class="reference-drawer">
          <p class="drawer-note">以下为本次回答实际引用的资料。节选不代表完整文献，可通过来源链接进一步阅读。</p>
          <el-empty v-if="!drawerCards.length" description="本次回答没有可展示的引用资料" />
          <article v-for="card in drawerCards" :id="referenceElementId(card)" :key="card.chunk_id" :class="['reference-card', { selected: selectedCitation === card.citation_id }]">
            <div class="reference-heading"><span class="citation-badge">{{ card.citation_id }}</span><span>{{ referenceSource(card) }}</span></div>
            <h3>{{ card.title || '资料标题未提供' }}</h3>
            <p v-if="referenceIdentifier(card)" class="reference-identifier">{{ referenceIdentifier(card) }}</p>
            <div class="reference-excerpt">{{ card.context_excerpt || card.text || '本次回答未提供资料节选。' }}</div>
            <a v-if="sourceUrl(card)" :href="sourceUrl(card)" target="_blank" rel="noopener noreferrer" class="source-link">查看来源 <span aria-hidden="true">↗</span></a>
          </article>
        </div>
      </el-drawer>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Collection, DocumentCopy, InfoFilled, Plus, Position, Reading, RefreshRight } from '@element-plus/icons-vue'
import { plainAnswer, sourceLabel, sourceUrl, retrievalPresentation, chatAvailability, isGeneralKnowledgeAnswer, generalKnowledgeNotice, responseEvidence } from '~/utils/ragPresentation'
import type { EvidenceCard, RagMessage } from '~/utils/ragPresentation'
import { PRODUCT_SHORT_NAME } from '~/utils/product'

useHead({ title: `医学知识问答 · ${PRODUCT_SHORT_NAME}` })

type VisitorMessage = RagMessage & { generationTruncated?: boolean }
const { agentChat, getAgentStatus, getModels, setApiKey } = useApi()
const publicDemo = String(useRuntimeConfig().public.publicDemo) === 'true'
const accessKey = ref('')
const runtimeStatus = ref<Record<string, any> | null>(null)
const statusError = ref('')
const checkingStatus = ref(false)
const localModels = ref<{ name: string; ready: boolean }[]>([])
const currentModel = ref('')
const userInput = ref('')
const enableDeepThink = ref(true)
const isGenerating = ref(false)
const chatHistory = ref<VisitorMessage[]>([])
const messageListRef = ref<HTMLElement | null>(null)
const inputRef = ref<HTMLTextAreaElement | null>(null)
const evidenceDrawerVisible = ref(false)
const activeDrawerMsg = ref<VisitorMessage | null>(null)
const selectedCitation = ref('')
let nextMessageId = 0

const quickPrompts = ['铅暴露与高血压', '镉暴露与肾损伤', '砷与镉复合暴露']
const modelReady = computed(() => runtimeStatus.value?.model?.ready === true && localModels.value.some(model => model.name === currentModel.value && model.ready))
const retrievalState = computed(() => retrievalPresentation(runtimeStatus.value?.retrieval))
const serviceAvailable = computed(() => chatAvailability(runtimeStatus.value, modelReady.value, retrievalState.value.ready))
const canSend = computed(() => serviceAvailable.value && !checkingStatus.value && !isGenerating.value)
const corpusName = computed(() => runtimeStatus.value?.corpus?.name || '')
const messageRetrieval = (msg: VisitorMessage) => retrievalPresentation(msg.retrieval, { bm25: msg.sparseHits.length, medcpt: msg.denseHits.length })
const generalAnswerNotice = '本次回答未获检索资料支持，仅供一般知识参考'
// Only remove exact known transport notices at the start; keep all substantive limitations in the answer.
const fallbackPrefixes = [
  generalAnswerNotice,
  generalAnswerNotice + '。',
  generalKnowledgeNotice,
  '检索信息不足。以下为模型一般知识回答，未获本次检索证据支持，不构成诊断或治疗建议。',
  '检索信息不足；以下为模型一般知识回答，未获本次检索证据支持。'
]
const answerContent = (msg: VisitorMessage) => {
  if (!isGeneralKnowledgeAnswer(msg)) return msg.content
  const content = msg.content.trimStart()
  const prefix = fallbackPrefixes.find(notice => content.startsWith(notice) && (!content.slice(notice.length) || /^\s/.test(content.slice(notice.length))))
  return prefix ? content.slice(prefix.length).trimStart() : msg.content
}
const referenceCards = (msg: VisitorMessage) => isGeneralKnowledgeAnswer(msg) ? [] : msg.evidenceCards.filter(card => card.is_cited && /^E[1-9]\d*$/.test(String(card.citation_id || '')))
const citationIds = (msg: VisitorMessage) => referenceCards(msg).map(card => String(card.citation_id))
const drawerCards = computed(() => activeDrawerMsg.value ? referenceCards(activeDrawerMsg.value) : [])
const referenceSource = (card: EvidenceCard) => {
  const labels: Record<string, string> = { pubmed: 'PubMed', textbooks: '医学教材', statpearls: 'StatPearls', normative: '规范资料', scientific: '科学文献', guidelines: '指南资料' }
  return labels[String(card.source)] || sourceLabel(card)
}
const referenceIdentifier = (card: EvidenceCard) => card.standard_no_or_doi || card.doi || (card.pmid ? `PMID ${card.pmid}` : '')
const referenceElementId = (card: EvidenceCard) => `reference-${String(card.citation_id || '').replace(/[^A-Za-z0-9_-]/g, '')}`
const answerNotices = (msg: VisitorMessage) => {
  const notices: string[] = []
  if (msg.generationTruncated) notices.push('回答可能未完整显示，可缩小问题范围后重新提问。')
  if (!isGeneralKnowledgeAnswer(msg)) {
    const diagnostics = msg.retrieval.diagnostics || {}
    if (msg.retrieval.degraded || diagnostics.partial || diagnostics.search_state === 'partial' || diagnostics.failed_sources?.length || msg.warnings.some(warning => /检索未完成|检索.*超时|分库.*(?:失败|未访问)/.test(warning))) notices.push('部分资料暂未检索完成，回答仅基于本次可用资料。')
    if (msg.status === 'insufficient_evidence') notices.push('暂未找到足够资料，请补充问题背景或换个问法。')
  }
  return notices
}
const friendlyError = (error: string) => {
  if (/401|403|访问密钥|unauthori[sz]ed|forbidden/i.test(error)) return publicDemo ? '服务访问暂时受限，请稍后重试。' : '访问验证未通过，请检查访问设置。'
  if (/429|busy|繁忙/i.test(error)) return '当前提问较多，请稍后重试。'
  if (/timeout|timed out|504|超时/i.test(error)) return '等待回答超时，请稍后重试或缩短问题。'
  if (/未返回回答内容|empty answer/i.test(error)) return '未收到有效回答，请重新提问。'
  if (/network|fetch|连接|503|unavailable/i.test(error)) return '暂时无法连接问答服务，请稍后重试。'
  return '暂时无法完成回答，请稍后重试。'
}
const refreshStatus = async () => {
  if (checkingStatus.value || isGenerating.value) return
  checkingStatus.value = true
  statusError.value = ''
  try {
    const [statusResult, modelResult] = await Promise.all([getAgentStatus(), getModels()])
    if (!statusResult.success || !statusResult.data) throw new Error(statusResult.error || '无法获取问答服务状态')
    runtimeStatus.value = statusResult.data as Record<string, any>
    if (!modelResult.success || !modelResult.data) throw new Error(modelResult.error || '无法获取模型列表')
    const payload = modelResult.data as Record<string, any>
    localModels.value = (Array.isArray(payload.models) ? payload.models : []).filter((model: any) => model && typeof model.name === 'string').map((model: any) => ({ name: model.name, ready: model.ready === true }))
    currentModel.value = localModels.value.some(model => model.name === payload.default) ? payload.default : localModels.value[0]?.name || ''
  } catch (error: any) {
    runtimeStatus.value = null
    localModels.value = []
    currentModel.value = ''
    statusError.value = error?.message || '获取服务状态失败'
  } finally { checkingStatus.value = false }
}
const applyAccessKey = () => { if (publicDemo) return; setApiKey(accessKey.value); accessKey.value = ''; refreshStatus() }
const clearAccessKey = () => { if (publicDemo) return; setApiKey(''); accessKey.value = ''; refreshStatus() }
const scrollToBottom = async () => { await nextTick(); messageListRef.value?.scrollTo({ top: messageListRef.value.scrollHeight, behavior: 'smooth' }) }
const usePrompt = (prompt: string) => { userInput.value = prompt; inputRef.value?.focus() }
const handleInputKeydown = (event: KeyboardEvent) => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing && event.keyCode !== 229) { event.preventDefault(); sendMessage() } }
const newConversation = () => {
  if (isGenerating.value) return
  chatHistory.value = []; userInput.value = ''; activeDrawerMsg.value = null; evidenceDrawerVisible.value = false; selectedCitation.value = ''; inputRef.value?.focus()
}
const retryQuestion = (msg: VisitorMessage) => {
  if (isGenerating.value) return
  const index = chatHistory.value.findIndex(item => item.id === msg.id)
  const question = chatHistory.value[index - 1]
  if (question?.role === 'user') usePrompt(question.content)
}
const openEvidenceDrawer = (msg: VisitorMessage) => {
  if (!referenceCards(msg).length) return
  activeDrawerMsg.value = msg; selectedCitation.value = ''; evidenceDrawerVisible.value = true
}
const scrollToReference = async () => {
  if (!selectedCitation.value) return
  await nextTick()
  document.getElementById(`reference-${selectedCitation.value}`)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}
const openCitation = (msg: VisitorMessage, citation: string) => {
  if (!citationIds(msg).includes(citation)) return
  activeDrawerMsg.value = msg; selectedCitation.value = citation; evidenceDrawerVisible.value = true; scrollToReference()
}
const copyWithSelection = (content: string) => {
  const focused = document.activeElement as HTMLElement | null
  const input = focused as HTMLInputElement | HTMLTextAreaElement | null
  const start = typeof input?.selectionStart === 'number' ? input.selectionStart : null
  const end = typeof input?.selectionEnd === 'number' ? input.selectionEnd : null
  const direction = input?.selectionDirection || undefined
  const selection = document.getSelection()
  const ranges = selection ? Array.from({ length: selection.rangeCount }, (_, index) => selection.getRangeAt(index).cloneRange()) : []
  const field = document.createElement('textarea')
  field.value = content; field.readOnly = true; field.tabIndex = -1
  field.setAttribute('aria-hidden', 'true')
  Object.assign(field.style, { position: 'fixed', left: '-9999px', top: '0', opacity: '0' })
  try {
    document.body.appendChild(field)
    field.select(); field.setSelectionRange(0, content.length)
    return document.execCommand('copy') === true
  } finally {
    field.remove()
    focused?.focus({ preventScroll: true })
    if (start !== null && end !== null) input?.setSelectionRange(start, end, direction)
    if (selection) { selection.removeAllRanges(); ranges.forEach(range => selection.addRange(range)) }
  }
}
const copyText = async (content: string) => {
  let copied = false
  try {
    if (navigator.clipboard?.writeText) { await navigator.clipboard.writeText(content); copied = true }
  } catch { /* HTTP and denied clipboard access use the user-triggered plain-text fallback. */ }
  if (!copied) { try { copied = copyWithSelection(content) } catch { copied = false } }
  if (copied) ElMessage.success('已复制到剪贴板')
  else ElMessage.error('复制未成功，请选择回答文字后手动复制。')
}
const makeMessage = (role: 'user' | 'assistant', content: string): VisitorMessage => ({ id: ++nextMessageId, role, content, loading: false, error: '', status: '', answerMode: '', evidenceSupport: '', evidenceCards: [], boundaries: [], sparseHits: [], denseHits: [], warnings: [], corpusName: corpusName.value, model: {}, retrieval: {}, dualPathSummary: {}, timings: {} })
const sendMessage = async () => {
  const question = userInput.value.trim()
  if (!question || isGenerating.value) return
  if (question.length > 2000) { ElMessage.warning('问题超过 2000 字符，请缩短后提交。'); return }
  if (!canSend.value) { ElMessage.warning('问答服务暂时不可用，请重新连接后再试。'); return }
  // Send only successful prior turns; interface notices and failed requests are not model context.
  const history: { role: 'user' | 'assistant'; content: string }[] = []
  for (let index = 0; index < chatHistory.value.length - 1; index++) {
    const user = chatHistory.value[index]
    const assistant = chatHistory.value[index + 1]
    if (user?.role === 'user' && assistant?.role === 'assistant' && !assistant.error && !assistant.loading && assistant.content) history.push({ role: 'user', content: user.content }, { role: 'assistant', content: assistant.content })
  }
  chatHistory.value.push(makeMessage('user', question))
  const responseMessage = makeMessage('assistant', '')
  responseMessage.loading = true
  chatHistory.value.push(responseMessage)
  const messageIndex = chatHistory.value.length - 1
  userInput.value = ''; isGenerating.value = true; scrollToBottom()
  try {
    const result = await agentChat(question, { model: currentModel.value, history: history.slice(-12), enableDeepThink: enableDeepThink.value })
    if (!result.success || !result.data) throw new Error(result.error || '问答请求失败')
    const data = result.data as Record<string, any>
    const content = plainAnswer(data)
    if (!content && data.status !== 'insufficient_evidence') throw new Error('后端未返回回答内容，不能判定生成成功。')
    const msg = chatHistory.value[messageIndex]!
    msg.content = content || '检索结果不足以生成有依据的回答。'
    msg.status = String(data.status || 'answered'); msg.answerMode = String(data.answer_mode || ''); msg.evidenceSupport = String(data.evidence_support || '')
    Object.assign(msg, responseEvidence(data))
    msg.warnings = Array.isArray(data.warnings) ? data.warnings.map(String) : []
    msg.model = data.model && typeof data.model === 'object' ? data.model : {}
    msg.retrieval = data.retrieval && typeof data.retrieval === 'object' ? data.retrieval : {}
    msg.dualPathSummary = data.dual_path_summary && typeof data.dual_path_summary === 'object' ? data.dual_path_summary : {}
    msg.timings = data.timings && typeof data.timings === 'object' ? data.timings : {}
    msg.corpusName = data.corpus?.name || corpusName.value
    msg.generationTruncated = data.generation_truncated === true
  } catch (error: any) { chatHistory.value[messageIndex]!.error = error?.message || '问答请求失败' }
  finally { chatHistory.value[messageIndex]!.loading = false; isGenerating.value = false; scrollToBottom() }
}
onMounted(refreshStatus)
</script>

<style scoped>
:global(.application-root > .agent-chat-page ~ .public-demo-note) { display: none; }
.system-layout { --chat-width: 1280px; --chat-gutter: clamp(20px, 2.5vw, 48px); display: flex; height: 100vh; height: 100dvh; overflow: hidden; background: #f7f9fc; color: #263c54; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.system-layout :deep(.sidebar) { height: 100%; overflow-y: auto; }
.main-content { min-width: 0; flex: 1; display: flex; flex-direction: column; }
.page-header { flex-shrink: 0; display: flex; justify-content: space-between; gap: 24px; align-items: center; padding: 18px 32px 17px; border-bottom: 1px solid #e7edf4; background: #fff; }
.home-link { display: inline-flex; align-items: center; gap: 5px; color: #8190a3; text-decoration: none; font-size: 12px; margin-bottom: 9px; }
.home-link:hover { color: #2578b6; }
.page-heading h1 { margin: 0; color: #233a53; font-size: 23px; font-weight: 650; letter-spacing: .04em; }
.page-heading p { margin: 7px 0 0; font-size: 13px; line-height: 1.6; color: #7c8ca0; }
.header-actions { display: flex; align-items: center; gap: 20px; flex-shrink: 0; }
.service-status { display: inline-flex; align-items: center; gap: 7px; padding: 6px 0; border: 0; background: none; font-size: 12px; color: #8994a3; cursor: pointer; white-space: nowrap; }
.service-status:disabled { cursor: default; }
.status-dot { width: 6px; height: 6px; border-radius: 50%; background: #a7b2bf; }
.service-status.available { color: #528075; }
.available .status-dot { background: #60a58e; }
.new-chat { border-radius: 9px; height: 36px; color: #397da9; border-color: #dce6ef; }
.new-chat .el-icon { margin-right: 6px; }
.access-settings { flex-shrink: 0; background: #fff; padding: 8px 36px; border-bottom: 1px solid #e8eef5; color: #7c8ca0; font-size: 12px; }
.access-settings summary { width: fit-content; cursor: pointer; }
.access-key-row { display: flex; align-items: center; gap: 10px; max-width: 640px; padding: 12px 0 4px; }
.access-key-row label { white-space: nowrap; }
.service-notice { flex-shrink: 0; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px 20px; font-size: 12px; line-height: 1.6; background: #fff8ed; color: #98713e; }
.service-notice button { padding: 0; border: 0; background: transparent; color: #967039; text-decoration: underline; white-space: nowrap; cursor: pointer; }
.conversation-scroll { flex: 1; min-height: 0; overflow-y: auto; overscroll-behavior: contain; scroll-behavior: smooth; scrollbar-width: thin; scrollbar-color: #cfdae7 transparent; }
.conversation-content { box-sizing: border-box; width: 100%; max-width: calc(var(--chat-width) + var(--chat-gutter) + var(--chat-gutter)); margin: 0 auto; padding: 24px var(--chat-gutter) 28px; }
.welcome-panel { max-width: 780px; margin: min(6vh, 64px) auto 20px; text-align: center; }
.welcome-symbol { display: flex; align-items: center; justify-content: center; width: 66px; height: 66px; margin: 0 auto 22px; color: #377fb8; background: linear-gradient(145deg,#e5f2ff,#eef5fc); border: 1px solid #dceafb; border-radius: 21px; font-size: 30px; box-shadow: 0 8px 26px #376c9e0b; }
.welcome-eyebrow { font-size: 12px; color: #7b9cb8; letter-spacing: .18em; }
.welcome-panel h2 { margin: 13px 0 14px; color: #284766; font-size: 29px; font-weight: 600; letter-spacing: .04em; }
.welcome-panel > p { margin: 0 auto; font-size: 14px; line-height: 1.8; color: #7b8da2; }
.quick-prompts { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 14px; margin-top: 36px; text-align: left; }
.quick-prompts button { position: relative; min-height: 150px; padding: 20px 20px 32px; border: 1px solid #e1e9f2; border-radius: 14px; background: #fff; color: #445d76; font: inherit; text-align: left; cursor: pointer; transition: border-color .18s, transform .18s, box-shadow .18s; }
.quick-prompts button:hover { transform: translateY(-2px); border-color: #a8c9e4; box-shadow: 0 8px 22px #315c8410; }
.prompt-label { display: block; margin-bottom: 13px; font-size: 11px; letter-spacing: .08em; color: #8aa0b6; }
.prompt-question { font-size: 13px; line-height: 1.9; }
.prompt-arrow { position: absolute; right: 18px; bottom: 12px; color: #93b1c9; font-size: 17px; }
.message-list { display: flex; flex-direction: column; gap: 22px; padding: 0 0 4px; }
.message { display: flex; align-items: flex-start; gap: 12px; min-width: 0; }
.assistant-heading { display: flex; align-items: center; gap: 11px; margin-bottom: 18px; }
.assistant-avatar { --rag-avatar-size: 34px; --rag-avatar-radius: 11px; }
.user-avatar { --rag-avatar-size: 34px; --rag-avatar-radius: 11px; margin-top: 23px; }
.message-body { min-width: 0; flex: 1; }
.message-label { font-size: 12px; font-weight: 500; color: #7b8c9e; }
.message.user { justify-content: flex-end; }
.user .message-body { max-width: min(78%, 880px); flex: 0 1 auto; }
.user .message-label { text-align: right; margin: 0 4px 8px; }
.user-text { background: #eaf2fb; color: #325574; padding: 12px 18px; border: 1px solid #deebf5; border-radius: 15px 4px 15px 15px; line-height: 1.85; font-size: 14px; white-space: pre-wrap; overflow-wrap: anywhere; }
.general-answer-notice, .answer-notice { display: flex; align-items: flex-start; gap: 7px; margin: 0 0 15px; color: #9a7747; background: #fbf4e9; border-radius: 8px; padding: 10px 12px; font-size: 12px; line-height: 1.7; }
.general-answer-notice .el-icon, .answer-notice .el-icon { margin-top: 4px; flex-shrink: 0; }
.answer-notice { background: #edf3f9; color: #6e849c; }
.answer-error { padding: 17px 19px; border-radius: 12px; background: #fff4f1; color: #a56856; }
.answer-error strong { font-size: 14px; font-weight: 500; }
.answer-error p { font-size: 13px; line-height: 1.8; margin: 9px 0 12px; }
.answer-error button { border: 0; background: none; color: #a56856; font-size: 12px; padding: 0; cursor: pointer; }
.answer-actions { display: flex; align-items: center; gap: 18px; margin-top: 19px; }
.answer-actions button { display: inline-flex; align-items: center; gap: 6px; background: none; border: 0; font-size: 12px; color: #8b9bae; padding: 4px 0; cursor: pointer; }
.answer-actions .references-button { color: #5787af; }
.references-button > span { background: #e9f1f9; border-radius: 4px; padding: 1px 5px; margin-left: 1px; font-size: 11px; }
.composer-area { flex-shrink: 0; padding: 8px var(--chat-gutter) 12px; background: linear-gradient(0deg,#f7f9fc 80%,#f7f9fc00); }
.composer-wrap { width: 100%; max-width: var(--chat-width); margin: 0 auto; }
.composer { padding: 13px 17px 11px; border: 1px solid #dbe6f1; border-radius: 16px; background: #fff; box-shadow: 0 5px 24px #3e668d08; transition: border-color .18s, box-shadow .18s; }
.composer:focus-within { border-color: #99bfdc; box-shadow: 0 4px 22px #3e668d0e; }
.composer textarea { display: block; width: 100%; padding: 0; min-height: 46px; max-height: 180px; resize: vertical; box-sizing: border-box; border: 0; outline: none; background: transparent; color: #334d67; font: inherit; font-size: 14px; line-height: 1.8; }
.composer textarea::placeholder { color: #a1afbf; }
.composer-actions { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-top: 9px; }
.composer-actions small { color: #a2aebc; font-size: 11px; }
.send-actions { display: flex; align-items: center; justify-content: flex-end; gap: 12px; margin-left: auto; }
.send-actions .el-button { height: 34px; border-radius: 9px; padding: 0 18px; font-size: 13px; }
.send-actions .el-icon { margin-right: 5px; }
.privacy-note { margin: 9px 0 0; text-align: center; font-size: 10px; line-height: 1.7; color: #9ba8b8; }
.reference-drawer { padding: 0 5px 24px; }
.drawer-note { margin: 0 0 22px; color: #8898aa; font-size: 12px; line-height: 1.9; }
.reference-card { padding: 20px; margin-bottom: 16px; border: 1px solid #e4ebf2; border-radius: 13px; background: #fff; scroll-margin-top: 20px; }
.reference-card.selected { border-color: #94bede; background: #f8fbff; }
.reference-heading { display: flex; align-items: center; gap: 9px; color: #8295a9; font-size: 11px; }
.citation-badge { background: #e8f1fb; color: #4a82af; border-radius: 5px; padding: 3px 6px; font-size: 11px; }
.reference-card h3 { margin: 13px 0 9px; font-size: 15px; line-height: 1.75; color: #385773; font-weight: 600; overflow-wrap: anywhere; }
.reference-identifier { font-size: 11px; line-height: 1.7; color: #92a1b0; overflow-wrap: anywhere; }
.reference-excerpt { margin: 14px 0; color: #62758b; line-height: 1.9; font-size: 13px; white-space: pre-wrap; overflow-wrap: anywhere; }
.source-link { display: inline-flex; align-items: center; gap: 7px; text-decoration: none; color: #4882b0; font-size: 12px; }
button:focus-visible, a:focus-visible, summary:focus-visible { outline: 2px solid #78a6cf; outline-offset: 4px; }
.page-header { position: relative; background: linear-gradient(110deg, #fff 66%, #f5faff); }
.page-header::after { content: ''; position: absolute; height: 1px; bottom: -1px; left: 0; right: 0; background: linear-gradient(90deg, #cee1f3, #d9ece9 55%, #e7edf4); pointer-events: none; }
.page-heading h1::before { content: ''; display: inline-block; width: 4px; height: 19px; margin-right: 10px; border-radius: 3px; vertical-align: -1px; background: linear-gradient(#629cc8, #77b7ba); }
.conversation-scroll { background-image: radial-gradient(ellipse 360px 250px at 84% 8%, #dff2ef66, transparent 78%), radial-gradient(ellipse 440px 280px at 14% 2%, #e4eefb80, transparent 80%); background-repeat: no-repeat; }
.welcome-symbol { position: relative; background: linear-gradient(140deg, #e2efff, #edf8f6); border-color: #d5e7f0; box-shadow: 0 9px 28px #6e9fbb13, inset 0 1px 0 #ffffffc9; }
.welcome-symbol::before { content: ''; position: absolute; inset: -9px; border: 1px solid #dce8f1; border-radius: 28px; transform: rotate(-12deg); pointer-events: none; }
.welcome-symbol::after { content: ''; position: absolute; width: 5px; height: 5px; right: -16px; top: 5px; background: #98c7c3; border-radius: 50%; box-shadow: -84px 48px 0 -1px #a9c7e6, -70px -5px 0 -1px #b7d4df; pointer-events: none; }
.welcome-eyebrow { display: inline-flex; align-items: center; gap: 12px; }
.welcome-eyebrow::before, .welcome-eyebrow::after { content: ''; width: 22px; height: 1px; background: linear-gradient(90deg, transparent, #bdcfe0); }
.welcome-eyebrow::after { transform: rotate(180deg); }
.quick-prompts button { --prompt-color: #5b8ebc; --prompt-tint: #edf5ff; --prompt-border: #dce9f7; overflow: hidden; background: linear-gradient(135deg, #fff 62%, var(--prompt-tint)); box-shadow: 0 3px 12px #44678804; }
.quick-prompts .prompt-card-1 { --prompt-color: #579a98; --prompt-tint: #eff9f6; --prompt-border: #dceee8; }
.quick-prompts .prompt-card-2 { --prompt-color: #788fbd; --prompt-tint: #f0f4fc; --prompt-border: #e1e8f5; }
.quick-prompts button::before { content: ''; position: absolute; left: 20px; right: 50%; top: 0; height: 2px; background: linear-gradient(90deg, var(--prompt-border), transparent); pointer-events: none; }
.quick-prompts button:hover { border-color: var(--prompt-color); box-shadow: 0 8px 22px #315c8410; }
.prompt-heading { display: flex; align-items: center; gap: 9px; margin-bottom: 15px; }
.prompt-icon { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 9px; border: 1px solid var(--prompt-border); color: var(--prompt-color); background: var(--prompt-tint); flex-shrink: 0; }
.prompt-icon svg { width: 17px; height: 17px; }
.prompt-label { margin-bottom: 0; color: var(--prompt-color); }
.prompt-arrow { color: var(--prompt-color); }
.assistant .message-body { padding: 22px 28px 20px; font-size: 15px; border: 1px solid #e0e9f2; border-radius: 18px; background: linear-gradient(145deg, #fff, #fcfdff); box-shadow: 0 4px 18px #2c5c8205; }
.assistant .message-label { display: flex; align-items: center; gap: 12px; margin: 0; font-size: 13px; color: #537793; font-weight: 600; }
.assistant .message-label::after { content: ''; width: 34px; height: 1px; background: linear-gradient(90deg, #d1e1ef, transparent); }
.user-text { background: linear-gradient(125deg, #eaf2fc, #e9f4f8); box-shadow: inset 0 1px 0 #ffffff8c; }
.answer-actions { padding-top: 12px; border-top: 1px solid #edf2f7; }
.composer { position: relative; border-color: #d5e4f0; box-shadow: 0 5px 24px #3e668d0b; }
.composer::before { content: ''; position: absolute; left: 18px; right: 18px; top: 0; height: 1px; background: linear-gradient(90deg, transparent, #a7c8e3, #b5dcd4, transparent); pointer-events: none; }
.send-actions .el-button:not(.is-disabled) { background: linear-gradient(110deg, #3484bc, #3e98ab); border-color: transparent; box-shadow: 0 3px 8px #4d8eac19; }
@media (max-width: 1200px) { .page-header { padding: 18px 26px; } .header-actions { gap: 14px; } .conversation-content { padding-top: 24px; padding-bottom: 20px; } .quick-prompts { gap: 10px; } .quick-prompts button { padding: 17px 15px 30px; } }
@media (max-width: 900px) { .welcome-panel { margin-top: 5vh; } }
@media (max-width: 600px) { .system-layout { --chat-gutter: 14px; } .page-header { align-items: flex-start; gap: 12px; padding: 17px 18px; } .home-link { margin-bottom: 10px; font-size: 11px; } .page-heading h1 { font-size: 20px; } .page-heading p { max-width: 220px; font-size: 11px; margin-top: 7px; } .header-actions { flex-direction: column; align-items: flex-end; gap: 12px; } .service-status { font-size: 10px; gap: 5px; } .new-chat { height: 30px; font-size: 11px; padding: 0 10px; } .access-settings { padding: 7px 18px; } .access-key-row { flex-wrap: wrap; gap: 8px; } .access-key-row .el-input { width: calc(100% - 70px); } .conversation-content { padding: 18px var(--chat-gutter); } .welcome-panel { margin: 18px auto 6px; } .welcome-symbol { width: 52px; height: 52px; border-radius: 17px; font-size: 25px; margin-bottom: 16px; } .welcome-panel h2 { font-size: 24px; margin: 11px 0; } .welcome-panel > p { font-size: 12px; padding: 0 16px; } .quick-prompts { grid-template-columns: 1fr; gap: 9px; margin-top: 25px; } .quick-prompts button { min-height: auto; padding: 14px 34px 14px 16px; border-radius: 11px; } .prompt-label { margin-bottom: 4px; font-size: 10px; } .prompt-question { font-size: 12px; } .prompt-arrow { right: 15px; bottom: 19px; } .message-list { gap: 18px; } .message { gap: 9px; } .assistant-avatar, .user-avatar { --rag-avatar-size: 29px; --rag-avatar-radius: 10px; } .user-avatar { margin-top: 20px; } .assistant-heading { gap: 9px; margin-bottom: 14px; } .message-label { font-size: 11px; } .user .message-body { max-width: calc(100% - 38px); } .user-text { padding: 12px 15px; font-size: 13px; } .composer-area { padding: 7px var(--chat-gutter) max(10px, env(safe-area-inset-bottom)); } .composer { padding: 12px 13px 10px; border-radius: 13px; } .composer textarea { min-height: 47px; font-size: 16px; } .keyboard-hint { display: none; } .privacy-note { margin: 9px 5px 0; font-size: 9px; } .general-answer-notice, .answer-notice { font-size: 11px; } .reference-card { padding: 16px; } }
@media (prefers-reduced-motion: reduce) { .conversation-scroll { scroll-behavior: auto; } .quick-prompts button { transition: none; } .quick-prompts button:hover { transform: none; } }
@media (max-width: 600px) { .page-heading h1::before { height: 16px; width: 3px; margin-right: 8px; } .conversation-scroll { background-size: 100% 380px; } .welcome-symbol::before { inset: -7px; border-radius: 23px; } .welcome-symbol::after { right: -12px; width: 4px; height: 4px; box-shadow: -67px 37px 0 -1px #a9c7e6; } .quick-prompts button { padding-left: 58px; } .prompt-heading { margin-bottom: 4px; } .prompt-label { margin-bottom: 0; } .prompt-icon { position: absolute; left: 15px; top: 19px; } .assistant .message-body { padding: 16px 16px 15px; border-radius: 15px; font-size: 14px; } .assistant .message-label { margin: 0; font-size: 12px; } .answer-actions { padding-top: 10px; margin-top: 15px; } }

@media screen and (max-width: 1024px) {
  .page-header { padding: 16px 22px; }
  .welcome-panel { margin-top: 26px; }
  .quick-prompts { grid-template-columns: repeat(3,minmax(0,1fr)); }
}
@media screen and (max-width: 600px) {
  .page-header { padding: 12px 14px; gap: 10px; }
  .page-heading { min-width: 0; }
  .page-heading h1 { font-size: 18px; }
  .page-heading p { max-width: 190px; }
  .home-link { margin-bottom: 6px; }
  .header-actions { flex-shrink: 0; gap: 6px; }
  .quick-prompts { grid-template-columns: 1fr; }
  .service-status { min-height: 32px; }
  .composer-area { flex-shrink: 0; }
  .answer-actions { flex-wrap: wrap; }
  .send-actions .el-button { min-height: 40px; }
}
@media screen and (max-width: 360px) {
  .page-heading p { max-width: 165px; }
  .page-heading h1 { font-size: 17px; }
  .welcome-panel h2 { font-size: 21px; }
}
</style>
