<template>
  <div class="system-layout">
    <Sidebar default-active="6" />
    <main class="main-content">
      <header class="page-header">
        <NuxtLink to="/" class="home-link"><el-icon><ArrowLeft /></el-icon> 首页</NuxtLink>
        <span class="header-divider">/</span><h1>医学检索问答 · 本地 RAG</h1>
        <el-tag effect="plain">辅助研究，不替代诊疗判断</el-tag>
      </header>

      <div class="page-container">
        <section class="runtime-panel" aria-label="检索与模型状态">
          <div class="runtime-heading">
            <div><span class="eyebrow">LOCAL RETRIEVAL · LOCAL GENERATION</span><h2>优先参考检索原文，信息不足时明确提示</h2></div>
            <el-button :loading="checkingStatus" :disabled="isGenerating" @click="refreshStatus"><el-icon><RefreshRight /></el-icon> 刷新状态</el-button>
          </div>
          <div class="runtime-grid">
            <div class="runtime-item">
              <span class="runtime-label">检索库</span><strong>{{ corpusName }}</strong>
              <span :class="['state-label', { ready: corpusReady }]">{{ corpusReady ? '预检通过' : '未就绪' }}</span>
              <small v-if="corpusCount !== null">{{ corpusCount.toLocaleString() }} 个切块（后端报告）</small>
              <small>预检不等于全文检索或问答验收；以实际请求结果为准。</small>
            </div>
            <div class="runtime-item">
              <span class="runtime-label">本地生成模型</span>
              <el-select v-model="currentModel" :disabled="isGenerating || !localModels.length" placeholder="暂无可用模型" aria-label="本地生成模型">
                <el-option v-for="model in localModels" :key="model.name" :label="`${model.name}${model.ready ? '' : '（未就绪）'}`" :value="model.name" :disabled="!model.ready" />
              </el-select>
              <span :class="['state-label', { ready: modelReady }]">{{ modelReady ? '服务就绪' : '服务未就绪' }}</span>
            </div>
            <div class="runtime-item">
              <span class="runtime-label">检索预检</span><strong>{{ retrievalState.label }}</strong>
              <span :class="['state-label', { ready: retrievalReady }]">{{ retrievalReady ? '检索依赖就绪' : '检索依赖未就绪' }}</span>
              <small>以每次回答返回的执行信息为准，不模拟稠密检索。</small>
            </div>
          </div>
          <div class="channel-status-grid">
            <div><strong>BM25 词法通路</strong><span :class="{ 'channel-ready': retrievalState.bm25.ready === true }">{{ channelStatusLabel(retrievalState.bm25.ready) }}</span><small>{{ retrievalState.bm25.scope || '范围由实际请求报告' }}</small></div>
            <div><strong>MedCPT 向量通路</strong><span :class="{ 'channel-ready': retrievalState.medcpt.ready === true }">{{ channelStatusLabel(retrievalState.medcpt.ready) }}</span><small>{{ retrievalState.medcpt.scope || '独立召回范围尚未提供' }}</small></div>
          </div>
          <el-alert v-if="retrievalState.warning && runtimeStatus" :title="retrievalState.warning" type="warning" :closable="false" show-icon />
          <div v-if="!publicDemo" class="access-key-row">
            <label for="rag-access-key">服务器访问密钥</label>
            <el-input id="rag-access-key" v-model="accessKey" type="password" autocomplete="off" placeholder="仅存于本次浏览器内存；本地未设密钥可留空" :disabled="isGenerating || checkingStatus" @keydown.enter.prevent="applyAccessKey" />
            <el-button :disabled="isGenerating || checkingStatus" @click="applyAccessKey">应用并检查</el-button>
            <el-button text :disabled="isGenerating || checkingStatus" @click="clearAccessKey">清除</el-button>
          </div>
          <el-alert v-if="statusError" :title="statusError" type="error" :closable="false" show-icon />
          <el-alert v-else-if="!canSend && !checkingStatus && !isGenerating" title="模型服务或问答接口未就绪。请检查后端配置并刷新状态；系统不会提供模拟答案。" type="warning" :closable="false" show-icon />
          <el-alert v-else-if="canSend && (!corpusReady || !retrievalReady)" title="模型可用，检索依赖尚未全部就绪。仍可提问；未获得足够检索信息时，回答将明确标为模型一般知识，而不是检索文献支持的结论。" type="warning" :closable="false" show-icon />
          <div v-if="statusWarnings.length" class="warning-list" role="status"><p v-for="(warning, index) in statusWarnings" :key="index"><el-icon><Warning /></el-icon>{{ warning }}</p></div>
        </section>

        <section v-if="!chatHistory.length" class="welcome-panel">
          <el-icon class="welcome-icon"><Reading /></el-icon><h2>从问题到原文，保留每一步的边界</h2>
          <p>优先使用检索到的切块回答；检索信息不足或中文概念未匹配时，仍由真实模型回答，并明确标注未获检索文献支持。只有实际返回的文献才展示出处。</p>
          <div class="quick-prompts"><button v-for="prompt in quickPrompts" :key="prompt" :disabled="isGenerating" @click="usePrompt(prompt)">{{ prompt }} <span>↗</span></button></div>
        </section>

        <section v-else ref="messageListRef" class="message-list" aria-label="问答记录" aria-live="polite">
          <article v-for="msg in chatHistory" :key="msg.id" :class="['message', msg.role]">
            <div class="message-avatar"><el-icon v-if="msg.role === 'assistant'"><Monitor /></el-icon><el-icon v-else><User /></el-icon></div>
            <div class="message-body">
              <div class="message-label">{{ msg.role === 'user' ? '我的问题' : '本地检索问答' }}</div>
              <div v-if="msg.loading" class="loading-line" role="status"><el-icon class="is-loading"><Loading /></el-icon> 等待后端检索与生成结果；尚未确认任何执行阶段。</div>
              <el-alert v-else-if="msg.error" :title="msg.error" description="此次请求失败，未生成有效回答。可以检查状态后重新提交；系统没有使用模板内容兜底。" type="error" :closable="false" show-icon />
              <template v-else>
                <el-alert v-if="msg.role === 'assistant' && isGeneralKnowledgeAnswer(msg)" class="general-answer-notice" :title="generalKnowledgeNotice" type="warning" :closable="false" show-icon />
                <!-- 文本插值：模型、语料及用户输入均不直接执行 HTML。 -->
                <div class="answer-text">{{ msg.content }}</div>
                <template v-if="msg.role === 'assistant'">
                  <el-alert v-if="msg.status === 'insufficient_evidence'" title="当前检索结果不足以支持回答。请补充实体、结局或问题范围；这不表示不存在相关证据。" type="warning" :closable="false" show-icon />
                  <div class="execution-meta">
                    <span>模型：{{ msg.model?.name || '后端未提供' }}</span><span>后端：{{ msg.model?.backend || '后端未提供' }}</span>
                    <span>回答方式：{{ isGeneralKnowledgeAnswer(msg) ? '模型一般知识（未获检索支持）' : '检索问答' }}</span>
                    <span>检索：{{ messageRetrieval(msg).label }}</span><span v-if="!isGeneralKnowledgeAnswer(msg)">切块来源：{{ msg.corpusName }}</span>
                    <span v-if="msg.timings?.total_ms !== undefined">耗时：{{ Number(msg.timings.total_ms).toLocaleString() }} ms</span>
                  </div>
                  <el-alert v-if="messageRetrieval(msg).warning" :title="messageRetrieval(msg).warning" type="warning" :closable="false" show-icon />
                  <div class="channel-execution">
                    <span>BM25：{{ channelStatusLabel(messageRetrieval(msg).bm25.ready) }} · 返回 {{ msg.sparseHits.length }} 条</span>
                    <span>MedCPT：{{ channelStatusLabel(messageRetrieval(msg).medcpt.ready) }} · 返回 {{ msg.denseHits.length }} 条</span>
                    <small v-if="messageRetrieval(msg).medcpt.scope">MedCPT 范围：{{ messageRetrieval(msg).medcpt.scope }}</small>
                  </div>
                  <div v-if="msg.warnings.length" class="warning-list"><p v-for="(warning, warningIndex) in msg.warnings" :key="warningIndex"><el-icon><Warning /></el-icon>{{ warning }}</p></div>
                  <div v-if="!isGeneralKnowledgeAnswer(msg)" class="evidence-overview">
                    <div><strong>融合后上下文切块 {{ msg.evidenceCards.length }}</strong><span>正文标记引用 {{ citedCards(msg).length }} · BM25 原始候选 {{ msg.sparseHits.length }} · MedCPT 原始候选 {{ msg.denseHits.length }}</span><small v-if="msg.retrieval?.candidate_count !== undefined">两路去重候选总数：{{ msg.retrieval.candidate_count }}（不是两路数量相加，也不是论文数）</small></div>
                    <el-button v-if="msg.evidenceCards.length || msg.sparseHits.length || msg.denseHits.length || msg.boundaries.length" plain @click="openEvidenceDrawer(msg)"><el-icon><Collection /></el-icon> 查看原文与出处</el-button>
                  </div>
                  <div v-else-if="msg.sparseHits.length || msg.denseHits.length || msg.boundaries.length" class="evidence-overview">
                    <div><strong>候选材料未用于支持本次回答</strong><span>不展示正文引用，不将候选材料算作已引用文献。</span></div>
                    <el-button plain @click="openEvidenceDrawer(msg)"><el-icon><Collection /></el-icon> 查看检索候选</el-button>
                  </div>
                  <p v-if="!isGeneralKnowledgeAnswer(msg)" class="evidence-disclaimer">“正文标记引用”仅表示模型在回答中使用了该编号；未进行人工评价、引用蕴含验证或临床有效性确认。RRF 是基于排名的融合分数，不是概率、医学证据等级或结论可信度。</p>
                  <div v-if="msg.evidenceCards.length" class="inline-evidence">
                    <button v-for="(card, index) in msg.evidenceCards.slice(0, 3)" :key="`${card.chunk_id}-${index}`" class="evidence-preview" @click="openChunkDetail(card)"><span :class="['citation-badge', { cited: card.is_cited }]">{{ card.citation_id || '候选' }}</span><span>{{ card.title || '标题未提供' }}</span><small>{{ card.is_cited ? '正文标记引用 · 未核验' : '检索候选 · 未被正文引用' }}</small></button>
                  </div>
                  <el-button class="copy-answer" text :disabled="!msg.content" @click="copyText(msg.content)"><el-icon><DocumentCopy /></el-icon> 复制回答</el-button>
                </template>
              </template>
            </div>
          </article>
        </section>

        <section class="composer" aria-label="输入问题">
          <textarea v-model="userInput" placeholder="职业铅暴露与高血压的关系有哪些人群研究证据？" :disabled="isGenerating" :maxlength="2000" rows="3" aria-label="医学检索问题" @keydown="handleInputKeydown" />
          <div class="composer-actions">
            <div class="composer-tools"><el-switch v-model="enableDeepThink" :disabled="isGenerating" active-text="扩展检索" /><small>按后端支持启用，不展示模拟思考过程。</small></div>
            <div class="send-actions"><small>{{ userInput.length }}/2000 · Enter 发送 · Shift + Enter 换行</small><el-button type="primary" :loading="isGenerating" :disabled="!userInput.trim() || !canSend" @click="sendMessage"><el-icon><Position /></el-icon> {{ isGenerating ? '处理中' : '发送' }}</el-button></div>
          </div>
          <p class="privacy-note">当前不提供联网检索、附件上传或私有知识库创建。请勿输入姓名、证件号等可识别个人身份的信息。</p>
        </section>
      </div>

      <el-drawer v-model="evidenceDrawerVisible" title="检索切块 · 原文与出处" size="min(780px, 100vw)" destroy-on-close>
        <template v-if="activeDrawerMsg">
          <p v-if="isGeneralKnowledgeAnswer(activeDrawerMsg)" class="drawer-note">本次回答未获得足够检索信息。以下仅为检索候选，不是本次回答的引用文献，也不表示支持该回答。</p>
          <p v-else class="drawer-note">BM25 与 MedCPT 标签展示各路真实原始候选；融合后上下文切块才用于模型输入。候选材料不等同于支持结论，正文引用未经过人工核验。原文是本地切块，并非完整论文。</p>
          <el-alert v-if="messageRetrieval(activeDrawerMsg).warning" :title="messageRetrieval(activeDrawerMsg).warning" type="warning" :closable="false" show-icon />
          <el-tabs v-model="drawerActiveTab">
            <el-tab-pane v-if="!isGeneralKnowledgeAnswer(activeDrawerMsg)" :label="`融合上下文 (${activeDrawerMsg.evidenceCards.length})`" name="candidates" /><el-tab-pane v-if="!isGeneralKnowledgeAnswer(activeDrawerMsg)" :label="`正文标记引用 (${citedCards(activeDrawerMsg).length})`" name="cited" />
            <el-tab-pane :label="`BM25 原始候选 (${activeDrawerMsg.sparseHits.length})`" name="sparse" /><el-tab-pane :label="`MedCPT 原始候选 (${activeDrawerMsg.denseHits.length})`" name="dense" />
            <el-tab-pane v-if="activeDrawerMsg.boundaries.length" :label="`规范条款候选 (${activeDrawerMsg.boundaries.length})`" name="boundaries" />
          </el-tabs>
          <el-empty v-if="!drawerCards.length" description="此分类没有返回切块，不使用预设数量或替代材料。" />
          <button v-for="(card, index) in drawerCards" :key="`${card.chunk_id}-${index}`" class="evidence-card" @click="openChunkDetail(card)">
            <div class="card-heading"><span :class="['citation-badge', { cited: card.is_cited }]">{{ card.citation_id || `候选 ${index + 1}` }}</span><span>{{ card.is_cited ? '正文标记引用 · 未核验' : '检索候选' }}</span></div>
            <h3>{{ card.title || '标题未提供' }}</h3><p class="card-source">{{ sourceLabel(card) }} · {{ card.standard_no_or_doi || card.doi || (card.pmid ? `PMID ${card.pmid}` : '文献编号未提供') }}</p><p class="card-text">{{ card.text }}</p>
            <div class="card-footer"><span>{{ retrievalChannelLabel(card) }}</span><span v-if="isRank(card.bm25_rank)">BM25 排名 {{ card.bm25_rank }}</span><span v-if="isRank(card.dense_rank)">MedCPT 排名 {{ card.dense_rank }}</span><span v-if="isFiniteScore(card.rrf_score)">RRF 融合分 {{ formatScore(card.rrf_score) }}</span><span>查看切块详情 →</span></div>
          </button>
        </template>
      </el-drawer>

      <el-dialog v-model="chunkDetailVisible" title="检索切块原文" width="min(780px, 95vw)" append-to-body>
        <template v-if="selectedChunk">
          <el-alert :title="selectedChunk.is_cited ? '模型正文标记引用；未进行人工核验或结论支持性确认。' : '检索候选材料；不能据此认定支持回答。'" type="info" :closable="false" show-icon />
          <dl class="chunk-metadata">
            <dt>标题</dt><dd>{{ selectedChunk.title || '未提供' }}</dd><dt>来源</dt><dd>{{ sourceLabel(selectedChunk) }}</dd><dt>切块编号</dt><dd>{{ selectedChunk.chunk_id || '未提供' }}</dd>
            <dt>文献标识</dt><dd>{{ selectedChunk.standard_no_or_doi || selectedChunk.doi || (selectedChunk.pmid ? `PMID ${selectedChunk.pmid}` : '未提供，不生成占位编号') }}</dd><dt>人工评价</dt><dd>{{ selectedChunk.priority_label || '未人工评价' }}</dd>
            <dt v-if="selectedChunk.section_title">章节</dt><dd v-if="selectedChunk.section_title">{{ selectedChunk.section_title }}</dd>
            <dt>召回通路</dt><dd>{{ retrievalChannelLabel(selectedChunk) }}</dd>
            <dt v-if="isRank(selectedChunk.bm25_rank)">BM25 排名</dt><dd v-if="isRank(selectedChunk.bm25_rank)">{{ selectedChunk.bm25_rank }}</dd>
            <dt v-if="isRank(selectedChunk.dense_rank)">MedCPT 排名</dt><dd v-if="isRank(selectedChunk.dense_rank)">{{ selectedChunk.dense_rank }}</dd>
            <dt v-if="isFiniteScore(selectedChunk.rrf_score)">RRF 融合分</dt><dd v-if="isFiniteScore(selectedChunk.rrf_score)">{{ formatScore(selectedChunk.rrf_score) }}（不是概率或证据可信度）</dd>
          </dl>
          <a v-if="sourceUrl(selectedChunk)" :href="sourceUrl(selectedChunk)" target="_blank" rel="noopener noreferrer" class="source-link">打开来源链接（外部网站） ↗</a>
          <h3 class="original-label">语料中的切块原文</h3><div class="original-text">{{ selectedChunk.text || '本次响应未提供原文。' }}</div>
          <template v-if="selectedChunk.context_excerpt"><h3 class="original-label">实际模型上下文节选{{ selectedChunk.excerpt_truncated ? '（已截断）' : '' }}</h3><div class="original-text">{{ selectedChunk.context_excerpt }}</div></template>
        </template>
        <template #footer><el-button @click="chunkDetailVisible = false">关闭</el-button><el-button type="primary" :disabled="!selectedChunk?.text" @click="copyText(selectedChunk?.text || '')">复制原文</el-button></template>
      </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Collection, DocumentCopy, Loading, Monitor, Position, Reading, RefreshRight, User, Warning } from '@element-plus/icons-vue'
import { plainAnswer, sourceLabel, sourceUrl, retrievalPresentation, retrievalChannelLabel, chatAvailability, isGeneralKnowledgeAnswer, generalKnowledgeNotice, responseEvidence } from '~/utils/ragPresentation'
import type { EvidenceCard, RagMessage } from '~/utils/ragPresentation'

const { agentChat, getAgentStatus, getModels, setApiKey } = useApi()
const publicDemo = String(useRuntimeConfig().public.publicDemo) === 'true'
const accessKey = ref('')
const runtimeStatus = ref<Record<string, any> | null>(null)
const statusError = ref('')
const checkingStatus = ref(false)
const localModels = ref<{ name: string; ready: boolean }[]>([])
const currentModel = ref('Llama-3.1-8B')
const userInput = ref('')
const enableDeepThink = ref(true)
const isGenerating = ref(false)
const chatHistory = ref<RagMessage[]>([])
const messageListRef = ref<HTMLElement | null>(null)
const evidenceDrawerVisible = ref(false)
const activeDrawerMsg = ref<RagMessage | null>(null)
const drawerActiveTab = ref('candidates')
const chunkDetailVisible = ref(false)
const selectedChunk = ref<EvidenceCard | null>(null)
let nextMessageId = 0

// 常用医学问题示例；未知中文概念也允许提交，不暗示已成功翻译或检索。
const quickPrompts = ['职业铅暴露与高血压的关系有哪些人群研究证据？', '镉暴露与肾损伤有哪些人体研究证据？', '砷与镉暴露有哪些人体研究证据？']
const corpusReady = computed(() => runtimeStatus.value?.corpus?.ready === true)
const modelReady = computed(() => runtimeStatus.value?.model?.ready === true && localModels.value.some(model => model.name === currentModel.value && model.ready))
const retrievalState = computed(() => retrievalPresentation(runtimeStatus.value?.retrieval))
const retrievalReady = computed(() => retrievalState.value.ready)
const canSend = computed(() => chatAvailability(runtimeStatus.value, modelReady.value, retrievalReady.value) && !checkingStatus.value && !isGenerating.value)
const corpusName = computed(() => runtimeStatus.value?.corpus?.name || runtimeStatus.value?.corpus?.corpus_name || '本地检索库（名称未提供）')
const corpusCount = computed(() => { const count = runtimeStatus.value?.corpus?.chunk_count ?? runtimeStatus.value?.corpus?.total_chunks; return typeof count === 'number' && Number.isFinite(count) ? count : null })
const statusWarnings = computed(() => {
  const warnings = [...(runtimeStatus.value?.warnings || [])]
  if (runtimeStatus.value?.model?.error) warnings.push(runtimeStatus.value.model.error)
  if (runtimeStatus.value?.corpus?.error) warnings.push(runtimeStatus.value.corpus.error)
  if (retrievalState.value.bm25.error) warnings.push(retrievalState.value.bm25.error)
  if (retrievalState.value.medcpt.error) warnings.push(retrievalState.value.medcpt.error)
  return warnings.map(String)
})
const channelStatusLabel = (ready: boolean | null) => ready === true ? '可用（后端报告）' : ready === false ? '不可用' : '未报告'
const messageRetrieval = (msg: RagMessage) => retrievalPresentation(msg.retrieval, { bm25: msg.sparseHits.length, medcpt: msg.denseHits.length })
const citedCards = (msg: RagMessage) => msg.evidenceCards.filter(card => card.is_cited)
const drawerCards = computed(() => {
  const msg = activeDrawerMsg.value
  if (!msg) return []
  if (drawerActiveTab.value === 'cited') return citedCards(msg)
  if (drawerActiveTab.value === 'sparse') return msg.sparseHits
  if (drawerActiveTab.value === 'dense') return msg.denseHits
  if (drawerActiveTab.value === 'boundaries') return msg.boundaries
  return msg.evidenceCards
})
const isFiniteScore = (score: unknown) => typeof score === 'number' && Number.isFinite(score)
const isRank = (rank: unknown) => typeof rank === 'number' && Number.isInteger(rank) && rank > 0
const formatScore = (score: number | undefined) => typeof score === 'number' ? score.toFixed(6) : '未提供'

const refreshStatus = async () => {
  if (checkingStatus.value || isGenerating.value) return
  checkingStatus.value = true
  statusError.value = ''
  try {
    const [statusResult, modelResult] = await Promise.all([getAgentStatus(), getModels()])
    if (!statusResult.success || !statusResult.data) throw new Error(statusResult.error || '无法获取 RAG 服务状态')
    runtimeStatus.value = statusResult.data as Record<string, any>
    if (!modelResult.success || !modelResult.data) throw new Error(modelResult.error || '无法获取模型列表')
    const payload = modelResult.data as Record<string, any>
    localModels.value = (Array.isArray(payload.models) ? payload.models : []).filter((model: any) => model && typeof model.name === 'string').map((model: any) => ({ name: model.name, ready: model.ready === true }))
    if (!localModels.value.some(model => model.name === currentModel.value)) currentModel.value = payload.default || localModels.value[0]?.name || ''
  } catch (error: any) {
    runtimeStatus.value = null
    localModels.value = []
    statusError.value = error?.message || '获取服务状态失败'
  } finally { checkingStatus.value = false }
}
const applyAccessKey = () => { if (publicDemo) return; setApiKey(accessKey.value); accessKey.value = ''; refreshStatus() }
const clearAccessKey = () => { if (publicDemo) return; setApiKey(''); accessKey.value = ''; refreshStatus() }
const scrollToBottom = async () => { await nextTick(); messageListRef.value?.scrollTo({ top: messageListRef.value.scrollHeight, behavior: 'smooth' }) }
const usePrompt = (prompt: string) => { userInput.value = prompt }
const handleInputKeydown = (event: KeyboardEvent) => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); sendMessage() } }
const openEvidenceDrawer = (msg: RagMessage) => { activeDrawerMsg.value = msg; drawerActiveTab.value = isGeneralKnowledgeAnswer(msg) ? (msg.sparseHits.length ? 'sparse' : msg.denseHits.length ? 'dense' : 'boundaries') : 'candidates'; evidenceDrawerVisible.value = true }
const openChunkDetail = (card: EvidenceCard) => { selectedChunk.value = card; chunkDetailVisible.value = true }
const copyText = async (content: string) => {
  try {
    if (!navigator.clipboard?.writeText) throw new Error('浏览器未开放剪贴板权限，请使用 HTTPS 或手动选择文字复制。')
    await navigator.clipboard.writeText(content)
    ElMessage.success('已复制到剪贴板')
  } catch (error: any) { ElMessage.error(error?.message || '复制失败，请手动选择文字复制。') }
}
const makeMessage = (role: 'user' | 'assistant', content: string): RagMessage => ({ id: ++nextMessageId, role, content, loading: false, error: '', status: '', answerMode: '', evidenceSupport: '', evidenceCards: [], boundaries: [], sparseHits: [], denseHits: [], warnings: [], corpusName: corpusName.value, model: {}, retrieval: {}, dualPathSummary: {}, timings: {} })
const sendMessage = async () => {
  const question = userInput.value.trim()
  if (!question || isGenerating.value) return
  if (question.length > 2000) { ElMessage.warning('问题超过 2000 字符，请缩短后提交。'); return }
  if (!canSend.value) { ElMessage.warning('模型服务或问答接口未就绪，请先刷新服务状态。'); return }
  // 仅发送成功完成的往轮，排除失败提示、UI 元信息及当前问题。
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
  userInput.value = ''
  isGenerating.value = true
  scrollToBottom()
  try {
    const result = await agentChat(question, { model: currentModel.value, history: history.slice(-12), enableDeepThink: enableDeepThink.value })
    if (!result.success || !result.data) throw new Error(result.error || '问答请求失败')
    const data = result.data as Record<string, any>
    const content = plainAnswer(data)
    if (!content && data.status !== 'insufficient_evidence') throw new Error('后端未返回回答内容，不能判定生成成功。')
    const msg = chatHistory.value[messageIndex]!
    msg.content = content || '检索结果不足以生成有依据的回答。'
    msg.status = String(data.status || 'answered')
    msg.answerMode = String(data.answer_mode || '')
    msg.evidenceSupport = String(data.evidence_support || '')
    Object.assign(msg, responseEvidence(data))
    msg.warnings = Array.isArray(data.warnings) ? data.warnings.map(String) : []
    msg.model = data.model && typeof data.model === 'object' ? data.model : {}
    msg.retrieval = data.retrieval && typeof data.retrieval === 'object' ? data.retrieval : {}
    msg.dualPathSummary = data.dual_path_summary && typeof data.dual_path_summary === 'object' ? data.dual_path_summary : {}
    msg.timings = data.timings && typeof data.timings === 'object' ? data.timings : {}
    msg.corpusName = data.corpus?.name || corpusName.value
  } catch (error: any) { chatHistory.value[messageIndex]!.error = error?.message || '问答请求失败' }
  finally { chatHistory.value[messageIndex]!.loading = false; isGenerating.value = false; scrollToBottom() }
}
onMounted(refreshStatus)
</script>

<style scoped>
.system-layout { display: flex; min-height: 100vh; background: #f5f8fc; color: #172b45; }
.main-content { flex: 1; min-width: 0; }
.system-layout :deep(.sidebar) { position: sticky; top: 0; height: 100vh; }
.page-header { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; min-height: 80px; padding: 18px 36px; border-bottom: 1px solid #e2e8f0; background: white; }
.page-header h1 { margin: 0; flex: 1; font-size: 20px; font-weight: 650; }
.home-link { display: flex; gap: 6px; align-items: center; text-decoration: none; color: #1f77b4; }
.header-divider { color: #cbd5e1; }
.page-container { max-width: 1160px; margin: 0 auto; padding: 28px 32px 40px; }
.runtime-panel { background: white; border: 1px solid #dce6f1; border-radius: 18px; padding: 24px; box-shadow: 0 6px 24px #173d6710; }
.runtime-heading { display: flex; justify-content: space-between; gap: 20px; align-items: center; }
.eyebrow { color: #4780af; font-size: 10px; letter-spacing: 1.8px; font-weight: 700; }
.runtime-heading h2 { margin: 8px 0 0; font-size: 20px; }
.runtime-grid { display: grid; grid-template-columns: 1fr 1.1fr 1fr; gap: 20px; margin: 24px 0 16px; }
.runtime-item { display: flex; flex-direction: column; align-items: flex-start; gap: 8px; min-width: 0; padding-right: 16px; border-right: 1px solid #edf1f7; }
.runtime-item:last-child { border: 0; }
.runtime-item strong { overflow-wrap: anywhere; font-size: 14px; }
.runtime-item .el-select { width: 100%; max-width: 300px; }
.runtime-label { color: #66788f; font-size: 12px; }
.state-label { color: #b45309; font-size: 12px; }
.state-label::before { content: '●'; margin-right: 6px; font-size: 9px; }
.state-label.ready { color: #158065; }
.runtime-item small { color: #718096; font-size: 11px; line-height: 1.6; }
.channel-status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 14px 0; }
.channel-status-grid > div { display: flex; flex-wrap: wrap; gap: 6px 12px; padding: 12px 14px; border: 1px solid #e4ebf3; border-radius: 10px; background: #f9fbfe; }
.channel-status-grid strong { font-size: 12px; color: #456783; }
.channel-status-grid span { margin-left: auto; font-size: 11px; color: #a96724; }
.channel-status-grid span.channel-ready { color: #158065; }
.channel-status-grid small { flex-basis: 100%; color: #7e8ea1; font-size: 10px; overflow-wrap: anywhere; }
.channel-execution { display: flex; flex-wrap: wrap; gap: 8px 16px; padding: 10px 0; color: #597692; font-size: 11px; }
.channel-execution small { flex-basis: 100%; color: #8a98a9; overflow-wrap: anywhere; }
.access-key-row { display: flex; align-items: center; gap: 10px; margin: 18px 0; }
.access-key-row label { flex-shrink: 0; color: #66788f; font-size: 12px; }
.access-key-row .el-input { max-width: 430px; }
.warning-list { margin: 10px 0; color: #9a611b; font-size: 12px; line-height: 1.7; }
.warning-list p { display: flex; gap: 8px; align-items: flex-start; margin: 4px 0; overflow-wrap: anywhere; }
.general-answer-notice { margin-bottom: 14px; border: 1px solid #eac58b; }
.warning-list .el-icon { margin-top: 4px; flex-shrink: 0; }
.welcome-panel { text-align: center; max-width: 740px; margin: 42px auto 32px; }
.welcome-icon { background: #e4effc; color: #1f77b4; font-size: 25px; width: 58px; height: 58px; border-radius: 18px; }
.welcome-panel h2 { font-size: 24px; margin: 20px 0 14px; }
.welcome-panel > p { color: #687b92; font-size: 14px; line-height: 1.9; }
.quick-prompts { display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-top: 24px; }
.quick-prompts button { display: flex; justify-content: space-between; gap: 12px; font-size: 12px; color: #3b5f81; border: 1px solid #d9e5f1; background: white; padding: 12px 16px; border-radius: 10px; cursor: pointer; text-align: left; }
.quick-prompts button:hover { border-color: #7fa9d4; background: #f0f7ff; }
.message-list { max-height: calc(100vh - 410px); min-height: 280px; overflow-y: auto; padding: 32px 8px; scroll-behavior: smooth; }
.message { display: flex; align-items: flex-start; gap: 14px; margin-bottom: 30px; }
.message-avatar { display: grid; place-items: center; color: #1f77b4; background: #e5effc; width: 36px; height: 36px; border-radius: 12px; flex: 0 0 36px; }
.message.user .message-avatar { background: #e2e8f0; color: #526276; }
.message-body { min-width: 0; flex: 1; padding: 16px 20px; background: white; border-radius: 0 16px 16px; border: 1px solid #e4ebf3; }
.message.user .message-body { background: #edf4fc; }
.message-label { color: #66809b; font-size: 11px; margin-bottom: 10px; font-weight: 650; }
.answer-text { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.85; font-size: 14px; color: #253b53; }
.loading-line { display: flex; gap: 8px; align-items: center; color: #647a93; font-size: 13px; }
.execution-meta { display: flex; gap: 6px 16px; flex-wrap: wrap; padding: 12px 0; border-bottom: 1px solid #eaf0f6; font-size: 11px; color: #718096; overflow-wrap: anywhere; }
.evidence-overview { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-top: 18px; }
.evidence-overview > div { display: flex; flex-direction: column; gap: 6px; }
.evidence-overview strong { font-size: 13px; color: #355c80; }
.evidence-overview span, .evidence-overview small { font-size: 11px; color: #7b8b9d; }
.evidence-disclaimer { color: #8a6b42; font-size: 11px; line-height: 1.7; margin: 12px 0; }
.inline-evidence { display: grid; gap: 8px; }
.evidence-preview { display: flex; gap: 10px; align-items: center; text-align: left; border: 1px solid #e4ebf3; padding: 10px; border-radius: 9px; background: #f8fafd; cursor: pointer; color: #354e68; font-size: 12px; }
.evidence-preview > span:nth-child(2) { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.evidence-preview small { color: #7d8da0; font-size: 10px; }
.citation-badge { display: inline-block; font-size: 11px; color: #55728d; background: #e7edf3; border-radius: 5px; padding: 3px 6px; flex-shrink: 0; }
.citation-badge.cited { color: #1b6f80; background: #dff2f3; }
.copy-answer { margin-top: 12px; color: #6984a0; }
.composer { position: sticky; bottom: 16px; border: 1px solid #cddcec; border-radius: 16px; background: white; padding: 18px 22px 10px; box-shadow: 0 10px 36px #173d6714; margin-top: 24px; }
.composer textarea { width: 100%; resize: vertical; min-height: 76px; max-height: 240px; border: 0; outline: 0; color: #253b53; font-size: 14px; line-height: 1.8; background: transparent; font-family: inherit; }
.composer textarea::placeholder { color: #93a2b4; }
.composer-actions { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin: 8px 0 10px; }
.composer-tools { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.composer-actions small { color: #8b99a9; font-size: 10px; }
.send-actions { display: flex; gap: 12px; align-items: center; }
.privacy-note { font-size: 10px; color: #8a98a9; margin: 0; padding-top: 10px; border-top: 1px solid #f0f3f7; }
.drawer-note { padding: 12px 16px; background: #f6f9fd; color: #6e8096; font-size: 12px; line-height: 1.8; border-radius: 10px; }
.evidence-card { display: block; text-align: left; width: 100%; border: 1px solid #dfe8f2; border-radius: 12px; padding: 16px; margin-bottom: 14px; cursor: pointer; background: white; font-family: inherit; color: #334d68; }
.evidence-card:hover { border-color: #83add4; background: #fbfdff; }
.card-heading, .card-footer { display: flex; justify-content: space-between; align-items: center; gap: 10px; font-size: 11px; color: #7b8fa3; }
.evidence-card h3 { font-size: 14px; line-height: 1.6; margin: 12px 0 6px; }
.card-source { color: #6a849f; font-size: 11px; overflow-wrap: anywhere; }
.card-text { display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.8; font-size: 12px; color: #667b91; white-space: pre-wrap; }
.card-footer { padding-top: 10px; border-top: 1px solid #edf2f7; flex-wrap: wrap; }
.chunk-metadata { display: grid; grid-template-columns: 90px 1fr; gap: 12px; margin: 24px 0; font-size: 13px; }
.chunk-metadata dt { color: #8091a4; }
.chunk-metadata dd { margin: 0; overflow-wrap: anywhere; color: #37516b; }
.source-link { color: #1f77b4; font-size: 12px; text-decoration: none; }
.original-label { font-size: 13px; color: #37516b; margin-top: 24px; }
.original-text { white-space: pre-wrap; overflow-wrap: anywhere; font-size: 13px; line-height: 1.85; background: #f6f9fc; border: 1px solid #e3ebf3; padding: 18px; max-height: 48vh; overflow-y: auto; border-radius: 10px; }
@media (max-width: 1200px) { .system-layout :deep(.sidebar) { width: 220px; } .page-container { padding: 24px; } .evidence-preview small { display: none; } }
@media (max-width: 900px) { .runtime-grid { grid-template-columns: 1fr; gap: 16px; } .channel-status-grid { grid-template-columns: 1fr; } .runtime-item { padding: 0 0 12px; border-right: 0; border-bottom: 1px solid #edf1f7; } .message-list { max-height: 55vh; } .page-header { padding: 18px 24px; } .page-header > .el-tag { display: none; } .runtime-heading h2 { font-size: 16px; } .composer-tools small, .send-actions small { display: none; } }
@media (max-width: 640px) { .system-layout :deep(.sidebar) { display: none; } .page-container { padding: 14px; } .page-header { padding: 16px; gap: 8px; } .page-header h1 { font-size: 16px; } .runtime-panel { padding: 18px; } .message-body { padding: 14px; } .message-avatar { display: none; } .composer { padding: 14px; bottom: 8px; } .welcome-panel h2 { font-size: 20px; } .runtime-heading > .el-button { font-size: 11px; padding: 8px; } .access-key-row { flex-wrap: wrap; } }
</style>
