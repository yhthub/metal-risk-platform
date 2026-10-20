/** Whole-file page state and component contracts; mocked HTTP, no actual model calls. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const dependency = (prefix, name) => require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name))
const ts = dependency('typescript@', 'typescript')
const compiler = dependency('@vue+compiler-sfc@', '@vue/compiler-sfc')
const sass = dependency('sass-embedded@', 'sass-embedded')
const source = fs.readFileSync(path.join(root, 'app/pages/risk/index.vue'), 'utf8')
const componentPath = path.join(root, 'app/components/RiskCohortDashboard.vue')
const component = fs.readFileSync(componentPath, 'utf8')
const warningPath = path.join(root, 'app/components/RiskCohortWarning.vue')
const warningComponent = fs.readFileSync(warningPath, 'utf8')
const block = source.match(/\/\/ RISK_COHORT_RUN_START[\s\S]*?\/\/ RISK_COHORT_RUN_END/)[0]
const script = ts.transpileModule(block, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText
const plain = value => JSON.parse(JSON.stringify(value))
function load(file, imports = {}) {
  const exports = {}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils', file), 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText, { exports, require: name => imports[name], setTimeout: () => {} })
  return exports
}
const risk = load('riskPrediction.ts')
const cohort = load('riskCohort.ts', { './riskPrediction': risk, './riskPalette': load('riskPalette.ts'), './riskChartTheme': load('riskChartTheme.ts') })
const targets = ['sbp', 'dbp', 'creatinine', 'bun', 'urate', 'uacr', 'hba1c', 'cholesterol', 'hdl', 'alt', 'ast', 'ggt']
function fixture(n = 45, skipped = 2) {
  const records = Array.from({ length: n }, (_, index) => {
    if (index < skipped) return { row_number: index + 1, person_id: '' + (index + 1), status: 'INPUT_NOT_ELIGIBLE', reason: 'BMI缺测', results: null }
    const input = plain(risk.createPredictionDraft())
    Object.assign(input.person, { id: '' + (index + 1), age: 45, gender: index % 2 ? 'female' : 'male', gender_confirmed: true, bmi: 24, pb: 1, cd: .3, hg: 1 })
    return { row_number: index + 1, person_id: '' + (index + 1), status: 'ESTIMATES_NOT_DIAGNOSES', input, results: targets.map(target => ({ target, label_zh: target, unit: 'mmHg', prediction: target === 'sbp' ? 100 + index : null, status: target === 'sbp' ? 'EXPLORATORY_ESTIMATE' : 'INSUFFICIENT_VALIDATED_ACCURACY', reason: target === 'sbp' ? null : '验证准确性不足' })) }
  })
  const accepted = n - skipped
  return { model_version: 'offline-fixture', run_id: 'fixture-no-model', profile: 'basic', file_id: 'FILE-aabbccdd', analysis_scope: 'all_uploaded_records', complete: true, total_records: n, processed_records: accepted, skipped_records: skipped, offset: 0, limit: n, has_more: false, records, summary: targets.map(target => ({ target, label_zh: target, unit: 'mmHg', estimated_count: target === 'sbp' ? accepted : 0, withheld_count: target === 'sbp' ? 0 : accepted, mean_prediction: target === 'sbp' && accepted ? 100 + (skipped + n - 1) / 2 : null, statistics: { n: target === 'sbp' ? accepted : 0, mean: target === 'sbp' && accepted ? 100 + (skipped + n - 1) / 2 : null, median: null, q1: null, q3: null, min: null, max: null, std: null }, histogram: { status: 'AVAILABLE', bin_edges: [0, 100 + n], counts: [target === 'sbp' ? accepted : 0], counted_records: target === 'sbp' ? accepted : 0 }, by_gender: [], by_age_band: [] })), warnings: [] }
}
function setup(overrides = {}) {
  const calls = []
  const state = { active: true, epoch: 0, suppressSelection: false, mode: vue.ref('batch'), selectedTarget: vue.ref('sbp'), isReasoning: vue.ref(false), inputErrors: vue.ref([]), predictionError: vue.ref(''), inputDialog: vue.ref(false), batchIntake: vue.ref({ file_id: 'FILE-aabbccdd' }), draft: vue.ref(risk.createPredictionDraft()), serviceStatus: vue.ref({ ready: true }), showIndividualDetail: vue.ref(true), isThinkingExpanded: vue.ref(false), requestLogs: vue.ref([]), batchResult: vue.ref(null), cohortResult: vue.ref(null), selectedRow: vue.ref(9) }
  const context = vm.createContext({ ...state, measurementErrors: () => [], clonePrediction: plain, cohortResponseError: cohort.cohortResponseError, nextTick: async () => {}, clearCharts: () => {}, invalidate: () => { state.batchResult.value = null; state.cohortResult.value = null; state.selectedRow.value = null }, api: { predictCohort: async body => { calls.push(plain(body)); return { success: true, data: fixture() } } }, ...overrides })
  vm.runInContext(script + '\nglobalThis.run = runBatch;', context)
  return { context, state, calls, run: () => context.run() }
}

test('whole-file run submits no offset/limit and keeps all objects rather than first twenty', async () => {
  const data = fixture(1005, 2)
  const calls = []
  const { state, run } = setup({ api: { predictCohort: async body => { calls.push(plain(body)); return { success: true, data } } } })
  await run()
  assert.equal(calls.length, 1)
  assert.deepEqual(Object.keys(calls[0]).sort(), ['file_id', 'measurements'])
  assert.equal(state.cohortResult.value.records.length, 1005)
  assert.equal(state.batchResult.value.records.length, 1005)
  assert.equal(state.selectedRow.value, null)
  assert.equal(state.showIndividualDetail.value, false)
  assert.equal(state.isReasoning.value, false)
  assert(!/refreshSelectedDashboard|first\.input|offset|limit: 20|predictBatch/.test(block))
})
test('zero eligible objects still produces complete cohort counts and reasons, not fatal empty success', async () => {
  const { state, run } = setup({ api: { predictCohort: async () => ({ success: true, data: fixture(3, 3) }) } })
  await run()
  assert.equal(state.cohortResult.value.total_records, 3)
  assert.equal(state.cohortResult.value.processed_records, 0)
  assert.equal(state.cohortResult.value.skipped_records, 3)
  assert.equal(state.predictionError.value, '')
  assert.equal(state.cohortResult.value.records[0].reason, 'BMI缺测')
})
test('legacy page-shaped, incomplete and wrong-file responses never become cohort conclusions', async () => {
  for (const changed of [{ complete: false }, { has_more: true }, { offset: 20 }, { file_id: 'FILE-ffffffff' }, { records: fixture().records.slice(0, 20) }]) {
    const { state, run } = setup({ api: { predictCohort: async () => ({ success: true, data: { ...fixture(), ...changed } }) } })
    await run()
    assert.equal(state.cohortResult.value, null)
    assert(state.predictionError.value)
    assert.equal(state.isReasoning.value, false)
  }
})
test('double-clicks do not launch two full-cohort computations', async () => {
  let resolve
  const waiting = new Promise(done => { resolve = done })
  let count = 0
  const { run, state } = setup({ api: { predictCohort: async () => { count++; return waiting } } })
  const first = run(); await run()
  assert.equal(count, 1)
  assert.equal(state.isReasoning.value, true)
  resolve({ success: true, data: fixture() }); await first
  assert.equal(state.cohortResult.value.total_records, 45)
})
test('changing only selected target during full inference keeps the target-independent cohort result', async () => {
  let resolve
  const waiting = new Promise(done => { resolve = done })
  const { run, context, state } = setup({ api: { predictCohort: () => waiting } })
  const pending = run()
  context.selectedTarget.value = 'dbp'
  resolve({ success: true, data: fixture() }); await pending
  assert.equal(state.cohortResult.value.total_records, 45)
  assert.equal(state.selectedTarget.value, 'dbp')
})
test('file, input or mode changes and navigation invalidate late full-cohort responses', async () => {
  for (const change of [context => { context.epoch++ }, context => { context.active = false }, context => { context.mode.value = 'individual' }, context => { context.batchIntake.value.file_id = 'FILE-12345678' }]) {
    let resolve
    const waiting = new Promise(done => { resolve = done })
    const { run, context, state } = setup({ api: { predictCohort: () => waiting } })
    const pending = run(); change(context)
    resolve({ success: true, data: fixture() }); await pending
    assert.equal(state.cohortResult.value, null)
  }
})
test('cohort view renders independently of a personal dashboard and personal inspection is explicit', () => {
  assert.match(source, /v-if="mode === 'batch' && cohortResult"/)
  assert.match(source, /<RiskCohortDashboard/)
  assert.match(source, /@inspect-person="inspectCohortPerson"/)
  assert.match(source, /mode\.value === 'batch' && !showIndividualDetail\.value/)
  assert.match(source, /以下所有曲线和贡献图仅属于/)
  assert(!/特异性高危易感人群预警榜/.test(source))
  assert.match(component, /<RiskCohortWarning/)
  assert.match(warningComponent, /特异性高危易感人群预警榜/)
  assert.match(warningComponent, /本批次相对预警 · 非临床诊断/)
  assert(!/useApi\(|\bfetch\(|predictCohort|predictBatch/.test(component + warningComponent))
})
test('cohort component keeps the profile above one full-row merged warning and three model cards', () => {
  const parsed = compiler.parse(component, { filename: componentPath })
  assert.deepEqual(parsed.errors, [])
  const main = parsed.descriptor.template.content.split('<div class="results-grid">')[1].split('<section class="result-card all-records">')[0]
  assert.equal((main.match(/class="result-card /g) || []).length, 3)
  assert.equal((main.match(/<RiskCohortWarning\b/g) || []).length, 1)
  assert(component.indexOf('<RiskCohortProfile ') < component.indexOf('<RiskCohortWarning '))
  assert(component.indexOf('<RiskCohortProfile ') < component.indexOf('模型计算结果与群体指标分析'))
  assert.match(component, /:profile="result\.demographic_profile"/)
  assert.match(component, /:total-records="result\.total_records"/)
  assert.match(component, /:processed-records="result\.processed_records"/)
  assert.match(component, /:skipped-records="result\.skipped_records"/)
  assert.match(main, /<RiskCohortWarning class="col-span-6" :result="result" :threshold="warningThreshold \?\? 80" @update:threshold="emit\('update:warningThreshold', \$event\)"/)
  assert.match(main, /class="result-card col-span-3 accent-blue"/)
  assert.match(main, /class="result-card col-span-3 accent-blue"/)
  assert.match(main, /class="result-card col-span-6 accent-amber"/)
  const remainingTitles = [...main.matchAll(/<h4>([^<]*)/g)].map(match => match[1].trim())
  assert.deepEqual(remainingTitles, ['全群指标估计分布', '12 项结局 · 全群概览', '全群估计统计概览'])
  assert(!/prototypeGaugeRef|buildOriginalUnavailableOption\('gauge',|\brankRef\b|\brankLimit\b/.test(component), 'The parent must not leave duplicate ranking/share cards or chart instances')
  assert.equal((warningComponent.match(/<article\b/g) || []).length, 1, 'Both panes share a single outer card')
  assert.match(warningComponent, /class="ranking-pane"/)
  assert.match(warningComponent, /class="share-pane"/)
  assert.match(warningComponent, /grid-column:1\/-1/)
  assert.match(warningComponent, /\.warning-body\{display:grid;grid-template-columns:minmax\(0,2fr\) minmax\(260px,1fr\)/)
  assert.match(warningComponent, /\.share-pane\{[^}]*border-left:1px dashed/)
  assert.match(warningComponent, /warning\.status === 'ALERT'/)
  assert.match(warningComponent, /warning\.status === 'CLEAR'/)
  assert.match(warningComponent, /可比较数据不足/)
  assert.match(warningComponent, /不显示绿色“无预警”/)
  assert(!/性别分层概览|年龄分层概览|\bgenderRef\b|\bageRef\b|\bgenderOption\b|\bageOption\b|\bbuildCohortGroupOption\b/.test(component))
  assert.equal(typeof cohort.buildCohortGroupOption, 'function', 'Shared grouped statistics builders remain available to reports')
  assert(!main.includes('整份文件有效输入覆盖率'))
  assert(!main.includes('全群数据质量与保留原因'))
  assert.match(main, /全群估计统计概览/)
  for (const name of ['mean', 'median', 'q1', 'q3', 'min', 'max', 'std']) assert(main.includes('view.statistics?.' + name))
  assert(component.indexOf('class="cohort-exclusions"') < component.indexOf('<div class="results-grid">'))
  const compiledScript = compiler.compileScript(parsed.descriptor, { id: 'risk-cohort-page' })
  const template = compiler.compileTemplate({ source: parsed.descriptor.template.content, filename: componentPath, id: 'risk-cohort-page', compilerOptions: { bindingMetadata: compiledScript.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(template.errors, [])
  assert(compiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename: componentPath, id: 'risk-cohort-page' }).errors.length === 0)
  assert.match(component, /grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/)
  assert.match(component, /\.stat-grid\{[^}]*grid-template-columns:repeat\(3,minmax\(0,1fr\)\)/)
  assert.match(component, /全量完成 · 非分页推理/)
  assert.match(component, /下方仅显示分页，不限制模型计算人群/)
  assert(!/原图与功能边界|prototypeImportanceRef|prototypeJointRef|buildOriginalUnavailableOption/.test(parsed.descriptor.template.content + parsed.descriptor.scriptSetup.content), 'The cohort page must not restore uncomputed prototype chart cards')
  assert.match(component, /onDeactivated\(pause\)/)
  const warningParsed = compiler.parse(warningComponent, { filename: warningPath })
  assert.deepEqual(warningParsed.errors, [])
  const warningScript = compiler.compileScript(warningParsed.descriptor, { id: 'risk-cohort-warning' })
  const warningTemplate = compiler.compileTemplate({ source: warningParsed.descriptor.template.content, filename: warningPath, id: 'risk-cohort-warning', compilerOptions: { bindingMetadata: warningScript.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(warningTemplate.errors, [])
  assert.deepEqual(compiler.compileStyle({ source: warningParsed.descriptor.styles[0].content, filename: warningPath, id: 'risk-cohort-warning', scoped: true }).errors, [])
})
test('shared threshold and normative row identifiers do not replace source IDs or re-run inference', () => {
  assert.match(source, /:warning-threshold="cohortWarningThreshold"/)
  assert.match(source, /@update:warning-threshold="cohortWarningThreshold = \$event"/)
  assert.match(source, /下载综合预警排序/)
  assert.match(source, /下载所选结局排序/)
  assert.match(source, /warningRankingCsv\(buildCohortWarning\(cohortResult\.value, cohortWarningThreshold\.value\)\)/)
  assert.match(component, /<th>规范编号<\/th><th>原始编号<\/th><th>原始行号<\/th>/)
  assert.match(component, /cohortDisplayId\(row\.record\.row_number\)/)
  assert.match(component, /row\.record\.person_id/)
  assert.match(component, /本表为所选结局的单项排序，综合预警与12项名次见上方合并卡片/)
  assert.match(warningComponent, /综合分 ≥/)
  assert.match(warningComponent, /分母仅为使用相同有效结局完成综合比较的对象/)
  assert.match(warningComponent, /修改阈值只更新本页统计，不重新调用模型/)
})
test('client table sorts all cohort members, retains excluded records, and paginates display only', () => {
  const parsed = compiler.parse(component, { filename: componentPath })
  const ast = ts.createSourceFile(componentPath, parsed.descriptor.scriptSetup.content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  const names = ['view', 'skippedReasons', 'tableRows', 'visibleRows', 'pageStart', 'pageEnd']
  const statements = ast.statements.filter(node => ts.isVariableStatement(node) && node.declarationList.declarations.some(item => names.includes(item.name.getText(ast)))).map(node => node.getText(ast)).join('\n')
  const props = vue.reactive({ result: fixture(45, 2), target: 'sbp' })
  const tablePage = vue.ref(1)
  const exports = {}
  vm.runInNewContext(ts.transpileModule(statements + '\nexports.view=view;exports.rows=tableRows;exports.visible=visibleRows;exports.reasons=skippedReasons;', { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, { exports, props, computed: vue.computed, buildCohortView: cohort.buildCohortView, tableOrder: vue.ref('rank'), tablePage, pageSize: vue.ref(20) })
  assert.equal(exports.rows.value.length, 45)
  assert.equal(exports.visible.value.length, 20)
  assert.equal(exports.visible.value[0].record.row_number, 45, 'Highest value is outside the original first twenty and must rank globally')
  assert.equal(exports.visible.value[0].rank, 1)
  tablePage.value = 3
  assert.equal(exports.visible.value.length, 5)
  assert.equal(exports.visible.value.filter(row => !row.record.input).length, 2)
  assert.deepEqual(plain(exports.reasons.value), [{ reason: 'BMI缺测', count: 2 }])
  props.target = 'dbp'
  assert.equal(exports.rows.value.length, 45)
  assert.equal(exports.view.value.estimated_count, 0)
  assert.equal(exports.view.value.withheld_count, 43)
})
test('keep-alive return after report target change closes stale personal graphs but preserves whole cohort', () => {
  const parsed = compiler.parse(source)
  const ast = ts.createSourceFile('risk-index.ts', parsed.descriptor.scriptSetup.content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  const functions = ast.statements.filter(node => ts.isFunctionDeclaration(node) && ['activateDashboard', 'closeIndividualDetail', 'clearCurrentExplanation', 'resetStaleGroupDemoThreshold'].includes(node.name?.text)).map(node => node.getText(ast)).join('\n')
  const complete = fixture(45, 2)
  let renders = 0
  const context = vm.createContext({
    active: false, epoch: 1, mode: vue.ref('batch'), showIndividualDetail: vue.ref(true), selectedTarget: vue.ref('dbp'), selectedRow: vue.ref(45),
    cohortWarningDemoPreset: vue.ref(null), cohortWarningThreshold: vue.ref(80), batchIntake: vue.ref(null), applyingGroupDemo: false,
    dashboard: vue.ref({ charts: { target: 'sbp' } }), cohortResult: vue.ref(complete), batchResult: vue.ref(complete),
    lastResult: vue.ref({}), lastRequest: vue.ref({}), lastDashboardRequest: vue.ref({ target: 'sbp' }), isReasoning: vue.ref(false), requestLogs: vue.ref([]),
    applyIntakeContext: () => {}, refreshStatus: () => {}, window: { addEventListener: () => {} }, resizeCharts: () => {}, clearCharts: () => {},
    initDashboardCharts: () => { renders++; assert.equal(context.dashboard.value, null, 'Old SBP graph must be cleared before re-render') },
  })
  vm.runInContext(ts.transpileModule(functions + '\nglobalThis.activate = activateDashboard;', { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, context)
  context.activate()
  assert.equal(renders, 1)
  assert.equal(context.active, true)
  assert.equal(context.showIndividualDetail.value, false)
  assert.equal(context.selectedRow.value, null)
  assert.equal(context.dashboard.value, null)
  assert.equal(context.selectedTarget.value, 'dbp')
  assert.equal(context.cohortResult.value.records.length, 45)
  assert.equal(context.batchResult.value.records.length, 45)
  assert.match(context.requestLogs.value[0], /群体视角/)
})
