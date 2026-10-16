/** Population profile rendering only: no model, API, or sensitive source data. */
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
const filename = path.join(root, 'app/components/RiskCohortProfile.vue')
const source = fs.readFileSync(filename, 'utf8')
const parsed = compiler.parse(source, { filename })
assert.deepEqual(parsed.errors, [])
const script = compiler.compileScript(parsed.descriptor, { id: 'cohort-profile-test', inlineTemplate: true })
const runtime = { exports: {} }
vm.runInNewContext(ts.transpileModule(script.content, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText, { exports: runtime.exports, module: runtime, require: name => { assert.equal(name, 'vue'); return vue } })
const component = runtime.exports.default
const category = (key, label, count, total = 10) => ({ key, label, count, percent: count / total * 100 })
const group = categories => ({ source_columns: ['public_test_column'], available: true, valid_count: categories.filter(item => item.key !== 'unknown').reduce((sum, item) => sum + item.count, 0), missing_count: categories.find(item => item.key === 'unknown')?.count || 0, unknown_count: categories.find(item => item.key === 'unknown')?.count || 0, categories })
function fixture() {
  return { scope: 'all_uploaded_records', total_records: 10, denominator: 'all_uploaded_records', weighted: false,
    sex: group([category('male', '男性', 4), category('female', '女性', 3), category('unknown', '缺失或未明确', 3)]),
    marital: group([category('married', '已婚', 3), category('never_married', '未婚', 2), category('unknown', '缺失或未明确', 5)]),
    education: group([category('college_or_above', '大学及以上', 6), category('unknown', '缺失或未明确', 4)]),
    age: { source_columns: ['public_age'], available: true, valid_count: 8, missing_count: 2, invalid_count: 0, unknown_count: 2, mean: 46.25, median: 44, min: 20, max: 79, bands: [category('18_39', '18–39岁', 4), category('40_59', '40–59岁', 3), category('60_80', '60–80岁', 1), category('unknown', '缺失或未明确', 2)] }, notes: [] }
}
const render = props => renderToString(vue.createSSRApp(component, props))

test('profile SFC/template/style compile without heavy charts or model calls', () => {
  const template = compiler.compileTemplate({ source: parsed.descriptor.template.content, filename, id: 'cohort-profile-test', compilerOptions: { bindingMetadata: script.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(template.errors, [])
  assert.deepEqual(compiler.compileStyle({ source: parsed.descriptor.styles[0].content, filename, id: 'cohort-profile-test' }).errors, [])
  assert(!/echarts|useApi\(|\bfetch\(|predictCohort|predictBatch/.test(source))
  assert.match(source, /grid-template-columns:repeat\(4,minmax\(0,1fr\)\)/)
  assert.match(source, /grid-template-columns:repeat\(2,minmax\(0,1fr\)\)/)
})
test('top population totals include ineligible objects and categories use all-file denominator', async () => {
  const html = await render({ profile: fixture(), totalRecords: 10, processedRecords: 7, skippedRecords: 3 })
  assert.match(html, /本次上传总人数/)
  assert.match(html, /满足模型必需输入/)
  assert.match(html, /输入不合格 \/ 未计算/)
  assert.match(html, /分类人数及比例以全部 10 人为分母/)
  assert.match(html, /男性 4 人，占全部对象 40\.0%/)
  assert.match(html, /女性 3 人，占全部对象 30\.0%/)
  assert.match(html, /缺失或未明确 3 人，占全部对象 30\.0%/)
  assert(!html.includes('57.1%'), 'Never divide demographic counts by seven model-eligible objects')
  assert.match(html, /46\.3/)
  assert.match(html, /8 人有效年龄/)
  assert.match(html, /婚姻情况/)
  assert.match(html, /学历情况/)
  assert.match(html, /大学及以上/)
})
test('all-unknown source columns remain explicit, null age never turns into zero', async () => {
  const profile = fixture()
  for (const key of ['sex', 'marital', 'education']) profile[key] = { ...group([category('unknown', '缺失或未明确', 10)]), available: false, source_columns: [] }
  Object.assign(profile.age, { valid_count: 0, missing_count: 10, unknown_count: 10, available: false, source_columns: [], mean: null, median: null, min: null, max: null, bands: [category('unknown', '缺失或未明确', 10)] })
  const html = await render({ profile, totalRecords: 10, processedRecords: 0, skippedRecords: 10 })
  assert.match(html, /缺失或未明确 10 人，占全部对象 100\.0%/)
  assert.match(html, /未提供有效年龄/)
  assert.match(html, /<strong>—<small>岁 · 平均年龄/)
  assert(!html.includes('范围 0–0'))
})
test('empty and legacy data do not derive a fake cohort from model-accepted records', async () => {
  const empty = await render({ totalRecords: 0, processedRecords: 0, skippedRecords: 0 })
  assert.match(empty, /尚无上传对象/)
  const legacy = await render({ totalRecords: 10, processedRecords: 7, skippedRecords: 3 })
  assert.match(legacy, /尚未包含完整的原始人口学资料/)
  assert(!legacy.includes('conic-gradient'))
  for (const profile of [{ ...fixture(), total_records: 7 }, { ...fixture(), denominator: 'eligible_records' }, { ...fixture(), weighted: true }]) {
    const html = await render({ profile, totalRecords: 10, processedRecords: 7, skippedRecords: 3 })
    assert.match(html, /尚未包含完整的原始人口学资料/)
    assert(!html.includes('男性 4 人'))
  }
})
test('color variety represents categories and unknown is gray, not a disease-risk rule', async () => {
  const html = await render({ profile: fixture(), totalRecords: 10, processedRecords: 7, skippedRecords: 3 })
  assert.match(html, /conic-gradient\(#3B82F6 0% 40%, #F97316 40% 70%, #CBD5E1 70% 100%\)/)
  assert.match(html, /人口学分布不等同于风险差异/)
  assert(!/markLine|high_risk|danger_threshold/.test(source))
})
test('missing, invalid or non-closing profile blocks fall back safely without inventing counts', async () => {
  for (const mutate of [
    profile => { delete profile.sex },
    profile => { profile.education.categories = null },
    profile => { profile.marital.categories[0].count = 99 },
    profile => { profile.sex.categories[0].percent = 57.1 },
    profile => { profile.age.bands[0].count-- },
    profile => { profile.age.mean = null },
    profile => { profile.age.invalid_count = 4 },
    profile => { profile.sex.categories.push({ ...profile.sex.categories[0] }) },
  ]) {
    const profile = fixture(); mutate(profile)
    const html = await render({ profile, totalRecords: 10, processedRecords: 7, skippedRecords: 3 })
    assert.match(html, /尚未包含完整的原始人口学资料/)
    assert(!html.includes('conic-gradient'))
    assert(!html.includes('男性 4 人'))
  }
})
