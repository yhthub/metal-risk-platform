/** Original risk-page hues. Visual roles only: no thresholds or risk labels. */
export const RISK_PALETTE = {
  blue: '#3B82F6', red: '#EF4444', peach: '#FCA5A5', orange: '#F97316',
  lightOrange: '#FDBA74', amber: '#F59E0B', gold: '#FBBF24', green: '#10B981',
  purple: '#8B5CF6', gray: '#9CA3AF', lightGray: '#E5EDF7',
} as const
export function chartGradient(from: string, to: string, vertical = false) {
  return { type: 'linear', x: 0, y: 0, x2: vertical ? 0 : 1, y2: vertical ? 1 : 0,
    colorStops: [{ offset: 0, color: from }, { offset: 1, color: to }] }
}
export function rankingGradient() {
  return { ...chartGradient('#B91C1C', '#FECACA'), colorStops: [
    { offset: 0, color: '#B91C1C' }, { offset: 0.55, color: RISK_PALETTE.red }, { offset: 1, color: '#FECACA' },
  ] }
}
export function featureAccent(feature: string): string {
  const colors: Record<string, string> = {
    pb: RISK_PALETTE.red, blood_lead_ug_dl: RISK_PALETTE.red,
    cd: RISK_PALETTE.orange, blood_cadmium_ug_l: RISK_PALETTE.orange,
    hg: RISK_PALETTE.amber, blood_total_mercury_ug_l: RISK_PALETTE.amber,
    age: RISK_PALETTE.blue, age_years: RISK_PALETTE.blue,
    bmi: RISK_PALETTE.purple, bmi_kg_m2: RISK_PALETTE.purple, sex_female: RISK_PALETTE.green,
    education: '#6366F1', marital: '#14B8A6', smoking: '#FBBF24',
    alcohol_any_past_year: '#F97316', other_unprovided_model_features: RISK_PALETTE.gray,
  }
  return colors[feature] || RISK_PALETTE.gray
}
