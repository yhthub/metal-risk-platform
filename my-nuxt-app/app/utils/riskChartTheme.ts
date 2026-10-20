/** Shared presentation only: these helpers never transform model values. */
export const RISK_CHART_COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#6366F1'] as const
export const RISK_SPLIT_LINE = { show: true, lineStyle: { color: '#E2E8F0', type: 'dashed', width: 1 } }

export function riskChartBase() {
  return {
    animationDuration: 650,
    animationDurationUpdate: 350,
    animationEasing: 'cubicOut',
    color: [...RISK_CHART_COLORS],
    textStyle: { color: '#475569', fontFamily: 'Inter, Microsoft YaHei, sans-serif', fontSize: 11 },
    aria: { enabled: true },
  }
}

export function riskTooltip(overrides: Record<string, unknown> = {}) {
  return {
    confine: true,
    backgroundColor: 'rgba(255,255,255,0.97)',
    borderColor: '#E2E8F0',
    borderWidth: 1,
    padding: [10, 12],
    textStyle: { color: '#334155', fontSize: 12, lineHeight: 20 },
    extraCssText: 'box-shadow:0 10px 28px rgba(15,23,42,.10);border-radius:10px;',
    ...overrides,
  }
}

export function riskValueAxis(overrides: Record<string, unknown> = {}) {
  return {
    type: 'value',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#64748B', fontSize: 10, margin: 10 },
    nameTextStyle: { color: '#64748B', fontSize: 10, padding: [0, 0, 6, 0] },
    splitLine: RISK_SPLIT_LINE,
    ...overrides,
  }
}

export function riskCategoryAxis(overrides: Record<string, unknown> = {}) {
  return {
    type: 'category',
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#475569', fontSize: 10, margin: 10 },
    nameTextStyle: { color: '#64748B', fontSize: 10, padding: [0, 0, 6, 0] },
    splitLine: { show: false },
    ...overrides,
  }
}
