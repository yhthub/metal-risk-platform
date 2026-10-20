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

test('blue heatmap retains actual bounds and response values without safety thresholds', () => {
  const input = { label_zh: '收缩压', unit: 'mmHg', joint_response: {
    status: 'AVAILABLE', x_values: [0, 1], y_values: [0, 2], x_unit: 'ug/dL', y_unit: 'ug/L', values: [[0, 0, 120], [1, 1, 132]] } }
  const option = charts.buildJointOption(input)
  assert.deepEqual(plain(option.visualMap.inRange.color), ['#EFF6FF', '#BFDBFE', '#60A5FA', '#1E40AF'])
  assert.equal(option.visualMap.min, 120); assert.equal(option.visualMap.max, 132)
  assert.deepEqual(plain(option.series[0].data), input.joint_response.values)
  assert.deepEqual(plain(option.visualMap.text), ['估计值高', '估计值低'])
  assert.equal(option.visualMap.pieces, undefined)
  assert.equal(option.series[0].itemStyle.borderColor, '#fff')
  assert.equal(option.series[0].itemStyle.borderRadius, 5)
  assert.match(option.series[0].label.formatter({ value: [0, 0, 120] }), /\{dark\|120\}/)
  assert.match(option.series[0].label.formatter({ value: [1, 1, 132] }), /\{light\|132\}/)
})

test('single and cohort chart builders share quiet gridlines, typography and white rounded tooltips', () => {
  const theme = load('riskChartTheme')
  const dose = charts.buildDoseOption({ label_zh: '收缩压', unit: 'mmHg', dose_response: { status: 'AVAILABLE', unit: 'ug/dL', values: [{ x: 0, prediction: 120 }, { x: 2, prediction: 123 }] } })
  const cohortInput = { summary: [{ target: 'sbp', unit: 'mmHg', estimated_count: 7, histogram: { counts: [3, 4], bin_edges: [100, 120, 140] } }] }
  const before = plain(cohortInput)
  const distribution = cohort.buildCohortDistributionOption(cohortInput, 'sbp')
  assert.equal(dose.animationEasing, 'cubicOut')
  assert.match(dose.textStyle.fontFamily, /Microsoft YaHei/)
  assert.equal(dose.tooltip.confine, true)
  assert.match(dose.tooltip.backgroundColor, /255,255,255/)
  assert.match(dose.tooltip.extraCssText, /box-shadow:.*border-radius:10px/)
  assert.deepEqual(plain(dose.yAxis.splitLine), plain(theme.RISK_SPLIT_LINE))
  assert.equal(dose.yAxis.axisLine.show, false)
  assert.equal(dose.yAxis.axisTick.show, false)
  assert.deepEqual(plain(distribution.series[0].data), [3, 4])
  assert.deepEqual(plain(distribution.yAxis.splitLine), plain(dose.yAxis.splitLine))
  assert.deepEqual(plain(distribution.textStyle), plain(dose.textStyle))
  assert.equal(distribution.tooltip.extraCssText, dose.tooltip.extraCssText)
  assert.equal(distribution.xAxis.name, 'mmHg')
  assert.deepEqual(plain(cohortInput), before)
})

test('cohort histogram uses slim separated blue columns and readable two-line bin labels without changing counts', () => {
  const input = { summary: [{ target: 'sbp', unit: 'mmHg', estimated_count: 20, histogram: {
    counts: [2, 2, 1, 0, 0, 1, 2, 4, 3, 5],
    bin_edges: [114.61, 116.667, 118.724, 120.781, 122.838, 124.895, 126.952, 129.009, 131.066, 133.123, 135.18],
  } }] }
  const before = plain(input)
  const option = cohort.buildCohortDistributionOption(input, 'sbp')
  const bars = option.series[0]
  assert.equal(bars.barMaxWidth, 26)
  assert.equal(bars.barCategoryGap, '44%')
  assert.deepEqual(plain(bars.itemStyle.color.colorStops), [{ offset: 0, color: '#60A5FA' }, { offset: 1, color: '#2563EB' }])
  assert.equal(bars.itemStyle.color.x2, 0)
  assert.equal(bars.itemStyle.color.y2, 1)
  assert.deepEqual(plain(bars.data), before.summary[0].histogram.counts)
  assert.equal(bars.data.reduce((sum, count) => sum + count, 0), 20)
  assert.equal(option.xAxis.axisLabel.rotate, 0)
  assert.equal(option.xAxis.axisLabel.interval, 'auto')
  assert.equal(option.xAxis.axisLabel.hideOverlap, true)
  assert.equal(option.xAxis.axisLabel.formatter(option.xAxis.data[0]), '114.61–\n116.67')
  assert.equal(option.xAxis.data[0], '114.61–116.67', 'Tooltip categories retain the complete original bin label')
  assert.equal(option.xAxis.name, 'mmHg')
  assert.equal(option.yAxis.name, '人数')
  assert.equal(option.yAxis.minInterval, 1)
  assert.equal(bars.label.formatter({ value: 0 }), '', 'A genuinely empty bin is not shown as a person')
  assert.equal(String(bars.label.formatter({ value: 5 })), '5')
  assert.match(option.tooltip.formatter([{ name: option.xAxis.data[0], value: 2 }]), /114\.61–116\.67 mmHg/)
  assert.deepEqual(plain(input), before, 'Styling cannot alter interval boundaries or original count arrays')
})

test('histogram styling preserves invalid or missing distribution guards instead of creating zero-filled data', () => {
  const input = { summary: [{ target: 'sbp', unit: 'mmHg', estimated_count: 7, histogram: { counts: [3, 4], bin_edges: [100, 120, 140] } }] }
  for (const mutate of [
    value => { value.summary[0].histogram = undefined },
    value => { value.summary[0].estimated_count = 0 },
    value => { value.summary[0].histogram.counts = [3, 3] },
    value => { value.summary[0].histogram.bin_edges = [100, 140] },
  ]) {
    const changed = plain(input)
    mutate(changed)
    const before = plain(changed)
    assert.equal(cohort.buildCohortDistributionOption(changed, 'sbp'), null)
    assert.deepEqual(plain(changed), before)
  }
  assert.equal(cohort.buildCohortDistributionOption(input, 'missing-target'), null)
})

test('coverage green means input completeness, never a traffic-light risk classification', () => {
  const option = cohort.buildCohortCoverageOption({ total_records: 10, processed_records: 7 })
  assert.deepEqual(plain(option.series[0].progress.itemStyle.color.colorStops), [{ offset: 0, color: '#6EE7B7' }, { offset: 1, color: '#10B981' }])
  assert.equal(option.series[0].data[0].value, 70)
  assert.deepEqual(plain(option.series[0].axisLine.lineStyle.color), [[1, '#E5EDF7']])
  assert.match(option.tooltip.formatter, /不是高危比例/)
})

test('ranking gradient has pronounced dark-to-light red contrast without value-based risk bins', () => {
  const gradient = palette.rankingGradient()
  assert.deepEqual(plain(gradient.colorStops), [{ offset: 0, color: '#B91C1C' }, { offset: .55, color: '#EF4444' }, { offset: 1, color: '#FECACA' }])
  assert.equal(gradient.type, 'linear'); assert.equal(gradient.x2, 1); assert.equal(gradient.y2, 0)
})
