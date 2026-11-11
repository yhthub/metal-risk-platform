import type { CausalSource } from './causalEvidence'

export interface StudyComparison {
  population: string
  measure: string
  result: string
}

export interface FieldCheck {
  verify: string
  record: string
}

export interface KnowledgeRelation {
  id: string
  metals: string[]
  kind: 'health' | 'mechanism' | 'control'
  from: string
  to: string
  title: string
  finding: string
  detail?: string
  limit: string
  topic?: 'renal' | 'sbp' | 'other'
  source: Omit<CausalSource, 'year'> & { year?: number }
  studyType: string
  study?: StudyComparison
  field?: FieldCheck
}

export const elementNames: Record<string, string> = {
  Pb: '铅', Cd: '镉', Hg: '汞', As: '砷', Cr: '铬', Ni: '镍', Mn: '锰', Se: '硒',
}

export const relationKinds = { health: '健康影响', mechanism: '作用机制', control: '岗位防护' } as const

export function readElements(value: unknown): string[] {
  if (typeof value !== 'string') return []
  return [...new Set(value.split(/[,，、]/).map(code => code.trim()).filter(code => Object.hasOwn(elementNames, code)))]
}
