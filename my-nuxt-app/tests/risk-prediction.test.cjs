/** Offline prediction contract/export checks. Does not run a server or fit models. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const tsDir = fs.readdirSync(pnpm).find(item => item.startsWith('typescript@'))
const ts = require(path.join(pnpm, tsDir, 'node_modules/typescript'))
const sourcePath = path.join(root, 'app/utils/riskPrediction.ts')
const source = fs.readFileSync(sourcePath, 'utf8')
const transpiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
assert.equal(transpiled.diagnostics.length, 0)
const exportsObject = {}
vm.runInNewContext(transpiled.outputText, { exports: exportsObject, setTimeout: () => {} })
const lib = exportsObject
const plain = value => JSON.parse(JSON.stringify(value))
let count = 0
function check(name, run) { run(); count++; console.log('PASS ' + name) }
function fixture() {
  const draft = lib.createPredictionDraft()
  Object.assign(draft.person, { id: 'SYNTHETIC', age: 45, gender: 'female', gender_confirmed: true, bmi: 24, pb: 1.2, cd: 0.3, hg: 1 })
  for (const metal of lib.METAL_FIELDS) Object.assign(draft.measurements[metal.key], { sample: 'whole_blood', unit: metal.unit, analyte: metal.analyte, confirmed: true })
  return draft
}
const validRow = { target: 'sbp', label_zh: '收缩压', unit: 'mmHg', prediction: 120.5, status: 'EXPLORATORY_ESTIMATE', reference_interval: { lower: 100, upper: 140, nominal_calibration_level: .9, guaranteed_coverage: false }, test_metrics: { MAE: 12, RMSE: 16, R2: .2, n: 500 }, selection_R2: .3, model_family: ['xgboost'], candidate_id: 'a' }
const withheldRow = { ...validRow, target: 'uacr_mg_g', label_zh: '尿白蛋白 / 肌酐比', unit: 'mg/g', prediction: 999, status: 'INSUFFICIENT_VALIDATED_ACCURACY', reason: '验证不足', reference_interval: null }
const response = { model_version: 'v5', run_id: 'fixture-only', profile: 'basic', person_id: '=HYPERLINK("evil")', status: 'ESTIMATES_NOT_DIAGNOSES', scope: 'exploratory', results: [validRow, withheldRow], warnings: [] }
check('empty form defaults are genuinely unknown and independently allocated', () => {
  const first = lib.createPredictionDraft(); const second = lib.createPredictionDraft()
  assert.equal(first.person.gender, null); assert.equal(first.person.gender_confirmed, false)
  for (const key of ['age', 'bmi', 'pb', 'cd', 'hg']) assert.equal(first.person[key], null)
  for (const value of Object.values(first.covariates)) assert.equal(value, null)
  for (const key of ['pb', 'cd', 'hg']) { assert.equal(first.measurements[key].confirmed, false); assert.equal(first.measurements[key].sample, '') }
  first.measurements.pb.confirmed = true
  assert.equal(second.measurements.pb.confirmed, false)
})
check('missing and illegal numerics never become zero', () => {
  for (const value of ['', '  ', null, undefined, false, true, {}, NaN, Infinity, 'x', '0x10', '0o12', '0b10']) assert.equal(lib.parsePredictionNumber(value), null)
  assert.equal(lib.parsePredictionNumber(0), 0); assert.equal(lib.parsePredictionNumber('0'), 0)
  assert.equal(lib.parsePredictionNumber(' 1.2 '), 1.2)
  assert.equal(lib.parsePredictionNumber('1.2e-3'), .0012)
})
check('valid explicit whole-blood contract preserves unknown optional data and source values', () => {
  const draft = fixture(); const before = plain(draft)
  const built = lib.buildPredictionRequest(draft)
  assert.deepEqual(plain(built.errors), [])
  assert.deepEqual(plain(built.payload), before)
  assert.deepEqual(plain(draft), before)
  built.payload.measurements.pb.confirmed = false
  assert.equal(draft.measurements.pb.confirmed, true)
})
check('recorded zero exposure is legal but blank exposure is not', () => {
  const draft = fixture(); draft.person.pb = 0
  assert.equal(lib.buildPredictionRequest(draft).errors.length, 0)
  draft.person.pb = ''
  const result = lib.buildPredictionRequest(draft)
  assert.equal(result.payload.person.pb, null)
  assert(result.errors.some(error => /实测值/.test(error)))
})
check('age, sex confirmation and specimen definition fail closed', () => {
  for (const age of [17, 81, 45.5, null]) { const draft = fixture(); draft.person.age = age; assert(lib.buildPredictionRequest(draft).errors.some(error => /18–80/.test(error))) }
  const draft = fixture(); draft.person.gender_confirmed = false; draft.measurements.cd.sample = 'urine'; draft.measurements.hg.analyte = 'methyl_mercury'; draft.measurements.pb.unit = 'ug/g Cr'
  const errors = lib.buildPredictionRequest(draft).errors.join(' ')
  assert.match(errors, /生理性别/); assert.match(errors, /全血/); assert.match(errors, /分析物/); assert.match(errors, /原始报告单位/)
})
check('adapter does not silently convert source blood concentration or unknown categories', () => {
  const draft = fixture(); draft.person.pb = 15; draft.measurements.pb.unit = 'μg/L'
  const built = lib.buildPredictionRequest(draft)
  assert.equal(built.errors.length, 0); assert.equal(built.payload.person.pb, 15); assert.equal(built.payload.measurements.pb.unit, 'μg/L')
  assert.equal(built.payload.covariates.smoking, null)
  draft.measurements.hg.unit = 'ng/mL'
  assert.equal(lib.buildPredictionRequest(draft).errors.length, 0)
})
check('withheld status never exposes a numeric result even if malformed upstream sends one', () => {
  assert.equal(lib.predictionHasValue(validRow), true)
  assert.equal(lib.predictionHasValue(withheldRow), false)
  assert.equal(lib.predictionStatusLabel(withheldRow), '暂不出值')
  assert.equal(lib.predictionIntervalLabel(withheldRow), '—')
  assert.equal(lib.predictionHasValue({ ...validRow, prediction: Infinity }), false)
})
check('CSV exports units/status/limitations and escapes formulas, quotes and multiline identifiers', () => {
  assert.equal(lib.csvCell('=A1'), '"\'=A1"')
  for (const value of ['+x', '-x', '@x', '\t=1', '  =1']) assert(lib.csvCell(value).startsWith('"\''))
  assert.equal(lib.csvCell(-1.2), '"-1.2"')
  assert.equal(lib.csvCell('a,"b"\nc'), '"a,""b""\nc"')
  const csv = lib.predictionCsv(response)
  assert(csv.startsWith('\uFEFF')); assert.match(csv, /test_MAE/); assert.match(csv, /mmHg/); assert.match(csv, /验证不足/); assert.match(csv, /不保证个体覆盖率/)
  assert(!csv.includes('"999"')); assert.match(csv, /'\=HYPERLINK/)
})
check('JSON report carries the actual request, response and scope warnings', () => {
  const result = JSON.parse(lib.predictionJson(fixture(), response))
  assert.deepEqual(result.input, plain(fixture())); assert.deepEqual(result.result, plain(response))
  assert(result.notes.some(note => /不是未来发病概率/.test(note)))
})
check('batch CSV retains skipped rows and withheld outcomes, with no fabricated summary', () => {
  const csv = lib.batchPredictionCsv({ model_version: 'v5', run_id: 'fixture', profile: 'basic', file_id: 'FILE-test', records: [{ row_number: 1, person_id: '1', status: 'OK', results: [validRow, withheldRow] }, { row_number: 2, person_id: '2', status: 'SKIPPED', reason: '缺少 BMI' }] })
  assert.match(csv, /SKIPPED/); assert.match(csv, /缺少 BMI/); assert.match(csv, /INSUFFICIENT_VALIDATED_ACCURACY/); assert(!csv.includes('"999"'))
})
check('frontend source removes old fictional disease/causal output and rejects stale responses', () => {
  const index = fs.readFileSync(path.join(root, 'app/pages/risk/index.vue'), 'utf8')
  const report = fs.readFileSync(path.join(root, 'app/pages/risk/report.vue'), 'utf8')
  const state = fs.readFileSync(path.join(root, 'app/composables/usePredictionState.ts'), 'utf8')
  assert(!/Math\.random|highRiskWorkers|diseaseRisks|shapData|68\.5/.test(index + report))
  assert.match(index, /current !== epoch/); assert.match(index, /watch\(draft/); assert.match(index, /invalidate\(\)/)
  assert.match(index, /onActivated/); assert.match(index, /onDeactivated/); assert.match(index, /modeFromQuery\(value\)/)
  assert.match(report, /hasReport/); assert.match(report, /暂无本次预测报告/)
  assert(!/localStorage\s*\.|sessionStorage\s*\.|document\.cookie/.test(index + report + state))
  assert.match(index, /confirmed = false/); assert.match(index, /缺少BMI/)
})
check('mode navigation is URL-driven, explicit and immune to old batch intake', () => {
  const index = fs.readFileSync(path.join(root, 'app/pages/risk/index.vue'), 'utf8')
  const sidebar = fs.readFileSync(path.join(root, 'app/components/Sidebar.vue'), 'utf8')
  const definition = index.match(/function modeFromQuery\(value: unknown\)[\s\S]*?\n}/)
  assert(definition, 'The actual component query-mode resolver must be tested')
  const module = ts.transpileModule(definition[0] + '\nexports.resolve = modeFromQuery', { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } })
  const modeExports = {}
  vm.runInNewContext(module.outputText, { exports: modeExports })
  assert.equal(modeExports.resolve('batch'), 'batch')
  for (const query of ['individual', undefined, null, '', 'other', ['batch']]) assert.equal(modeExports.resolve(query), 'individual')
  assert.match(index, /@click="selectMode\('individual'\)"/)
  assert.match(index, /@click="selectMode\('batch'\)"/)
  assert.match(index, /router\.push\(\{ path: '\/risk', query: \{ \.\.\.route\.query, mode: next } }\)/)
  assert.match(index, /mode\.value = modeFromQuery\(route\.query\.mode\)/)
  assert.match(index, /if \(route\.path === '\/risk'\) mode\.value = modeFromQuery\(value\)/)
  assert(!/route\.query\.mode[^\n]*\|\|\s*(?:intake|batchIntake)\.value/.test(index))
  assert.match(sidebar, /goTo\('\/risk\?mode=individual'\)/)
  assert.match(sidebar, /goTo\('\/risk\?mode=batch'\)/)
})
check('new prediction utility passes strict local TypeScript semantic checks', () => {
  const program = ts.createProgram([sourcePath], { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, strict: true, noEmit: true, skipLibCheck: true, types: [] })
  const diagnostics = ts.getPreEmitDiagnostics(program)
  assert.equal(diagnostics.length, 0, diagnostics.map(item => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'))
})
console.log('\n' + count + ' offline prediction frontend checks passed; no server or model invoked.')
