/** Offline input/reference/UI regressions. No medical model, HTTP, dataset, or server calls. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const packagePath = (prefix, name) => path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name)
const ts = require(packagePath('typescript@', 'typescript'))
const compiler = require(packagePath('@vue+compiler-sfc@', '@vue/compiler-sfc'))
const vue = require(path.join(root, 'node_modules/vue'))
const transpile = source => {
  const result = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
  assert.equal(result.diagnostics.length, 0)
  return result.outputText
}
const evaluate = (source, imports = {}, globals = {}) => {
  const exports = {}
  vm.runInNewContext(transpile(source), { exports, require: name => { if (!(name in imports)) throw Error('Unexpected import: ' + name); return imports[name] }, ...globals })
  return exports
}
const refs = evaluate(fs.readFileSync(path.join(root, 'app/utils/individualReferences.ts'), 'utf8'))
const helpers = evaluate(fs.readFileSync(path.join(root, 'app/utils/individualProfile.ts'), 'utf8'), { './individualReferences': refs })
const demo = evaluate(fs.readFileSync(path.join(root, 'app/utils/individualDemo.ts'), 'utf8'), { './individualReferences': refs })
const metadata = (key, overrides = {}) => {
  const result = refs.createIndividualMetadata()
  if (key) Object.assign(result[key], { sample: 'whole_blood', unit: 'μg/L' }, overrides)
  return result
}
const row = (raw, meta, key) => helpers.buildIndividualProfile(raw, meta).rows.find(item => item.key === key)
let checks = 0
const check = (name, run) => { run(); checks++; console.log('PASS ' + name) }
const asyncCheck = async (name, run) => { await run(); checks++; console.log('PASS ' + name) }

check('missing is not a measured zero; strict finite nonnegative parsing', () => {
  for (const value of [null, undefined, '', '   ']) assert.equal(helpers.parseMeasurement(value).state, 'missing')
  for (const value of [0, '0', '0.00', 1.25, '1.25', '1e2']) assert.equal(helpers.parseMeasurement(value).state, 'valid')
  for (const value of [-1, '-1', NaN, Infinity, '1e309', '0x10', '1,234', '12abc', true, {}, []]) assert.equal(helpers.parseMeasurement(value).state, 'invalid')
})
check('empty profile has null ratios/offsets/coverage and exact missing counts', () => {
  const profile = helpers.buildIndividualProfile({}, metadata())
  assert.equal(profile.counts.missing, 10)
  assert.equal(profile.counts.comparable, 0)
  assert.equal(profile.coverage, null)
  assert(profile.rows.every(item => item.value === null && item.ratio === null && item.offset === null))
})
check('whole-blood lead adult gte boundary and genuine zero', () => {
  assert.equal(row({ age: 18, pb: 35 }, metadata('pb'), 'pb').reached, true)
  assert.equal(row({ age: 18, pb: 34.99 }, metadata('pb'), 'pb').reached, false)
  const zero = row({ age: 18, pb: 0 }, metadata('pb'), 'pb')
  assert.equal(zero.ratio, 0)
  assert.equal(zero.offset, -100)
})
check('age and explicit sample govern adult references, not entered identity or job', () => {
  for (const age of [undefined, '', 17, -1]) assert.equal(row({ age, pb: 35 }, metadata('pb'), 'pb').ratio, null)
  assert.equal(row({ age: 30, pb: 35 }, metadata('pb', { sample: 'serum' }), 'pb').ratio, null)
  assert.equal(row({ age: 30, cd: 8, job: 'smelting' }, metadata('cd'), 'cd').ratio, null)
})
check('safe same-sample volume unit conversions preserve raw values', () => {
  const pb = row({ age: 30, pb: 3.5 }, metadata('pb', { unit: 'μg/dL' }), 'pb')
  assert.equal(pb.raw, 3.5)
  assert.equal(pb.convertedValue, 35)
  assert.equal(pb.ratio, 100)
  assert.equal(row({ hg: 10 }, metadata('hg', { unit: 'ng/mL' }), 'hg').ratio, 100)
  assert.equal(helpers.convertReferenceUnit(5, 'μg/L', 'μg/g Cr'), null)
  assert.equal(helpers.convertReferenceUnit(5, 'μg/g Cr', 'μmol/mol Cr'), null)
})
check('OSHA cadmium uses explicit occupational context and strictly greater boundary', () => {
  const m = metadata('cd', { context: 'occupational_cadmium' })
  assert.equal(row({ age: 30, cd: 5 }, m, 'cd').ratio, 100)
  assert.equal(row({ age: 30, cd: 5 }, m, 'cd').reached, false)
  assert.equal(row({ age: 30, cd: 5.01 }, m, 'cd').reached, true)
  const urine = metadata('cd', { sample: 'urine', unit: 'μg/g Cr', context: 'occupational_cadmium' })
  assert.equal(row({ age: 30, cd: 3 }, urine, 'cd').reached, false)
  assert.equal(row({ age: 30, cd: 3.01 }, urine, 'cd').reached, true)
  urine.cd.unit = 'μg/g'
  assert.equal(row({ age: 30, cd: 4 }, urine, 'cd').ratio, null)
})
check('Mayo whole-blood mercury works without adult-only or occupational assumptions', () => {
  assert.equal(row({ hg: 10 }, metadata('hg'), 'hg').reached, true)
  assert.equal(row({ age: 8, hg: 10 }, metadata('hg'), 'hg').ratio, 100)
  assert.equal(row({ hg: 10 }, metadata('hg', { sample: 'urine' }), 'hg').ratio, null)
})
check('HSE mercury requires adult stable occupational random urine and exact molar unit', () => {
  const m = metadata('hg', { sample: 'random_urine', unit: 'μmol/mol Cr', context: 'occupational_mercury_stable' })
  assert.equal(row({ age: 30, hg: 20 }, m, 'hg').reached, true)
  assert.equal(row({ age: 17, hg: 20 }, m, 'hg').ratio, null)
  for (const override of [{ sample: 'urine' }, { unit: 'μg/g Cr' }, { context: '' }]) {
    assert.equal(row({ age: 30, hg: 20 }, metadata('hg', { ...m.hg, ...override }), 'hg').ratio, null)
  }
})
check('arsenic must be speciated toxic random urine, never total/unknown or creatinine units', () => {
  const m = metadata('as', { sample: 'random_urine', unit: 'μg/L', analyte: 'toxic_speciated' })
  assert.equal(row({ as: 35 }, m, 'as').reached, true)
  for (const override of [{ analyte: 'total' }, { analyte: '' }, { sample: 'urine' }, { unit: 'μg/g Cr' }]) {
    assert.equal(row({ as: 35 }, metadata('as', { ...m.as, ...override }), 'as').ratio, null)
  }
})
check('radon requires residential annual indoor-air context and exact air unit', () => {
  const m = metadata('rn', { sample: 'indoor_air', unit: 'Bq/m³', context: 'residential_annual' })
  assert.equal(row({ rn: 100 }, m, 'rn').reached, true)
  assert.equal(row({ rn: 99 }, m, 'rn').reached, false)
  for (const override of [{ context: '' }, { context: 'other' }, { sample: 'whole_blood' }, { unit: 'μg/L' }]) {
    assert.equal(row({ rn: 100 }, metadata('rn', { ...m.rn, ...override }), 'rn').ratio, null)
  }
})
check('unregistered elements retain raw values but never receive invented references', () => {
  for (const key of ['th', 'li', 'cr', 'ni', 'co']) {
    const item = row({ [key]: 4 }, metadata(key), key)
    assert.equal(item.raw, 4)
    assert.equal(item.reference, null)
    assert.equal(item.ratio, null)
  }
})
check('metadata confirmation is fail-closed and never rewrites a number', () => {
  const m = metadata('pb', { confirmed: false })
  const item = row({ age: 30, pb: 35 }, m, 'pb')
  assert.equal(item.raw, 35)
  assert.equal(item.ratio, null)
  assert.equal(item.conditions.reference.state, 'pending')
  m.pb.confirmed = true
  assert.equal(row({ age: 30, pb: 35 }, m, 'pb').ratio, 100)
})
check('overflow and malformed reference values fail closed', () => {
  assert.equal(row({ age: 30, pb: 1e308 }, metadata('pb', { unit: 'μg/dL' }), 'pb').ratio, null)
  const custom = [{ ...refs.INDIVIDUAL_REFERENCES[0], value: 0 }]
  assert.equal(helpers.buildIndividualProfile({ age: 30, pb: 35 }, metadata('pb'), custom).counts.comparable, 0)
})
check('pure profile recomputes on changed inputs and does not mutate inputs/metadata/registry', () => {
  const raw = { age: 30, pb: 35 }
  const m = metadata('pb')
  const before = JSON.stringify({ raw, m, refs: refs.INDIVIDUAL_REFERENCES })
  assert.equal(helpers.buildIndividualProfile(raw, m).comparable[0].ratio, 100)
  assert.equal(JSON.stringify({ raw, m, refs: refs.INDIVIDUAL_REFERENCES }), before)
  raw.pb = 70
  assert.equal(helpers.buildIndividualProfile(raw, m).comparable[0].ratio, 200)
  assert.equal(helpers.buildIndividualProfile(raw, m).coverage, 100)
})
check('unknown samples or units cannot produce reference ratios', () => {
  assert.equal(row({ age: 30, pb: 35 }, metadata('pb', { sample: 'unrecognized' }), 'pb').ratio, null)
  assert.equal(row({ age: 30, pb: 35 }, metadata('pb', { unit: 'unrecognized' }), 'pb').ratio, null)
})
check('pure TypeScript utility types have no strict semantic diagnostics', () => {
  const program = ts.createProgram(['individualReferences.ts', 'individualProfile.ts'].map(file => path.join(root, 'app/utils', file)), { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, strict: true, noEmit: true, skipLibCheck: true, types: [] })
  const diagnostics = ts.getPreEmitDiagnostics(program)
  assert.equal(diagnostics.length, 0, diagnostics.map(item => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'))
})
const source = fs.readFileSync(path.join(root, 'app/pages/datainput/index.vue'), 'utf8')
const parsed = compiler.parse(source, { filename: 'individual.vue' })
check('single-page Vue script/template compile with original seven chart slots', () => {
  assert.equal(parsed.errors.length, 0)
  const script = compiler.compileScript(parsed.descriptor, { id: 'individual-offline' })
  const template = compiler.compileTemplate({ source: parsed.descriptor.template.content, filename: 'individual.vue', id: 'individual-offline', compilerOptions: { bindingMetadata: script.bindings } })
  assert.equal(template.errors.length, 0, String(template.errors))
  assert.equal((source.match(/id="singleChart/g) || []).length, 7)
  assert(source.includes('height: 350px;'))
})
check('single controls are cleared/explicit and old medical simulations are removed', () => {
  assert.match(source, /pb: null, cd: null, hg: null/)
  const singleCharts = source.slice(source.indexOf('const initSingleECharts'), source.indexOf('onMounted(() =>', source.indexOf('const initSingleECharts')))
  assert(!singleCharts.includes('Math.random'))
  assert(!singleCharts.includes('2022'))
  assert(!singleCharts.includes('报警红区'))
  assert(!singleCharts.includes('早期预警界限'))
  assert.match(source, /v-model="individualMetadata\[field.key\].sample"/)
  assert.match(source, /watch\(individualProfile/)
})
check('existing batch visual-results and chart renderer remain intact beside explicit public-source banner', () => {
  const git = 'C:/Users/30643/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe'
  const baseline = execFileSync(git, ['show', 'HEAD:my-nuxt-app/app/pages/datainput/index.vue'], { cwd: path.dirname(root), encoding: 'utf8' }).replace(/\r\n/g, '\n')
  const currentWithPublicSource = source.replace(/\r\n/g, '\n')
  // A source/provenance banner is intentionally new; all pre-existing chart
  // slots, KPI bindings and the batch renderer remain byte-for-byte protected.
  // The new public-data state/consent/API behavior has dedicated group-demo tests.
  const publicSourceLine = /^.*<div v-if="groupDemoSource" class="group-demo-dashboard-source">.*<\/div>\n/gm
  assert.equal((currentWithPublicSource.match(publicSourceLine) || []).length, 1)
  assert.match(currentWithPublicSource, /公开数据体验 · NHANES/)
  assert.match(currentWithPublicSource, /图表为未加权描述性统计/)
  const publicDisclosure = /^            <details v-if="groupDemoSource && analysisData\?\.metadata\.warnings\?\.length" class="analysis-notes-details">[\s\S]*?^            <\/details>\n/gm
  assert.equal((currentWithPublicSource.match(publicDisclosure) || []).length, 1)
  const normalize = text => text.replace(publicSourceLine, '').replace(publicDisclosure, '')
    .replace('ref="groupDashboardRef" ', '')
    .replace('v-if="!groupDemoSource && analysisData?.metadata.warnings?.length"', 'v-if="analysisData?.metadata.warnings?.length"')
  const current = normalize(currentWithPublicSource)
  const comparableBaseline = normalize(baseline)
  for (const [start, end] of [['          <!-- 群体模式大屏 -->', '          <!-- 单人模式科研图表 -->'], ['const initBatchECharts', '/* ==============================================']]) {
    const get = (text, first, last) => {
      const begin = text.indexOf(first)
      const finish = text.indexOf(last, begin)
      assert(begin >= 0 && finish > begin, first)
      return text.slice(begin, finish)
    }
    const currentEnd = end.includes('setTimeout') ? '\n  showDashboard.value = true\n  currentStep.value = 2' : end
    assert.equal(get(current, start, currentEnd).trimEnd(), get(comparableBaseline, start, end).trimEnd())
  }
})

async function componentChecks() {
  const settle = async () => { await vue.nextTick(); await new Promise(resolve => setImmediate(resolve)) }
  const nodes = new Map(['Master', 'Radar', 'Timeline', 'Percentile', 'RiskPie', 'ZScore', 'Anomaly'].map(name => ['singleChart' + name, { id: 'singleChart' + name }]))
  const charts = new Map()
  const options = new Map()
  const confirmations = []
  const confirmationResponses = []
  const scrolls = []
  let apiCalls = 0
  const chartApi = {
    getInstanceByDom: node => charts.get(node.id),
    init: node => { const chart = { setOption: value => options.set(node.id, value), dispose: () => charts.delete(node.id), resize() {} }; charts.set(node.id, chart); return chart },
    graphic: { LinearGradient: function(x, y, x2, y2, stops) { this.colorStops = stops } }
  }
  const component = evaluate(parsed.descriptor.scriptSetup.content + '\nexport { formData, individualMetadata, individualProfile, showDashboard, runAnalysis, handleMetadataChange, confirmMetadata, handleModeChange, fillIndividualDemo, clearIndividualInput, demoSource, demoEdited, demoSnapshot, hasIndividualInput, createEmptySingleData, singleDashboardRef, currentStep, disposeSingleCharts, selectedFile, selectedOutcomeId, uploadResult, analysisData };', {
    vue: { ...vue, onMounted() {}, onBeforeUnmount() {} },
    'element-plus': {
      ElMessage: { info() {}, warning() {}, error() {}, success() {} },
      ElMessageBox: { confirm: async (...args) => {
        confirmations.push(args)
        if (confirmationResponses.shift() === false) throw 'cancel'
        return 'confirm'
      } }
    },
    '~/composables/useBatchAnalysisCharts': { renderBatchAnalysisCharts: () => { throw Error('Batch unexpectedly rendered') } },
    '~/utils/individualProfile': helpers,
    '~/utils/individualReferences': refs,
    '~/utils/individualDemo': demo,
    echarts: chartApi
  }, {
    document: { getElementById: id => nodes.get(id) }, window: { scrollTo() {} }, useRouter: () => ({}),
    usePredictionState: () => ({ invalidate() {}, setIntake() {}, batchIntake: vue.ref(null) }),
    useApi: () => ({ getOutcomeConfigs: () => { apiCalls++; throw Error('Unexpected API') }, uploadBatchData: () => { apiCalls++; throw Error('Unexpected API') }, getDatasetAnalysis: () => { apiCalls++; throw Error('Unexpected API') } })
  })
  component.formData.value.mode = 'single'
  await component.runAnalysis()
  check('all-missing UI renders explicit empties and factual missing-count ring without model/API calls', () => {
    assert.equal(options.size, 7)
    assert.equal(options.get('singleChartMaster').series.length, 0)
    assert.match(options.get('singleChartAnomaly').graphic[0].style.text, /不可计算/)
    assert.equal(options.get('singleChartRiskPie').series[0].data[0].value, 10)
    assert.equal(apiCalls, 0)
  })
  check('condition matrix uses bounded one-character labels and neutral blue-gray states', () => {
    const matrix = options.get('singleChartTimeline')
    const label = matrix.series[0].label
    assert.equal(label.width, 12)
    assert.equal(label.overflow, 'truncate')
    for (const code of [-1, 0, 1, 2]) assert.equal(label.formatter({ value: [0, 0, code] }).length, 1)
    assert.equal(label.formatter({ value: [0, 0, -1] }), '空')
    assert.equal(matrix.visualMap.pieces.find(item => item.value === -1).color, '#F1F5F9')
    assert(matrix.visualMap.pieces.every(item => ['#F1F5F9', '#CBD5E1', '#93C5FD', '#DBEAFE'].includes(item.color)))
  })
  check('short matrix labels preserve full reasons in tooltip and explicit legend', () => {
    const matrix = options.get('singleChartTimeline')
    assert.match(matrix.tooltip.formatter({ data: [0, 0, -1] }), /尚未录入；不当作零/)
    assert.match(matrix.tooltip.formatter({ data: [0, 1, -1] }), /样本类型未指定/)
    assert.match(source, /可=条件满足，空=未提供，×=不匹配，待=口径确认/)
    assert.match(source, /\.range\.individual-reference-status \{ color: #64748B; \}/)
  })
  component.formData.value.singleData.age = 30
  component.formData.value.singleData.pb = 35
  Object.assign(component.individualMetadata.value.pb, { sample: 'whole_blood', unit: 'μg/L' })
  await settle()
  check('real Vue watcher updates values after visible input without rebuilding or simulated waiting', () => {
    assert.equal(component.individualProfile.value.counts.comparable, 1, JSON.stringify(component.individualProfile.value.rows[0]))
    assert.equal(charts.size, 7)
    assert.equal(options.get('singleChartMaster').series[0].data[0].value, 100)
    assert.equal(options.get('singleChartMaster').series[0].data[1].value, null)
    assert.equal(options.get('singleChartAnomaly').series[0].data[0].value, 100)
  })
  check('master reference-line label is short and explicitly inside the plot', () => {
    const line = options.get('singleChartMaster').series[0].markLine.data[0]
    assert.equal(line.yAxis, 100)
    assert.equal(line.label.position, 'insideMiddle')
    assert.equal(line.label.formatter, '参考100%')
  })
  check('coverage value and factual count title have separate explicit vertical positions', () => {
    const gauge = options.get('singleChartAnomaly').series[0]
    assert.equal(gauge.detail.offsetCenter[1], '6%')
    assert.equal(gauge.title.offsetCenter[1], '38%')
    assert.equal(gauge.pointer.show, false)
    assert.equal(gauge.progress.show, true)
    assert.equal(gauge.progress.itemStyle.color, '#3B82F6')
    assert.equal(gauge.axisLine.lineStyle.color.length, 1)
    assert.equal(gauge.axisLine.lineStyle.color[0][0], 1)
    assert.equal(gauge.axisLine.lineStyle.color[0][1], '#E2E8F0')
    assert.equal(gauge.data[0].value, 100)
    assert.match(gauge.data[0].name, /1 \/ 1项（非医疗分）/)
  })
  check('input-status outer ring keeps all ten short codes inside and retains raw-value tooltip', () => {
    const pie = options.get('singleChartRiskPie')
    const outer = pie.series[1]
    assert.equal(outer.label.position, 'inside')
    assert.equal(outer.labelLine.show, false)
    assert.equal(outer.data.length, 10)
    assert(outer.data.every(item => item.name.length === 2 && item.value === 1))
    assert.match(pie.tooltip.formatter({ seriesIndex: 1, dataIndex: 0 }), /原始值：35 μg\/L/)
  })
  check('status summary is centered independently of slices and counts remain explicit', () => {
    const pie = options.get('singleChartRiskPie')
    assert.equal(pie.graphic[0].left, 'center')
    assert.equal(pie.graphic[0].top, 'middle')
    assert.equal(pie.graphic[0].silent, true)
    assert.match(pie.graphic[0].style.text, /1\/10/)
    assert.match(pie.graphic[0].style.text, /有效录入/)
    assert.equal(pie.series[0].label.show, false)
    assert.equal(pie.legend.selectedMode, false)
    assert.equal(pie.legend.formatter('有效'), '有效 1项')
    assert.equal(pie.legend.formatter('缺失'), '缺失 9项')
    assert.equal(pie.series[0].data.reduce((total, item) => total + item.value, 0), 10)
  })
  check('format conversion and descriptive summaries never assert clinically safe downstream models', () => {
    assert.doesNotMatch(source, /可以安全地将特征矩阵推入|临床监测基线参考/)
    assert.match(source, /真实指标估计另需年龄、性别、BMI及三种全血金属/)
    assert.match(source, /缺失必需字段会提示，不自动补值/)
  })
  check('ratio reference line remains at 100 without a label competing with the axis tick', () => {
    const ratio = options.get('singleChartPercentile')
    const line = ratio.series[0].markLine.data[0]
    assert.equal(line.xAxis, 100)
    assert.equal(line.label.show, false)
    assert.match(ratio.tooltip.formatter([{ dataIndex: 0 }]), /CDC\/CSTE 成人血铅升高参考/)
  })
  component.formData.value.singleData.pb = 70
  await settle()
  check('same input metric changes actual bar and offset values', () => {
    assert.equal(options.get('singleChartMaster').series[0].data[0].value, 200)
    assert.equal(options.get('singleChartZScore').series[0].data[0].value, 100)
  })
  component.individualMetadata.value.pb.unit = 'μg/dL'
  component.handleMetadataChange('pb')
  await settle()
  check('changing metadata removes stale ratio until explicit confirmation without changing numeric input', () => {
    assert.equal(component.formData.value.singleData.pb, 70)
    assert.equal(options.get('singleChartMaster').series.length, 0)
    assert.equal(component.individualProfile.value.rows[0].conditions.reference.state, 'pending')
  })
  component.confirmMetadata('pb')
  await settle()
  check('confirming new unit computes new ratio; reference is not an automatic safe-risk judgment', () => {
    assert.equal(options.get('singleChartMaster').series[0].data[0].value, 2000)
    assert.equal(apiCalls, 0)
    assert.match(component.individualProfile.value.rows[0].comparisonLabel, /参考值/)
  })
  component.handleModeChange('batch')
  check('leaving single mode disposes only single charts and preserves batch API inactivity', () => {
    assert.equal(charts.size, 0)
    assert.equal(apiCalls, 0)
  })

  // The actual reactive page script is exercised, not an alternative demo implementation.
  const resetSingle = async () => {
    component.disposeSingleCharts()
    component.formData.value.mode = 'single'
    component.formData.value.job = 'smelting'
    component.formData.value.singleData = component.createEmptySingleData()
    component.individualMetadata.value = refs.createIndividualMetadata()
    component.demoSource.value = false
    component.demoSnapshot.value = ''
    component.showDashboard.value = false
    component.currentStep.value = 1
    confirmations.length = 0
    confirmationResponses.length = 0
    options.clear()
    await settle()
  }
  const snapshot = () => JSON.stringify({
    form: component.formData.value, metadata: component.individualMetadata.value,
    source: component.demoSource.value, edited: component.demoEdited.value,
    demoSnapshot: component.demoSnapshot.value, visible: component.showDashboard.value,
    step: component.currentStep.value, chartIds: [...charts.keys()], options: [...options.entries()]
  })
  const assertSynthetic = (edited) => {
    assert.equal(component.demoSource.value, true)
    assert.equal(component.demoEdited.value, edited)
    assert.equal(apiCalls, 0)
  }
  component.singleDashboardRef.value = { scrollIntoView: option => scrolls.push(option) }
  await resetSingle()
  await asyncCheck('one click on an empty form fills ten synthetic measurements and renders all seven charts with no API calls', async () => {
    assert.equal(component.hasIndividualInput.value, false)
    await component.fillIndividualDemo()
    await settle()
    assert.equal(confirmations.length, 0)
    assert.equal(component.individualProfile.value.counts.valid, 10)
    assert.equal(component.individualProfile.value.counts.missing, 0)
    assert.equal(component.individualProfile.value.counts.invalid, 0)
    assert.equal(component.individualProfile.value.counts.comparable, 5)
    assert.equal(component.individualProfile.value.coverage, 50)
    assert.equal(component.showDashboard.value, true)
    assert.equal(component.currentStep.value, 2)
    assert.equal(charts.size, 7)
    assert.equal(options.size, 7)
    assert.equal(options.get('singleChartRadar').series[0].data[0].value.length, 5)
    assert.equal(options.get('singleChartAnomaly').series[0].data[0].value, 50)
    assert(component.individualProfile.value.rows.every(item => item.metadata.confirmed))
    assert.match(component.formData.value.singleData.name, /合成/)
    assert.match(component.formData.value.singleData.history, /非真实/)
    assertSynthetic(false)
  })
  check('single analysis scrolls to the rendered section instead of a hard-coded document offset', () => {
    assert.equal(scrolls.length, 1)
    assert.equal(scrolls[0].block, 'start')
    assert.equal(scrolls[0].behavior, 'smooth')
  })
  check('demo has explicit arsenic and residential radon contexts and does not invent references for other elements', () => {
    assert.equal(component.individualMetadata.value.as.analyte, 'toxic_speciated')
    assert.equal(component.individualMetadata.value.as.sample, 'random_urine')
    assert.equal(component.individualMetadata.value.rn.context, 'residential_annual')
    assert.equal(component.individualMetadata.value.rn.sample, 'indoor_air')
    assert.deepEqual(Array.from(component.individualProfile.value.comparable, item => item.key), ['pb', 'cd', 'hg', 'as', 'rn'])
    assert(component.individualProfile.value.rows.filter(item => ['th', 'li', 'cr', 'ni', 'co'].includes(item.key)).every(item => item.reference === null && item.ratio === null))
  })
  check('reference offset labels cannot collide with the category axis and the axis title stays below the plot', () => {
    const offset = options.get('singleChartZScore')
    assert.equal(offset.series[0].label.position, 'right')
    assert(offset.series[0].data.every(item => !item.label))
    assert.equal(offset.xAxis.nameLocation, 'middle')
    assert.equal(offset.xAxis.nameGap, 28)
  })
  await asyncCheck('repeating an untouched demo only reopens the result without replacing or confirming input', async () => {
    const before = snapshot()
    await component.fillIndividualDemo()
    await settle()
    assert.equal(snapshot(), before)
    assert.equal(confirmations.length, 0)
    assertSynthetic(false)
  })
  await asyncCheck('changing a demo number keeps synthetic provenance and updates the real Vue chart', async () => {
    component.formData.value.singleData.pb = 70
    await settle()
    assertSynthetic(true)
    assert.equal(options.get('singleChartMaster').series[0].data[0].value, 200)
    assert.equal(options.get('singleChartZScore').series[0].data[0].value, 100)
  })
  await asyncCheck('changing demo metadata remains synthetic and requires confirmation without rewriting the number', async () => {
    component.individualMetadata.value.pb.unit = 'μg/dL'
    component.handleMetadataChange('pb')
    await settle()
    assertSynthetic(true)
    assert.equal(component.formData.value.singleData.pb, 70)
    assert.equal(component.individualMetadata.value.pb.confirmed, false)
    assert.equal(component.individualProfile.value.rows[0].ratio, null)
    assert.equal(options.get('singleChartMaster').series[0].data[0].value, null)
    component.confirmMetadata('pb')
    await settle()
    assert.equal(component.individualProfile.value.rows[0].ratio, 2000)
    assertSynthetic(true)
  })
  await asyncCheck('changing demographic, name or job fields never relabels the synthetic input as a real record', async () => {
    // Restore demo through the page action, then change otherwise non-measurement fields.
    await component.fillIndividualDemo()
    await settle()
    assertSynthetic(false)
    for (const [key, value] of [['name', 'Edited person'], ['age', 40], ['history', 'Edited history']]) {
      const prior = component.formData.value.singleData[key]
      component.formData.value.singleData[key] = value
      await settle()
      assertSynthetic(true)
      component.formData.value.singleData[key] = prior
      await settle()
      assertSynthetic(false)
    }
    component.formData.value.job = 'welding'
    await settle()
    assertSynthetic(true)
  })

  const existingInputs = [
    ['name only', () => { component.formData.value.singleData.name = 'Existing person' }],
    ['measured zero', () => { component.formData.value.singleData.pb = 0 }],
    ['invalid measurement', () => { component.formData.value.singleData.pb = 'invalid' }],
    ['metadata only', () => { component.individualMetadata.value.pb.unit = 'μg/L' }]
  ]
  for (const [name, enter] of existingInputs) {
    for (const [action, invoke] of [['demo fill', () => component.fillIndividualDemo()], ['clear', () => component.clearIndividualInput()]]) {
      await asyncCheck(`${action} asks before replacing ${name}; cancellation preserves all current input and chart state`, async () => {
        await resetSingle()
        enter()
        await settle()
        assert.equal(component.hasIndividualInput.value, true)
        const before = snapshot()
        const chartInstances = [...charts.values()]
        confirmationResponses.push(false)
        await invoke()
        await settle()
        assert.equal(confirmations.length, 1)
        assert.match(confirmations[0][0], /会替换当前单人档案和测量口径/)
        assert.equal(confirmations[0][2].closeOnClickModal, false)
        assert.equal(confirmations[0][2].cancelButtonText, '保留当前数据')
        assert.equal(snapshot(), before)
        assert.deepEqual([...charts.values()], chartInstances)
        assert.equal(apiCalls, 0)
      })
    }
    await asyncCheck(`confirmed replacement of ${name} replaces the whole input with a clean synthetic demo`, async () => {
      await resetSingle()
      enter()
      await settle()
      confirmationResponses.push(true)
      await component.fillIndividualDemo()
      await settle()
      assert.equal(confirmations.length, 1)
      assert.equal(JSON.stringify(component.formData.value.singleData), JSON.stringify(demo.createIndividualDemo().singleData))
      assert.equal(JSON.stringify(component.individualMetadata.value), JSON.stringify(demo.createIndividualDemo().metadata))
      assert.equal(charts.size, 7)
      assertSynthetic(false)
    })
  }
  await asyncCheck('cancelling clear on a modified visible demo keeps synthetic provenance and all seven chart instances', async () => {
    component.formData.value.singleData.name = 'Modified demo'
    component.individualMetadata.value.cd.sample = 'random_urine'
    component.handleMetadataChange('cd')
    await settle()
    const before = snapshot()
    const chartInstances = [...charts.values()]
    confirmationResponses.push(false)
    await component.clearIndividualInput()
    await settle()
    assert.equal(snapshot(), before)
    assert.deepEqual([...charts.values()], chartInstances)
    assert.equal(charts.size, 7)
    assert.equal(component.individualMetadata.value.cd.confirmed, false)
    assertSynthetic(true)
  })
  await asyncCheck('confirmed clear completely restores empty measurements and metadata and releases the charts', async () => {
    confirmationResponses.push(true)
    await component.clearIndividualInput()
    await settle()
    assert.equal(JSON.stringify(component.formData.value.singleData), JSON.stringify(component.createEmptySingleData()))
    assert.equal(JSON.stringify(component.individualMetadata.value), JSON.stringify(refs.createIndividualMetadata()))
    assert.equal(component.hasIndividualInput.value, false)
    assert.equal(component.demoSource.value, false)
    assert.equal(component.demoEdited.value, false)
    assert.equal(component.demoSnapshot.value, '')
    assert.equal(component.showDashboard.value, false)
    assert.equal(component.currentStep.value, 1)
    assert.equal(component.individualProfile.value.counts.missing, 10)
    assert.equal(component.individualProfile.value.counts.comparable, 0)
    assert.equal(component.individualProfile.value.coverage, null)
    assert.equal(charts.size, 0)
    assert.equal(apiCalls, 0)
  })
  await asyncCheck('demo actions and single/batch switches preserve batch upload, outcome and analysis state without requests', async () => {
    component.selectedFile.value = { name: 'existing-batch.csv', size: 512 }
    component.selectedOutcomeId.value = 'existing-outcome'
    component.uploadResult.value = { marker: 'existing-upload', total_records: 9 }
    component.analysisData.value = { marker: 'existing-analysis' }
    const batchSnapshot = () => JSON.stringify({ file: component.selectedFile.value, outcome: component.selectedOutcomeId.value, upload: component.uploadResult.value, analysis: component.analysisData.value })
    const beforeBatch = batchSnapshot()
    await component.fillIndividualDemo()
    await settle()
    const beforeSingle = JSON.stringify({ input: component.formData.value.singleData, metadata: component.individualMetadata.value })
    component.handleModeChange('batch')
    await settle()
    assert.equal(component.formData.value.mode, 'batch')
    assert.equal(charts.size, 0)
    assert.equal(component.showDashboard.value, false)
    assert.equal(batchSnapshot(), beforeBatch)
    assert.equal(JSON.stringify({ input: component.formData.value.singleData, metadata: component.individualMetadata.value }), beforeSingle)
    assertSynthetic(false)
    component.handleModeChange('single')
    await settle()
    assert.equal(component.showDashboard.value, false)
    assert.equal(batchSnapshot(), beforeBatch)
    assert.equal(JSON.stringify({ input: component.formData.value.singleData, metadata: component.individualMetadata.value }), beforeSingle)
    assertSynthetic(false)
    await component.clearIndividualInput()
    await settle()
    assert.equal(batchSnapshot(), beforeBatch)
    assert.equal(component.demoSource.value, false)
    assert.equal(apiCalls, 0)
  })
  check('synthetic provenance badges remain present on both the input and visual-results sections', () => {
    assert((source.match(/v-if="demoSource"/g) || []).length >= 2)
    assert.match(source, /合成示例 · 已修改/)
    assert.match(source, /合成示例 · 非真实数据/)
    assert.match(source, /@click="fillIndividualDemo"/)
    assert.match(source, /@click="clearIndividualInput"/)
  })
  const sass = require(packagePath('sass-embedded@', 'sass-embedded'))
  const css = sass.compileString(parsed.descriptor.styles[0].content)
  check('existing and added SCSS compile locally', () => assert(css.css.length > 0))
  console.log(`\n${checks} offline checks passed. No model, HTTP, dataset or server invocation.`)
}
componentChecks().catch(error => { console.error(error); process.exitCode = 1 })
