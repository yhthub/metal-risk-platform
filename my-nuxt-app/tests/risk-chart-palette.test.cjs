/** Original hues are presentation only; chart values and units remain model-derived. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith('typescript@')), 'node_modules/typescript'))
const modules = {}
function load(name) {
  if (modules[name]) return modules[name]
  const exports = {}; modules[name] = exports
  const source = fs.readFileSync(path.join(root, 'app/utils', name + '.ts'), 'utf8')
  vm.runInNewContext(ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.CommonJS } }).outputText,
    { exports, require: request => load(request.replace('./', '')), setTimeout() {} })
  return exports
}
const palette = load('riskPalette')
const charts = load('riskDashboard')
const cohort = load('riskCohort')
const plain = value => JSON.parse(JSON.stringify(value))
const explanation = { status: 'AVAILABLE', scale_label: 'mmHg', items: [
  { feature: 'pb', label_zh: '全血铅', value: 2 },
  { feature: 'cd', label_zh: '全血镉', value: -1 },
  { feature: 'hg', label_zh: '全血汞', value: .5 },
  { feature: 'age_years', label_zh: '年龄', value: 3 },
  { feature: 'bmi_kg_m2', label_zh: 'BMI', value: 1.5 },
  { feature: 'sex_female', label_zh: '性别', value: .25 },
] }

test('original feature hues are stable even when SHAP rank changes', () => {
  const before = plain(explanation)
  const first = charts.buildImportanceOption({ explanation }).series[0].data
  const second = charts.buildImportanceOption({ explanation: { ...explanation, items: [...explanation.items].reverse() } }).series[0].data
  for (const [name, color] of [['全血铅', '#EF4444'], ['全血镉', '#F97316'], ['全血汞', '#F59E0B'], ['年龄', '#3B82F6'], ['BMI', '#8B5CF6']]) {
    assert.equal(first.find(item => item.name === name).itemStyle.color, color)
    assert.equal(second.find(item => item.name === name).itemStyle.color, color)
  }
  assert.deepEqual(plain(explanation), before)
  assert.equal(first.reduce((sum, item) => sum + item.value, 0), 8.25)
  assert.equal(palette.featureAccent('unknown'), '#9CA3AF')
})

test('red dose curve and radar preserve predictions, native units and current-input marker', () => {
  const input = { label_zh: '收缩压', unit: 'mmHg', explanation,
    dose_response: { status: 'AVAILABLE', unit: 'ug/dL', current_value: 2, values: [{ x: 0, prediction: 120 }, { x: 2, prediction: 123 }] } }
  const dose = charts.buildDoseOption(input)
  assert.equal(dose.series[0].lineStyle.color, '#EF4444')
  assert.deepEqual(plain(dose.series[0].data), [[0, 120], [2, 123]])
  assert.deepEqual(plain(dose.series[0].markLine.data), [{ xAxis: 2 }])
  assert.equal(dose.yAxis.name, 'mmHg')
  const radar = charts.buildRadarOption(input)
  assert.equal(radar.series[0].data[0].lineStyle.color, '#EF4444')
  assert(Math.abs(radar.series[0].data[0].value.reduce((sum, value) => sum + value, 0) - 100) < 1e-10)
})

test('warm heatmap retains actual bounds and response values without safety thresholds', () => {
  const input = { label_zh: '收缩压', unit: 'mmHg', joint_response: {
    status: 'AVAILABLE', x_values: [0, 1], y_values: [0, 2], x_unit: 'ug/dL', y_unit: 'ug/L', values: [[0, 0, 120], [1, 1, 132]] } }
  const option = charts.buildJointOption(input)
  assert.deepEqual(plain(option.visualMap.inRange.color), ['#FFF7ED', '#FED7AA', '#FB923C', '#EF4444'])
  assert.equal(option.visualMap.min, 120); assert.equal(option.visualMap.max, 132)
  assert.deepEqual(plain(option.series[0].data), input.joint_response.values)
  assert.deepEqual(plain(option.visualMap.text), ['估计值高', '估计值低'])
  assert.equal(option.visualMap.pieces, undefined)
})

test('coverage green means input completeness, never a traffic-light risk classification', () => {
  const option = cohort.buildCohortCoverageOption({ total_records: 10, processed_records: 7 })
  assert.equal(option.series[0].progress.itemStyle.color, '#10B981')
  assert.equal(option.series[0].data[0].value, 70)
  assert.deepEqual(plain(option.series[0].axisLine.lineStyle.color), [[1, '#E5EDF7']])
  assert.match(option.tooltip.formatter, /不是高危比例/)
})

test('ranking gradient has pronounced dark-to-light red contrast without value-based risk bins', () => {
  const gradient = palette.rankingGradient()
  assert.deepEqual(plain(gradient.colorStops), [{ offset: 0, color: '#B91C1C' }, { offset: .55, color: '#EF4444' }, { offset: 1, color: '#FECACA' }])
  assert.equal(gradient.type, 'linear'); assert.equal(gradient.x2, 1); assert.equal(gradient.y2, 0)
})
