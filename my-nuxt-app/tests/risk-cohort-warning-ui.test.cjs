/** Composite-warning UI: rendering saved estimates only; no API, training or clinical inference. */
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
const { renderToString } = dependency('@vue+server-renderer@', '@vue/server-renderer')
const filename = path.join(root, 'app/components/RiskCohortWarning.vue')
const source = fs.readFileSync(filename, 'utf8')
const parsed = compiler.parse(source, { filename })
const modules = new Map()
function load(name) {
  const key = name.replace(/^~\/utils\//, '').replace(/^\.\//, '').replace(/\.ts$/, '')
  if (modules.has(key)) return modules.get(key)
  const runtime = { exports: {} }; modules.set(key, runtime.exports)
  const script = fs.readFileSync(path.join(root, 'app/utils', key + '.ts'), 'utf8')
  vm.runInNewContext(ts.transpileModule(script, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText, { module: runtime, exports: runtime.exports, require: load })
  return runtime.exports
}
const warningLogic = load('cohortWarning')
const risk = load('riskPrediction')
const compiled = compiler.compileScript(parsed.descriptor, { id: 'cohort-warning-test', inlineTemplate: true })
const runtime = { exports: {} }
vm.runInNewContext(ts.transpileModule(compiled.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText, { exports: runtime.exports, module: runtime, require: name => name === 'vue' ? vue : name === 'echarts' ? { init: () => { throw Error('SSR must not initialise a chart') } } : load(name), Number, window: undefined })
const component = runtime.exports.default
const plain = value => JSON.parse(JSON.stringify(value))
function fixture(options = {}) {
  const n = options.n ?? 10
  const usable = options.usable ?? 7
  const records = Array.from({ length: n }, (_, index) => {
    const input = plain(risk.createPredictionDraft())
    Object.assign(input.person, { id: String(93700 + index), age: 45, gender: index % 2 ? 'female' : 'male', gender_confirmed: true, bmi: 24, pb: 1, cd: .3, hg: 1 })
    return { row_number: index + 1, person_id: String(93700 + index), status: 'ESTIMATES_NOT_DIAGNOSES', input, results: warningLogic.COHORT_WARNING_TARGETS.map((item, targetIndex) => ({ target: item.target, label_zh: item.label_zh, unit: item.unit, prediction: targetIndex < usable ? 100 + index : null, status: targetIndex < usable ? 'EXPLORATORY_ESTIMATE' : 'INSUFFICIENT_VALIDATED_ACCURACY', reason: targetIndex < usable ? null : '验证准确性不足，暂不出值' })) }
  })
  return { model_version: 'offline-ui-fixture', run_id: 'not-a-model-run', profile: 'basic', file_id: 'FILE-aabbccdd', analysis_scope: 'all_uploaded_records', complete: true, total_records: n, processed_records: n, skipped_records: 0, offset: 0, limit: n, has_more: false, records, summary: warningLogic.COHORT_WARNING_TARGETS.map((item, index) => ({ ...item, estimated_count: index < usable ? n : 0, withheld_count: index < usable ? 0 : n, statistics: { n: index < usable ? n : 0 } })), warnings: [] }
}
async function render(result, threshold = 80) {
  const app = vue.createSSRApp(component, { result, threshold })
  const stub = vue.defineComponent({ inheritAttrs: false, setup: (_, { slots }) => () => vue.h('div', slots.default?.()) })
  for (const name of ['ElSelect', 'ElOption', 'ElPagination']) app.component(name, stub)
  return renderToString(app)
}

test('one full-width card has a left ranking and right proportion separated by a vertical dashed rule', () => {
  assert.deepEqual(parsed.errors, [])
  const template = compiler.compileTemplate({ source: parsed.descriptor.template.content, filename, id: 'cohort-warning-test', compilerOptions: { bindingMetadata: compiled.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(template.errors, [])
  assert.deepEqual(compiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename, id: 'cohort-warning-test' }).errors, [])
  assert.equal((source.match(/<article\b/g) || []).length, 1)
  assert.match(source, /grid-column:1\/-1/)
  assert.match(source, /grid-template-columns:minmax\(0,2fr\) minmax\(260px,1fr\)/)
  assert.match(source, /\.share-pane\{[^}]*border-left:1px dashed/)
  assert(!/class="result-card|border-radius:[^;}]*[^\n]*\.share-pane/.test(parsed.descriptor.template.content))
  assert.match(source, /onDeactivated\(pause\)/)
  assert.match(source, /onActivated\(resume\)/)
  assert(!/useApi\(|\bfetch\(|predictCohort|predictBatch|Math\.random/.test(source))
})
test('ALERT displays composite warning and evaluated denominator, not a selected single target or old source IDs on the axis', async () => {
  const result = fixture()
  const summary = warningLogic.buildCohortWarning(result, 80)
  const html = await render(result)
  assert.equal(summary.status, 'ALERT')
  assert.match(html, /state-alert/)
  assert.match(html, /综合相对预警对象/)
  assert.match(html, /高危预警对象人群占比/)
  assert.match(html, /可比较对象 · 占比分母/)
  assert.match(html, /共同结局 7 \/ 12 项/)
  assert.match(html, /P-000010/)
  assert.match(html, /原 ID：93709/)
  assert.match(html, /收缩压/)
  assert.match(html, /HDL胆固醇/)
  assert.match(html, /验证准确性不足/)
  assert.match(html, /暂不排名/)
  assert(!html.includes('暂无相对预警对象'))
  const option = warningLogic.buildWarningRankOption(summary, 10)
  assert(option.yAxis.data.every(value => /^P-\d{6}$/.test(value)))
  assert(!/target:|props\.target|selectedTarget/.test(parsed.descriptor.scriptSetup.content))
})
test('a sufficiently high threshold shows the new green no-warning state with health-boundary text', async () => {
  const result = fixture()
  // Opposing ranks yield max score below 100 without inventing values or changing model accuracy.
  result.records.forEach((record, index) => { record.results[1].prediction = 200 - index })
  const summary = warningLogic.buildCohortWarning(result, 100)
  assert.equal(summary.status, 'CLEAR')
  const html = await render(result, 100)
  assert.match(html, /state-clear/)
  assert.match(html, /暂无相对预警对象/)
  assert.match(html, /clear-icon/)
  assert.match(html, /未达到预警阈值/)
  assert.match(html, /不代表健康、无病或没有暴露风险/)
  assert(!html.includes('warning-rank-chart'))
  assert.equal(warningLogic.buildWarningShareOption(summary).series[0].data[0].value, 0)
})
test('insufficient people, too few common outcomes and illegal threshold are neutral unknown, never green zero-risk', async () => {
  for (const [result, threshold] of [[fixture({ n: 4 }), 80], [fixture({ usable: 2 }), 80], [fixture(), Number.NaN]]) {
    const summary = warningLogic.buildCohortWarning(result, threshold)
    const html = await render(result, threshold)
    assert.equal(summary.status, 'INSUFFICIENT_DATA')
    assert.equal(summary.percentage, null)
    assert.match(html, /state-insufficient/)
    assert.match(html, /可比较数据不足/)
    assert.match(html, /暂不计算占比/)
    assert(!html.includes('class="clear-state"'))
    assert(!html.includes('暂无相对预警对象'))
    assert(!html.includes('warning-share-chart'))
  }
})
test('threshold is controlled by shared state and only valid changes are emitted', () => {
  assert.match(source, /threshold\?: number/)
  assert.match(source, /threshold: 80/)
  assert.match(source, /emit\('update:threshold', value\)/)
  assert(!/const threshold\s*=\s*ref/.test(source))
  const ast = ts.createSourceFile('warning.ts', parsed.descriptor.scriptSetup.content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  const fn = ast.statements.find(node => ts.isFunctionDeclaration(node) && node.name.text === 'setThreshold').getText(ast)
  const emitted = []
  const context = vm.createContext({ emit: (...args) => emitted.push(args), Number })
  vm.runInContext(ts.transpileModule(fn + '\nglobalThis.set = setThreshold;', { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, context)
  for (const value of [0, 80, 100]) context.set(value)
  for (const value of [undefined, null, -1, 101, Infinity, NaN, '80']) context.set(value)
  assert.deepEqual(plain(emitted), [['update:threshold', 0], ['update:threshold', 80], ['update:threshold', 100]])
})
test('native numeric control commits shared threshold on change and restores blank or invalid entries', async () => {
  assert.match(source, /<input type="number" :value="warning\.threshold \?\? ''" min="0" max="100" step="5"/)
  assert.match(source, /@change="onThresholdChange"/)
  assert(!/el-input-number/.test(parsed.descriptor.template.content))
  const ast = ts.createSourceFile('warning.ts', parsed.descriptor.scriptSetup.content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
  const functions = ast.statements.filter(node => ts.isFunctionDeclaration(node) && ['setThreshold', 'onThresholdChange'].includes(node.name.text)).map(node => node.getText(ast)).join('\n')
  const emitted = []
  const props = { threshold: 80 }
  const context = vm.createContext({ emit: (...args) => { emitted.push(args); props.threshold = args[1] }, props, Number, String })
  vm.runInContext(ts.transpileModule(functions + '\nglobalThis.change = onThresholdChange;', { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText, context)
  for (const value of [75, 100, 0]) {
    const input = { value: String(value), valueAsNumber: value }
    context.change({ currentTarget: input })
    assert.equal(input.value, String(value))
    assert.equal(props.threshold, value)
  }
  props.threshold = 75
  for (const [text, value] of [['', NaN], ['wrong', NaN], ['101', 101], ['-5', -5], ['Infinity', Infinity]]) {
    const input = { value: text, valueAsNumber: value }
    context.change({ currentTarget: input })
    assert.equal(input.value, '75', 'Invalid or empty edits restore the active shared threshold')
    assert.equal(props.threshold, 75)
  }
  assert.deepEqual(plain(emitted), [['update:threshold', 75], ['update:threshold', 100], ['update:threshold', 0]])
  const html = await render(fixture(), 75)
  assert.match(html, /type="number" value="75" min="0" max="100" step="5"/)
})
test('all row and outcome details remain present while only table display is paginated', async () => {
  const result = fixture({ n: 25 })
  const html = await render(result, 80)
  assert.match(html, /共 25 人/)
  assert.match(html, /含原编号溯源/)
  assert.match(html, /12 项结局名次/)
  assert.match(html, /分页仅用于展示/)
  assert.equal((html.match(/class="id-column"><strong>/g) || []).length, 20)
  assert.equal((html.match(/低值端优先/g) || []).length, 1)
  assert.equal((html.match(/高值端优先/g) || []).length, 11)
  assert.match(source, /\.sort\(\(a, b\) => \(a\.rank \?\? Number\.MAX_SAFE_INTEGER\)/)
  assert.match(source, /orderedRows\.value\.slice\(\(tablePage\.value - 1\) \* 20/)
})
