/** Whole-upload views. Display pagination never limits the inference population. */
import { csvCell, formatPredictionNumber, predictionHasValue, PREDICTION_SCOPE_NOTE } from './riskPrediction'
import type { BatchPredictionOutcome, BatchPredictionResponse, PredictionOutcome, PredictionRequest } from './riskPrediction'
import type { ChartOption } from './riskDashboard'
import { RISK_PALETTE, chartGradient, rankingGradient } from './riskPalette'
import { riskChartBase, riskTooltip, riskValueAxis, riskCategoryAxis } from './riskChartTheme'

export interface CohortStatistics {
  n: number; mean: number | null; median: number | null; q1: number | null; q3: number | null
  min: number | null; max: number | null; std: number | null; std_definition?: string
}
export interface CohortHistogram { status: string; bin_edges: number[]; counts: number[]; counted_records: number; method?: string }
export interface CohortGroup {
  group: string; label_zh: string; eligible_count: number; estimated_count: number; withheld_count: number
  mean_prediction: number | null; statistics: CohortStatistics
}
/** Raw-file description: all uploaded people, including model-ineligible rows. */
export interface CohortProfileCategory { key: string; label: string; count: number; percent: number }
export interface CohortProfileCategorySummary {
  source_columns: string[]; available: boolean; valid_count: number; missing_count: number; unknown_count: number
  categories: CohortProfileCategory[]
}
export interface CohortProfileNumericSummary {
  source_columns: string[]; available: boolean; valid_count: number; missing_count: number; invalid_count: number; unknown_count: number
  mean: number | null; median: number | null; min: number | null; max: number | null; bands: CohortProfileCategory[]
}
export interface CohortDemographicProfile {
  scope: 'all_uploaded_records'; total_records: number; denominator: 'all_uploaded_records'; weighted: false
  sex: CohortProfileCategorySummary; marital: CohortProfileCategorySummary; education: CohortProfileCategorySummary
  age: CohortProfileNumericSummary; bmi?: CohortProfileNumericSummary; smoking?: CohortProfileCategorySummary; notes?: string[]
}
type BaseCohortSummary = BatchPredictionResponse['summary'][number]
export interface CohortSummary extends BaseCohortSummary {
  statistics: CohortStatistics; histogram: CohortHistogram; distribution?: CohortHistogram
  by_gender: CohortGroup[]; by_age_band: CohortGroup[]
}
export interface CohortPredictionResponse extends Omit<BatchPredictionResponse, 'summary'> {
  analysis_scope: 'all_uploaded_records'; complete: true; summary: CohortSummary[]
  scope?: string; provenance?: Record<string, unknown>; elapsed_ms?: number
  outcome_metadata?: Array<Record<string, unknown> & { target: string }>
  demographic_profile?: CohortDemographicProfile
}
export interface CohortRankRow {
  rank: number; row_number: number; person_id: string; prediction: number
  age: number | null; gender: string | null; input?: PredictionRequest; outcome: BatchPredictionOutcome
}
export interface CohortView {
  target: string; label_zh: string; unit: string; total_records: number; processed_records: number; skipped_records: number
  estimated_count: number; withheld_count: number; statistics: CohortStatistics | null
  rankings: CohortRankRow[]; excluded: BatchPredictionResponse['records']; histogram: CohortHistogram | null
  genderGroups: CohortGroup[]; ageGroups: CohortGroup[]; reason: string
}
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const html = (value: unknown) => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')

/** Reject legacy pages and incomplete successes before they enter cohort state. */
export function cohortResponseError(value: any): string | null {
  if (!value || value.complete !== true || value.analysis_scope !== 'all_uploaded_records' || value.has_more !== false || value.offset !== 0)
    return '尚未取得整份文件的完整群体结果；分页结果不能作为全群体分析。'
  if (!Number.isInteger(value.total_records) || value.total_records < 1 || value.limit !== value.total_records
    || !Number.isInteger(value.processed_records) || value.processed_records < 0
    || !Number.isInteger(value.skipped_records) || value.skipped_records < 0
    || value.processed_records + value.skipped_records !== value.total_records
    || !Array.isArray(value.records) || value.records.length !== value.total_records || !Array.isArray(value.summary))
    return '群体结果记录数不完整，未显示全群体结论。'
  const targets = new Set<string>(value.summary.map((row: any) => row.target))
  if (value.summary.length !== 12 || targets.size !== 12) return '群体结局列表不完整或重复。'
  const counts = new Map<string, number>([...targets].map(target => [target, 0]))
  const ids = new Set<string>(); let accepted = 0
  for (let index = 0; index < value.records.length; index++) {
    const row = value.records[index]
    if (!row || row.row_number !== index + 1 || typeof row.person_id !== 'string' || !row.person_id || ids.has(row.person_id))
      return '群体结果编号或原始行号不一致，未生成排序。'
    ids.add(row.person_id)
    if (row.status === 'ESTIMATES_NOT_DIAGNOSES') {
      if (!row.input || !Array.isArray(row.results) || row.results.length !== 12) return '存在未完整计算的合格对象，未显示全群体结论。'
      const rowTargets = new Set<string>()
      for (const outcome of row.results) {
        if (!outcome || !targets.has(outcome.target) || rowTargets.has(outcome.target)) return '对象的结局列表不完整或重复。'
        rowTargets.add(outcome.target)
        if (predictionHasValue(outcome)) counts.set(outcome.target, (counts.get(outcome.target) || 0) + 1)
      }
      accepted++
    } else if (row.status !== 'INPUT_NOT_ELIGIBLE' || row.results?.length) return '存在未完成或状态不明确的对象，未显示全群体结论。'
  }
  if (accepted !== value.processed_records || value.summary.length !== 12) return '群体汇总与全量对象不一致。'
  for (const summary of value.summary) {
    const count = counts.get(summary.target) || 0
    if (summary.estimated_count !== count || summary.withheld_count !== accepted - count || summary.statistics?.n !== count)
      return '结局汇总与全部逐人结果不一致，未显示群体结论。'
  }
  return null
}

export function buildCohortView(result: CohortPredictionResponse, target: string): CohortView {
  const summary = result.summary.find(item => item.target === target)
  const rankings: CohortRankRow[] = []
  for (const record of result.records) {
    const outcome = record.results?.find(item => item.target === target)
    if (!outcome || !predictionHasValue(outcome)) continue
    rankings.push({ rank: 0, row_number: record.row_number, person_id: record.person_id,
      prediction: outcome.prediction as number, age: record.input?.person.age ?? null, gender: record.input?.person.gender ?? null, input: record.input, outcome })
  }
  rankings.sort((a, b) => b.prediction - a.prediction || a.row_number - b.row_number)
  rankings.forEach((row, index) => { row.rank = index + 1 })
  return { target, label_zh: summary?.label_zh || target, unit: summary?.unit || '', total_records: result.total_records,
    processed_records: result.processed_records, skipped_records: result.skipped_records,
    estimated_count: rankings.length, withheld_count: summary?.withheld_count || 0,
    statistics: summary?.statistics?.n ? summary.statistics : null, rankings,
    excluded: result.records.filter(row => !row.input), histogram: summary?.histogram || summary?.distribution || null,
    genderGroups: summary?.by_gender || [], ageGroups: summary?.by_age_band || [],
    reason: rankings.length ? '' : result.processed_records === 0 ? '所有对象均不满足必需输入条件；请查看跳过原因。'
      : result.records.flatMap(row => row.results || []).find(row => row.target === target)?.reason || '当前结局验证不足，暂无可排序的估计值。' }
}

export function buildCohortRankOption(result: CohortPredictionResponse, target: string, limit = 10): ChartOption | null {
  const view = buildCohortView(result, target)
  const rows = view.rankings.slice(0, Math.max(1, Math.min(50, Math.floor(limit))))
  if (!rows.length) return null
  return { ...riskChartBase(), tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: any[]) => params.map(item => html(item.name) + '：' + formatPredictionNumber(item.value) + ' ' + html(view.unit) + '<br/>全体有效对象中的指标估计排序，非疾病风险概率').join('<br/>') }),
    grid: { left: 12, right: 76, top: 20, bottom: 36, containLabel: true },
    xAxis: riskValueAxis({ name: view.unit }),
    yAxis: riskCategoryAxis({ inverse: true, data: rows.map(row => row.person_id), axisLabel: { color: '#475569', fontSize: 11, width: 90, overflow: 'truncate' } }),
    series: [{ type: 'bar', name: view.label_zh, barMaxWidth: 23, data: rows.map(row => row.prediction), itemStyle: { color: rankingGradient(), borderRadius: [0, 6, 6, 0] }, emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(239,68,68,.20)' } }, label: { show: true, position: 'right', distance: 8, fontSize: 11, fontWeight: 600, color: RISK_PALETTE.red, formatter: (item: any) => formatPredictionNumber(item.value) } }] }
}

export function buildCohortCoverageOption(result: CohortPredictionResponse): ChartOption {
  const percentage = result.total_records ? result.processed_records / result.total_records * 100 : 0
  return { ...riskChartBase(), tooltip: riskTooltip({ formatter: '全文件有效输入：' + result.processed_records + ' / ' + result.total_records + '；不是高危比例' }),
    series: [{ type: 'gauge', startAngle: 180, endAngle: 0, center: ['50%', '72%'], radius: '94%', min: 0, max: 100,
      progress: { show: true, width: 18, roundCap: true, itemStyle: { color: chartGradient('#6EE7B7', RISK_PALETTE.green) } }, axisLine: { roundCap: true, lineStyle: { width: 18, color: [[1, '#E5EDF7']] } },
      pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false },
      detail: { offsetCenter: [0, '11%'], fontSize: 28, color: RISK_PALETTE.green, formatter: (value: number) => formatPredictionNumber(value, 1) + '%' },
      data: [{ value: percentage, name: result.processed_records + ' / ' + result.total_records + ' 人', title: { offsetCenter: [0, '40%'], fontSize: 11, color: '#64748B' } }] }] }
}

export function buildCohortDistributionOption(result: CohortPredictionResponse, target: string): ChartOption | null {
  const view = result.summary.find(row => row.target === target); const histogram = view?.histogram || view?.distribution
  if (!view || !histogram || !view.estimated_count || histogram.counts.length + 1 !== histogram.bin_edges.length
    || histogram.counts.reduce((a, b) => a + b, 0) !== view.estimated_count) return null
  const labels = histogram.counts.map((_, index) => formatPredictionNumber(histogram.bin_edges[index], 2) + '–' + formatPredictionNumber(histogram.bin_edges[index + 1], 2))
  return { ...riskChartBase(), tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: any[]) => params.map(item => html(item.name) + ' ' + html(view.unit) + '<br/>' + item.value + ' 人；全部有效估计，不是实测患病人数').join('<br/>') }),
    grid: { left: 12, right: 16, top: 36, bottom: 60, containLabel: true },
    xAxis: riskCategoryAxis({ data: labels, boundaryGap: true, axisLabel: { interval: 'auto', hideOverlap: true, rotate: 0, lineHeight: 16, fontSize: 10, color: '#8291A8', margin: 14, formatter: (label: string) => label.replace('–', '–\n') }, name: view.unit, nameLocation: 'middle', nameGap: 48, nameTextStyle: { color: '#64748B', fontSize: 11 } }),
    yAxis: riskValueAxis({ minInterval: 1, name: '人数', nameGap: 18, max: (extent: { max: number }) => Math.max(1, Math.ceil(extent.max * 1.2)) }),
    series: [{ type: 'bar', name: '估计值分布', data: histogram.counts, barCategoryGap: '44%', barMaxWidth: 26,
      itemStyle: { color: chartGradient('#60A5FA', '#2563EB', true), borderRadius: [5, 5, 0, 0] },
      label: { show: true, position: 'top', distance: 8, color: '#5075A6', fontSize: 11, fontWeight: 600, formatter: (item: { value: number }) => item.value > 0 ? String(item.value) : '' },
      emphasis: { itemStyle: { color: chartGradient('#3B82F6', '#1D4ED8', true), shadowBlur: 12, shadowColor: 'rgba(37,99,235,.16)' } } }] }
}

export function buildCohortGroupOption(result: CohortPredictionResponse, target: string, groupBy: 'gender' | 'age'): ChartOption | null {
  const view = result.summary.find(row => row.target === target)
  if (!view) return null
  const groups = groupBy === 'gender' ? view.by_gender : view.by_age_band
  if (!groups.some(group => group.estimated_count > 0 && finite(group.mean_prediction))) return null
  return { ...riskChartBase(), tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: any[]) => params.map(item => {
    const group = groups[item.dataIndex]
    return html(group.label_zh) + '<br/>有效估计 ' + group.estimated_count + ' 人<br/>均值：' + formatPredictionNumber(group.mean_prediction) + ' ' + html(view.unit) + '<br/>组间描述，未调整混杂，不是因果效应'
  }).join('<br/>') }), grid: { left: 18, right: 24, top: 38, bottom: 38, containLabel: true },
    xAxis: riskCategoryAxis({ data: groups.map(group => groupBy === 'age' ? group.label_zh.split('（')[0] : group.label_zh), axisLabel: { interval: 0, fontSize: 11, color: '#475569', margin: 12 } }),
    yAxis: riskValueAxis({ name: view.unit }),
    series: [{ type: 'bar', name: view.label_zh + '均值', barMaxWidth: 48, data: groups.map(group => finite(group.mean_prediction) ? group.mean_prediction : null),
      itemStyle: { color: (item: { dataIndex: number }) => (groupBy === 'gender' ? [RISK_PALETTE.blue, RISK_PALETTE.orange] : [RISK_PALETTE.green, RISK_PALETTE.blue, RISK_PALETTE.amber])[item.dataIndex % (groupBy === 'gender' ? 2 : 3)], borderRadius: [5, 5, 0, 0] }, label: { show: true, position: 'top', distance: 8, color: '#475569', fontSize: 11, fontWeight: 600, formatter: (item: any) => formatPredictionNumber(item.value) } }] }
}

export function cohortSummaryCsv(result: CohortPredictionResponse): string {
  const columns = ['file_id', 'analysis_scope', 'total_records', 'processed_records', 'skipped_records', 'target', 'label_zh', 'unit', 'estimated_count', 'withheld_count', 'mean', 'median', 'q1', 'q3', 'min', 'max', 'population_std', 'scope_note']
  const rows = result.summary.map(row => [result.file_id, result.analysis_scope, result.total_records, result.processed_records, result.skipped_records,
    row.target, row.label_zh, row.unit, row.estimated_count, row.withheld_count, row.statistics?.mean, row.statistics?.median, row.statistics?.q1,
    row.statistics?.q3, row.statistics?.min, row.statistics?.max, row.statistics?.std, PREDICTION_SCOPE_NOTE + ' 按上传文件全部有效对象未加权汇总；不是人群代表性估计。'])
  return '\uFEFF' + [columns, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n')
}
export function cohortRankingCsv(result: CohortPredictionResponse, target: string): string {
  const view = buildCohortView(result, target)
  const rows = view.rankings.map(row => [result.file_id, row.rank, row.row_number, row.person_id, target, view.label_zh, view.unit, row.prediction, '所选指标估计值降序；不是临床高危等级或疾病概率'])
  return '\uFEFF' + [['file_id', 'rank', 'row_number', 'person_id', 'target', 'label_zh', 'unit', 'prediction', 'note'], ...rows].map(row => row.map(csvCell).join(',')).join('\r\n')
}
