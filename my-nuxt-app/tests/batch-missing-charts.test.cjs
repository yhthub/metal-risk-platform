/** Missing chart values stay absent; no null-to-zero exposure circles. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const pnpm = path.join(__dirname, '../node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(name => name.startsWith('typescript@')), 'node_modules/typescript'))
const source = fs.readFileSync(path.join(__dirname, '../app/composables/useBatchAnalysisCharts.ts'), 'utf8')
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 }, reportDiagnostics: true })
assert.equal(compiled.diagnostics.length, 0)

function render(overrides = {}) {
  const context = vm.createContext({ exports: {}, document: { getElementById: id => ({ id }) }, window: { devicePixelRatio: 1 } })
  vm.runInContext(compiled.outputText, context)
  const options = {}
  const echarts = {
    graphic: { LinearGradient: class {} },
    init: element => ({ setOption: option => { options[element.id] = option } })
  }
  const analysis = {
    correlation: { labels: ['Pb'], matrix: [[null]] },
    quartiles: { labels: ['Pb', 'Cd'], q1: [null, 1], median: [null, 2], q3: [null, 3] },
    boxplot: { labels: ['Pb', 'Cd'], values: [[null, null, null, null, null], [-1, -0.5, 0, 0.5, 1]], outliers: [] },
    pca: { explained_variance: [0, 0], points: [] }, completeness: [],
    density: { series: [{ name: 'Pb', x: [], values: [] }, { name: 'Cd', x: [-1, 0, 1], values: [0.1, 0.2, 0.1] }] },
    histogram: { labels: [], series: [] },
    bubble: { points: [
      { age: 40, mean_sbp: 120, mean_dbp: 75, exposure_percentile: null, group: '正常血压组' },
      { age: 41, mean_sbp: 125, mean_dbp: 80, exposure_percentile: 0, group: '正常血压组' },
      { age: 42, mean_sbp: 150, mean_dbp: 95, exposure_percentile: 75, group: '高血压组' },
      { age: 43, mean_sbp: 155, mean_dbp: 98, exposure_percentile: '75', group: '高血压组' }
    ] },
    demographics: { marital: [], education: [], income: [] }, ...overrides
  }
  context.exports.renderBatchAnalysisCharts(analysis, echarts)
  return options
}

test('null/strings are not plotted as exposure points, genuine numeric zero is retained', () => {
  const option = render().batchChartBubble
  assert.equal(option.series[0].data.length, 1)
  assert.equal(option.series[0].data[0][2], 0)
  assert.equal(option.series[1].data.length, 1)
  assert.equal(option.series[1].data[0][2], 75)
})

test('empty first metal does not erase the other density series axis', () => {
  const option = render().batchChartDensity
  assert.deepEqual(Array.from(option.xAxis.data), [-1, 0, 1])
  assert.equal(option.series[0].data.length, 0)
  assert.deepEqual(Array.from(option.series[1].data), [0.1, 0.2, 0.1])
})

test('missing boxplot is an absent category slot, not a zero-valued box', () => {
  const option = render().batchChartBoxplot
  assert.equal(option.series[0].data[0], '-')
  assert.deepEqual(Array.from(option.series[0].data[1]), [-1, -0.5, 0, 0.5, 1])
  assert.equal(option.xAxis.data.length, 2)
})
