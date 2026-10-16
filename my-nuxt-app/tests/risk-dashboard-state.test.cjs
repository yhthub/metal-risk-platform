/** Memory-only state boundaries for the restored risk dashboard. No network. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const tsDir = fs.readdirSync(pnpm).find(name => name.startsWith('typescript@'))
const ts = require(path.join(pnpm, tsDir, 'node_modules/typescript'))
function compile(relative) {
  return ts.transpileModule(fs.readFileSync(path.join(root, relative), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText
}
const utility = {}
vm.runInNewContext(compile('app/utils/riskPrediction.ts'), { exports: utility, setTimeout() {} })
const cache = new Map()
const stateModule = {}
vm.runInNewContext(compile('app/composables/usePredictionState.ts'), {
  exports: stateModule,
  require(name) { assert.equal(name, '~/utils/riskPrediction'); return utility },
  useState(key, init) { if (!cache.has(key)) cache.set(key, { value: init() }); return cache.get(key) },
})
const state = stateModule.usePredictionState()
const plain = value => JSON.parse(JSON.stringify(value))
let count = 0
function check(name, run) { run(); count++; console.log('PASS ' + name) }
check('dashboard and batch records are memory-only, shared and initially empty', () => {
  for (const key of ['dashboard', 'batchResult', 'cohortResult', 'selectedRow', 'lastDashboardRequest']) assert.equal(state[key].value, null)
  assert.equal(state.selectedTarget.value, 'sbp')
  assert.equal(state.cohortWarningThreshold.value, 80)
  assert.equal(stateModule.usePredictionState().dashboard, state.dashboard)
})
check('composite threshold is shared with reports and kept independent of single-target navigation', () => {
  const reportState = stateModule.usePredictionState()
  assert.equal(reportState.cohortWarningThreshold, state.cohortWarningThreshold)
  state.cohortWarningThreshold.value = 90
  state.selectedTarget.value = 'dbp'
  assert.equal(reportState.cohortWarningThreshold.value, 90)
  state.invalidate()
  assert.equal(state.cohortWarningThreshold.value, 90, 'Invalidating estimates must not silently change the user-selected comparison rule')
  state.cohortWarningThreshold.value = 80
})
check('intake preserves unknowns and source measurement values without sharing mutable input', () => {
  const input = utility.createPredictionDraft()
  input.person.age = 38; input.person.pb = 42
  input.measurements.pb.unit = 'μg/L'
  state.batchIntake.value = { file_id: 'FILE-1234abcd' }
  state.setIntake(input)
  input.person.pb = 99
  assert.equal(state.draft.value.person.pb, 42)
  assert.equal(state.draft.value.measurements.pb.unit, 'μg/L')
  assert.equal(state.draft.value.covariates.education, null)
  assert.equal(state.batchIntake.value, null)
})
check('input invalidation clears every prior chart, batch, request and report result', () => {
  state.selectedTarget.value = 'dbp'
  for (const key of ['lastResult', 'lastRequest', 'dashboard', 'batchResult', 'cohortResult', 'lastDashboardRequest']) state[key].value = { fixture: true }
  state.selectedRow.value = 3
  state.invalidate()
  for (const key of ['lastResult', 'lastRequest', 'dashboard', 'batchResult', 'cohortResult', 'lastDashboardRequest', 'selectedRow']) assert.equal(state[key].value, null, key)
  assert.equal(state.selectedTarget.value, 'dbp')
})
check('report input and result are frozen copies of the actual inference response', () => {
  const input = plain(state.draft.value)
  const output = { model_version: 'v5', results: [{ target: 'sbp', prediction: 123.4 }] }
  state.setResult(input, output)
  input.person.age = 60; output.results[0].prediction = 999
  assert.equal(state.lastRequest.value.person.age, 38)
  assert.equal(state.lastResult.value.results[0].prediction, 123.4)
})
check('batch demo provenance remains tied to the imported file, not a claimed model result', () => {
  state.batchIntake.value = { file_id: 'FILE-1234abcd', filename: 'public-demo.csv', provenance: { cycle: '2017–2018', rows: 20 } }
  state.invalidate()
  assert.equal(state.batchIntake.value.file_id, 'FILE-1234abcd')
  assert.equal(state.batchIntake.value.provenance.rows, 20)
  assert.equal(state.dashboard.value, null)
  assert.equal(state.batchResult.value, null)
})
check('switching to a new single-person input removes prior batch provenance', () => {
  state.setIntake(utility.createPredictionDraft())
  assert.equal(state.batchIntake.value, null)
})
console.log('\n' + count + ' dashboard-state checks passed; no HTTP, model or storage calls.')
