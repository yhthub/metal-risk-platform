import { MEASUREMENTS, INDIVIDUAL_REFERENCES, UNIT_OPTIONS, SAMPLE_OPTIONS } from './individualReferences'
import type { MeasurementKey, MeasurementMetadata, IndividualReference } from './individualReferences'

export type InputState = 'valid' | 'missing' | 'invalid'
export type ConditionState = 'pass' | 'missing' | 'incompatible' | 'pending'
export interface ProfileCondition { state: ConditionState; reason: string }
export interface IndividualMeasurement {
  key: MeasurementKey
  label: string
  raw: unknown
  value: number | null
  inputState: InputState
  metadata: MeasurementMetadata
  reference: IndividualReference | null
  convertedValue: number | null
  ratio: number | null
  offset: number | null
  reached: boolean | null
  comparisonLabel: string
  conditions: { input: ProfileCondition; sample: ProfileCondition; unit: ProfileCondition; reference: ProfileCondition }
}
export function parseMeasurement(raw: unknown): { state: InputState; value: number | null } {
  if (raw === null || raw === undefined || (typeof raw === 'string' && !raw.trim())) return { state: 'missing', value: null }
  if (typeof raw !== 'number' && typeof raw !== 'string') return { state: 'invalid', value: null }
  if (typeof raw === 'string' && !/^[+\-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+\-]?\d+)?$/.test(raw.trim())) return { state: 'invalid', value: null }
  const value = Number(raw)
  return Number.isFinite(value) && value >= 0 ? { state: 'valid', value } : { state: 'invalid', value: null }
}
/** Only same-sample volumetric mass units are interchangeable; no blood/urine or creatinine conversion. */
export function convertReferenceUnit(value: number, from: string, to: string): number | null {
  if (!Number.isFinite(value) || value < 0) return null
  const factors: Record<string, number> = { 'μg/L': 1, 'ng/mL': 1, 'μg/dL': 10 }
  if (!from || !to) return null
  const converted = from === to ? value : factors[from] && factors[to] ? value * factors[from] / factors[to] : NaN
  return Number.isFinite(converted) ? converted : null
}
const condition = (state: ConditionState, reason: string): ProfileCondition => ({ state, reason })
export function buildIndividualProfile(
  raw: Partial<Record<MeasurementKey, unknown>> & { age?: unknown },
  metadata: Record<MeasurementKey, MeasurementMetadata>,
  references: ReadonlyArray<IndividualReference> = INDIVIDUAL_REFERENCES
) {
  const age = parseMeasurement(raw.age)
  const rows: IndividualMeasurement[] = MEASUREMENTS.map(({ key, label }) => {
    const parsed = parseMeasurement(raw[key])
    const meta = { ...metadata[key] }
    const all = references.filter(ref => ref.key === key && Number.isFinite(ref.value) && ref.value > 0)
    const sampleMatches = all.filter(ref => ref.samples.includes(meta.sample))
    const unitMatches = sampleMatches.filter(ref => convertReferenceUnit(0, meta.unit, ref.unit) !== null)
    const applicable = unitMatches.filter(ref =>
      (!ref.adultOnly || (age.state === 'valid' && age.value! >= 18)) &&
      (!ref.context || ref.context === meta.context) && (!ref.analyte || ref.analyte === meta.analyte)
    )
    const reference = applicable.length === 1 ? applicable[0]! : null
    const pending = meta.confirmed === false && parsed.state === 'valid'
    const inputCondition = parsed.state === 'valid' ? condition('pass', '有限、非负实测值（真实零值有效）') :
      parsed.state === 'missing' ? condition('missing', '尚未录入；不当作零') : condition('incompatible', '须为有限的非负数')
    const sampleCondition = !meta.sample ? condition('missing', '样本类型未指定') : !SAMPLE_OPTIONS.some(item => item.value === meta.sample) ? condition('incompatible', '未知样本类型') : pending ? condition('pending', '口径变化后须确认原数值') :
      all.length && !sampleMatches.length ? condition('incompatible', '该样本无匹配参考') : condition('pass', '样本已明确')
    const unitCondition = !meta.unit ? condition('missing', '单位未指定') : pending ? condition('pending', '口径变化后须确认原数值') :
      !UNIT_OPTIONS.includes(meta.unit) || (sampleMatches.length > 0 && !unitMatches.length) ? condition('incompatible', '单位不匹配；不擅自肌酐/质量摩尔换算') : condition('pass', '单位已明确')
    let referenceCondition: ProfileCondition
    if (pending) referenceCondition = condition('pending', '须确认当前数值的样本、单位与情境')
    else if (!all.length) referenceCondition = condition('missing', '本登记表暂无该指标的匹配参考，不硬填阈值')
    else if (sampleCondition.state !== 'pass' || unitCondition.state !== 'pass') referenceCondition = condition('incompatible', '请先满足样本与单位条件')
    else if (!reference) {
      const reasons = unitMatches.flatMap(ref => [
        ref.adultOnly && !(age.state === 'valid' && age.value! >= 18) ? '须明确年龄≥18岁' : '',
        ref.context && ref.context !== meta.context ? '须明确适用职业/住宅年均情境' : '',
        ref.analyte && ref.analyte !== meta.analyte ? '须明确为分型毒性砷（非总砷）' : ''
      ]).filter(Boolean)
      referenceCondition = condition('incompatible', [...new Set(reasons)].join('；') || '没有唯一适用参考')
    } else referenceCondition = condition('pass', `${reference.title}；${reference.boundary === 'gt' ? '严格大于' : '大于或等于'} ${reference.value} ${reference.unit}`)
    let convertedValue: number | null = null
    let ratio: number | null = null
    let offset: number | null = null
    let reached: boolean | null = null
    if (parsed.state === 'valid' && referenceCondition.state === 'pass' && reference) {
      convertedValue = convertReferenceUnit(parsed.value!, meta.unit, reference.unit)
      const candidate = convertedValue === null ? NaN : convertedValue / reference.value * 100
      if (Number.isFinite(candidate)) {
        ratio = candidate
        offset = candidate - 100
        reached = reference.boundary === 'gt' ? convertedValue! > reference.value : convertedValue! >= reference.value
      } else referenceCondition = condition('incompatible', '换算/比例超出有限数值范围，保留原始输入')
    }
    const comparisonLabel = pending ? '待确认数值口径' : parsed.state !== 'valid' ? inputCondition.reason : ratio === null ? referenceCondition.reason :
      reached ? (reference!.boundary === 'gt' ? '超过该参考值（>）' : '达到或超过该参考值（≥）') : '未触发该参考边界（不表示安全）'
    return { key, label, raw: raw[key], value: parsed.value, inputState: parsed.state, metadata: meta, reference,
      convertedValue, ratio, offset, reached, comparisonLabel,
      conditions: { input: inputCondition, sample: sampleCondition, unit: unitCondition, reference: referenceCondition } }
  })
  const valid = rows.filter(row => row.inputState === 'valid').length
  const missing = rows.filter(row => row.inputState === 'missing').length
  const comparable = rows.filter(row => row.ratio !== null)
  const denominator = MEASUREMENTS.length
  return {
    rows, comparable, sorted: [...comparable].sort((a, b) => b.ratio! - a.ratio!),
    counts: { total: denominator, valid, missing, invalid: denominator - valid - missing, comparable: comparable.length },
    coverage: valid === 0 ? null : comparable.length / valid * 100,
    scaleMax: Math.max(150, ...comparable.map(row => row.ratio!))
  }
}
