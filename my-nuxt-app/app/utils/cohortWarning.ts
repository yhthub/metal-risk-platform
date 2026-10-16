/** Batch-relative prioritisation only. Reuses saved estimates; never reruns or relaxes a model. */
import { cohortResponseError } from './riskCohort'
import type { CohortPredictionResponse } from './riskCohort'
import type { ChartOption } from './riskDashboard'
import { csvCell, formatPredictionNumber, predictionHasValue } from './riskPrediction'
import { RISK_PALETTE, rankingGradient } from './riskPalette'

export type WarningDirection = 'HIGH' | 'LOW'
export type CohortWarningStatus = 'ALERT' | 'CLEAR' | 'INSUFFICIENT_DATA'
export interface CohortWarningOutcome {
  target: string; label_zh: string; unit: string; value: number | null; rank: number | null
  percentile: number | null; direction: WarningDirection; status: string; reason: string
}
export interface CohortWarningRow {
  row_number: number; display_id: string; person_id: string; status: 'EVALUATED' | 'NOT_EVALUATED'
  score: number | null; rank: number | null; is_warning: boolean; used_count: number; threshold: number | null
  reason: string; outcomes: CohortWarningOutcome[]
}
export interface CohortWarning {
  algorithm_version: string
  status: CohortWarningStatus; file_id: string; total_records: number; eligible_count: number
  evaluated_count: number; not_evaluated_count: number; warning_count: number
  percentage: number | null; total_percentage: number | null; threshold: number | null; threshold_valid: boolean
  available_outcome_count: number; expected_outcome_count: 12; min_outcome_count: number; min_cohort_size: number
  max_score: number | null; reason: string; scope_note: string
  excluded_targets: Array<{ target: string; label_zh: string; reason: string }>
  rows: CohortWarningRow[]; rankings: CohortWarningRow[]
}

/** Same 12 target identifiers as backend nhanes_prediction_service.TARGETS / frozen v5 registry. */
export const COHORT_WARNING_TARGETS: ReadonlyArray<{ target: string; label_zh: string; unit: string; direction: WarningDirection }> = [
  { target: 'sbp', label_zh: '收缩压', unit: 'mmHg', direction: 'HIGH' },
  { target: 'dbp', label_zh: '舒张压', unit: 'mmHg', direction: 'HIGH' },
  { target: 'serum_creatinine_mg_dl', label_zh: '血清肌酐', unit: 'mg/dL', direction: 'HIGH' },
  { target: 'bun_mg_dl', label_zh: '尿素氮', unit: 'mg/dL', direction: 'HIGH' },
  { target: 'uric_acid_mg_dl', label_zh: '尿酸', unit: 'mg/dL', direction: 'HIGH' },
  { target: 'uacr_mg_g', label_zh: '尿白蛋白肌酐比', unit: 'mg/g', direction: 'HIGH' },
  { target: 'hba1c_percent', label_zh: '糖化血红蛋白HbA1c', unit: 'percent', direction: 'HIGH' },
  { target: 'total_cholesterol_mg_dl', label_zh: '总胆固醇', unit: 'mg/dL', direction: 'HIGH' },
  { target: 'hdl_cholesterol_mg_dl', label_zh: 'HDL胆固醇', unit: 'mg/dL', direction: 'LOW' },
  { target: 'alt_u_l', label_zh: '丙氨酸氨基转移酶ALT', unit: 'U/L', direction: 'HIGH' },
  { target: 'ast_u_l', label_zh: '天冬氨酸氨基转移酶AST', unit: 'U/L', direction: 'HIGH' },
  { target: 'ggt_u_l', label_zh: '谷氨酰转移酶GGT', unit: 'U/L', direction: 'HIGH' },
]
export const COHORT_WARNING_SCOPE_NOTE = '批次内相对预警：各共同可用结局按方向计算全群并列平均名次和百分位，再等权平均；HDL按低值端，其余指标按高值端。仅用于本批次优先复核，不是疾病概率、临床高危诊断或重金属因果效应；未达阈值不代表无健康风险。'
export const COHORT_WARNING_ALGORITHM_VERSION = 'cohort_relative_midrank_v1'
const MIN_COHORT_SIZE = 5
const MIN_OUTCOME_COUNT = 3
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value)
const html = (value: unknown) => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')

/** Stable within the uploaded file, independent of external identifiers and chart rank. */
export function cohortDisplayId(rowNumber: number): string {
  return Number.isSafeInteger(rowNumber) && rowNumber > 0 ? 'P-' + String(rowNumber).padStart(6, '0') : 'P-UNKNOWN'
}

/** O(T * N log N). All people use the same common dimensions and denominator; missing is never zero.
 * The default 80 is a configurable product-screening choice, not a clinically established cutoff.
 */
export function buildCohortWarning(result: CohortPredictionResponse, threshold = 80): CohortWarning {
  const thresholdValid = finite(threshold) && threshold >= 0 && threshold <= 100
  const safeThreshold = thresholdValid ? threshold : null
  const rawRecords = Array.isArray(result?.records) ? result.records : []
  const rawSummaries = Array.isArray(result?.summary) ? result.summary : []
  const validShape = object(result) && Array.isArray(result.records) && Array.isArray(result.summary)
    && rawRecords.every(record => object(record) && (record.results == null || (Array.isArray(record.results) && record.results.every(object)))
      && (record.input == null || object(record.input))) && rawSummaries.every(object)
  const records: CohortPredictionResponse['records'] = rawRecords.map((record, index) => object(record) ? record : {
    row_number: index + 1, person_id: '', status: 'CORRUPTED_INPUT', reason: '原始结果记录结构损坏，未参与评估。', results: null,
  })
  const summaries = new Map(rawSummaries.filter(object).map(row => [row.target, row]))
  const rows: CohortWarningRow[] = records.map(record => {
    const saved = new Map((Array.isArray(record.results) ? record.results : []).filter(object).map(row => [row.target, row]))
    const eligible = record.status === 'ESTIMATES_NOT_DIAGNOSES' && !!record.input
    return { row_number: record.row_number, display_id: cohortDisplayId(record.row_number), person_id: record.person_id,
      status: 'NOT_EVALUATED', score: null, rank: null, is_warning: false, used_count: 0, threshold: safeThreshold,
      reason: eligible ? '' : record.reason || '该对象不满足模型必需输入，未参与综合排序。',
      outcomes: COHORT_WARNING_TARGETS.map(definition => {
        const savedOutcome = saved.get(definition.target); const summary = summaries.get(definition.target)
        const valid = eligible && !!savedOutcome && predictionHasValue(savedOutcome)
        return { target: definition.target, label_zh: summary?.label_zh || definition.label_zh, unit: summary?.unit || definition.unit,
          value: valid ? savedOutcome!.prediction : null, rank: null, percentile: null, direction: definition.direction,
          status: savedOutcome?.status || (eligible ? 'MISSING_RESULT' : 'INPUT_NOT_ELIGIBLE'),
          reason: valid ? '' : savedOutcome?.reason || record.reason || '暂无可用模型估计，不能按零值参与排序。' }
      }) }
  })
  const eligibleRows = rows.filter((_, index) => records[index]?.status === 'ESTIMATES_NOT_DIAGNOSES' && !!records[index]?.input)
  let contractError = validShape ? cohortResponseError(result) : '群体结果基本结构损坏或不完整，未生成综合预警。'
  if (!contractError && (summaries.size !== COHORT_WARNING_TARGETS.length || COHORT_WARNING_TARGETS.some(row => !summaries.has(row.target))))
    contractError = '结局标识与已部署的12项模型不一致，未生成综合预警。'
  const commonIndices: number[] = []
  const excluded: CohortWarning['excluded_targets'] = []
  for (let index = 0; index < COHORT_WARNING_TARGETS.length; index++) {
    const definition = COHORT_WARNING_TARGETS[index]!
    const invalid = eligibleRows.find(row => !finite(row.outcomes[index]!.value))
    let reason = ''
    if (contractError) reason = contractError
    else if (!eligibleRows.length) reason = '没有满足输入要求的对象。'
    else if (invalid) reason = invalid.outcomes[index]!.reason || '部分有效输入对象没有可用估计；为保持相同维度和分母，本项整体不参与综合分。'
    else if (eligibleRows.length < MIN_COHORT_SIZE) reason = '有效对象少于5人，不能稳定计算本批次相对预警。'
    if (reason) {
      excluded.push({ target: definition.target, label_zh: summaries.get(definition.target)?.label_zh || definition.label_zh, reason })
      for (const row of rows) if (!row.outcomes[index]!.reason) row.outcomes[index]!.reason = reason
      continue
    }
    commonIndices.push(index)
    const ordered = eligibleRows.slice().sort((a, b) => (definition.direction === 'HIGH' ? -1 : 1) * (a.outcomes[index]!.value! - b.outcomes[index]!.value!) || a.row_number - b.row_number)
    for (let start = 0; start < ordered.length;) {
      let end = start + 1
      while (end < ordered.length && ordered[end]!.outcomes[index]!.value === ordered[start]!.outcomes[index]!.value) end++
      const rank = (start + 1 + end) / 2
      const percentile = 100 * (ordered.length - rank) / (ordered.length - 1)
      for (let cursor = start; cursor < end; cursor++) Object.assign(ordered[cursor]!.outcomes[index]!, { rank, percentile })
      start = end
    }
  }
  let insufficientReason = !thresholdValid ? '预警阈值须为0至100之间的有限数值，当前未生成预警。' : contractError || ''
  if (!insufficientReason && eligibleRows.length < MIN_COHORT_SIZE) insufficientReason = '有效对象不足5人，暂不能判定本批次相对预警；不能解释为无人高危。'
  if (!insufficientReason && commonIndices.length < MIN_OUTCOME_COUNT) insufficientReason = '共同可用结局不足3项，暂不能形成综合预警；未出值的结局没有按零值处理。'
  if (!insufficientReason) {
    for (const row of eligibleRows) {
      // Average mid-ranks first: half-integer rank sums preserve mathematical ties across target permutations.
      const sumRanks = commonIndices.reduce((sum, index) => sum + row.outcomes[index]!.rank!, 0)
      row.score = 100 * (eligibleRows.length * commonIndices.length - sumRanks) / ((eligibleRows.length - 1) * commonIndices.length)
      row.status = 'EVALUATED'; row.used_count = commonIndices.length; row.is_warning = row.score >= safeThreshold!
      row.reason = row.is_warning ? '达到本批次综合相对预警阈值，建议优先复核。' : '未达到本批次综合相对预警阈值，不代表临床无风险。'
    }
  } else for (const row of eligibleRows) row.reason = insufficientReason
  const rankings = rows.filter(row => row.status === 'EVALUATED').sort((a, b) => b.score! - a.score! || a.row_number - b.row_number)
  for (let start = 0; start < rankings.length;) {
    let end = start + 1
    while (end < rankings.length && rankings[end]!.score === rankings[start]!.score) end++
    const rank = (start + 1 + end) / 2
    for (let cursor = start; cursor < end; cursor++) rankings[cursor]!.rank = rank
    start = end
  }
  const count = rankings.reduce((sum, row) => sum + Number(row.is_warning), 0)
  const total = Number.isInteger(result?.total_records) && result.total_records >= 0 ? result.total_records : records.length
  const status: CohortWarningStatus = insufficientReason ? 'INSUFFICIENT_DATA' : count ? 'ALERT' : 'CLEAR'
  return { algorithm_version: COHORT_WARNING_ALGORITHM_VERSION, status, file_id: result?.file_id || '', total_records: total, eligible_count: eligibleRows.length,
    evaluated_count: rankings.length, not_evaluated_count: Math.max(0, total - rankings.length), warning_count: count,
    percentage: rankings.length ? 100 * count / rankings.length : null, total_percentage: rankings.length && total ? 100 * count / total : null,
    threshold: safeThreshold, threshold_valid: thresholdValid, available_outcome_count: commonIndices.length, expected_outcome_count: 12,
    min_outcome_count: MIN_OUTCOME_COUNT, min_cohort_size: MIN_COHORT_SIZE, max_score: rankings[0]?.score ?? null,
    reason: insufficientReason || (count ? '本批次有' + count + '人达到综合相对预警阈值，建议优先复核。' : '本批次暂无达到综合阈值的预警对象；未达阈值不代表无健康风险。'),
    scope_note: COHORT_WARNING_SCOPE_NOTE, excluded_targets: excluded, rows, rankings }
}

/** Only flagged rows enter the warning chart; Top-N is a display limit, never an evaluation limit. */
export function buildWarningRankOption(warning: CohortWarning, limit = 10): ChartOption | null {
  if (warning.status !== 'ALERT') return null
  const displayLimit = finite(limit) ? Math.max(1, Math.min(50, Math.floor(limit))) : 10
  const rows = warning.rankings.filter(row => row.is_warning).slice(0, displayLimit)
  if (!rows.length) return null
  return { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: Array<{ dataIndex: number }>) => params.map(item => {
    const row = rows[item.dataIndex]
    return row ? html(row.display_id) + '<br/>原始编号：' + html(row.person_id) + '<br/>综合相对分：' + formatPredictionNumber(row.score) + ' / 100<br/>综合名次：' + formatPredictionNumber(row.rank, 1) + '<br/>参与结局：' + row.used_count + ' / 12<br/>批次内相对排序，非疾病概率或临床高危诊断' : ''
  }).join('<br/>') }, grid: { left: '3%', right: '12%', top: '5%', bottom: '15%', containLabel: true },
    xAxis: { type: 'value', min: 0, max: 100, name: '综合相对分', nameLocation: 'middle', nameGap: 28, splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: { type: 'category', inverse: true, data: rows.map(row => row.display_id), axisTick: { show: false }, axisLabel: { width: 90, overflow: 'truncate' } },
    series: [{ type: 'bar', name: '综合相对分', data: rows.map(row => row.score), barMaxWidth: 26,
      itemStyle: { color: rankingGradient(), borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', color: RISK_PALETTE.red, formatter: (item: { value: number }) => formatPredictionNumber(item.value) } }] }
}

/** Warning proportion has an explicit evaluated-person denominator, not the upload or a fake probability. */
export function buildWarningShareOption(warning: CohortWarning): ChartOption | null {
  if (warning.status === 'INSUFFICIENT_DATA' || warning.percentage === null) return null
  const color = warning.status === 'ALERT' ? RISK_PALETTE.red : RISK_PALETTE.green
  return { tooltip: { trigger: 'item', formatter: (item: { name: string; value: number }) => html(item.name) + '：' + item.value + '人<br/>分母：已评估' + warning.evaluated_count + '人；未评估' + warning.not_evaluated_count + '人另列<br/>批次内相对预警，不是疾病概率' },
    graphic: [{ type: 'text', left: 'center', top: '42%', style: { text: formatPredictionNumber(warning.percentage, 1) + '%', fill: color, fontSize: 29, fontWeight: 700, textAlign: 'center' } },
      { type: 'text', left: 'center', top: '58%', style: { text: warning.warning_count + ' / ' + warning.evaluated_count + ' 人', fill: '#64748B', fontSize: 12, textAlign: 'center' } }],
    series: [{ type: 'pie', radius: ['64%', '83%'], center: ['50%', '50%'], startAngle: 90, label: { show: false }, labelLine: { show: false },
      data: [{ name: '达到相对预警阈值', value: warning.warning_count, itemStyle: { color } },
        { name: '未达到相对预警阈值', value: warning.evaluated_count - warning.warning_count, itemStyle: { color: '#E5EDF7' } }] }] }
}

/** Long format preserves every uploaded row and every target, including withheld and excluded dimensions. */
export function warningRankingCsv(warning: CohortWarning): string {
  const columns = ['algorithm_version', 'file_id', 'row_number', 'display_id', 'original_person_id', 'evaluation_status', 'composite_rank', 'composite_score', 'threshold', 'is_warning', 'used_outcome_count', 'evaluated_count', 'total_records', 'target', 'label_zh', 'unit', 'estimate', 'direction', 'target_rank', 'target_percentile', 'outcome_status', 'outcome_reason', 'not_evaluated_reason', 'scope_note']
  const lines = [columns.map(csvCell).join(',')]
  const exclusions = new Map(warning.excluded_targets.map(row => [row.target, row.reason]))
  for (const row of warning.rows) for (const outcome of row.outcomes) lines.push([
    warning.algorithm_version, warning.file_id, row.row_number, row.display_id, row.person_id, row.status, row.rank, row.score, warning.threshold_valid ? warning.threshold : null,
    row.status === 'EVALUATED' ? row.is_warning : null, row.used_count, warning.evaluated_count, warning.total_records,
    outcome.target, outcome.label_zh, outcome.unit, outcome.value, outcome.direction, outcome.rank, outcome.percentile, outcome.status,
    outcome.reason || exclusions.get(outcome.target) || '', row.status === 'NOT_EVALUATED' ? row.reason : '', warning.scope_note,
  ].map(csvCell).join(','))
  return '\uFEFF' + lines.join('\r\n')
}
