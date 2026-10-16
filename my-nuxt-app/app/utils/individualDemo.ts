import { createIndividualMetadata } from './individualReferences'
import type { MeasurementKey, MeasurementMetadata } from './individualReferences'

/** Synthetic presentation fixture only: no real person, laboratory report or clinical conclusion. */
export const INDIVIDUAL_DEMO_LABEL = '合成演示数据'
export const INDIVIDUAL_DEMO_NOTE = '所有数值均为合成示例，仅用于体验录入与参考比较；氡为住宅室内年均环境指标，不是人体样本或工作场所读数。'

export type IndividualDemoData = Record<MeasurementKey, number> & {
  name: string
  gender: 'male' | 'female'
  age: number
  workYears: number
  education: string
  marital: string
  smoking: string
  drinking: string
  bmi: number
  ppe: string
  history: string
}

export interface IndividualDemo {
  job: 'smelting'
  singleData: IndividualDemoData
  metadata: Record<MeasurementKey, MeasurementMetadata>
}

/** Each call returns independent mutable objects, so user edits never alter later demos. */
export function createIndividualDemo(): IndividualDemo {
  const metadata = createIndividualMetadata()
  for (const key of ['pb', 'cd', 'hg', 'th', 'li', 'cr', 'ni', 'co'] as const) {
    Object.assign(metadata[key], { sample: 'whole_blood', unit: 'μg/L' })
  }
  // These are explicitly selected synthetic reference conditions, not inferred from job.
  metadata.cd.context = 'occupational_cadmium'
  metadata.hg.analyte = 'total_mercury'
  Object.assign(metadata.as, { sample: 'random_urine', unit: 'μg/L', analyte: 'toxic_speciated' })
  Object.assign(metadata.rn, { sample: 'indoor_air', unit: 'Bq/m³', context: 'residential_annual' })
  return {
    job: 'smelting',
    singleData: {
      name: 'DEMO-001（合成示例）', gender: 'male', age: 38, workYears: 11,
      education: 'high', marital: 'married', smoking: 'never', drinking: 'occasional',
      bmi: 24.2, ppe: 'standard', history: '合成示例：未记录职业病史（非真实人员）',
      pb: 42, cd: 3.2, hg: 6.8, th: 0.4, li: 12, cr: 2.4, ni: 3.6, co: 0.7,
      as: 28, rn: 120
    },
    metadata
  }
}
