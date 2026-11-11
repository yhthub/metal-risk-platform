const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
function load(name) {
  const source = fs.readFileSync(path.join(root, 'app/utils', name + '.ts'), 'utf8')
  const exports = {}
  const compilerOptions = { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS }
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions }).outputText, { exports, require: load })
  return exports
}
const { riskPathContext, causalPlanOrigin } = load('causalNavigation')
const single = { charts: { target: 'sbp' }, prediction: { person_id: 'SZ-105', results: [{ target: 'sbp' }] } }
const batch = { complete: true, summary: [{ target: 'sbp' }] }

test('only the corresponding completed single risk result identifies a person', () => {
  const query = { from: 'risk', mode: 'individual', target: 'sbp', person: 'SZ-284' }
  assert.equal(riskPathContext(query, single, batch).person, 'SZ-105')
  assert.equal(riskPathContext(query, null, batch).current, false)
  assert.equal(riskPathContext({ ...query, target: 'dbp' }, single, batch).person, '')
  assert.equal(riskPathContext({ ...query, from: 'unknown' }, single, batch).target, '')
  const cohort = riskPathContext({ ...query, mode: 'batch' }, single, batch)
  assert.equal(cohort.current, true)
  assert.equal(cohort.person, '')
})

test('plan and report round-trip retain the original source, even after switching objects', () => {
  const initial = { from: 'causal', metals: 'Pb,Cd', outcome: 'renal', edge: 'renal-pb',
    person: 'SZ-105', sourceMode: 'individual', sourceTarget: 'uacr_mg_g' }
  const intent = causalPlanOrigin(initial)
  const report = causalPlanOrigin({ ...intent.origin, person: 'SZ-032' })
  assert.equal(report.back.person, 'SZ-105')
  assert.equal(report.back.from, 'risk')
  assert.equal(report.back.target, 'uacr_mg_g')
  assert.equal(report.back.edge, 'renal-pb')
  assert.equal(report.back.metals, 'Pb,Cd')
})

test('a new visitor or cohort browsing the catalogue does not acquire its first preset object', () => {
  const first = causalPlanOrigin({ from: 'causal', metals: 'Pb,Cd', outcome: 'renal', view: 'coverage' })
  const next = causalPlanOrigin({ ...first.origin, person: 'SZ-105' })
  assert.equal(next.back.person, undefined)
  assert.equal(causalPlanOrigin({ from: 'risk', mode: 'batch' }), null)
  assert.equal(causalPlanOrigin({ from: 'causal', outcome: 'constructor' }), null)
  const hostile = causalPlanOrigin({ from: 'causal', metals: 'Pb,constructor,Cd,Pb',
    outcome: 'sbp', edge: '</script>', person: 'name', sourceMode: 'batch', sourceTarget: 'unknown' })
  assert.equal(hostile.back.metals, 'Pb,Cd')
  assert.equal(hostile.back.person, undefined)
  assert.equal(hostile.back.edge, undefined)
  assert.equal(hostile.back.from, undefined)
})
