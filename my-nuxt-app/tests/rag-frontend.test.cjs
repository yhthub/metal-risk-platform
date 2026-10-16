/** Offline regression checks. Run with Node; uses already-installed project deps. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules', '.pnpm')
const packagePath = (prefix, name) => path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name)
const ts = require(packagePath('typescript@', 'typescript'))
const vueCompiler = require(packagePath('@vue+compiler-sfc@', '@vue/compiler-sfc'))
const compileTs = source => {
  const result = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
  assert.equal((result.diagnostics || []).length, 0, 'TypeScript syntax diagnostics')
  return result.outputText
}
const evaluate = (source, context = {}) => {
  const exports = {}
  vm.runInNewContext(compileTs(source), { exports, URL, ...context })
  return exports
}
const helpers = evaluate(fs.readFileSync(path.join(root, 'app/utils/ragPresentation.ts'), 'utf8'))
let checks = 0
const check = (name, run) => { run(); checks++; console.log(`PASS ${name}`) }

check('empty retrieval remains zero without placeholder cards', () => {
  assert.equal(helpers.normalizeEvidenceCards([]).length, 0)
  assert.equal(helpers.normalizeEvidenceCards(null).length, 0)
})
check('model-ready fallback is available but unavailable model or explicit can_chat=false still blocks', () => {
  const generalOnly = { can_chat: true, status: 'general_only', corpus: { ready: false }, model: { ready: true }, general_fallback_enabled: true }
  assert.equal(helpers.chatAvailability(generalOnly, true, false), true)
  assert.equal(helpers.chatAvailability(generalOnly, false, false), false)
  assert.equal(helpers.chatAvailability({ ...generalOnly, model: { ready: false } }, true, false), false)
  assert.equal(helpers.chatAvailability({ ...generalOnly, can_chat: false }, true, false), false)
  assert.equal(helpers.chatAvailability({ model: { ready: true }, corpus: { ready: false } }, true, false), false)
  assert.equal(helpers.chatAvailability({ model: { ready: true }, general_fallback_enabled: true }, true, false), true)
})
check('general knowledge answer suppresses fabricated citation cards and candidate citation flags', () => {
  const response = { answer_mode: 'general_knowledge', status: 'general_answer', evidence_cards: [{ chunk_id: 'fake', is_cited: true, citation_id: 'E1' }], citations: [{ chunk_id: 'candidate', id: 'E1' }], sparse_hits: [{ chunk_id: 'candidate', is_cited: true, citation_id: 'E1', text: 'candidate only', context_excerpt: 'not-used-as-model-context' }] }
  const evidence = helpers.responseEvidence(response)
  assert.equal(helpers.isGeneralKnowledgeAnswer(response), true)
  assert.equal(helpers.isGeneralKnowledgeAnswer({ answerMode: 'general_knowledge' }), true)
  assert.equal(helpers.isGeneralKnowledgeAnswer({ status: 'insufficient_evidence' }), false)
  assert.equal(evidence.evidenceCards.length, 0)
  assert.equal(evidence.sparseHits[0].is_cited, false)
  assert.equal(evidence.sparseHits[0].citation_id, undefined)
  assert.equal(evidence.sparseHits[0].context_excerpt, undefined)
  assert.match(helpers.generalKnowledgeNotice, /检索信息不足.*模型一般知识回答.*未获检索文献支持/)
})
check('candidates and marked citations remain distinct', () => {
  const cards = helpers.normalizeEvidenceCards([{ chunk_id: 'a', text: 'A' }, { chunk_id: 'b', text: 'B' }], [{ chunk_id: 'b', id: 'E2' }])
  assert.equal(cards[0].is_cited, false)
  assert.equal(cards[1].is_cited, true)
  assert.equal(cards[0].standard_no_or_doi, undefined)
})
check('unknown source is explicit instead of fabricated attribution', () => {
  assert.equal(helpers.sourceLabel({ source: '' }), '来源名称未提供')
  assert.equal(helpers.sourceLabel({ source: { name: 'PubMed' } }), 'PubMed')
})
check('source links reject executable URLs and preserve real identifiers', () => {
  assert.equal(helpers.sourceUrl({ url: 'javascript:alert(1)' }), '')
  assert.equal(helpers.sourceUrl({ url: 'data:text/html,<script>1</script>' }), '')
  assert.equal(helpers.sourceUrl({ standard_no_or_doi: '未提供' }), '')
  assert.equal(helpers.sourceUrl({ doi: '10.1234/example' }), 'https://doi.org/10.1234/example')
  assert.equal(helpers.sourceUrl({ pmid: '12345' }), 'https://pubmed.ncbi.nlm.nih.gov/12345/')
})
check('plain answer is preferred and never requires HTML injection', () => {
  assert.equal(helpers.plainAnswer({ answer: '原文 [E1]', message: '<b>legacy</b>' }), '原文 [E1]')
  assert.equal(helpers.plainAnswer({ message: '<b>legacy</b>' }), 'legacy')
  assert.equal(helpers.plainAnswer({}), '')
})
check('hybrid retrieval requires explicit independent channel status', () => {
  const display = helpers.retrievalPresentation({ mode: 'hybrid_medcpt_bm25', ready: true, channels: { bm25: { ready: true, count: 32 }, medcpt: { ready: true, count: 32, scope: 'full corpus FAISS index' } } })
  assert.equal(display.hybridConfirmed, true)
  assert.equal(display.ready, true)
  assert.equal(display.warning, '')
  assert.equal(display.medcpt.count, 32)
  assert.equal(helpers.retrievalPresentation({ mode: 'hybrid', ready: true, channels: { bm25: { ready: true }, medcpt: { ready: true } } }).ready, true)
})
check('encoder directory or dense_score alone cannot assert dense readiness', () => {
  const display = helpers.retrievalPresentation({ mode: 'hybrid_medcpt_bm25', ready: true, query_encoder_available: true, dense_score: 0.99, channels: { bm25: { ready: true }, medcpt: { ready: false } } })
  assert.equal(display.hybridConfirmed, false)
  assert.equal(display.ready, false)
  assert.match(display.warning, /不是双路已跑通/)
})
check('explicit degradation remains visible even with both ready flags', () => {
  const display = helpers.retrievalPresentation({ mode: 'hybrid_medcpt_bm25', degraded: true, ready: true, channels: { bm25: { ready: true }, medcpt: { ready: true } } })
  assert.equal(display.hybridConfirmed, false)
  assert.equal(display.ready, false)
  assert.match(display.warning, /降级/)
})
check('intentional BM25-only configuration is labeled single route, not successful hybrid or fabricated degradation', () => {
  const display = helpers.retrievalPresentation({ mode: 'bm25', ready: true, channels: { bm25: { ready: true }, medcpt: { ready: false } } })
  assert.equal(display.label, 'BM25 单路')
  assert.equal(display.hybridConfirmed, false)
  assert.equal(display.degraded, false)
  assert.equal(display.warning, '')
})
check('zero hits do not mean unavailable channel or fabricated count', () => {
  const display = helpers.retrievalPresentation({ mode: 'hybrid_medcpt_bm25', channels: { bm25: { ready: true, count: 0 }, medcpt: { ready: true, count: 0 } } })
  assert.equal(display.hybridConfirmed, true)
  assert.equal(display.bm25.count, 0)
  assert.equal(display.medcpt.count, 0)
})
check('explicit not-executed routes cannot be labeled successful hybrid even when dependency flags are ready', () => {
  const display = helpers.retrievalPresentation({ mode: 'hybrid_medcpt_bm25', ready: true, diagnostics: { dual_route_executed: false, channels: { bm25: { ready: true }, medcpt: { ready: true } } } })
  assert.equal(display.hybridConfirmed, false)
  assert.equal(display.ready, false)
  assert.match(display.warning, /不是双路已跑通/)
})
check('raw channel candidates preserve content, ranks and true provenance', () => {
  const card = helpers.normalizeEvidenceCards([{ chunk_id: 'raw', content: 'raw source excerpt', retrieval_channels: ['bm25', 'medcpt'], bm25_rank: 4, dense_rank: 2, rrf_score: 0.030 }], [{ chunk_id: 'raw', id: 'E1' }])[0]
  assert.equal(card.text, 'raw source excerpt')
  assert.equal(card.citation_id, 'E1')
  assert.equal(card.bm25_rank, 4)
  assert.equal(card.dense_rank, 2)
  assert.equal(card.rrf_score, 0.030)
  assert.equal(helpers.retrievalChannelLabel(card), 'BM25 词法 + MedCPT 向量')
})

const vueFile = path.join(root, 'app/pages/agent/index.vue')
const source = fs.readFileSync(vueFile, 'utf8')
const parsed = vueCompiler.parse(source, { filename: vueFile })
check('Vue SFC is well formed', () => { assert.equal(parsed.errors.length, 0) })
const script = vueCompiler.compileScript(parsed.descriptor, { id: 'rag-offline-test' })
const template = vueCompiler.compileTemplate({ source: parsed.descriptor.template.content, filename: vueFile, id: 'rag-offline-test', compilerOptions: { bindingMetadata: script.bindings } })
check('Vue template and TypeScript compile', () => { assert.equal(template.errors.length, 0); compileTs(script.content) })
const style = vueCompiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename: vueFile, id: 'rag-offline-test', scoped: true })
check('scoped CSS compiles', () => { assert.equal(style.errors.length, 0) })
check('no simulated answers, fabricated counts, HTML injection or fake process animation', () => {
  assert.equal(/mockKnowledgeBase|retrieveKnowledge|v-html|setTimeout|XGBoost|全部通过交叉核验|已核验/.test(source), false)
})
check('starter prompts and placeholder use the reviewed explicit terminology questions', () => {
  const prompts = ['职业铅暴露与高血压的关系有哪些人群研究证据？', '镉暴露与肾损伤有哪些人体研究证据？', '砷与镉暴露有哪些人体研究证据？']
  for (const prompt of prompts) assert.equal(source.includes(`'${prompt}'`), true)
  assert.equal(source.includes(`placeholder="${prompts[0]}"`), true)
  assert.equal(source.includes('职业性铅暴露与高血压之间'), false)
  assert.equal(source.includes('镉暴露与慢性肾病'), false)
})

;(async () => {
  const calls = []
  const apiSource = fs.readFileSync(path.join(root, 'app/composables/useApi.ts'), 'utf8')
  const api = evaluate(apiSource, {
    useRuntimeConfig: () => ({ public: { apiBase: 'https://rag.example/' } }),
    $fetch: async (url, options) => { calls.push({ url, options }); return { answer: 'answer' } }
  }).useApi()
  api.setApiKey(' secret-key ')
  await api.agentChat('current question', { history: [{ role: 'user', content: 'earlier' }, { role: 'assistant', content: 'reply' }], model: 'Llama-3.1-8B' })
  check('configured API base, history and memory-only Authorization', () => {
    assert.equal(calls[0].url, 'https://rag.example/api/agent/chat')
    assert.equal(calls[0].options.headers.Authorization, 'Bearer secret-key')
    assert.equal(calls[0].options.body.history.length, 2)
    assert.equal(calls[0].options.body.history.some(item => item.content === 'current question'), false)
    assert.equal(calls[0].options.body.knowledge_bases.length, 0)
    assert.equal(/localStorage|sessionStorage/.test(apiSource), false)
  })
  api.setApiKey('')
  await api.getAgentStatus()
  check('clearing key removes Authorization', () => { assert.equal(calls[1].options.headers.Authorization, undefined) })
  await api.searchEvidence('lead hypertension', 40)
  check('evidence search uses bounded top_k, not old per-channel contract', () => { assert.equal(calls[2].options.body.top_k, 12); assert.equal(calls[2].options.body.top_k_per_channel, undefined) })
  await api.agentChat('question', { history: Array.from({ length: 20 }, (_, index) => ({ role: index % 2 ? 'assistant' : 'user', content: 'x'.repeat(9000) })) })
  check('history conforms to backend maximum 12 messages / 8000 chars', () => { assert.equal(calls[3].options.body.history.length, 12); assert.equal(calls[3].options.body.history.every(item => item.content.length === 8000), true) })
  const unauthorizedApi = evaluate(apiSource, { useRuntimeConfig: () => ({ public: { apiBase: '' } }), $fetch: async () => { throw { statusCode: 401, message: 'unauthorized' } } }).useApi()
  const unauthorized = await unauthorizedApi.getAgentStatus()
  check('401 is explicit, never a successful simulated result', () => { assert.equal(unauthorized.success, false); assert.match(unauthorized.error, /401/) })

  const componentCalls = []
  const ref = value => ({ value })
  const computed = callback => ({ get value() { return callback() } })
  check('public demo hides the page-specific key form without injecting a browser credential', () => {
    assert.match(source, /<div v-if="!publicDemo" class="access-key-row"/)
    for (const [setting, enabled] of [[true, true], ['true', true], [false, false], ['false', false], [undefined, false]]) {
      const installedKeys = []
      const publicComponent = evaluate(parsed.descriptor.scriptSetup.content + '\nexport { publicDemo, applyAccessKey, clearAccessKey };', {
        require: name => {
          if (name === 'vue') return { ref, computed, nextTick: async () => {}, onMounted: () => {} }
          if (name === 'element-plus') return { ElMessage: {} }
          if (name === '~/utils/ragPresentation') return helpers
          if (name === '@element-plus/icons-vue') return {}
          throw new Error(`Unexpected import ${name}`)
        },
        useRuntimeConfig: () => ({ public: { publicDemo: setting } }),
        useApi: () => ({ setApiKey: key => installedKeys.push(key) })
      })
      assert.equal(publicComponent.publicDemo, enabled)
      if (enabled) {
        publicComponent.applyAccessKey()
        publicComponent.clearAccessKey()
        assert.equal(installedKeys.length, 0)
      }
    }
  })
  let failChat = false
  let serverModelReady = false
  let serverRetrieval = { mode: 'hybrid_medcpt_bm25', ready: true, channels: { bm25: { ready: true }, medcpt: { ready: true, scope: 'full corpus FAISS index' } } }
  let nextResponse = { answer: 'actual answer', evidence_cards: [], sparse_hits: [], dense_hits: [], warnings: [], status: 'answered', model: { name: 'Llama-3.1-8B' } }
  const component = evaluate(parsed.descriptor.scriptSetup.content + '\nexport { refreshStatus, sendMessage, userInput, chatHistory, canSend, messageRetrieval, retrievalState };', {
    require: name => {
      if (name === 'vue') return { ref, computed, nextTick: async () => {}, onMounted: () => {} }
      if (name === 'element-plus') return { ElMessage: { warning: () => {}, error: () => {}, success: () => {} } }
      if (name === '~/utils/ragPresentation') return helpers
      if (name === '@element-plus/icons-vue') return {}
      throw new Error(`Unexpected import ${name}`)
    },
    useRuntimeConfig: () => ({ public: { publicDemo: false } }),
    useApi: () => ({
      setApiKey: () => {},
      getAgentStatus: async () => ({ success: true, data: { status: 'healthy', can_chat: serverModelReady, general_fallback_enabled: true, corpus: { ready: true, name: 'test', query_encoder_available: true }, model: { ready: serverModelReady }, retrieval: serverRetrieval } }),
      getModels: async () => ({ success: true, data: { default: 'Llama-3.1-8B', models: [{ name: 'Llama-3.1-8B', ready: true }] } }),
      agentChat: async (question, options) => { componentCalls.push({ question, options }); return failChat ? { success: false, error: 'real failure' } : { success: true, data: nextResponse } }
    })
  })
  await component.refreshStatus()
  check('health text and model list alone cannot enable RAG when model status is not ready', () => { assert.equal(component.canSend.value, false) })
  serverModelReady = true
  const hybridReady = serverRetrieval
  serverRetrieval = { ...hybridReady, ready: false, channels: { bm25: { ready: true }, medcpt: { ready: false } } }
  await component.refreshStatus()
  check('component permits model answers with missing dense route while keeping hybrid unavailable warning', () => { assert.equal(component.canSend.value, true); assert.match(component.retrievalState.value.warning, /不是双路已跑通/); assert.equal(component.retrievalState.value.hybridConfirmed, false) })
  serverRetrieval = hybridReady
  await component.refreshStatus()
  assert.equal(component.canSend.value, true)
  component.userInput.value = 'x'.repeat(2001)
  await component.sendMessage()
  check('question exceeds backend 2000-char limit: no request dispatched', () => { assert.equal(componentCalls.length, 0); assert.equal(component.chatHistory.value.length, 0) })
  component.userInput.value = 'first'
  await component.sendMessage()
  component.userInput.value = 'second'
  await component.sendMessage()
  check('real send path returns answer and forwards successful history only', () => {
    assert.equal(component.chatHistory.value[1].content, 'actual answer')
    assert.equal(component.chatHistory.value[1].evidenceCards.length, 0)
    assert.equal(componentCalls[1].options.history.length, 2)
    assert.equal(componentCalls[1].options.history[0].content, 'first')
  })
  failChat = true
  component.userInput.value = 'failed turn'
  await component.sendMessage()
  check('failed request has explicit error and empty answer', () => { const last = component.chatHistory.value.at(-1); assert.equal(last.error, 'real failure'); assert.equal(last.content, ''); assert.equal(last.loading, false) })
  failChat = false
  component.userInput.value = 'after failure'
  await component.sendMessage()
  check('failed turns do not become model context', () => { assert.equal(componentCalls.at(-1).options.history.some(item => item.content === 'failed turn' || item.content === 'real failure'), false) })
  nextResponse = {
    answer: 'supported text [E1]', status: 'answered', model: { name: 'Llama-3.1-8B' }, warnings: [],
    evidence_cards: [{ chunk_id: 'shared', text: 'context chunk', retrieval_channels: ['bm25', 'medcpt'], rrf_score: 0.032, bm25_rank: 1, dense_rank: 1 }],
    sparse_hits: [{ chunk_id: 'shared', content: 'raw shared' }, { chunk_id: 'sparse-only', content: 'raw sparse' }],
    dense_hits: [{ chunk_id: 'shared', content: 'raw shared' }, { chunk_id: 'dense-only', content: 'raw dense' }],
    citations: [{ id: 'E1', chunk_id: 'shared' }],
    retrieval: { mode: 'hybrid_medcpt_bm25', candidate_count: 3, diagnostics: { channels: { bm25: { ready: true, count: 2 }, medcpt: { ready: true, count: 2, scope: 'full corpus FAISS index' } } } },
    dual_path_summary: { sparse_retrieved: 2, dense_retrieved: 2, total_candidates: 3 }
  }
  component.userInput.value = 'hybrid question'
  await component.sendMessage()
  check('actual two-route candidates stay separate from fused model context and deduplicated count', () => {
    const msg = component.chatHistory.value.at(-1)
    assert.equal(msg.sparseHits.length, 2)
    assert.equal(msg.denseHits.length, 2)
    assert.equal(msg.evidenceCards.length, 1)
    assert.equal(msg.dualPathSummary.total_candidates, 3)
    assert.equal(component.messageRetrieval(msg).hybridConfirmed, true)
    assert.equal(msg.denseHits[1].text, 'raw dense')
  })
  nextResponse = { ...nextResponse, dense_hits: [], retrieval: { mode: 'bm25', degraded: true, diagnostics: { channels: { bm25: { ready: true, count: 2 }, medcpt: { ready: false, count: 0, error: 'index missing' } } } } }
  component.userInput.value = 'degraded question'
  await component.sendMessage()
  check('answered degraded response still visibly warns that hybrid execution did not complete', () => {
    const msg = component.chatHistory.value.at(-1)
    assert.equal(msg.denseHits.length, 0)
    assert.match(component.messageRetrieval(msg).warning, /不是双路已跑通/)
    assert.equal(component.messageRetrieval(msg).hybridConfirmed, false)
  })
  serverRetrieval = { mode: 'hybrid', ready: false, degraded: true, channels: { bm25: { ready: false }, medcpt: { ready: false } } }
  await component.refreshStatus()
  nextResponse = {
    answer: '检索信息不足；以下为模型一般知识回答，未获本次检索证据支持。\n一般知识回答正文', status: 'general_answer', answer_mode: 'general_knowledge', evidence_support: 'none', model: { name: 'Llama-3.1-8B' }, warnings: [],
    evidence_cards: [{ chunk_id: 'must-not-be-cited', is_cited: true, citation_id: 'E1' }], citations: [{ chunk_id: 'must-not-be-cited', id: 'E1' }],
    sparse_hits: [{ chunk_id: 'candidate-only', content: 'candidate text', is_cited: true, citation_id: 'E2' }], dense_hits: [],
    retrieval: { mode: 'unavailable', degraded: true, diagnostics: { dual_route_executed: false, channels: { bm25: { ready: false }, medcpt: { ready: false } } } }
  }
  component.userInput.value = '未在医学术语词典里的中文概念还可以回答吗？'
  await component.sendMessage()
  check('unknown Chinese question is submitted and authentic general answer has no claimed citations', () => {
    const msg = component.chatHistory.value.at(-1)
    assert.match(componentCalls.at(-1).question, /未在医学术语词典/)
    assert.match(msg.content, /一般知识回答正文/)
    assert.equal(msg.status, 'general_answer')
    assert.equal(msg.answerMode, 'general_knowledge')
    assert.equal(msg.evidenceSupport, 'none')
    assert.equal(msg.evidenceCards.length, 0)
    assert.equal(msg.sparseHits[0].is_cited, false)
    assert.equal(msg.sparseHits[0].citation_id, undefined)
    assert.equal(component.messageRetrieval(msg).hybridConfirmed, false)
  })
  nextResponse = { status: 'general_answer', answer_mode: 'general_knowledge', answer: '' }
  component.userInput.value = 'empty model answer'
  await component.sendMessage()
  check('general-answer mode does not fabricate text when real model returned no answer', () => {
    const msg = component.chatHistory.value.at(-1)
    assert.equal(msg.content, '')
    assert.match(msg.error, /后端未返回回答内容/)
  })
  check('general-answer notice precedes answer and no citation overview or cited drawer tab is shown for fallback', () => {
    assert.equal(source.indexOf('class="general-answer-notice"') < source.indexOf('class="answer-text"'), true)
    assert.match(source, /v-if="!isGeneralKnowledgeAnswer\(msg\)" class="evidence-overview"/)
    assert.match(source, /v-if="!isGeneralKnowledgeAnswer\(activeDrawerMsg\)" :label="`正文标记引用/)
    assert.equal(source.includes('不展示正文引用，不将候选材料算作已引用文献'), true)
  })
  check('UI labels raw routes, RRF non-probability and actual model excerpt explicitly', () => {
    assert.match(source, /BM25 原始候选/)
    assert.match(source, /MedCPT 原始候选/)
    assert.match(source, /不是概率或证据可信度/)
    assert.match(source, /实际模型上下文节选/)
    assert.equal(/rrf_score[^\n]*\*\s*100/.test(source), false)
  })
  console.log(`\n${checks} offline frontend checks passed. No model or network calls.`)
})().catch(error => { console.error(error); process.exitCode = 1 })
