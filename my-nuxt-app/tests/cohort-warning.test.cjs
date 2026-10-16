/** Pure saved-result prioritisation. No server, model, API, file mutation or clinical cutoffs. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const loaded = {}
function load(name) {
  if (loaded[name]) return loaded[name]
  const exported = {}; loaded[name] = exported
  const code = ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils', name + '.ts'), 'utf8'), { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }, reportDiagnostics: true })
  assert.equal(code.diagnostics.length, 0)
  vm.runInNewContext(code.outputText, { exports: exported, require: request => load(request.replace('./', '')), setTimeout() {} })
  return exported
}
const warning = load('cohortWarning')
const defs = warning.COHORT_WARNING_TARGETS
const plain = value => JSON.parse(JSON.stringify(value))
function fixture(count = 10) {
  const records = Array.from({ length: count }, (_, index) => ({ row_number: index + 1, person_id: String(93703 + index), status: 'ESTIMATES_NOT_DIAGNOSES', input: { person: { age: 40, gender: index % 2 ? 'female' : 'male' } },
    results: defs.map(({ target, label_zh, unit, direction }) => ({ target, label_zh, unit, prediction: direction === 'LOW' ? count - index : index, status: 'EXPLORATORY_ESTIMATE' })) }))
  const stats = { n: count, mean: 4, median: 4, q1: 1, q3: 7, min: 0, max: 9, std: 1 }
  return { model_version: 'fixture', run_id: 'fixture', profile: 'basic', file_id: 'FILE-1234abcd', complete: true, analysis_scope: 'all_uploaded_records',
    total_records: count, limit: count, offset: 0, has_more: false, processed_records: count, skipped_records: 0, records,
    summary: defs.map(({ target, label_zh, unit }) => ({ target, label_zh, unit, estimated_count: count, withheld_count: 0, mean_prediction: 4, statistics: { ...stats },
      histogram: { status: 'AVAILABLE', bin_edges: [0, count], counts: [count], counted_records: count }, by_gender: [], by_age_band: [] })), warnings: [] }
}
function refreshCounts(result) {
  const eligible = result.records.filter(row => row.status === 'ESTIMATES_NOT_DIAGNOSES')
  result.processed_records = eligible.length; result.skipped_records = result.total_records - eligible.length
  for (const summary of result.summary) {
    const count = eligible.filter(row => { const value = row.results.find(item => item.target === summary.target); return value.status === 'EXPLORATORY_ESTIMATE' && typeof value.prediction === 'number' && Number.isFinite(value.prediction) }).length
    summary.estimated_count = count; summary.withheld_count = eligible.length - count; summary.statistics.n = count
  }
}
function withhold(result, indices) {
  for (const row of result.records) for (const index of indices) Object.assign(row.results[index], { status: 'INSUFFICIENT_VALIDATED_ACCURACY', prediction: 98765, reason: '冻结策略暂不出值' })
  refreshCounts(result)
}

test('the canonical 12 targets match the deployed registry, with low-end HDL only', () => {
  const registry = JSON.parse(fs.readFileSync(path.join(root, '../models/nhanes_v5/registry.json'), 'utf8'))
  assert.deepEqual(plain(defs.map(row => row.target)), registry.results.filter(row => row.profile === 'basic').map(row => row.target))
  assert.equal(defs.filter(row => row.direction === 'LOW').length, 1)
  assert.equal(defs.find(row => row.direction === 'LOW').target, 'hdl_cholesterol_mg_dl')
})
test('full-file ranks include row 601, use normalized identifiers, and never mutate saved results', () => {
  const result = fixture(601); const before = plain(result); const output = warning.buildCohortWarning(result)
  assert.equal(output.status, 'ALERT'); assert.equal(output.evaluated_count, 601); assert.equal(output.available_outcome_count, 12)
  assert.equal(output.rankings[0].row_number, 601); assert.equal(output.rankings[0].display_id, 'P-000601'); assert.equal(output.rankings[0].person_id, '94303')
  assert.equal(output.rankings[0].score, 100); assert.equal(output.rankings[0].rank, 1)
  assert.equal(output.warning_count, 121); assert.equal(output.percentage, 121 / 601 * 100)
  assert.deepEqual(plain(result), before)
  assert.deepEqual(plain(output.rows.map(row => row.row_number)), Array.from({ length: 601 }, (_, index) => index + 1))
})
test('an exact threshold is compared with unrounded scores, not rendered labels', () => {
  const result = fixture(601); const output = warning.buildCohortWarning(result, 80)
  const below = output.rows[479]; const exact = output.rows[480]
  assert(below.score < 80); assert.equal(below.is_warning, false)
  assert.equal(exact.score, 80); assert.equal(exact.is_warning, true)
  assert.equal(warning.buildCohortWarning(result, 79.84).rows[479].is_warning, false)
})
test('mid-rank handles ties and stable source ordering; all constants have score 50, not forced danger', () => {
  const result = fixture(6)
  for (const row of result.records) for (const outcome of row.results) outcome.prediction = 7
  const output = warning.buildCohortWarning(result)
  assert.equal(output.status, 'CLEAR'); assert.equal(output.warning_count, 0); assert.equal(output.percentage, 0)
  for (const row of output.rows) { assert.equal(row.score, 50); assert.equal(row.rank, 3.5); for (const outcome of row.outcomes) { assert.equal(outcome.rank, 3.5); assert.equal(outcome.percentile, 50) } }
  assert.deepEqual(plain(output.rankings.map(row => row.row_number)), [1, 2, 3, 4, 5, 6])
  assert.match(output.reason, /不代表/)
})
test('nonconstant target ties use average rank and never depend on initial tied order', () => {
  const result = fixture(5)
  for (let index = 0; index < 5; index++) for (const outcome of result.records[index].results) outcome.prediction = outcome.target === 'hdl_cholesterol_mg_dl' ? -[1, 3, 3, 5, 5][index] : [1, 3, 3, 5, 5][index]
  const output = warning.buildCohortWarning(result)
  assert.equal(output.rows[3].outcomes[0].rank, 1.5); assert.equal(output.rows[3].outcomes[0].percentile, 87.5)
  assert.equal(output.rows[1].outcomes[0].rank, 3.5); assert.equal(output.rows[1].score, 37.5)
  assert.equal(output.rows[3].rank, 1.5); assert.equal(output.rows[4].rank, 1.5)
  assert.deepEqual(plain(output.rankings.map(row => row.row_number)), [4, 5, 2, 3, 1])
})
test('cross-outcome rank permutations preserve mathematical ties and the exact 80 boundary', () => {
  const result = fixture(11); withhold(result, [2, 3, 5, 6, 8])
  const used = [0, 1, 4, 7, 9, 10, 11]
  const ranksA = [1, 2, 3, 4, 5, 1, 5]; const ranksB = [2, 3, 4, 5, 1, 5, 1]
  for (let column = 0; column < used.length; column++) {
    const target = used[column]
    const remaining = Array.from({ length: 11 }, (_, index) => index + 1).filter(rank => rank !== ranksA[column] && rank !== ranksB[column])
    for (let index = 0; index < 11; index++) {
      const rank = index === 0 ? ranksA[column] : index === 1 ? ranksB[column] : remaining[index - 2]
      result.records[index].results[target].prediction = 12 - rank
    }
  }
  const output = warning.buildCohortWarning(result, 80)
  assert.equal(output.rows[0].score, 80); assert.equal(output.rows[1].score, 80)
  assert.equal(output.rows[0].rank, output.rows[1].rank)
  assert.equal(output.rows[0].is_warning, true); assert.equal(output.rows[1].is_warning, true)
  assert(output.rankings.indexOf(output.rows[0]) < output.rankings.indexOf(output.rows[1]), 'Equal composite scores retain original-row ordering')
  assert.equal(warning.buildCohortWarning(result, 80.00000000001).rows[0].is_warning, false)
})
test('HDL ranks from the lower end while high-end targets rank descending', () => {
  const result = fixture(5); const output = warning.buildCohortWarning(result)
  const top = output.rows[4]; const hdl = top.outcomes.find(row => row.target === 'hdl_cholesterol_mg_dl')
  assert.equal(hdl.direction, 'LOW'); assert.equal(hdl.value, 1); assert.equal(hdl.rank, 1); assert.equal(hdl.percentile, 100)
  assert.equal(top.outcomes[0].direction, 'HIGH'); assert.equal(top.outcomes[0].value, 4); assert.equal(top.outcomes[0].rank, 1)
})
test('withheld numeric fields remain null, shared dimensions exclude partially missing targets for every person', () => {
  const result = fixture(10); withhold(result, [2, 3, 5, 6, 8])
  Object.assign(result.records[0].results[4], { prediction: null, status: 'MISSING_RESULT', reason: '原始估计缺失' }); refreshCounts(result)
  const output = warning.buildCohortWarning(result)
  assert.equal(output.available_outcome_count, 6); assert.equal(output.excluded_targets.length, 6)
  for (const row of output.rows) {
    assert.equal(row.used_count, 6); assert.equal(row.outcomes.length, 12); assert.equal(row.outcomes[2].value, null)
    assert.equal(row.outcomes[2].rank, null); assert.equal(row.outcomes[4].rank, null)
  }
  assert.equal(output.rows[1].outcomes[4].value, 1, 'Valid saved values remain available, but are not mixed into a different denominator')
})
test('one or four valid people cannot yield a green no-warning claim; no eligible remains insufficient', () => {
  for (const count of [1, 4]) {
    const output = warning.buildCohortWarning(fixture(count)); assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.percentage, null); assert.equal(output.evaluated_count, 0)
    assert.equal(warning.buildWarningShareOption(output), null)
  }
  const result = fixture(5)
  result.records = result.records.map(row => ({ ...row, status: 'INPUT_NOT_ELIGIBLE', reason: 'BMI缺失', input: undefined, results: null })); refreshCounts(result)
  const output = warning.buildCohortWarning(result)
  assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.eligible_count, 0); assert.equal(output.not_evaluated_count, 5)
  assert(output.rows.every(row => row.score === null && row.is_warning === false))
})
test('fewer than three common outcomes cannot create safe or warning conclusions', () => {
  const result = fixture(10); withhold(result, [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])
  const output = warning.buildCohortWarning(result)
  assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.available_outcome_count, 2); assert.equal(output.evaluated_count, 0)
  assert.equal(output.rows[0].score, null); assert.equal(output.rows[0].outcomes[0].percentile, 0)
})
test('non-finite and string predictions never enter scores; zeros are genuine values, not missing', () => {
  for (const invalid of [NaN, Infinity, '4']) {
    const result = fixture(5); result.records[0].results[0].prediction = invalid; refreshCounts(result)
    const output = warning.buildCohortWarning(result)
    assert.equal(output.available_outcome_count, 11); assert.equal(output.rows[0].outcomes[0].value, null)
    assert.equal(output.rows[4].used_count, 11)
  }
  assert.equal(warning.buildCohortWarning(fixture(5)).rows[0].outcomes[0].value, 0)
})
test('invalid thresholds and invalid complete-population contracts fail closed without throwing', () => {
  for (const threshold of [NaN, Infinity, -1, 101, '80', null]) {
    const output = warning.buildCohortWarning(fixture(10), threshold)
    assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.threshold_valid, false); assert.equal(output.threshold, null); assert.equal(output.percentage, null)
    assert.equal(output.evaluated_count, 0); assert.match(output.reason, /阈值/)
  }
  for (const mutate of [r => { r.complete = false }, r => { r.records.pop() }, r => { r.has_more = true }, r => { r.summary[0].target = 'unknown_target' }, r => { r.records[1].person_id = r.records[0].person_id }]) {
    const result = fixture(10); mutate(result)
    const output = warning.buildCohortWarning(result)
    assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.evaluated_count, 0); assert.equal(output.percentage, null)
  }
})
test('corrupted basic structures return insufficient data without crashing rendering', () => {
  for (const value of [undefined, null, '', {}, { records: null, summary: null }, { records: [null], summary: [null] }]) {
    let output
    assert.doesNotThrow(() => { output = warning.buildCohortWarning(value) })
    assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.percentage, null)
  }
  for (const mutate of [r => { r.records[1] = null }, r => { r.records[1].results = 'invalid' }, r => { r.records[1].results[0] = null },
    r => { r.summary[1] = null }, r => { r.summary = 'invalid' }, r => { r.records[1].input = [] }]) {
    const result = fixture(10); mutate(result)
    const output = warning.buildCohortWarning(result)
    assert.equal(output.status, 'INSUFFICIENT_DATA'); assert.equal(output.evaluated_count, 0); assert.equal(output.percentage, null)
  }
})
test('threshold 100 does not force top-tail flags when outcomes disagree', () => {
  const result = fixture(10)
  for (let index = 0; index < 10; index++) result.records[index].results[0].prediction = 10 - index
  const output = warning.buildCohortWarning(result, 100)
  assert.equal(output.status, 'CLEAR'); assert.equal(output.warning_count, 0); assert(output.max_score < 100)
})
test('warning share uses evaluated denominator, distinguishes skipped and never fills missing with zero', () => {
  const result = fixture(11)
  result.records[10] = { row_number: 11, person_id: 'SKIPPED', status: 'INPUT_NOT_ELIGIBLE', reason: '无BMI', results: null }; refreshCounts(result)
  const output = warning.buildCohortWarning(result)
  assert.equal(output.evaluated_count, 10); assert.equal(output.not_evaluated_count, 1); assert.equal(output.warning_count, 2)
  assert.equal(output.percentage, 20); assert.equal(output.total_percentage, 2 / 11 * 100)
  const option = warning.buildWarningShareOption(output)
  assert.deepEqual(plain(option.series[0].data.map(row => row.value)), [2, 8])
  assert.match(option.tooltip.formatter({ name: '预警', value: 2 }), /已评估10人；未评估1人/)
})
test('Top20 display limits do not change complete warning counts or include unflagged objects', () => {
  const output = warning.buildCohortWarning(fixture(601)); const before = plain(output)
  const rank = warning.buildWarningRankOption(output, 20)
  assert.equal(rank.series[0].data.length, 20); assert.equal(rank.yAxis.data[0], 'P-000601')
  assert.equal(output.warning_count, 121); assert.deepEqual(plain(output), before)
  assert.equal(warning.buildWarningRankOption(warning.buildCohortWarning(fixture(4))), null)
  assert.equal(warning.cohortDisplayId(1), 'P-000001'); assert.equal(warning.cohortDisplayId(1000000), 'P-1000000'); assert.equal(warning.cohortDisplayId(NaN), 'P-UNKNOWN')
})
test('escaped tooltips retain original IDs; CSV neutralizes formulas and preserves all twelve outcomes', () => {
  const result = fixture(10); result.records[9].person_id = '=1+1<img src=x onerror=alert(1)>'
  const output = warning.buildCohortWarning(result)
  const text = warning.buildWarningRankOption(output).tooltip.formatter([{ dataIndex: 0 }])
  assert(text.includes('&lt;img')); assert(!text.includes('<img')); assert(text.includes('P-000010'))
  const csv = warning.warningRankingCsv(output)
  assert.equal(csv.split('\r\n').length, 121); assert(csv.includes("'=1+1<img")); assert(csv.includes('P-000010')); assert(csv.includes('HDL'))
  assert.equal(output.algorithm_version, 'cohort_relative_midrank_v1')
  assert(csv.split('\r\n').slice(1).every(line => line.startsWith('"cohort_relative_midrank_v1",')))
  assert.match(csv, /不是疾病概率/)
  const invalid = warning.warningRankingCsv(warning.buildCohortWarning(result, Infinity))
  assert(!invalid.includes('Infinity')); assert(!invalid.includes('NaN'))
})
test('warning implementation passes strict TypeScript semantics', () => {
  const program = ts.createProgram([path.join(root, 'app/utils/cohortWarning.ts')], { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ESNext, moduleResolution: ts.ModuleResolutionKind.Bundler, strict: true, skipLibCheck: true, noEmit: true })
  const diagnostics = ts.getPreEmitDiagnostics(program).filter(item => /[\\/]app[\\/]utils[\\/]/.test(item.file?.fileName || ''))
  assert.equal(diagnostics.length, 0, diagnostics.map(item => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'))
})
