/** Real-public demo UI state contract only: no remote/model calls or fabricated scientific results. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const pageSource = fs.readFileSync(path.join(__dirname, '../app/pages/datainput/index.vue'), 'utf8')
const block = pageSource.match(/\/\/ PUBLIC_GROUP_DEMO_START[\s\S]*?\/\/ PUBLIC_GROUP_DEMO_END/)[0]
const info = { id: 'nhanes_2017_2018_public_adults_300', rows: 300, eligible_records: 3739, cycle: '2017–2018', limitations: ['未加权'], source_links: [], sample_filename: 'public.csv' }
const payload = { import_result: { file_id: 'new-independent-id', outcome_id: 'blood_pressure', analysis_records: 300 }, analysis: { kpis: { analysis_records: 300 } }, provenance: info }
const plain = value => JSON.parse(JSON.stringify(value))
function createPage(overrides = {}) {
  const calls = { import: 0, confirms: 0, charts: 0, scrolls: 0, messages: [] }
  const state = {
    isAnalyzing: vue.ref(false), selectedFile: vue.ref(null), uploadResult: vue.ref(null), analysisData: vue.ref(null),
    selectedOutcomeId: vue.ref('blood_pressure'), batchImportError: vue.ref(''), showDashboard: vue.ref(false), currentStep: vue.ref(1)
  }
  const context = vm.createContext({
    ref: vue.ref, ...state, nextTick: vue.nextTick,
    getGroupDemo: async () => ({ success: true, data: structuredClone(info) }),
    importGroupDemo: async () => { calls.import += 1; return { success: true, data: structuredClone(payload) } },
    ElMessageBox: { confirm: async () => { calls.confirms += 1 } },
    ElMessage: { success: message => calls.messages.push(message) },
    initBatchECharts: () => { calls.charts += 1 },
    window: { scrollTo: () => { calls.scrolls += 1 } }, formatNumber: String,
    ...overrides
  })
  vm.runInContext(`${block}\nglobalThis.demo = {loadGroupDemo,fillGroupDemo,groupDemoInfo,groupDemoSource,groupDemoError,groupDemoRunning,groupDemoLoading,groupDashboardRef}`, context)
  return { state, demo: context.demo, calls }
}

test('metadata is fetched, not invented; a missing sample blocks one-click import', async () => {
  const { demo, calls } = createPage({ getGroupDemo: async () => ({ success: false, error: '未部署样本' }) })
  await demo.loadGroupDemo()
  assert.equal(demo.groupDemoInfo.value, null)
  assert.equal(demo.groupDemoError.value, '未部署样本')
  await demo.fillGroupDemo()
  assert.equal(calls.import, 0)
})

test('public demo warnings remain inspectable and result scrolling targets the dashboard', () => {
  assert.match(pageSource, /ref="groupDashboardRef" class="batch-dashboard-container/)
  assert.match(block, /groupDashboardRef\.value\?\.scrollIntoView/)
  assert.doesNotMatch(block, /scrollTo\(\{ top: 800/)
  assert.match(pageSource, /<details v-if="groupDemoSource && analysisData\?\.metadata\.warnings\?\.length"/)
  assert.match(pageSource, /查看处理说明、PCA 缺失处理与公开数据局限/)
})

test('one-click demo commits actual import, analysis and source together', async () => {
  const { demo, state, calls } = createPage()
  demo.groupDashboardRef.value = { scrollIntoView: () => { calls.scrolls += 1 } }
  await demo.loadGroupDemo()
  await demo.fillGroupDemo()
  assert.equal(calls.import, 1)
  assert.equal(calls.confirms, 0)
  assert.equal(state.selectedFile.value, null)
  assert.equal(state.uploadResult.value.file_id, 'new-independent-id')
  assert.equal(state.analysisData.value.kpis.analysis_records, 300)
  assert.equal(demo.groupDemoSource.value.id, info.id)
  assert.equal(state.showDashboard.value, true)
  assert.equal(state.currentStep.value, 2)
  assert.equal(calls.charts, 1)
  assert.equal(calls.scrolls, 1)
  assert.equal(demo.groupDemoRunning.value, false)
})

test('cancelled replacement preserves current uploaded input and valid analysis', async () => {
  const { demo, state, calls } = createPage({ ElMessageBox: { confirm: async () => { throw new Error('cancel') } } })
  await demo.loadGroupDemo()
  state.selectedFile.value = { name: 'user.csv' }
  state.uploadResult.value = { file_id: 'old-user-id' }
  state.analysisData.value = { kpis: { analysis_records: 5 } }
  state.showDashboard.value = true
  await demo.fillGroupDemo()
  assert.equal(calls.import, 0)
  assert.equal(state.selectedFile.value.name, 'user.csv')
  assert.equal(state.uploadResult.value.file_id, 'old-user-id')
  assert.equal(state.analysisData.value.kpis.analysis_records, 5)
  assert.equal(state.showDashboard.value, true)
})

test('failed server import never replaces existing batch state', async () => {
  const { demo, state } = createPage({ importGroupDemo: async () => ({ success: false, error: '完整性校验失败' }) })
  await demo.loadGroupDemo()
  state.selectedFile.value = { name: 'user.csv' }
  state.uploadResult.value = { file_id: 'old-user-id' }
  state.analysisData.value = { kpis: { analysis_records: 5 } }
  state.showDashboard.value = true
  await demo.fillGroupDemo()
  assert.equal(demo.groupDemoError.value, '完整性校验失败')
  assert.equal(state.selectedFile.value.name, 'user.csv')
  assert.equal(state.uploadResult.value.file_id, 'old-user-id')
  assert.equal(state.showDashboard.value, true)
})

test('incomplete API response leaves existing valid result untouched', async () => {
  const { demo, state } = createPage({ importGroupDemo: async () => ({ success: true, data: { import_result: { file_id: 'incomplete' } } }) })
  await demo.loadGroupDemo()
  state.analysisData.value = { kpis: { analysis_records: 5 } }
  await demo.fillGroupDemo()
  assert.equal(state.analysisData.value.kpis.analysis_records, 5)
  assert.match(demo.groupDemoError.value, /响应不完整/)
  assert.equal(demo.groupDemoSource.value, null)
})

test('double-clicks do not create simultaneous demo imports', async () => {
  let resolve
  const pending = new Promise(done => { resolve = done })
  let imports = 0
  const { demo, state } = createPage({ importGroupDemo: () => { imports += 1; return pending } })
  await demo.loadGroupDemo()
  const running = demo.fillGroupDemo()
  await demo.fillGroupDemo()
  assert.equal(imports, 1)
  assert.equal(state.isAnalyzing.value, true)
  resolve({ success: true, data: structuredClone(payload) })
  await running
  assert.equal(state.isAnalyzing.value, false)
})

test('a chart-render failure reports imported data honestly instead of claiming rollback', async () => {
  const { demo, state } = createPage({ initBatchECharts: () => { throw new Error('render') } })
  await demo.loadGroupDemo()
  await demo.fillGroupDemo()
  assert.equal(state.uploadResult.value.file_id, 'new-independent-id')
  assert.match(demo.groupDemoError.value, /已载入.*渲染失败/)
})

test('labels preserve public survey scope and distinguish lifetime questionnaire semantics', () => {
  assert.match(pageSource, /终生吸烟 ≥100支/)
  assert.match(pageSource, /终生曾饮酒 ≥1杯/)
  assert.match(pageSource, /振荡式血压方法比较研究/)
  assert.match(pageSource, /不是临床诊断/)
  assert.match(pageSource, /真实公开子样本/)
  assert.match(pageSource, /不是模拟数据，也不是职业人群/)
  assert.match(pageSource, /载入 \$\{formatNumber\(payload.import_result.analysis_records\)\}/)
})

test('API methods retain shared authentication and never use user-specific source paths', async () => {
  const root = path.resolve(__dirname, '..')
  const pnpm = path.join(root, 'node_modules/.pnpm')
  const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
  const source = fs.readFileSync(path.join(root, 'app/composables/useApi.ts'), 'utf8')
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } })
  const requests = []
  const exportsObject = {}
  vm.runInNewContext(compiled.outputText, {
    exports: exportsObject, Blob, FormData, encodeURIComponent,
    useRuntimeConfig: () => ({ public: { apiBase: 'http://127.0.0.1:8001' } }),
    $fetch: async (url, options) => { requests.push({ url, options }); return info }
  })
  const api = exportsObject.useApi()
  api.setApiKey('demo-key')
  await api.getGroupDemo()
  await api.importGroupDemo()
  assert.equal(requests[0].url, 'http://127.0.0.1:8001/api/datainput/demo')
  assert.equal(requests[1].url, 'http://127.0.0.1:8001/api/datainput/demo/import')
  assert.equal(requests[1].options.method, 'POST')
  assert.equal(requests[1].options.headers.Authorization, 'Bearer demo-key')
  assert.equal(requests[1].options.body, undefined)
  assert.equal(requests[1].options.retry, 0)
})
