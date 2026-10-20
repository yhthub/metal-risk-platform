/** Legacy helper safety and computed-only visible dashboard, offline only. */
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const assert = require('node:assert/strict')
const root = path.resolve(__dirname, '..')
const pnpm = path.join(root, 'node_modules/.pnpm')
const ts = require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith('typescript@')), 'node_modules/typescript'))
function load(file, imports = {}) {
  const exports = {}
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path.join(root, 'app/utils', file), 'utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } }).outputText, { exports, require: name => { assert(Object.hasOwn(imports, name)); return imports[name] }, setTimeout: () => {} })
  return exports
}
const risk = load('riskPrediction.ts')
const charts = load('riskDashboard.ts', { './riskPrediction': risk, './riskPalette': load('riskPalette.ts'), './riskChartTheme': load('riskChartTheme.ts') })
const plain = value => JSON.parse(JSON.stringify(value))
let checks = 0
function check(name, run) { run(); checks++; console.log('PASS ' + name) }
check('unavailable original charts have original neutral shapes but no numeric or probability series', () => {
  for (const kind of ['bar', 'gauge', 'rose', 'heatmap']) {
    const option = charts.buildOriginalUnavailableOption(kind, '缺少对应模型')
    assert.equal(option.animation, false)
    assert.equal(option.tooltip.show, false)
    assert.equal(option.series, undefined)
    assert.equal(option.xAxis, undefined)
    assert.equal(option.yAxis, undefined)
    assert(option.graphic[0].children.length > 0)
    assert.match(option.graphic[1].style.text, /原图保留/)
    assert.match(option.graphic[1].style.text, /缺少对应模型/)
    assert.match(option.graphic[1].style.text, /不表示0或任何比例/)
    assert(!/\d+(?:\.\d+)?%|0%|高危比例[:：]\s*\d/.test(option.graphic[1].style.text))
  }
})
check('the original half gauge has no needle or fabricated fill; Pb-As heatmap remains empty', () => {
  const gauge = charts.buildOriginalUnavailableOption('gauge', '风险分类模型尚未接入')
  assert.equal(gauge.graphic[0].children[0].type, 'arc')
  assert.equal(gauge.pointer, undefined)
  assert.equal(gauge.data, undefined)
  const heat = charts.buildOriginalUnavailableOption('heatmap', '没有砷输入或Pb×As效应模型')
  assert.equal(heat.graphic[0].children.length, 25)
  assert(heat.graphic[0].children.every(item => item.type === 'rect' && item.style.fill === '#F1F5F9'))
  assert.match(heat.graphic[1].style.text, /没有砷输入或Pb×As效应模型/)
})
check('single-person dashboard removes disease, uncomputed gauge and Pb-As placeholders instead of drawing zeros', () => {
  const source = fs.readFileSync(path.join(root, 'app/pages/risk/index.vue'), 'utf8')
  const template = source.split('<template>')[1].split('<script setup')[0]
  assert(!/original-disease-empty|empty-probability-track|待疾病概率模型|原图型骨架|Pb × As|高发职业病靶向预测/.test(template))
  assert(!/buildOriginalUnavailableOption|originalGaugeRef|originalImportanceRef|originalJointRef/.test(source))
  assert.match(template, /v-if="doseOption" class="result-card/)
  assert.match(template, /v-if="jointOption" class="result-card/)
  assert.match(template, /全血铅 × 全血镉的实际模型网格/)
  assert.match(template, /非因果剂量反应/)
  assert.match(template, /不代表因果效应、安全阈值或职业病风险等级/)
})
check('real radar preserves six spokes and absolute contribution mass without mixing original concentration units', () => {
  const items = Array.from({ length: 11 }, (_, index) => ({ feature: 'f' + index, label_zh: '特征' + index, value: (index % 2 ? -1 : 1) * (index + 1) }))
  const input = { explanation: { status: 'AVAILABLE', items } }
  const before = plain(input)
  const option = charts.buildRadarOption(input)
  assert.equal(option.radar.indicator.length, 6)
  assert.equal(option.series[0].type, 'radar')
  assert(option.radar.indicator.every(item => item.max === 100))
  const values = option.series[0].data[0].value
  assert(Math.abs(values.reduce((sum, value) => sum + value, 0) - 100) < 1e-10)
  assert(Math.abs(values[5] - (1 + 2 + 3 + 4 + 5 + 6) / 66 * 100) < 1e-10)
  assert.match(option.radar.indicator[5].name, /其他特征/)
  assert.deepEqual(plain(input), before)
  assert.match(option.tooltip.formatter(), /不是暴露浓度、患病概率或因果重要性/)
  assert.match(option.tooltip.formatter(), /其他特征（合计）/)
  assert(option.radar.indicator.every(item => item.name.length <= 7), 'Compact axis labels must fit the original report slot; tooltips retain full names')
})
check('radar refuses insufficient dimensions, zero mass or withheld results instead of manufacturing axes', () => {
  const item = { feature: 'one', label_zh: '一项', value: 1 }
  assert.equal(charts.buildRadarOption({ explanation: { status: 'AVAILABLE', items: [item] } }), null)
  assert.equal(charts.buildRadarOption({ explanation: { status: 'AVAILABLE', items: Array.from({ length: 5 }, (_, i) => ({ ...item, feature: '' + i, value: 0 })) } }), null)
  assert.equal(charts.buildRadarOption({ explanation: { status: 'INSUFFICIENT_VALIDATED_ACCURACY', items: Array.from({ length: 5 }, () => item) } }), null)
})
console.log('\n' + checks + ' chart-preservation checks passed; no model, browser or server invoked.')
