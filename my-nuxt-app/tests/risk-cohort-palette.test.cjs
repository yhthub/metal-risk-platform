/** Palette-only regression guards; no HTTP, model inference or clinical thresholds. */
const test = require('node:test')
const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const root = path.resolve(__dirname, '..')
const filename = path.join(root, 'app/components/RiskCohortDashboard.vue')
const source = fs.readFileSync(filename, 'utf8')
const pnpm = path.join(root, 'node_modules/.pnpm')
const compiler = require(path.join(pnpm, fs.readdirSync(pnpm).find(item => item.startsWith('@vue+compiler-sfc@')), 'node_modules/@vue/compiler-sfc'))
const parsed = compiler.parse(source, { filename })
const template = parsed.descriptor.template.content
const css = parsed.descriptor.styles[0].content
const warningFilename = path.join(root, 'app/components/RiskCohortWarning.vue')
const warningSource = fs.readFileSync(warningFilename, 'utf8')
const warningParsed = compiler.parse(warningSource, { filename: warningFilename })
const warningTemplate = warningParsed.descriptor.template.content
const warningCss = warningParsed.descriptor.styles[0].content

test('cohort distribution uses the new blue accent while outcome and summary roles stay distinct', () => {
  for (const [accent, title] of [
    ['accent-blue', '全群指标估计分布'],
    ['accent-blue', '12 项结局 · 全群概览'],
    ['accent-amber', '全群估计统计概览'],
  ]) assert.match(template, new RegExp('class="result-card [^"\\n]*' + accent + '"[\\s\\S]*?<h4>' + title))
  assert.match(warningTemplate, /特异性高危易感人群预警榜/)
  assert.match(warningCss, /\.cohort-warning-card\{--state:#ef4444;--state-dark:#991b1b/)
  assert.match(warningCss, /\.state-clear\{--state:#10b981;--state-dark:#047857/)
  assert.match(warningCss, /\.state-insufficient\{--state:#d69a31;--state-dark:#956215/)
  assert.match(css, /\.accent-blue\{--section-accent:#3B82F6\}/)
  assert.match(css, /\.accent-amber\{--section-accent:#F59E0B\}/)
  assert.match(css, /\.accent-orange\{--section-accent:#F97316\}/)
  assert(!template.includes('性别分层概览'))
  assert(!template.includes('年龄分层概览'))
})

test('all twelve outcome buttons use category-only colors, not estimated disease risk', () => {
  assert.match(template, /'outcome-' \+ item.target/)
  assert.match(template, /色条仅区分指标类别，不表示疾病风险/)
  const groups = [
    [['sbp', 'dbp'], '#EF4444'],
    [['serum_creatinine_mg_dl', 'bun_mg_dl', 'uric_acid_mg_dl', 'uacr_mg_g'], '#3B82F6'],
    [['hba1c_percent', 'total_cholesterol_mg_dl', 'hdl_cholesterol_mg_dl'], '#F97316'],
    [['alt_u_l', 'ast_u_l', 'ggt_u_l'], '#10B981'],
  ]
  for (const [targets, color] of groups) for (const target of targets) {
    const selector = '.outcome-row.outcome-' + target
    const rule = css.split('\n').find(line => line.startsWith('.outcome-row.outcome-') && line.split('{')[0].split(',').includes(selector))
    assert(rule, 'Missing category style for ' + target)
    assert(rule.includes('--outcome-accent:' + color), target + ' category hue changed')
  }
  assert.match(css, /\.outcome-row\.selected\{background:var\(--outcome-tint\)\}/)
})

test('model values retain green/neutral hues while input counts sit in the top profile, not a lower count card', () => {
  assert.match(template, /class="stat-estimated"/)
  assert.match(template, /<RiskCohortProfile/)
  assert.match(template, /全群估计统计概览/)
  assert.match(template, /!row\.record\.input \? 'status-skipped' : row\.outcome && predictionHasValue\(row\.outcome\) \? 'status-estimated' : 'status-withheld'/)
  assert.match(css, /\.stat-estimated strong,\.status-estimated\{color:#10B981\}/)
  assert.match(css, /\.stat-withheld strong,\.status-withheld\{color:#B7790C\}/)
  assert.match(css, /\.stat-skipped strong,\.status-skipped,\.stat-neutral strong,\.reason-list dd\{color:#64748B\}/)
  assert(!/\.(?:stat-skipped|status-skipped)[^{]*\{[^}]*#(?:EF4444|FCA5A5)/i.test(css))
  assert.match(template, /仍纳入上方基本资料统计/)
  assert(!template.includes('全群数据质量与保留原因'))
})

test('white full-row warning merges ranking and a computed share beside a dashed internal divider', () => {
  const main = template.split('<div class="results-grid">')[1].split('<section class="result-card all-records">')[0]
  assert.equal((main.match(/class="result-card /g) || []).length, 3)
  assert.equal((main.match(/<RiskCohortWarning\b/g) || []).length, 1)
  assert.match(main, /<RiskCohortWarning class="col-span-6"/)
  assert.equal((warningTemplate.match(/<article\b/g) || []).length, 1)
  assert.match(warningTemplate, /class="ranking-pane"/)
  assert.match(warningTemplate, /<aside class="share-pane" aria-label="高危预警对象人群占比"/)
  assert.match(warningTemplate, /ref="shareRef"/)
  assert.match(warningTemplate, /按综合分达到当前阈值计算，不是患病率/)
  assert.match(warningCss, /grid-column:1\/-1/)
  assert.match(warningCss, /\.share-pane\{[^}]*border-left:1px dashed/)
  assert(!/尚无高危判定模型与定义|prototypeGaugeRef/.test(source + warningSource))
  assert.match(main, /class="result-card col-span-6 accent-amber"/)
  assert.match(css, /\.stat-grid\{[^}]*grid-template-columns:repeat\(3,minmax\(0,1fr\)\)/)
  assert.match(css, /grid-template-columns:repeat\(6,minmax\(0,1fr\)\)/)
  assert.match(css, /\.result-card\{background:white;/)
  assert.match(css, /\.result-card\{border-color:#dce5f1;border-radius:14px;padding:24px;box-shadow:/)
  assert.match(css, /\.r-head\{[^}]*border-bottom:1px dashed #e8eef7/)
  assert.match(template, /完整全群记录与排序/)
  assert(!/原图与功能边界|prototype-fold|prototype-empty|prototypeImportanceRef|prototypeJointRef|buildOriginalUnavailableOption/.test(template + parsed.descriptor.scriptSetup.content))
})

test('palette-only template classes and scoped CSS compile offline', () => {
  assert.deepEqual(parsed.errors, [])
  const script = compiler.compileScript(parsed.descriptor, { id: 'risk-cohort-palette' })
  const compiled = compiler.compileTemplate({ source: template, filename, id: 'risk-cohort-palette', compilerOptions: { bindingMetadata: script.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(compiled.errors, [])
  const style = compiler.compileStyle({ source: css, filename, id: 'risk-cohort-palette', scoped: true })
  assert.deepEqual(style.errors, [])
  assert.deepEqual(warningParsed.errors, [])
  const warningScript = compiler.compileScript(warningParsed.descriptor, { id: 'risk-warning-palette' })
  const warningCompiled = compiler.compileTemplate({ source: warningTemplate, filename: warningFilename, id: 'risk-warning-palette', compilerOptions: { bindingMetadata: warningScript.bindings, expressionPlugins: ['typescript'] } })
  assert.deepEqual(warningCompiled.errors, [])
  assert.deepEqual(compiler.compileStyle({ source: warningCss, filename: warningFilename, id: 'risk-warning-palette', scoped: true }).errors, [])
})
