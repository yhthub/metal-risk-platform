/** Frozen, source-specific comparison references. Not diagnostic or universal safe limits. */
export const REFERENCE_RETRIEVED_AT = '2026-10-11'
export type MeasurementKey = 'pb' | 'cd' | 'hg' | 'th' | 'li' | 'cr' | 'ni' | 'co' | 'as' | 'rn'
export type SampleType = '' | 'whole_blood' | 'serum' | 'urine' | 'random_urine' | 'indoor_air'
export type ReferenceContext = '' | 'occupational_cadmium' | 'occupational_mercury_stable' | 'residential_annual' | 'other'
export type AnalyteType = '' | 'total' | 'toxic_speciated' | 'total_mercury'
export interface MeasurementMetadata {
  sample: SampleType
  unit: string
  context: ReferenceContext
  analyte: AnalyteType
  confirmed: boolean
}
export interface IndividualReference {
  id: string
  key: MeasurementKey
  samples: readonly SampleType[]
  unit: string
  value: number
  boundary: 'gte' | 'gt'
  adultOnly?: boolean
  context?: ReferenceContext
  analyte?: AnalyteType
  kind: string
  title: string
  note: string
  source: string
}
export const MEASUREMENTS: ReadonlyArray<{ key: MeasurementKey; label: string }> = [
  { key: 'pb', label: 'Pb (铅)' }, { key: 'cd', label: 'Cd (镉)' },
  { key: 'hg', label: 'Hg (汞)' }, { key: 'th', label: 'Th (钍)' },
  { key: 'li', label: 'Li (锂)' }, { key: 'cr', label: 'Cr (铬)' },
  { key: 'ni', label: 'Ni (镍)' }, { key: 'co', label: 'Co (钴)' },
  { key: 'as', label: 'As (砷)' }, { key: 'rn', label: 'Rn (氡)' }
]
export const SAMPLE_OPTIONS = [
  { value: '', label: '样本未指定' }, { value: 'whole_blood', label: '全血' },
  { value: 'serum', label: '血清' }, { value: 'urine', label: '尿（采样方式未限定）' },
  { value: 'random_urine', label: '随机尿' }, { value: 'indoor_air', label: '室内空气' }
]
export const UNIT_OPTIONS = ['', 'μg/L', 'ng/mL', 'μg/dL', 'μg/g Cr', 'μmol/mol Cr', 'μg/g', 'Bq/m³']
export const INDIVIDUAL_REFERENCES: ReadonlyArray<IndividualReference> = [
  {
    id: 'cdc-adult-bll', key: 'pb', samples: ['whole_blood'], unit: 'μg/L', value: 35, boundary: 'gte', adultOnly: true,
    kind: 'elevated_blood_lead_reference', title: 'CDC/CSTE 成人血铅升高参考',
    note: '35 μg/L 等于 3.5 μg/dL；仅对成人全血比较，不是安全线或中国法定限值。',
    source: 'https://www.cdc.gov/niosh/lead/bll-reference/index.html'
  },
  {
    id: 'osha-cd-blood', key: 'cd', samples: ['whole_blood'], unit: 'μg/L', value: 5, boundary: 'gt', adultOnly: true,
    context: 'occupational_cadmium', kind: 'occupational_biological_monitoring_reference', title: 'OSHA 职业镉全血监测行动参考',
    note: '须明确属于职业镉生物监测；仅在严格大于参考值时标记超过，不由工种自动推定。',
    source: 'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1027'
  },
  {
    id: 'osha-cd-urine', key: 'cd', samples: ['urine', 'random_urine'], unit: 'μg/g Cr', value: 3, boundary: 'gt', adultOnly: true,
    context: 'occupational_cadmium', kind: 'occupational_biological_monitoring_reference', title: 'OSHA 职业镉肌酐校正尿监测行动参考',
    note: '必须是已按肌酐校正的尿镉；不把 μg/L 或含义未明的 μg/g 自动校正。',
    source: 'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1027'
  },
  {
    id: 'mayo-hg-blood', key: 'hg', samples: ['whole_blood'], unit: 'μg/L', value: 10, boundary: 'gte',
    kind: 'laboratory_reference_upper_bound', title: 'Mayo 全血汞实验室参考上界',
    note: '10 ng/mL 等于 10 μg/L；实验室参考比较，不是中毒诊断或通用安全限值。',
    source: 'https://pediatric.testcatalog.org/show/HG'
  },
  {
    id: 'hse-hg-urine', key: 'hg', samples: ['random_urine'], unit: 'μmol/mol Cr', value: 20, boundary: 'gte', adultOnly: true,
    context: 'occupational_mercury_stable', kind: 'biological_monitoring_guidance_value', title: 'HSE 职业汞随机尿生物监测指导值',
    note: '须确认成人、中长期较稳定职业汞接触及随机尿；只按 μmol/mol Cr 精确比较，到达参考不代表行动判断。',
    source: 'https://books.hse.gov.uk/product/9780717667895'
  },
  {
    id: 'mayo-toxic-as-urine', key: 'as', samples: ['random_urine'], unit: 'μg/L', value: 35, boundary: 'gte',
    analyte: 'toxic_speciated', kind: 'laboratory_speciated_arsenic_reference', title: 'Mayo 随机尿毒性砷参考',
    note: '仅适用于已分型的无机砷与甲基化砷合计；总砷、未知分析物及 μg/g Cr 不套用。',
    source: 'https://mml.testcatalog.org/show/SPAS'
  },
  {
    id: 'who-residential-radon', key: 'rn', samples: ['indoor_air'], unit: 'Bq/m³', value: 100, boundary: 'gte',
    context: 'residential_annual', kind: 'residential_annual_reference_level', title: 'WHO 住宅室内氡年均参考',
    note: '仅比较住宅室内年平均浓度；不能用于普通工作场所、瞬时读数或人体样本。',
    source: 'https://www.who.int/news-room/fact-sheets/detail/radon-and-health'
  }
]
export function createIndividualMetadata(): Record<MeasurementKey, MeasurementMetadata> {
  return Object.fromEntries(MEASUREMENTS.map(({ key }) => [key, { sample: '', unit: '', context: '', analyte: '', confirmed: true }])) as Record<MeasurementKey, MeasurementMetadata>
}
