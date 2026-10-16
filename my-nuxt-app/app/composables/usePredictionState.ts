import { clonePrediction, createPredictionDraft } from '~/utils/riskPrediction'
import type { BatchPredictionResponse, PredictionDraft, PredictionRequest, PredictionResponse } from '~/utils/riskPrediction'
import type { DashboardResponse } from '~/utils/riskDashboard'
import type { CohortPredictionResponse } from '~/utils/riskCohort'

/** Health input stays in this browser session; never localStorage, URLs or cookies. */
export const usePredictionState = () => {
  const intake = useState<PredictionRequest | null>('prediction:intake', () => null)
  const batchIntake = useState<{ file_id: string; filename?: string; provenance?: Record<string, any> } | null>('prediction:batch-intake', () => null)
  const draft = useState<PredictionDraft>('prediction:draft', createPredictionDraft)
  const lastRequest = useState<PredictionRequest | null>('prediction:last-request', () => null)
  const lastResult = useState<PredictionResponse | null>('prediction:last-result', () => null)
  const dashboard = useState<DashboardResponse | null>('prediction:dashboard', () => null)
  const batchResult = useState<BatchPredictionResponse | null>('prediction:batch-result', () => null)
  const cohortResult = useState<CohortPredictionResponse | null>('prediction:cohort-result', () => null)
  const cohortWarningThreshold = useState<number>('prediction:cohort-warning-threshold', () => 80)
  const cohortWarningDemoPreset = useState<{ file_id: string; threshold: number } | null>('prediction:cohort-warning-demo-preset', () => null)
  const selectedTarget = useState<string>('prediction:target', () => 'sbp')
  const selectedRow = useState<number | null>('prediction:row', () => null)
  const lastDashboardRequest = useState<{ input: PredictionRequest; target: string } | null>('prediction:dashboard-request', () => null)
  const invalidate = () => {
    lastResult.value = null
    lastRequest.value = null
    dashboard.value = null
    batchResult.value = null
    cohortResult.value = null
    selectedRow.value = null
    lastDashboardRequest.value = null
  }
  const setIntake = (payload: PredictionRequest) => { intake.value = clonePrediction(payload); batchIntake.value = null; draft.value = clonePrediction(payload); lastRequest.value = null; invalidate() }
  const setResult = (payload: PredictionRequest, result: PredictionResponse) => { lastRequest.value = clonePrediction(payload); lastResult.value = clonePrediction(result) }
  return { intake, batchIntake, draft, lastRequest, lastResult, dashboard, batchResult, cohortResult, cohortWarningThreshold, cohortWarningDemoPreset,
    selectedTarget, selectedRow, lastDashboardRequest, invalidate, setIntake, setResult }
}
