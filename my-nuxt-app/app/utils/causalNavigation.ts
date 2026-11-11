import { participantCode } from './riskPrediction'
import type { DashboardResponse } from './riskDashboard'
import type { CohortPredictionResponse } from './riskCohort'
import { getInterventionPlan } from './interventionPlans'
import { elementNames } from './knowledgeTypes'

type Query = Record<string, unknown>
type Mode = 'individual' | 'batch'

export const riskTargetOptions = [
  { value: 'sbp', label: '收缩压 / mmHg' }, { value: 'dbp', label: '舒张压 / mmHg' },
  { value: 'serum_creatinine_mg_dl', label: '血清肌酐 / mg/dL' }, { value: 'bun_mg_dl', label: '血尿素氮 / mg/dL' },
  { value: 'uric_acid_mg_dl', label: '尿酸 / mg/dL' }, { value: 'uacr_mg_g', label: '尿白蛋白肌酐比 / mg/g' },
  { value: 'hba1c_percent', label: '糖化血红蛋白 / %' }, { value: 'total_cholesterol_mg_dl', label: '总胆固醇 / mg/dL' },
  { value: 'hdl_cholesterol_mg_dl', label: '高密度脂蛋白胆固醇 / mg/dL' }, { value: 'alt_u_l', label: 'ALT / U/L' },
  { value: 'ast_u_l', label: 'AST / U/L' }, { value: 'ggt_u_l', label: 'GGT / U/L' },
]

const knownTarget = (value: unknown) => riskTargetOptions.find(item => item.value === value)?.value || ''
const validMode = (value: unknown): Mode | null => value === 'individual' || value === 'batch' ? value : null

/** The URL selects a question. Only a completed result in this tab can supply a participant. */
export function riskPathContext(query: Query, dashboard?: DashboardResponse | null, cohort?: CohortPredictionResponse | null) {
  const mode = query.from === 'risk' ? validMode(query.mode) : null
  const target = mode ? knownTarget(query.target) : ''
  let person = ''
  let current = false
  if (target && mode === 'individual' && dashboard?.charts.target === target) {
    person = participantCode(dashboard.prediction.person_id)
    current = Boolean(person && dashboard.prediction.results.some(item => item.target === target))
    if (!current) person = ''
  } else if (target && mode === 'batch' && cohort?.complete) {
    current = cohort.summary.some(item => item.target === target)
  }
  return { mode, target, person, current }
}

const metalLabels = elementNames
const outcomeLabels: Record<string, string> = { all: '全部资料', renal: '肾脏指标', sbp: '收缩压', other: '其他健康指标', unsupported: '本次风险指标' }

/** Keep the original path selection separate from a different plan the visitor subsequently opens. */
export function causalPlanOrigin(query: Query) {
  if (query.from !== 'causal' || typeof query.outcome !== 'string' || !Object.hasOwn(outcomeLabels, query.outcome)) return null
  const outcome = query.outcome
  const metals = typeof query.metals === 'string'
    ? [...new Set(query.metals.split(',').filter(code => Object.hasOwn(metalLabels, code)))]
    : []
  const path: Record<string, string> = { outcome, metals: metals.join(',') }
  if (typeof query.edge === 'string' && /^[A-Za-z0-9_-]{1,80}$/.test(query.edge)) path.edge = query.edge
  const pathPerson = getInterventionPlan(query.pathPerson ?? query.person)?.id || ''
  const mode = validMode(query.sourceMode)
  const target = knownTarget(query.sourceTarget)
  const origin: Record<string, string> = { ...path, from: 'causal', pathPerson }
  const back: Record<string, string> = { ...path }
  if (pathPerson) back.person = pathPerson
  if (mode && target) {
    Object.assign(origin, { sourceMode: mode, sourceTarget: target })
    Object.assign(back, { from: 'risk', mode, target })
  }
  return {
    metals, origin, back,
    label: [metals.map(code => metalLabels[code]).join('、'), outcomeLabels[outcome]].filter(Boolean).join(' · '),
  }
}
