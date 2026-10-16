/** Synthetic-demo regression checks. No HTTP, database, dataset, model or server calls. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const tsDir = fs.readdirSync(pnpm).find(item => item.startsWith('typescript@'))
assert(tsDir, 'Existing TypeScript dependency is required; this test installs nothing.')
const ts = require(path.join(pnpm, tsDir, 'node_modules/typescript'))
const evaluate = (file, imports = {}) => {
  const source = fs.readFileSync(path.join(root, 'app/utils', file), 'utf8')
  const result = ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
    reportDiagnostics: true
  })
  assert.equal(result.diagnostics.length, 0)
  const exports = {}
  vm.runInNewContext(result.outputText, {
    exports,
    require: name => {
      assert(Object.hasOwn(imports, name), 'Unexpected import (network/runtime dependencies forbidden): ' + name)
      return imports[name]
    }
  })
  return { exports, source }
}
const refs = evaluate('individualReferences.ts').exports
const profile = evaluate('individualProfile.ts', { './individualReferences': refs }).exports
const moduleResult = evaluate('individualDemo.ts', { './individualReferences': refs })
const demo = moduleResult.exports
let checks = 0
const check = (name, run) => { run(); checks++; console.log('PASS ' + name) }
const plain = value => JSON.parse(JSON.stringify(value))

check('demo is explicitly synthetic and distinguishes residential radon from human/workplace samples', () => {
  assert.match(demo.INDIVIDUAL_DEMO_LABEL, /合成/)
  assert.match(demo.INDIVIDUAL_DEMO_NOTE, /所有数值均为合成/)
  assert.match(demo.INDIVIDUAL_DEMO_NOTE, /住宅室内年均/)
  assert.match(demo.INDIVIDUAL_DEMO_NOTE, /不是人体样本或工作场所/)
  assert.match(demo.createIndividualDemo().singleData.name, /DEMO.*合成/)
  assert.match(demo.createIndividualDemo().singleData.history, /非真实人员/)
})
check('all expected form fields are filled with valid existing options and finite nonnegative values', () => {
  const fixture = demo.createIndividualDemo()
  assert.equal(fixture.job, 'smelting')
  const choices = {
    gender: ['male', 'female'], education: ['primary', 'middle', 'high', 'college', 'bachelor', 'master'],
    marital: ['unmarried', 'married', 'divorced', 'widowed'],
    smoking: ['never', 'former', 'current_lt10', 'current_ge10'],
    drinking: ['never', 'occasional', 'frequent', 'daily'], ppe: ['none', 'basic', 'standard', 'full']
  }
  for (const [field, values] of Object.entries(choices)) assert(values.includes(fixture.singleData[field]), field)
  assert(fixture.singleData.age >= 18)
  assert(fixture.singleData.workYears <= fixture.singleData.age)
  for (const field of ['age', 'workYears', 'bmi', ...refs.MEASUREMENTS.map(item => item.key)]) {
    assert.equal(profile.parseMeasurement(fixture.singleData[field]).state, 'valid', field)
  }
  assert.deepEqual(Object.keys(fixture.singleData).sort(), [
    'name', 'gender', 'age', 'workYears', 'education', 'marital', 'smoking', 'drinking', 'bmi', 'ppe', 'history',
    ...refs.MEASUREMENTS.map(item => item.key)
  ].sort())
  assert.equal(Object.keys(fixture.metadata).length, 10)
})
check('each metric has independent explicit sample/unit metadata and confirmed synthetic conditions', () => {
  const fixture = demo.createIndividualDemo()
  for (const { key } of refs.MEASUREMENTS) {
    const metadata = fixture.metadata[key]
    assert(refs.SAMPLE_OPTIONS.some(item => item.value === metadata.sample && item.value !== ''), key)
    assert(refs.UNIT_OPTIONS.includes(metadata.unit) && metadata.unit !== '', key)
    assert.equal(metadata.confirmed, true, key)
  }
  for (const key of ['pb', 'cd', 'hg']) assert.equal(fixture.metadata[key].sample, 'whole_blood', key)
  assert.equal(fixture.metadata.cd.context, 'occupational_cadmium')
  assert.equal(fixture.metadata.hg.context, '')
  assert.equal(fixture.metadata.as.sample, 'random_urine')
  assert.equal(fixture.metadata.as.analyte, 'toxic_speciated')
  assert.equal(fixture.metadata.rn.sample, 'indoor_air')
  assert.equal(fixture.metadata.rn.unit, 'Bq/m³')
  assert.equal(fixture.metadata.rn.context, 'residential_annual')
})
check('profile has exactly ten valid measurements, five source-matched comparisons and 50 percent coverage', () => {
  const fixture = demo.createIndividualDemo()
  const result = profile.buildIndividualProfile(fixture.singleData, fixture.metadata)
  assert.deepEqual(plain(result.counts), { total: 10, valid: 10, missing: 0, invalid: 0, comparable: 5 })
  assert.equal(result.coverage, 50)
  assert.deepEqual(plain(result.comparable.map(item => item.key)), ['pb', 'cd', 'hg', 'as', 'rn'])
  const expected = {
    pb: ['cdc-adult-bll', 120, true], cd: ['osha-cd-blood', 64, false], hg: ['mayo-hg-blood', 68, false],
    as: ['mayo-toxic-as-urine', 80, false], rn: ['who-residential-radon', 120, true]
  }
  for (const row of result.comparable) {
    assert.equal(row.reference.id, expected[row.key][0], row.key)
    assert(Math.abs(row.ratio - expected[row.key][1]) < 1e-10, row.key)
    assert.equal(row.reached, expected[row.key][2], row.key)
  }
})
check('unsupported elements stay visible with raw measurements but never get invented thresholds', () => {
  const fixture = demo.createIndividualDemo()
  const result = profile.buildIndividualProfile(fixture.singleData, fixture.metadata)
  for (const key of ['th', 'li', 'cr', 'ni', 'co']) {
    const row = result.rows.find(item => item.key === key)
    assert.equal(row.value, fixture.singleData[key], key)
    assert.equal(row.reference, null, key)
    assert.equal(row.ratio, null, key)
    assert.equal(row.reached, null, key)
    assert.equal(row.conditions.reference.state, 'missing', key)
  }
})
check('factory returns independent nested mutable objects and deterministic repeatable values', () => {
  const first = demo.createIndividualDemo()
  const second = demo.createIndividualDemo()
  assert.deepEqual(plain(first), plain(second))
  assert.notEqual(first, second)
  assert.notEqual(first.singleData, second.singleData)
  assert.notEqual(first.metadata, second.metadata)
  for (const { key } of refs.MEASUREMENTS) {
    assert.notEqual(first.metadata[key], second.metadata[key], key)
    for (const { key: other } of refs.MEASUREMENTS) {
      if (key !== other) assert.notEqual(first.metadata[key], first.metadata[other], key + '/' + other)
    }
  }
  first.singleData.pb = 900
  first.singleData.name = 'edited'
  first.metadata.pb.unit = 'μg/dL'
  first.metadata.as.confirmed = false
  assert.deepEqual(plain(demo.createIndividualDemo()), plain(second))
})
check('edited metadata fails closed without changing the synthetic numeric value', () => {
  const fixture = demo.createIndividualDemo()
  fixture.metadata.pb.unit = 'μg/dL'
  fixture.metadata.pb.confirmed = false
  const row = profile.buildIndividualProfile(fixture.singleData, fixture.metadata).rows[0]
  assert.equal(row.raw, 42)
  assert.equal(row.ratio, null)
  assert.equal(row.conditions.reference.state, 'pending')
})
check('invalidating context cannot silently apply occupational, speciated or residential references', () => {
  const fixture = demo.createIndividualDemo()
  fixture.metadata.cd.context = ''
  fixture.metadata.as.analyte = 'total'
  fixture.metadata.rn.context = 'other'
  const result = profile.buildIndividualProfile(fixture.singleData, fixture.metadata)
  assert.equal(result.counts.comparable, 2)
  for (const key of ['cd', 'as', 'rn']) assert.equal(result.rows.find(item => item.key === key).ratio, null, key)
})
check('demo construction and profile building never mutate the source reference registry', () => {
  const before = JSON.stringify(refs.INDIVIDUAL_REFERENCES)
  const fixture = demo.createIndividualDemo()
  profile.buildIndividualProfile(fixture.singleData, fixture.metadata)
  assert.equal(JSON.stringify(refs.INDIVIDUAL_REFERENCES), before)
  assert(!/fetch\s*\(|useApi\s*\(|Math\.random\s*\(|Date\.now\s*\(/.test(moduleResult.source))
})
check('demo and existing utility types pass strict local TypeScript semantic checks', () => {
  const program = ts.createProgram(['individualReferences.ts', 'individualProfile.ts', 'individualDemo.ts'].map(file => path.join(root, 'app/utils', file)), {
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS, strict: true, noEmit: true, skipLibCheck: true, types: []
  })
  const diagnostics = ts.getPreEmitDiagnostics(program)
  assert.equal(diagnostics.length, 0, diagnostics.map(item => ts.flattenDiagnosticMessageText(item.messageText, '\n')).join('\n'))
})
console.log(`\n${checks} offline synthetic-demo checks passed. No model, HTTP, dataset or server invocation.`)
