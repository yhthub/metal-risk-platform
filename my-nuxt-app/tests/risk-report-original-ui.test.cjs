/** Offline only: original report layout and actual-input rendering contract. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
function dependency(prefix, name) { return require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith(prefix)), 'node_modules', name)) }
const compiler = dependency('@vue+compiler-sfc@', '@vue/compiler-sfc')
const ts = dependency('typescript@', 'typescript')
const sass = dependency('sass-embedded@', 'sass-embedded')
const filename = path.join(root, 'app/pages/risk/report.vue')
const source = fs.readFileSync(filename, 'utf8')
const parsed = compiler.parse(source, { filename })
let checks = 0
function check(name, fn) { fn(); checks++; console.log('PASS ' + name) }

check('report retains its document layout but only renders available individual model chart sections', () => {
  for (const name of ['system-layout', 'main-content', 'ep-header', 'nav-wrapper', 'report-view-wrapper', 'report-paper', 'report-watermark', 'report-header', 'rh-left', 'rh-right', 'risk-seal', 'worker-table', 'disease-list', 'report-footer', 'sign-area', 'report-btns']) assert(source.includes('class="' + name + '"'), name)
  for (const numeral of ['一、', '二、', '三、', '四、', '五、']) assert(parsed.descriptor.template.content.includes(numeral), numeral)
  for (const ref of ['reportGaugeRef', 'reportRadarRef', 'reportBloodRef', 'reportShapRef', 'reportDoseResponseRef', 'reportJointEffectRef']) assert(source.includes('ref="' + ref + '"'), ref)
  assert.match(source, /<template v-else-if="!isBatchMode && hasReport">/)
  assert.match(source, /<div v-if="radarOption \|\| shapOption" class="report-section">/)
  assert.match(source, /<el-col v-if="radarOption"/)
  assert.match(source, /<el-col v-if="shapOption"/)
  assert.match(source, /<div v-if="doseOption" class="report-section highlight">/)
  assert.match(source, /<div v-if="jointOption" class="report-section">/)
  assert(!/buildOriginalUnavailableOption|原图型骨架/.test(source))
})
check('SFC script/template and original SCSS compile offline', () => {
  assert.deepEqual(parsed.errors, [])
  const script = compiler.compileScript(parsed.descriptor, { id: 'risk-report-original-ui' })
  const template = compiler.compileTemplate({ source: parsed.descriptor.template.content, filename, id: 'risk-report-original-ui', compilerOptions: { bindingMetadata: script.bindings } })
  assert.deepEqual(template.errors, [])
  const transformed = ts.transpileModule(script.content, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
  assert.equal(transformed.diagnostics.length, 0)
  const css = sass.compileString(parsed.descriptor.styles[0].content)
  assert(css.css.includes('.risk-seal')); assert(css.css.includes('@media print'))
})
check('report has no hardcoded names, probabilities, synthetic curves or causal model claims', () => {
  assert(!/张建国|第一熔炼车间|2026-05-12|68\.5|Math\.random|Math\.exp|highRiskWorkers|diseaseRisks|shapData|Bayesian DAG|WARNING/.test(source))
  assert(!/致病概率|疾病图谱|极度危险界限|爆发拐点|因果风险增幅/.test(source))
  assert.match(source, /不是患病概率/)
  assert.match(source, /蓝色条仅标记“已提供估计值”，不是风险概率，也不表示指标数值大小/)
  assert.match(source, /不能证明协同致毒/)
  assert.match(source, /原生|scale_label/)
  assert.match(source, /暂无本次预测报告/)
  assert.match(source, /v-if="!hasReport"/)
  assert(!/localStorage|sessionStorage|document\.cookie|\bfetch\(|\buseApi\(/.test(source))
})
check('report keeps real individual builders separate from complete whole-file cohort state', () => {
  for (const name of ['buildGaugeOption', 'buildRadarOption', 'buildShapOption', 'buildDoseOption', 'buildJointOption', 'predictionHasValue', 'predictionReason', 'predictionIntervalLabel']) assert.match(source, new RegExp(name))
  assert.match(source, /isBatchMode = computed\(\(\) => route\.query\.mode === 'batch'\)/)
  assert.match(source, /cohortResult\.value\?\.complete === true && !cohortResponseError\(cohortResult\.value\)/)
  assert.match(source, /result = computed\(\(\) => isBatchMode\.value \? null/)
  assert.match(source, /<template v-if="isBatchMode && cohort">/)
  assert.match(source, /<template v-else-if="!isBatchMode && hasReport">/)
  assert(!/visibleBatch|batch_current_page|selectedRow|本页人员|当前已处理页面/.test(source))
  assert.match(source, /buildGaugeOption\(result\.value\)/, 'Gauge describes the current person 12 outcome coverage, not disease probability')
  assert.match(source, /batchPredictionCsv\(cohort\.value\)/)
  assert.match(source, /<RiskCohortWarning :result="cohort" :threshold="cohortWarningThreshold" @update:threshold="cohortWarningThreshold = \$event"/)
  assert.match(source, /所选结局单项数值排序 · Top 20 展示（不是综合预警榜）/)
  assert.match(source, /综合预警排序 CSV/)
  assert.match(source, /dashboard: dashboard\.value/)
  assert.match(source, /window\.print\(\)/)
  assert.match(source, /chart\.dispose\(\)/)
})
check('keep-alive lifecycle pauses hidden rendering and restores charts without duplicate listeners', () => {
  assert.match(source, /onActivated\(\(\) => \{ void resumeReport\(\) \}\)/)
  assert.match(source, /onDeactivated\(pauseReport\)/)
  assert.match(source, /if \(!mounted \|\| !active\) return/)
  assert.match(source, /if \(!mounted \|\| active\) return/)
  assert.match(source, /await nextTick\(\)[\s\S]*if \(!mounted \|\| !active\) return[\s\S]*initReportCharts\(\); resizeCharts\(\)/)
  assert.match(source, /if \(!resizeListening\) \{ window\.addEventListener\('resize', resizeCharts\); resizeListening = true \}/)
  assert.match(source, /if \(resizeListening\) \{ window\.removeEventListener\('resize', resizeCharts\); resizeListening = false \}/)
  assert.match(source, /function pauseReport\(\) \{[\s\S]*active = false[\s\S]*clearCharts\(\)/)
})
check('back navigation preserves batch versus individual mode explicitly', () => {
  assert.match(source, /navigateTo\(\{ path: '\/risk', query: \{ mode: isBatchMode\.value \? 'batch' : 'individual' \} \}\)/)
  assert(!/navigateTo\('\/risk'\)/.test(source))
})
check('original radar position uses true SHAP shares and input bars remain supplemental', () => {
  assert.match(source, /v-if="hasReport && radarOption" class="chart-box-report" ref="reportRadarRef"/)
  assert.match(source, /\[reportRadarRef\.value, radarOption\.value\]/)
  assert.match(source, /\[reportBloodRef\.value, buildBloodInputOption\(request\.value\)\]/)
  assert.match(source, /class="report-supplement"[\s\S]*ref="reportBloodRef"/)
  assert.match(source, /绝对 SHAP 贡献前 5 项与其他项合计/)
  assert.match(source, /不是金属浓度、疾病概率或因果作用/)
  assert.match(source, /modelChartAllowed = computed\(\(\) => !!activeOutcome\.value && predictionHasValue\(activeOutcome\.value\)\)/)
  assert.match(source, /charts\.value && modelChartAllowed\.value \? buildRadarOption\(charts\.value\) : null/)
})

const riskSource = fs.readFileSync(path.join(root, 'app/utils/riskPrediction.ts'), 'utf8')
const runtime = {}
vm.runInNewContext(ts.transpileModule(riskSource, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: runtime, setTimeout: () => {} })
const dashboardSource = fs.readFileSync(path.join(root, 'app/utils/riskDashboard.ts'), 'utf8')
const dashboardRuntime = {}
const paletteRuntime = {}
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils/riskPalette.ts'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: paletteRuntime })
const themeRuntime = {}
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils/riskChartTheme.ts'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: themeRuntime })
const chartImports = { './riskPrediction': runtime, './riskPalette': paletteRuntime, './riskChartTheme': themeRuntime }
vm.runInNewContext(ts.transpileModule(dashboardSource, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: dashboardRuntime, require: name => { assert(Object.hasOwn(chartImports, name)); return chartImports[name] } })
check('six-axis radar retains all absolute SHAP mass without inventing missing values', () => {
  const block = { target: 'sbp', label_zh: '收缩压', unit: 'mmHg', explanation: { status: 'AVAILABLE', scale_label: '原生输出尺度', items: [8, -6, 5, -4, 3, -2, 1].map((value, index) => ({ feature: 'f' + index, label_zh: '因素' + index, value })) } }
  const option = dashboardRuntime.buildRadarOption(block)
  assert(option)
  assert.equal(option.radar.indicator.length, 6)
  assert(option.radar.indicator.every(item => item.max === 100))
  const values = option.series[0].data[0].value
  assert.equal(values.length, 6)
  assert(Math.abs(values.reduce((sum, value) => sum + value, 0) - 100) < 1e-9)
  assert(Math.abs(values[5] - 3 / 29 * 100) < 1e-9, 'Other axis must aggregate remaining absolute contributions')
  assert.equal(dashboardRuntime.buildRadarOption({ ...block, explanation: { ...block.explanation, status: 'WITHHELD' } }), null)
  assert.equal(dashboardRuntime.buildRadarOption({ ...block, explanation: { ...block.explanation, items: block.explanation.items.slice(0, 4) } }), null)
  assert.equal(dashboardRuntime.buildRadarOption({ ...block, explanation: { ...block.explanation, items: block.explanation.items.map(item => ({ ...item, value: 0 })) } }), null)
})
const ast = ts.createSourceFile(filename, parsed.descriptor.scriptSetup.content, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS)
const selectedFunctions = ast.statements.filter(node => ts.isFunctionDeclaration(node) && ['buildBloodInputOption', 'metalLabel', 'tableRow'].includes(node.name?.text)).map(node => node.getText(ast)).join('\n')
const local = {}
vm.runInNewContext(ts.transpileModule(selectedFunctions + '\nexports.buildBloodInputOption=buildBloodInputOption; exports.metalLabel=metalLabel; exports.tableRow=tableRow;', { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: local, METAL_FIELDS: runtime.METAL_FIELDS, formatPredictionNumber: runtime.formatPredictionNumber, predictionHasValue: runtime.predictionHasValue, predictionReason: runtime.predictionReason })
const plain = value => JSON.parse(JSON.stringify(value))
const input = runtime.createPredictionDraft()
Object.assign(input.person, { age: 45, bmi: 24.5, pb: 12.3, cd: 0, hg: null })
Object.assign(input.measurements.pb, { unit: 'ug/L', sample: 'whole_blood' })
Object.assign(input.measurements.cd, { unit: 'ug/dL', sample: 'whole_blood' })
Object.assign(input.measurements.hg, { unit: 'ng/mL', sample: 'whole_blood' })
check('blood input charts use actual values and separate axes with each original unit', () => {
  const option = local.buildBloodInputOption(input)
  assert.equal(option.grid.length, 3)
  assert.deepEqual(plain(option.series.map(item => item.data)), [[12.3], [0], [null]])
  assert.deepEqual(plain(option.xAxis.map(item => item.name)), ['μg/L', 'μg/dL', 'ng/mL'])
  assert.deepEqual(plain(option.series.map(item => [item.xAxisIndex, item.yAxisIndex])), [[0, 0], [1, 1], [2, 2]])
  assert(option.series.every(item => item.type === 'bar'))
  assert.equal(local.metalLabel(input, 'cd'), '0 μg/dL')
  assert.equal(local.metalLabel(input, 'hg'), '未提供')
  assert.equal(local.metalLabel(undefined, 'pb'), '未提供')
})
check('table preserves original units and withheld/missing status without exposing bad numeric values', () => {
  const estimate = { target: 'sbp', prediction: 122.3, status: 'EXPLORATORY_ESTIMATE', unit: 'mmHg' }
  const row = local.tableRow('person', input, estimate, 'one', '本次对象')
  assert.equal(row.estimate, '122.3 mmHg'); assert.equal(row.pb, '12.3 μg/L')
  const withheld = local.tableRow('person', input, { ...estimate, prediction: 999, status: 'INSUFFICIENT_VALIDATED_ACCURACY', reason: '验证不足' }, 'one', '本次对象')
  assert.equal(withheld.estimate, '暂不出值'); assert.equal(withheld.reason, '验证不足')
  const missing = local.tableRow('', undefined, undefined, 'two', '原始行 2', 'BMI 缺失')
  assert.equal(missing.age, '—'); assert.equal(missing.pb, '未提供'); assert.equal(missing.reason, 'BMI 缺失')
})

const cohortSource = fs.readFileSync(path.join(root, 'app/utils/riskCohort.ts'), 'utf8')
const cohortRuntime = {}
vm.runInNewContext(ts.transpileModule(cohortSource, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: cohortRuntime, require: name => { assert(Object.hasOwn(chartImports, name)); return chartImports[name] } })
const warningRuntime = {}
const warningImports = { ...chartImports, './riskCohort': cohortRuntime }
vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils/cohortWarning.ts'), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports: warningRuntime, require: name => { assert(Object.hasOwn(warningImports, name)); return warningImports[name] } })
function cohortFixture() {
  const targets = ['sbp', 'dbp', 'serum_creatinine_mg_dl', 'bun_mg_dl', 'uric_acid_mg_dl', 'uacr_mg_g', 'hba1c_percent', 'total_cholesterol_mg_dl', 'hdl_cholesterol_mg_dl', 'alt_u_l', 'ast_u_l', 'ggt_u_l']
  const records = Array.from({ length: 25 }, (_, index) => ({ row_number: index + 1, person_id: 'SYNTHETIC-' + (index + 1), status: 'ESTIMATES_NOT_DIAGNOSES', input: { ...plain(input), person: { ...plain(input.person), id: 'SYNTHETIC-' + (index + 1), age: index + 20, gender: index % 2 ? 'male' : 'female' } }, results: targets.map((target, targetIndex) => ({ target, label_zh: target, unit: target === 'sbp' || target === 'dbp' ? 'mmHg' : 'test-unit', prediction: target === 'uacr_mg_g' ? null : 100 + index + targetIndex, status: target === 'uacr_mg_g' ? 'INSUFFICIENT_VALIDATED_ACCURACY' : 'EXPLORATORY_ESTIMATE', reason: target === 'uacr_mg_g' ? '验证不足' : '', reference_interval: null, test_metrics: { MAE: 1, RMSE: 2, R2: .2, n: 50 }, selection_R2: .2, model_family: ['xgboost'], candidate_id: 'fixture' })) }))
  records.push({ row_number: 26, person_id: 'SYNTHETIC-SKIPPED', status: 'INPUT_NOT_ELIGIBLE', reason: 'BMI 缺失' })
  const summary = targets.map((target, index) => {
    const withheld = target === 'uacr_mg_g'
    const statistics = { n: withheld ? 0 : 25, mean: withheld ? null : 112 + index, median: withheld ? null : 112 + index, q1: withheld ? null : 106 + index, q3: withheld ? null : 118 + index, min: withheld ? null : 100 + index, max: withheld ? null : 124 + index, std: withheld ? null : Math.sqrt(52) }
    const group = { group: 'fixture', label_zh: '合成测试组', eligible_count: 25, estimated_count: statistics.n, withheld_count: withheld ? 25 : 0, mean_prediction: statistics.mean, statistics }
    return { target, label_zh: target, unit: target === 'sbp' || target === 'dbp' ? 'mmHg' : 'test-unit', estimated_count: statistics.n, withheld_count: withheld ? 25 : 0, mean_prediction: statistics.mean, statistics, histogram: { status: withheld ? 'UNAVAILABLE' : 'AVAILABLE', bin_edges: withheld ? [] : [100 + index, 110 + index, 125 + index], counts: withheld ? [] : [10, 15], counted_records: statistics.n }, by_gender: [group], by_age_band: [group] }
  })
  return { model_version: 'fixture-v5', run_id: 'fixture-only', profile: 'basic', file_id: 'FILE-fixture', total_records: 26, offset: 0, limit: 26, processed_records: 25, skipped_records: 1, has_more: false, analysis_scope: 'all_uploaded_records', complete: true, records, summary, warnings: [], provenance: { fixture: 'SYNTHETIC_OFFLINE_TEST_ONLY' } }
}
function reportHarness() {
  const names = new Set(['isBatchMode', 'cohort', 'cohortEmptyReason', 'result', 'request', 'charts', 'hasReport', 'currentTarget', 'cohortView', 'compositeWarning', 'cohortTopRows', 'cohortExcluded', 'cohortRankOption', 'cohortDistributionOption', 'cohortGenderOption', 'cohortAgeOption', 'selectedLabel', 'reportRows', 'exportJson', 'exportCsv', 'exportCohortRanking', 'exportCompositeWarning', 'exportCohortSummary'])
  const statements = ast.statements.filter(node => ts.isVariableStatement(node) && node.declarationList.declarations.some(declaration => ts.isIdentifier(declaration.name) && names.has(declaration.name.text))).map(node => node.getText(ast)).join('\n')
  const state = { route: { query: { mode: 'batch' } }, cohortResult: { value: cohortFixture() }, cohortWarningThreshold: { value: 80 }, dashboard: { value: null }, lastResult: { value: null }, lastRequest: { value: null }, selectedTarget: { value: 'sbp' } }
  const exports = {}; const downloads = []
  const bindings = { ...runtime, ...cohortRuntime, ...warningRuntime, ...state, selectedOutcome: dashboardRuntime.selectedOutcome, tableRow: local.tableRow, computed: fn => ({ get value() { return fn() } }), exports, downloadPrediction: (content, format, filename) => downloads.push({ content, format, filename }) }
  vm.runInNewContext(ts.transpileModule(statements + '\nexports.report={' + [...names].join(',') + '};', { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, bindings)
  return { state, report: exports.report, downloads }
}
check('complete cohort report renders without any individual dashboard or last request', () => {
  const { state, report } = reportHarness()
  assert.equal(cohortRuntime.cohortResponseError(state.cohortResult.value), null)
  assert.equal(report.hasReport.value, true)
  assert.equal(report.result.value, null); assert.equal(report.request.value, null); assert.equal(report.charts.value, undefined)
  assert.equal(report.cohortView.value.estimated_count, 25)
  assert.equal(report.cohortTopRows.value.length, 20)
  assert.equal(report.cohortTopRows.value[0].person_id, 'SYNTHETIC-25')
  assert.equal(report.cohortExcluded.value[0].person_id, 'SYNTHETIC-SKIPPED')
  assert(report.cohortRankOption.value); assert(report.cohortDistributionOption.value); assert(report.cohortGenderOption.value); assert(report.cohortAgeOption.value)
  state.selectedTarget.value = 'uacr_mg_g'
  assert.equal(report.cohortView.value.estimated_count, 0)
  assert.equal(report.cohortTopRows.value.length, 0)
  assert.equal(report.cohortRankOption.value, null); assert.equal(report.cohortDistributionOption.value, null)
})
check('batch mode refuses partial pages and never substitutes a stale individual response', () => {
  const { state, report } = reportHarness()
  state.dashboard.value = { input, prediction: { person_id: 'OLD-INDIVIDUAL', results: [] }, charts: { target: 'sbp' } }
  state.lastRequest.value = input
  state.lastResult.value = state.dashboard.value.prediction
  state.cohortResult.value.complete = false
  assert.equal(report.hasReport.value, false)
  assert.equal(report.cohort.value, null); assert.equal(report.result.value, null); assert.equal(report.request.value, null)
  state.cohortResult.value.complete = true
  state.cohortResult.value.records.pop()
  assert.equal(report.hasReport.value, false)
  state.cohortResult.value = cohortFixture()
  state.route.query.mode = 'individual'
  assert.equal(report.cohort.value, null)
  assert.equal(report.result.value.person_id, 'OLD-INDIVIDUAL')
})
check('cohort JSON and CSV exports include every record and outcome, not the Top20 display slice', () => {
  const { report, downloads } = reportHarness()
  report.exportJson(); report.exportCsv(); report.exportCohortRanking(); report.exportCohortSummary()
  const json = JSON.parse(downloads[0].content)
  assert.equal(json.cohort.records.length, 26)
  assert.equal(json.cohort.records[24].results.length, 12)
  assert.equal(json.provenance.fixture, 'SYNTHETIC_OFFLINE_TEST_ONLY')
  assert.deepEqual(plain(json.composite_warning), plain(report.compositeWarning.value))
  const fullCsv = downloads[1].content
  assert.equal(fullCsv.split('\r\n').length, 302, '25 people x 12 outcomes + skipped record + header')
  assert(fullCsv.includes('SYNTHETIC-1')); assert(fullCsv.includes('SYNTHETIC-SKIPPED')); assert(fullCsv.includes('BMI 缺失')); assert(fullCsv.includes('验证不足'))
  assert.equal(downloads[2].content.split('\r\n').length, 26, 'All 25 estimates plus header, not just 20')
  assert.equal(downloads[3].content.split('\r\n').length, 13, 'All 12 summaries plus header')
})
check('report threshold, displayed composite rule and separate downloads remain identical across target changes', () => {
  const { state, report, downloads } = reportHarness()
  const baseline = plain(report.compositeWarning.value)
  assert.equal(baseline.threshold, 80)
  assert.equal(baseline.evaluated_count, 25)
  assert.equal(baseline.not_evaluated_count, 1)
  assert.equal(baseline.available_outcome_count, 11)
  state.selectedTarget.value = 'uacr_mg_g'
  assert.deepEqual(plain(report.compositeWarning.value), baseline, 'Choosing a different single outcome cannot change the composite warning population or rule')
  state.cohortWarningThreshold.value = 100
  const highThreshold = plain(report.compositeWarning.value)
  assert.equal(highThreshold.threshold, 100)
  assert.equal(highThreshold.status, 'CLEAR')
  assert.equal(highThreshold.warning_count, 0)
  assert.deepEqual(highThreshold.rankings.map(row => row.display_id), baseline.rankings.map(row => row.display_id), 'Threshold changes flagging, not underlying participant scores or numbering')
  report.exportJson(); report.exportCompositeWarning(); report.exportCohortRanking()
  const json = JSON.parse(downloads[0].content)
  assert.deepEqual(json.composite_warning, highThreshold)
  assert.equal(downloads[1].filename, 'NHANES_cohort_composite_warning')
  assert.equal(downloads[1].content, warningRuntime.warningRankingCsv(report.compositeWarning.value), 'The export must use the exact displayed composite rule')
  assert.equal(downloads[1].content.split('\r\n').length, 313, 'Every uploaded row x all 12 outcomes, including skipped objects, is traceable')
  assert.match(downloads[1].content, /P-000001/)
  assert.match(downloads[1].content, /SYNTHETIC-SKIPPED/)
  assert.match(downloads[1].content, /BMI 缺失/)
  assert.equal(downloads[2].filename, 'NHANES_cohort_ranking_uacr_mg_g')
  assert.equal(downloads[2].content.split('\r\n').length, 1, 'Withheld single-outcome ranking stays empty and does not masquerade as the composite export')
})
check('compact cohort outcomes and top-level metadata work without borrowing individual model cards', () => {
  const { state, report, downloads } = reportHarness()
  const compact = cohortFixture()
  compact.outcome_metadata = compact.records[0].results.map(({ target, test_metrics, selection_R2, model_family, candidate_id }) => ({ target, test_metrics, selection_R2, model_family, candidate_id }))
  for (const record of compact.records) record.results = record.results ? record.results.map(({ target, label_zh, unit, prediction, status, reason }) => ({ target, label_zh, unit, prediction, status, reason })) : null
  state.cohortResult.value = compact
  assert.equal(report.hasReport.value, true)
  assert.equal(report.cohortTopRows.value.length, 20)
  report.exportJson(); report.exportCsv()
  assert.equal(JSON.parse(downloads[0].content).cohort.outcome_metadata.length, 12)
  assert.equal(downloads[1].content.split('\r\n').length, 302)
  assert(downloads[1].content.includes('SYNTHETIC-SKIPPED'))
})
console.log('\n' + checks + ' original report checks passed; no server, browser or model invoked.')
