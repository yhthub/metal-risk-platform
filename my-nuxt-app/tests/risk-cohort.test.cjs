/** Complete-population analytical views; no model, browser or network. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const modules = {}
function load(name) {
  if (modules[name]) return modules[name]
  const exported = {}
  modules[name] = exported
  const file = path.join(root, 'app/utils', name + '.ts')
  const code = ts.transpileModule(fs.readFileSync(file, 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }, reportDiagnostics: true })
  assert.equal(code.diagnostics.length, 0)
  vm.runInNewContext(code.outputText, { exports: exported, require: request => load(request.replace('./', '')), setTimeout() {} })
  return exported
}
const cohort = load('riskCohort')
const targets = ['sbp', 'dbp', 'creatinine', 'bun', 'uric_acid', 'uacr', 'hba1c', 'cholesterol', 'hdl', 'alt', 'ast', 'ggt']
function fixture(count = 601) {
  const records = Array.from({ length: count }, (_, index) => ({ row_number: index + 1, person_id: 'PUBLIC-' + (index + 1), status: 'ESTIMATES_NOT_DIAGNOSES', input: { person: { age: 40, gender: index % 2 ? 'female' : 'male' } },
    results: targets.map(target => ({ target, label_zh: target, unit: 'unit', prediction: index, status: 'EXPLORATORY_ESTIMATE' })) }))
  const stats = { n: count, mean: (count - 1) / 2, median: (count - 1) / 2, q1: 0, q3: count - 1, min: 0, max: count - 1, std: 1 }
  const group = { group: 'male', label_zh: '男性', eligible_count: count, estimated_count: count, withheld_count: 0, mean_prediction: stats.mean, statistics: stats }
  return { model_version: 'fixture', run_id: 'fixture', profile: 'basic', file_id: 'FILE-1234abcd', complete: true, analysis_scope: 'all_uploaded_records',
    total_records: count, limit: count, offset: 0, has_more: false, processed_records: count, skipped_records: 0, records,
    summary: targets.map(target => ({ target, label_zh: target, unit: 'unit', estimated_count: count, mean_prediction: stats.mean, withheld_count: 0, statistics: { ...stats },
      histogram: { status: 'AVAILABLE', bin_edges: [0, count], counts: [count], counted_records: count }, by_gender: [group], by_age_band: [{ ...group, group: '40_59', label_zh: '40–59岁' }] })), warnings: [] }
}
const plain = value => JSON.parse(JSON.stringify(value))

test('a result after row 500 enters the global ranking instead of disappearing behind the first page', () => {
  const result = fixture()
  assert.equal(cohort.cohortResponseError(result), null)
  const before = plain(result)
  const view = cohort.buildCohortView(result, 'sbp')
  assert.equal(view.rankings.length, 601)
  assert.equal(view.rankings[0].person_id, 'PUBLIC-601')
  assert.equal(view.rankings[0].rank, 1)
  assert.equal(view.rankings[600].rank, 601)
  const chart = cohort.buildCohortRankOption(result, 'sbp')
  assert.equal(chart.series[0].data.length, 10)
  assert.equal(chart.series[0].data[0], 600)
  assert.deepEqual(plain(result), before, 'Rendering cannot mutate original participant order or predictions')
})
test('partial, legacy and misleadingly complete page responses are rejected', () => {
  for (const mutate of [r => { r.complete = false }, r => { r.analysis_scope = 'page' }, r => { r.has_more = true },
    r => { r.offset = 500 }, r => { r.limit = 20 }, r => { r.records.pop() }, r => { r.processed_records-- },
    r => { r.records[1].person_id = r.records[0].person_id }, r => { r.records[0].row_number = 2 },
    r => { r.records[0].results.pop() }, r => { r.summary[0].estimated_count-- }]) {
    const result = fixture(3)
    mutate(result)
    assert(cohort.cohortResponseError(result))
  }
})
test('tie ordering is deterministic and true zero remains in ranking', () => {
  const result = fixture(3)
  result.records[2].results[0].prediction = 1
  const view = cohort.buildCohortView(result, 'sbp')
  assert.deepEqual(plain(view.rankings.map(row => row.row_number)), [2, 3, 1])
  assert.equal(view.rankings[2].prediction, 0)
})
test('withheld values never enter charts or ranking even if an upstream numeric field is present', () => {
  const result = fixture(3)
  for (const row of result.records) Object.assign(row.results[0], { status: 'INSUFFICIENT_VALIDATED_ACCURACY', prediction: 999, reason: '验证不足' })
  Object.assign(result.summary[0], { estimated_count: 0, withheld_count: 3, statistics: { n: 0 }, histogram: { status: 'UNAVAILABLE', counts: [], bin_edges: [], counted_records: 0 } })
  const view = cohort.buildCohortView(result, 'sbp')
  assert.equal(view.rankings.length, 0)
  assert.equal(view.statistics, null)
  assert.equal(view.reason, '验证不足')
  assert.equal(cohort.buildCohortRankOption(result, 'sbp'), null)
  assert.equal(cohort.buildCohortDistributionOption(result, 'sbp'), null)
})
test('all-ineligible input remains a complete cohort with exclusions, not a fake zero distribution', () => {
  const result = fixture(3)
  result.records = result.records.map(row => ({ ...row, input: undefined, status: 'INPUT_NOT_ELIGIBLE', reason: 'BMI缺失', results: null }))
  Object.assign(result, { processed_records: 0, skipped_records: 3 })
  result.summary = result.summary.map(row => ({ ...row, estimated_count: 0, withheld_count: 0, mean_prediction: null, statistics: { n: 0 }, histogram: { counts: [], bin_edges: [], counted_records: 0 } }))
  assert.equal(cohort.cohortResponseError(result), null)
  const view = cohort.buildCohortView(result, 'sbp')
  assert.equal(view.excluded.length, 3)
  assert.equal(view.rankings.length, 0)
  assert.match(view.reason, /所有对象/)
})
test('distribution conserves the full estimated count and invalid histogram is not plotted', () => {
  const result = fixture(601)
  assert.deepEqual(plain(cohort.buildCohortDistributionOption(result, 'sbp').series[0].data), [601])
  result.summary[0].histogram.counts = [20]
  assert.equal(cohort.buildCohortDistributionOption(result, 'sbp'), null)
})
test('sex and age plots use group means in native units, never disease percentages', () => {
  const result = fixture(4)
  result.summary[0].by_age_band[0].label_zh = '60–80岁（80含公开年龄顶码）'
  for (const group of ['gender', 'age']) {
    const option = cohort.buildCohortGroupOption(result, 'sbp', group)
    assert.equal(option.series[0].data[0], 1.5)
    assert.equal(option.yAxis.name, 'unit')
    assert.match(option.tooltip.formatter([{ dataIndex: 0 }]), /未调整混杂/)
    assert.equal(option.xAxis.axisLabel.interval, 0, 'All group labels stay visible at desktop card width')
    if (group === 'age') {
      assert.equal(option.xAxis.data[0], '60–80岁')
      assert.match(option.tooltip.formatter([{ dataIndex: 0 }]), /年龄顶码/)
    }
  }
})
test('CSV export includes all persons and all outcomes in separate clearly scoped files', () => {
  const result = fixture(601)
  const ranking = cohort.cohortRankingCsv(result, 'sbp')
  assert.equal(ranking.split('\r\n').length, 602)
  assert(ranking.includes('PUBLIC-601'))
  assert(ranking.includes('PUBLIC-1'))
  assert.match(ranking, /不是临床高危等级或疾病概率/)
  const summary = cohort.cohortSummaryCsv(result)
  assert.equal(summary.split('\r\n').length, 13)
  assert.match(summary, /all_uploaded_records/)
  assert.match(summary, /未加权汇总/)
})
test('rank tooltips and downloadable participant identifiers are escaped', () => {
  const result = fixture(1)
  result.records[0].person_id = '=1+1'
  assert(cohort.cohortRankingCsv(result, 'sbp').includes("'=1+1"))
  const option = cohort.buildCohortRankOption(result, 'sbp')
  assert(!option.tooltip.formatter([{ name: '<img src=x>', value: 12 }]).includes('<img'))
})
test('cohort types and builders pass strict TypeScript checking', () => {
  const file = path.join(root, 'app/utils/riskCohort.ts')
  const program = ts.createProgram([file], { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, moduleResolution: ts.ModuleResolutionKind.Bundler, strict: true, skipLibCheck: true, noEmit: true })
  const diagnostics = ts.getPreEmitDiagnostics(program).filter(item => item.file?.fileName.includes('/app/utils/') || item.file?.fileName.includes('\\app\\utils\\'))
  assert.equal(diagnostics.length, 0, diagnostics.map(item => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'))
})
