/** Runtime one-click batch-demo state tests. Mock transport, no actual model calls. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const vue = require('vue')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const source = fs.readFileSync(path.join(root, 'app/pages/risk/index.vue'), 'utf8')
const block = source.match(/\/\/ RISK_GROUP_DEMO_START[\s\S]*?\/\/ RISK_GROUP_DEMO_END/)[0]
const script = ts.transpileModule(block, { compilerOptions: { target: ts.ScriptTarget.ES2022 } }).outputText
const plain = value => JSON.parse(JSON.stringify(value))
const measurements = {
  pb: { sample: 'whole_blood', unit: 'ug/dL', analyte: 'lead', confirmed: true },
  cd: { sample: 'whole_blood', unit: 'ug/L', analyte: 'cadmium', confirmed: true },
  hg: { sample: 'whole_blood', unit: 'ug/L', analyte: 'total_mercury', confirmed: true },
}
const payload = { import_result: { file_id: 'FILE-1234abcd', filename: 'NHANES_2017-2018_risk_demo_20.csv' },
  provenance: { id: 'nhanes_2017_2018_risk_demo_20', rows: 20, cycle: '2017-2018' }, measurements }
function setup(overrides = {}) {
  const calls = { imports: 0, confirms: 0, batches: [], batchThresholds: [] }
  const state = {
    active: true, epoch: 0, applyingGroupDemo: false, suppressSelection: false,
    groupDemoLoading: vue.ref(false), groupDemoVariant: vue.ref('standard'), isReasoning: vue.ref(false), mode: vue.ref('batch'),
    cohortWarningThreshold: vue.ref(80), cohortWarningDemoPreset: vue.ref(null),
    serviceStatus: vue.ref({ ready: true }), predictionError: vue.ref(''),
    batchIntake: vue.ref(null), batchResult: vue.ref(null),
    draft: vue.ref({ person: { age: null }, measurements: {} }), inputErrors: vue.ref([]),
    inputDialog: vue.ref(true), intakeNotice: vue.ref(''), demoNotice: vue.ref(''),
  }
  const context = vm.createContext({
    ...state, clonePrediction: plain, METAL_FIELDS: ['pb', 'cd', 'hg'].map(key => ({ key })),
    measurementErrors: values => Object.keys(measurements).filter(key => !values[key]?.confirmed),
    api: { importPredictionBatchDemo: async () => { calls.imports++; return { success: true, data: plain(payload) } } },
    ElMessageBox: { confirm: async () => { calls.confirms++ } },
    nextTick: async () => {}, runBatch: async (...args) => { calls.batches.push(args); calls.batchThresholds.push(state.cohortWarningThreshold.value) },
    ...overrides,
  })
  vm.runInContext(script + '\nglobalThis.demo = importGroupDemo; globalThis.resetDemoThreshold = resetStaleGroupDemoThreshold;', context)
  return { state, calls, context, run: variant => context.demo(variant), reset: () => context.resetDemoThreshold() }
}

test('empty batch page imports actual server file and metadata then invokes real batch workflow', async () => {
  const { state, calls, run } = setup()
  await run()
  assert.equal(calls.imports, 1)
  assert.equal(calls.confirms, 0)
  assert.deepEqual(calls.batches, [[]], 'One complete-file computation, without an offset or first-page limit')
  assert.equal(state.batchIntake.value.file_id, payload.import_result.file_id)
  assert.equal(state.batchIntake.value.provenance.rows, 20)
  assert.deepEqual(plain(state.draft.value.measurements), measurements)
  assert.equal(state.draft.value.person.age, null, 'Demo metadata must not fabricate a single-person record')
  assert.equal(state.batchResult.value, null, 'Import itself does not claim an inference result')
  assert.equal(state.groupDemoLoading.value, false)
  assert.equal(state.cohortWarningThreshold.value, 80)
  assert.equal(state.cohortWarningDemoPreset.value, null)
  assert.deepEqual(calls.batchThresholds, [80])
})
test('cancelled replacement preserves uploaded input, metadata and previous computed result', async () => {
  const { state, calls, run } = setup({ ElMessageBox: { confirm: async () => { throw new Error('cancel') } } })
  state.batchIntake.value = { file_id: 'FILE-aabbccdd', filename: 'user.csv' }
  state.batchResult.value = { processed_records: 8 }
  state.draft.value.measurements = { user: 'unchanged' }
  state.cohortWarningThreshold.value = 92
  await run('warning')
  assert.equal(calls.imports, 0)
  assert.deepEqual(calls.batches, [])
  assert.equal(state.batchIntake.value.filename, 'user.csv')
  assert.equal(state.batchResult.value.processed_records, 8)
  assert.deepEqual(plain(state.draft.value.measurements), { user: 'unchanged' })
  assert.equal(state.cohortWarningThreshold.value, 92)
  assert.equal(state.cohortWarningDemoPreset.value, null)
})
test('import failure and invalid metadata do not overwrite current data', async () => {
  for (const response of [{ success: false, error: 'hash failed' }, { success: true, data: { ...plain(payload), measurements: {} } },
    { success: true, data: { ...plain(payload), provenance: {} } },
    { success: true, data: { ...plain(payload), measurements: { ...plain(measurements), pb: { confirmed: false } } } }]) {
    const { state, calls, run } = setup({ api: { importPredictionBatchDemo: async () => response } })
    state.batchIntake.value = { file_id: 'FILE-aabbccdd' }
    state.batchResult.value = { processed_records: 8 }
    state.cohortWarningThreshold.value = 92
    await run('warning')
    assert.equal(state.batchIntake.value.file_id, 'FILE-aabbccdd')
    assert.equal(state.batchResult.value.processed_records, 8)
    assert(state.predictionError.value)
    assert.deepEqual(calls.batches, [])
    assert.equal(state.cohortWarningThreshold.value, 92)
    assert.equal(state.cohortWarningDemoPreset.value, null)
  }
})
test('double-clicks create only one import and one batch computation', async () => {
  let resolve
  const pending = new Promise(done => { resolve = done })
  let imports = 0
  const { calls, run, state } = setup({ api: { importPredictionBatchDemo: () => { imports++; return pending } } })
  const first = run()
  await run()
  assert.equal(imports, 1)
  assert.equal(state.groupDemoLoading.value, true)
  resolve({ success: true, data: plain(payload) })
  await first
  assert.deepEqual(calls.batches, [[]], 'Double-clicks must not submit multiple whole-file analyses')
  assert.equal(state.groupDemoLoading.value, false)
})
test('late response after navigation or input change cannot replace current data', async () => {
  for (const change of [context => { context.active = false }, context => { context.epoch++ }, context => { context.mode.value = 'individual' }]) {
    let resolve
    const pending = new Promise(done => { resolve = done })
    const { context, calls, run, state } = setup({ api: { importPredictionBatchDemo: () => pending } })
    state.batchIntake.value = { file_id: 'FILE-aabbccdd' }
    state.cohortWarningThreshold.value = 92
    const running = run('warning')
    await Promise.resolve()
    change(context)
    resolve({ success: true, data: plain(payload) })
    await running
    assert.equal(state.batchIntake.value.file_id, 'FILE-aabbccdd')
    assert.deepEqual(calls.batches, [])
    assert.equal(state.cohortWarningThreshold.value, 92)
    assert.equal(state.cohortWarningDemoPreset.value, null)
  }
})
test('unready model does not import records or pretend to execute inference', async () => {
  const { state, calls, run } = setup()
  state.serviceStatus.value.ready = false
  state.cohortWarningThreshold.value = 92
  await run('warning')
  assert.equal(calls.imports, 0)
  assert.deepEqual(calls.batches, [])
  assert.match(state.predictionError.value, /模型尚未就绪/)
  assert.equal(state.cohortWarningThreshold.value, 92)
  assert.equal(state.cohortWarningDemoPreset.value, null)
})

test('warning effect demo keeps the verified public data and real batch inference, with an explicit 75-point preset', async () => {
  const { state, calls, run } = setup()
  await run('warning')
  assert.equal(calls.imports, 1)
  assert.deepEqual(calls.batches, [[]])
  assert.deepEqual(calls.batchThresholds, [75], 'Apply the explicit preset before real whole-file inference')
  assert.equal(state.cohortWarningThreshold.value, 75)
  assert.deepEqual(plain(state.cohortWarningDemoPreset.value), { file_id: payload.import_result.file_id, threshold: 75 })
  assert.equal(state.batchIntake.value.provenance.id, payload.provenance.id)
  assert.deepEqual(plain(state.draft.value.measurements), measurements)
  assert.match(state.demoNotice.value, /75/)
  assert.match(state.demoNotice.value, /演示/)
  assert.match(state.demoNotice.value, /不是临床|非临床|不代表临床/)
  assert.equal(state.groupDemoVariant.value, 'warning')
  assert.equal(state.groupDemoLoading.value, false)
})

test('warning and standard buttons share a single lock during an outstanding import', async () => {
  for (const [firstVariant, secondVariant, expectedThreshold] of [['warning', 'standard', 75], ['standard', 'warning', 80]]) {
    let resolve
    const pending = new Promise(done => { resolve = done })
    let imports = 0
    const { state, calls, run } = setup({ api: { importPredictionBatchDemo: () => { imports++; return pending } } })
    const first = run(firstVariant)
    await run(secondVariant)
    assert.equal(imports, 1)
    assert.equal(state.groupDemoVariant.value, firstVariant)
    assert.equal(state.groupDemoLoading.value, true)
    resolve({ success: true, data: plain(payload) })
    await first
    assert.deepEqual(calls.batches, [[]])
    assert.deepEqual(calls.batchThresholds, [expectedThreshold])
    assert.equal(state.groupDemoLoading.value, false)
  }
})

test('standard public demo explicitly returns a prior warning preset to the normal 80-point rule', async () => {
  const { state, calls, run } = setup()
  await run('warning')
  assert.equal(state.cohortWarningThreshold.value, 75)
  await run()
  assert.deepEqual(calls.batchThresholds, [75, 80])
  assert.equal(state.cohortWarningThreshold.value, 80)
  assert.equal(state.cohortWarningDemoPreset.value, null)
  assert.equal(calls.confirms, 1, 'Replacing the existing demo remains explicit')
})

test('late nextTick navigation does not apply a warning preset or submit a prediction', async () => {
  let releaseTick
  const tick = new Promise(done => { releaseTick = done })
  const { context, state, calls, run } = setup({ nextTick: () => tick })
  state.cohortWarningThreshold.value = 92
  const pending = run('warning')
  await Promise.resolve()
  context.epoch++
  releaseTick()
  await pending
  assert.equal(state.cohortWarningThreshold.value, 92)
  assert.equal(state.cohortWarningDemoPreset.value, null)
  assert.deepEqual(calls.batches, [])
})

test('a new normal file or removed file resets only the old demo preset, not the new input', () => {
  for (const nextIntake of [{ file_id: 'FILE-aabbccdd', filename: 'user.csv' }, null]) {
    const { state, reset } = setup()
    state.cohortWarningThreshold.value = 75
    state.cohortWarningDemoPreset.value = { file_id: payload.import_result.file_id, threshold: 75 }
    state.batchIntake.value = nextIntake
    reset()
    assert.equal(state.cohortWarningThreshold.value, 80)
    assert.equal(state.cohortWarningDemoPreset.value, null)
    assert.deepEqual(plain(state.batchIntake.value), nextIntake)
  }
})

test('report navigation and same demo file preserve the warning preset without inference', () => {
  const { state, calls, reset } = setup()
  state.cohortWarningThreshold.value = 75
  state.cohortWarningDemoPreset.value = { file_id: payload.import_result.file_id, threshold: 75 }
  state.batchIntake.value = { file_id: payload.import_result.file_id }
  reset()
  assert.equal(state.cohortWarningThreshold.value, 75)
  assert.deepEqual(plain(state.cohortWarningDemoPreset.value), { file_id: payload.import_result.file_id, threshold: 75 })
  assert.equal(calls.imports, 0)
  assert.deepEqual(calls.batches, [])
})

test('new normal file preserves a user-adjusted threshold and clears the stale demo ownership', () => {
  const { state, reset } = setup()
  state.cohortWarningThreshold.value = 60
  state.cohortWarningDemoPreset.value = { file_id: payload.import_result.file_id, threshold: 75 }
  state.batchIntake.value = { file_id: 'FILE-aabbccdd' }
  reset()
  assert.equal(state.cohortWarningThreshold.value, 60)
  assert.equal(state.cohortWarningDemoPreset.value, null)
})

test('applying a verified demo cannot trigger the normal-upload threshold reset', () => {
  const { context, state, reset } = setup()
  state.cohortWarningThreshold.value = 75
  state.cohortWarningDemoPreset.value = { file_id: payload.import_result.file_id, threshold: 75 }
  state.batchIntake.value = { file_id: 'FILE-aabbccdd' }
  context.applyingGroupDemo = true
  reset()
  assert.equal(state.cohortWarningThreshold.value, 75)
  assert.deepEqual(plain(state.cohortWarningDemoPreset.value), { file_id: payload.import_result.file_id, threshold: 75 })
})

test('both visible buttons select a named scenario with a shared loading/disabled guard', () => {
  assert.match(source, /@click="importGroupDemo\('standard'\)"/)
  assert.match(source, /@click="importGroupDemo\('warning'\)"/)
  assert.match(source, /一键预警案例演示/)
  assert.match(source, /groupDemoLoading\s*&&\s*groupDemoVariant\s*===\s*'warning'/)
  assert.match(source, /watch\(batchIntake,[\s\S]*?resetStaleGroupDemoThreshold\(\)/)
  assert.match(source, /function activateDashboard\(\)[\s\S]*?resetStaleGroupDemoThreshold\(\)/)
})
test('public provenance and limitations stay visible and do not claim independent validation', () => {
  assert.match(source, /公开演示来源：\{\{ batchIntake.provenance.title \}\}/)
  assert.match(source, /v-for="note in batchIntake.provenance.limitations"/)
  assert.match(source, /BMI 按同周期参与者编号关联原始身体测量数据/)
})
