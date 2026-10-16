/** Local NHANES contract. No storage, network or simulated inference. */
export type MetalKey = 'pb' | 'cd' | 'hg'
export type NumericInput = number | '' | null
export interface PredictionMeasurement { sample: string; unit: string; analyte: string; confirmed: boolean }
export interface PredictionCovariates { education: string | null; marital: string | null; smoking: string | null; alcohol_any_past_year: boolean | null }
export interface PredictionRequest {
  person: { id?: string; age: number | null; gender: 'male' | 'female' | null; gender_confirmed: boolean; bmi: number | null; pb: number | null; cd: number | null; hg: number | null }
  measurements: Record<MetalKey, PredictionMeasurement>
  covariates: PredictionCovariates
}
export interface PredictionDraft extends Omit<PredictionRequest, 'person'> {
  person: Omit<PredictionRequest['person'], 'age' | 'bmi' | MetalKey> & { age: NumericInput; bmi: NumericInput; pb: NumericInput; cd: NumericInput; hg: NumericInput }
}
export interface PredictionOutcome {
  target: string; label_zh: string; unit: string; prediction: number | null; status: string; reason?: string
  reference_interval: { lower: number; upper: number; nominal_calibration_level: number; guaranteed_coverage: false; heldout_empirical_coverage?: number } | null
  test_metrics: { MAE: number; RMSE: number; R2: number; n: number }
  selection_R2: number; model_family: string[]; candidate_id: string
}
export interface PredictionResponse {
  model_version: string; run_id: string; profile: string; person_id: string; status: string; scope: string
  results: PredictionOutcome[]; warnings: string[]; measurement_audit?: unknown; encoded_input?: unknown; provenance?: unknown
}
/** Cohort results share model metadata once instead of repeating it for every person. */
export type BatchPredictionOutcome = Pick<PredictionOutcome, 'target' | 'label_zh' | 'unit' | 'prediction' | 'status' | 'reason'> & Partial<Omit<PredictionOutcome, 'target' | 'label_zh' | 'unit' | 'prediction' | 'status' | 'reason'>>
export interface PredictionStatus { ready: boolean; model_version: string; run_id: string; profile: string; target_count: number; estimate_target_count: number; withheld_target_count: number; reason?: string; contract?: unknown }
export interface BatchPredictionResponse {
  model_version: string; run_id: string; profile: string; file_id: string; total_records: number; offset: number; limit: number; processed_records: number; skipped_records: number; has_more: boolean
  records: Array<{ row_number: number; person_id: string; status: string; reason?: string; results?: BatchPredictionOutcome[] | null; input?: PredictionRequest }>
  summary: Array<{ target: string; label_zh: string; unit: string; estimated_count: number; mean_prediction: number | null; withheld_count: number }>
  warnings: string[]
}
export const METAL_FIELDS: ReadonlyArray<{ key: MetalKey; label: string; analyte: string; unit: string }> = [
  { key: 'pb', label: '全血铅 Pb', analyte: 'lead', unit: 'ug/dL' }, { key: 'cd', label: '全血镉 Cd', analyte: 'cadmium', unit: 'ug/L' }, { key: 'hg', label: '全血总汞 Hg', analyte: 'total_mercury', unit: 'ug/L' }
]
export const EDUCATION_OPTIONS = [
  { value: 'less_than_grade9', label: '美国年级定义：低于 9 年级' }, { value: 'grade9_11', label: '9–11 年级（未高中毕业）' }, { value: 'high_school_ged', label: '高中毕业 / GED' }, { value: 'some_college_aa', label: '部分大学教育 / AA 学位' }, { value: 'college_or_above', label: '大学毕业及以上' }
]
export const MARITAL_OPTIONS = [{ value: 'married', label: '已婚' }, { value: 'widowed', label: '丧偶' }, { value: 'divorced', label: '离婚' }, { value: 'separated', label: '分居' }, { value: 'never_married', label: '从未结婚' }, { value: 'living_with_partner', label: '与伴侣同居' }]
export const SMOKING_OPTIONS = [{ value: 'less_than_100_lifetime', label: '终生吸烟少于 100 支' }, { value: 'former', label: '终生至少 100 支，目前已戒烟' }, { value: 'current', label: '终生至少 100 支，目前仍吸烟' }]
export const PREDICTION_SCOPE_NOTE = '基于 NHANES 公开横断面数据的当次生理 / 生化指标估计，不是未来发病概率、临床诊断或重金属的因果效应。美国一般人群模型向中国职业暴露人群的适用性尚未验证。'
export const INTERVAL_NOTE = '探索性残差范围：来自历史校准误差，不保证个体覆盖率，不是临床正常范围，也不是可靠的 90% 置信区间。'
export function createPredictionDraft(): PredictionDraft {
  return { person: { id: '', age: null, gender: null, gender_confirmed: false, bmi: null, pb: null, cd: null, hg: null }, measurements: { pb: { sample: '', unit: '', analyte: '', confirmed: false }, cd: { sample: '', unit: '', analyte: '', confirmed: false }, hg: { sample: '', unit: '', analyte: '', confirmed: false } }, covariates: { education: null, marital: null, smoking: null, alcohol_any_past_year: null } }
}
export function clonePrediction<T>(value: T): T { return JSON.parse(JSON.stringify(value)) as T }
export function parsePredictionNumber(value: unknown): number | null {
  if (value === null || value === undefined || (typeof value === 'string' && value.trim() === '')) return null
  if (typeof value !== 'number' && typeof value !== 'string') return null
  if (typeof value === 'string' && !/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$/.test(value.trim())) return null
  const result = Number(value)
  return Number.isFinite(result) ? result : null
}
export function buildPredictionRequest(draft: PredictionDraft): { payload: PredictionRequest; errors: string[] } {
  const payload = clonePrediction(draft) as PredictionRequest
  for (const key of ['age', 'bmi', 'pb', 'cd', 'hg'] as const) payload.person[key] = parsePredictionNumber(draft.person[key])
  const errors: string[] = []
  const p = payload.person
  if (p.age === null || !Number.isInteger(p.age) || p.age < 18 || p.age > 80) errors.push('请输入 18–80 岁整数年龄；80 岁为 NHANES 顶码，超过 80 岁不能按 80 岁录入。')
  if (!['male', 'female'].includes(p.gender || '') || p.gender_confirmed !== true) errors.push('请选择并核对训练口径对应的生理性别。')
  if (p.bmi === null || p.bmi <= 0) errors.push('BMI 必须是大于 0 的实测值。')
  for (const metal of METAL_FIELDS) if (p[metal.key] === null || (p[metal.key] as number) < 0) errors.push(`${metal.label}须填写有限、非负实测值，缺测不能填 0。`)
  errors.push(...measurementErrors(payload.measurements))
  return { payload, errors }
}
export function measurementErrors(measurements: Record<MetalKey, PredictionMeasurement>): string[] {
  const errors: string[] = []
  for (const metal of METAL_FIELDS) {
    const metadata = measurements[metal.key]
    if (metadata.sample !== 'whole_blood') errors.push(`${metal.label}仅接受全血样本，不能使用血清或尿样。`)
    if (!['ug/L', 'ug/dL', 'μg/L', 'μg/dL', 'µg/L', 'µg/dL', 'ng/mL'].includes(metadata.unit)) errors.push(`${metal.label}请选择原始报告单位。`)
    if (metadata.analyte !== metal.analyte || metadata.confirmed !== true) errors.push(`请核对${metal.label}的分析物、样本和单位。`)
  }
  return errors
}
export function formatPredictionNumber(value: unknown, digits = 2): string { return typeof value === 'number' && Number.isFinite(value) ? value.toLocaleString('zh-CN', { maximumFractionDigits: digits }) : '—' }
export function predictionHasValue(row: Pick<PredictionOutcome, 'status' | 'prediction'>): boolean { return row.status === 'EXPLORATORY_ESTIMATE' && typeof row.prediction === 'number' && Number.isFinite(row.prediction) }
export function predictionStatusLabel(row: PredictionOutcome): string { return predictionHasValue(row) ? '探索性估计' : '暂不出值' }
export function predictionIntervalLabel(row: PredictionOutcome): string { return predictionHasValue(row) && row.reference_interval ? `${formatPredictionNumber(row.reference_interval.lower)} – ${formatPredictionNumber(row.reference_interval.upper)} ${row.unit}` : '—' }
export function predictionReason(row: Pick<PredictionOutcome, 'reason'>): string { return row.reason || '跨年份验证表现不足，当前默认不提供数值；不是该项指标正常或异常的判断。' }
export function csvCell(value: unknown): string {
  let text = value === null || value === undefined ? '' : String(value)
  if (typeof value === 'string' && /^[\s\uFEFF]*[=+\-@]/.test(text)) text = "'" + text
  return '"' + text.replace(/"/g, '""') + '"'
}
export function predictionCsv(result: PredictionResponse): string {
  const columns = ['person_id', 'model_version', 'run_id', 'target', 'label_zh', 'unit', 'prediction', 'status', 'reason', 'exploratory_lower', 'exploratory_upper', 'test_MAE', 'test_RMSE', 'test_R2', 'test_n', 'scope_note', 'interval_note']
  const rows = result.results.map(row => [result.person_id, result.model_version, result.run_id, row.target, row.label_zh, row.unit, predictionHasValue(row) ? row.prediction : null, row.status, predictionHasValue(row) ? '' : predictionReason(row), predictionHasValue(row) ? row.reference_interval?.lower : null, predictionHasValue(row) ? row.reference_interval?.upper : null, row.test_metrics?.MAE, row.test_metrics?.RMSE, row.test_metrics?.R2, row.test_metrics?.n, PREDICTION_SCOPE_NOTE, INTERVAL_NOTE])
  return '\uFEFF' + [columns, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n')
}
export function predictionJson(request: PredictionRequest, result: PredictionResponse): string { return JSON.stringify({ exported_at: new Date().toISOString(), input: request, result, notes: [PREDICTION_SCOPE_NOTE, INTERVAL_NOTE] }, null, 2) }
export function batchPredictionCsv(result: BatchPredictionResponse): string {
  const columns = ['file_id', 'model_version', 'run_id', 'row_number', 'person_id', 'record_status', 'record_reason', 'target', 'label_zh', 'unit', 'prediction', 'outcome_status', 'outcome_reason', 'exploratory_lower', 'exploratory_upper', 'test_MAE', 'scope_note', 'interval_note']
  const rows = result.records.flatMap(record => record.results?.length ? record.results.map(row => [result.file_id, result.model_version, result.run_id, record.row_number, record.person_id, record.status, record.reason, row.target, row.label_zh, row.unit, predictionHasValue(row) ? row.prediction : null, row.status, predictionHasValue(row) ? '' : predictionReason(row), predictionHasValue(row) ? row.reference_interval?.lower : null, predictionHasValue(row) ? row.reference_interval?.upper : null, row.test_metrics?.MAE, PREDICTION_SCOPE_NOTE, INTERVAL_NOTE]) : [[result.file_id, result.model_version, result.run_id, record.row_number, record.person_id, record.status, record.reason, '', '', '', null, '', '', null, null, null, PREDICTION_SCOPE_NOTE, INTERVAL_NOTE]])
  return '\uFEFF' + [columns, ...rows].map(row => row.map(csvCell).join(',')).join('\r\n')
}
export function downloadPrediction(content: string, format: 'csv' | 'json', filenamePrefix = 'NHANES_individual_prediction'): void {
  if (typeof document === 'undefined') return
  const url = URL.createObjectURL(new Blob([content], { type: format === 'csv' ? 'text/csv;charset=utf-8' : 'application/json;charset=utf-8' }))
  const safePrefix = filenamePrefix.replace(/[^A-Za-z0-9_.-]+/g, '_') || 'NHANES_prediction'
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${safePrefix}_${new Date().toISOString().slice(0, 10)}.${format}`; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
