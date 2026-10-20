/** Pure ECharts builders for the original risk dashboard and report. */
import { formatPredictionNumber, predictionHasValue } from './riskPrediction'
import type { BatchPredictionResponse, PredictionOutcome, PredictionRequest, PredictionResponse } from './riskPrediction'
import { RISK_PALETTE, chartGradient, featureAccent } from './riskPalette'
import { riskCategoryAxis, riskChartBase, riskTooltip, riskValueAxis } from './riskChartTheme'
export interface ChartBlock { status: string; reason?: string | null; note?: string }
export interface ShapItem { feature: string; label_zh: string; value: number }
export interface DashboardCharts extends ChartBlock {
  target: string; label_zh: string; unit: string; model_family: string[]
  explanation: ChartBlock & { scale_label?: string; base_value?: number; raw_prediction?: number; additivity_error?: number; items?: ShapItem[] }
  dose_response: ChartBlock & { feature?: string; unit?: string; values?: Array<{ x: number; prediction: number }>; current_value?: number }
  joint_response: ChartBlock & { x_feature?: string; y_feature?: string; x_unit?: string; y_unit?: string; x_values?: number[]; y_values?: number[]; values?: Array<[number, number, number]> }
}
export interface DashboardResponse { input: PredictionRequest; prediction: PredictionResponse; charts: DashboardCharts }
export interface DashboardBatchResponse extends Omit<BatchPredictionResponse, 'records'> {
  records: Array<BatchPredictionResponse['records'][number] & { input?: PredictionRequest }>
}
export type ChartOption = Record<string, unknown>
const finite = (value: unknown): value is number => typeof value === 'number' && Number.isFinite(value)
const html = (value: unknown) => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;')
export function chartReason(block: ChartBlock | undefined | null, fallback = '尚无本次真实计算结果'): string { return block?.reason || fallback }
export function selectedOutcome<T extends { target: string }>(prediction: { results: T[] } | null | undefined, target: string): T | undefined { return prediction?.results.find(row => row.target === target) }
export function availableShapItems(charts: DashboardCharts | null | undefined): ShapItem[] {
  if (charts?.explanation.status !== 'AVAILABLE') return []
  return (charts.explanation.items || []).filter(item => finite(item.value))
}
export function buildRankOption(prediction: PredictionResponse, target: string, batch?: DashboardBatchResponse | null): ChartOption | null {
  const current = selectedOutcome(prediction, target)
  const rows = batch ? batch.records.map(record => ({ id: record.person_id, row: selectedOutcome({ ...prediction, results: record.results || [] }, target) })) : [{ id: prediction.person_id || '本次对象', row: current }]
  const valid = rows.filter(item => item.row && predictionHasValue(item.row)).sort((a, b) => (b.row!.prediction as number) - (a.row!.prediction as number)).slice(0, 10)
  if (!valid.length || !current) return null
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(59,130,246,.05)' } }, formatter: (params: any[]) => params.map(item => html(item.name) + '：' + formatPredictionNumber(item.value) + ' ' + html(current.unit)).join('<br/>') }),
    grid: { left: 12, right: 60, top: 24, bottom: 28, containLabel: true },
    xAxis: riskValueAxis({ name: current.unit, nameLocation: 'middle', nameGap: 26, max: (value: { max: number }) => value.max > 0 ? value.max * 1.12 : value.max }),
    yAxis: riskCategoryAxis({ inverse: true, data: valid.map(item => item.id), axisLabel: { color: '#475569', width: 100, overflow: 'truncate', fontSize: 11, margin: 12 } }),
    series: [{ type: 'bar', name: current.label_zh, barMaxWidth: 30, data: valid.map(item => item.row!.prediction), showBackground: true, backgroundStyle: { color: '#F4F7FC', borderRadius: 5 }, itemStyle: { color: chartGradient('#93C5FD', RISK_PALETTE.blue), borderRadius: [0, 5, 5, 0] }, emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(59,130,246,.18)' } }, label: { show: true, position: 'right', distance: 8, formatter: (item: any) => formatPredictionNumber(item.value), color: '#2563EB', fontSize: 11, fontWeight: 600 } }],
  }
}
export function buildGaugeOption(prediction: PredictionResponse, batch?: DashboardBatchResponse | null): ChartOption {
  const numerator = batch ? batch.processed_records : prediction.results.filter(predictionHasValue).length
  const denominator = batch ? batch.records.length : prediction.results.length
  const percentage = denominator > 0 ? numerator / denominator * 100 : 0
  const availableName = batch ? '有效记录' : '可估计结局'
  const unavailableName = batch ? '未完成记录' : '暂不输出结局'
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ trigger: 'item', formatter: (item: any) => html(item.name) + '：' + item.value + ' / ' + denominator + '<br/>仅表示计算覆盖情况，不是患病概率' }),
    legend: { bottom: 4, left: 'center', icon: 'roundRect', itemWidth: 9, itemHeight: 9, itemGap: 16, textStyle: { color: '#64748B', fontSize: 10 } },
    graphic: [
      { type: 'text', left: 'center', top: '35%', style: { text: formatPredictionNumber(percentage, 1) + '%', fill: '#1E40AF', fontSize: 30, fontWeight: 700, fontFamily: 'Inter, Microsoft YaHei, sans-serif' } },
      { type: 'text', left: 'center', top: '51%', style: { text: numerator + ' / ' + denominator + (batch ? ' 条有效记录' : ' 项可估计'), fill: '#64748B', fontSize: 11 } },
    ],
    series: [{ name: '本次计算覆盖情况', type: 'pie', radius: ['58%', '78%'], center: ['50%', '44%'], startAngle: 90, avoidLabelOverlap: true, label: { show: false }, itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 }, emphasis: { scaleSize: 4, itemStyle: { shadowBlur: 12, shadowColor: 'rgba(59,130,246,.15)' } }, data: [
      { value: numerator, name: availableName, itemStyle: { color: chartGradient('#60A5FA', '#2563EB', true) } },
      { value: Math.max(denominator - numerator, 0), name: unavailableName, itemStyle: { color: '#E8EEF7' } },
    ] }],
  }
}
export function buildImportanceOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts).filter(item => item.value !== 0).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  if (!items.length) return null
  const data = items.slice(0, 5).map(item => ({ name: item.label_zh || item.feature, value: Math.abs(item.value), details: [item], itemStyle: { color: featureAccent(item.feature) } }))
  const remainder = items.slice(5)
  if (remainder.length) data.push({ name: '其他特征（合计）', value: remainder.reduce((sum, item) => sum + Math.abs(item.value), 0), details: remainder, itemStyle: { color: RISK_PALETTE.gray } })
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ trigger: 'item', formatter: (item: any) => html(item.name) + '<br/>绝对贡献份额：' + formatPredictionNumber(item.percent, 1) + '%<br/>原生尺度：' + html(charts.explanation.scale_label) + (item.data?.details?.length ? '<br/>' + item.data.details.map((detail: ShapItem) => html(detail.label_zh || detail.feature) + '：' + (detail.value > 0 ? '+' : '') + formatPredictionNumber(detail.value, 4)).join('<br/>') : '') }),
    graphic: [
      { type: 'text', left: 'center', bottom: 0, style: { text: '前5项 + 其他合计，保留全部绝对贡献', fill: '#94A3B8', fontSize: 9 } },
      { type: 'text', left: 'center', top: '39%', style: { text: 'SHAP\n贡献份额', fill: '#64748B', fontSize: 11, lineHeight: 19, align: 'center' } },
    ],
    series: [{ name: '绝对 SHAP 份额（不是 PIP）', type: 'pie', radius: ['40%', '67%'], center: ['50%', '46%'], minAngle: 0, itemStyle: { borderRadius: 5, borderColor: '#fff', borderWidth: 3 }, emphasis: { scaleSize: 5, itemStyle: { shadowBlur: 14, shadowColor: 'rgba(15,23,42,.12)' } }, label: { formatter: '{name|{b}}\n{value|{d}%}', fontSize: 10, width: 72, overflow: 'truncate', alignTo: 'edge', edgeDistance: 7, bleedMargin: 3, distanceToLabelLine: 4, rich: { name: { color: '#475569', fontSize: 10, lineHeight: 16 }, value: { color: '#334155', fontWeight: 600, fontSize: 11 } } }, labelLine: { length: 10, length2: 6, lineStyle: { width: 1 } }, labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' }, data }],
  }
}
export function buildDoseOption(charts: DashboardCharts): ChartOption | null {
  const block = charts.dose_response
  if (block.status !== 'AVAILABLE') return null
  const values = (block.values || []).filter(item => finite(item.x) && finite(item.prediction))
  if (values.length < 2) return null
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: '#CBD5E1', type: 'dashed' } }, formatter: (params: any[]) => params.map(item => '全血铅：' + formatPredictionNumber(item.value[0], 3) + ' ' + html(block.unit) + '<br/>' + html(charts.label_zh) + '估计：' + formatPredictionNumber(item.value[1]) + ' ' + html(charts.unit)).join('<br/>') }),
    grid: { left: 12, right: 22, top: 34, bottom: 48, containLabel: true },
    xAxis: riskValueAxis({ name: '全血铅 / ' + block.unit, nameLocation: 'middle', nameGap: 30, splitLine: { show: false } }),
    yAxis: riskValueAxis({ name: charts.unit, scale: true, splitNumber: 4 }),
    series: [{ type: 'line', name: charts.label_zh + '模型响应', data: values.map(item => [item.x, item.prediction]), smooth: false, symbol: 'circle', symbolSize: 5, showSymbol: true, lineStyle: { color: RISK_PALETTE.red, width: 2.5, cap: 'round', join: 'round' }, itemStyle: { color: RISK_PALETTE.red, borderColor: '#fff', borderWidth: 1.5 }, emphasis: { scale: 1.6 }, areaStyle: { color: chartGradient('rgba(239,68,68,.20)', 'rgba(239,68,68,.015)', true) }, markLine: finite(block.current_value) ? { silent: true, symbol: 'none', label: { formatter: '本次输入', fontSize: 10, color: '#64748B', backgroundColor: 'rgba(255,255,255,.90)', borderRadius: 4, padding: [4, 6] }, lineStyle: { color: '#94A3B8', type: 'dashed', width: 1 }, data: [{ xAxis: block.current_value }] } : undefined }],
  }
}
export function buildJointOption(charts: DashboardCharts): ChartOption | null {
  const block = charts.joint_response
  if (block.status !== 'AVAILABLE' || !block.x_values?.length || !block.y_values?.length) return null
  const values = (block.values || []).filter(item => item.length === 3 && item.every(finite) && Number.isInteger(item[0]) && Number.isInteger(item[1]) && item[0] >= 0 && item[1] >= 0 && item[0] < block.x_values!.length && item[1] < block.y_values!.length)
  if (!values.length) return null
  const numbers = values.map(item => item[2]); const min = Math.min(...numbers); const max = Math.max(...numbers)
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ position: 'top', formatter: (item: any) => '全血铅：' + formatPredictionNumber(block.x_values![item.value[0]], 3) + ' ' + html(block.x_unit) + '<br/>全血镉：' + formatPredictionNumber(block.y_values![item.value[1]], 3) + ' ' + html(block.y_unit) + '<br/>' + html(charts.label_zh) + '估计：' + formatPredictionNumber(item.value[2]) + ' ' + html(charts.unit) }),
    grid: { left: 12, right: 18, top: '15%', bottom: 76, containLabel: true },
    xAxis: riskCategoryAxis({ data: block.x_values.map(value => formatPredictionNumber(value, 3)), name: '全血铅 / ' + block.x_unit, nameLocation: 'middle', nameGap: 29, axisLabel: { color: '#64748B', fontSize: 10, margin: 12, interval: 0 } }),
    yAxis: riskCategoryAxis({ data: block.y_values.map(value => formatPredictionNumber(value, 3)), name: '全血镉 / ' + block.y_unit, axisLabel: { color: '#64748B', fontSize: 10, margin: 12 } }),
    visualMap: { min, max: max === min ? min + 1 : max, calculable: false, orient: 'horizontal', left: 'center', bottom: 4, itemWidth: 9, itemHeight: 120, precision: 1, text: ['估计值高', '估计值低'], textStyle: { color: '#64748B', fontSize: 10 }, borderColor: 'transparent', inRange: { color: ['#EFF6FF', '#BFDBFE', '#60A5FA', '#1E40AF'] } },
    series: [{ type: 'heatmap', name: charts.label_zh + '模型响应', data: values, label: { show: true, formatter: (item: any) => { const range = max - min; const tone = range > 0 && (item.value[2] - min) / range > .58 ? 'light' : 'dark'; return '{' + tone + '|' + formatPredictionNumber(item.value[2], 1) + '}' }, rich: { light: { color: '#fff', fontSize: 10, fontWeight: 600 }, dark: { color: '#1E3A8A', fontSize: 10, fontWeight: 600 } } }, itemStyle: { borderWidth: 3, borderColor: '#fff', borderRadius: 5 }, emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(37,99,235,.18)' } } }],
  }
}
export function buildShapOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts)
  if (!items.length) return null
  const extent = Math.max(...items.map(item => Math.abs(item.value)), 1e-6)
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ trigger: 'axis', axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(148,163,184,.06)' } }, formatter: (params: any[]) => params.map(item => html(item.name) + '<br/>带符号贡献：' + (item.value > 0 ? '+' : '') + formatPredictionNumber(item.value, 4) + '<br/>尺度：' + html(charts.explanation.scale_label)).join('<br/>') }),
    grid: { left: 12, right: 54, top: 18, bottom: 48, containLabel: true },
    xAxis: riskValueAxis({ name: charts.explanation.scale_label, min: -extent * 1.75, max: extent * 1.75, splitNumber: 4, nameLocation: 'middle', nameGap: 30, axisLabel: { color: '#94A3B8', fontSize: 10, formatter: (value: number) => formatPredictionNumber(value, 2) } }),
    yAxis: riskCategoryAxis({ inverse: true, data: items.map(item => item.label_zh || item.feature), axisLabel: { color: '#475569', width: 116, overflow: 'truncate', fontSize: 10, margin: 14 } }),
    series: [{ type: 'bar', name: '带符号 SHAP 贡献', barMaxWidth: 18, data: items.map(item => ({ value: item.value, itemStyle: { color: item.value < 0 ? chartGradient('#34D399', '#059669') : item.value > 0 ? chartGradient('#FB7185', '#EF4444') : '#94A3B8', borderRadius: item.value < 0 ? [4, 0, 0, 4] : [0, 4, 4, 0] }, label: { position: item.value < 0 ? 'left' : 'right', color: item.value < 0 ? '#059669' : item.value > 0 ? '#E11D48' : '#64748B', distance: 7 } })), label: { show: true, position: 'right', fontSize: 10, fontWeight: 600, formatter: (item: any) => (item.value > 0 ? '+' : '') + formatPredictionNumber(item.value, 3) }, emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(148,163,184,.18)' } }, markLine: { silent: true, symbol: 'none', lineStyle: { color: '#94A3B8', type: 'dashed', width: 1 }, label: { show: false }, data: [{ xAxis: 0 }] } }],
  }
}
export function buildRadarOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  const total = items.reduce((sum, item) => sum + Math.abs(item.value), 0)
  if (items.length < 5 || total === 0) return null
  const groups = items.slice(0, 5).map(item => ({ name: item.label_zh || item.feature, value: Math.abs(item.value) }))
  groups.push({ name: '其他特征（合计）', value: items.slice(5).reduce((sum, item) => sum + Math.abs(item.value), 0) })
  const share = (value: number) => value / total * 100
  return {
    ...riskChartBase(),
    tooltip: riskTooltip({ formatter: () => '本次对象绝对 SHAP 份额：前5项 + 其他合计<br/>不是暴露浓度、患病概率或因果重要性<br/>' + groups.map(item => html(item.name) + '：' + formatPredictionNumber(share(item.value), 1) + '%').join('<br/>') }),
    radar: { indicator: groups.map(item => ({ name: item.name.length > 7 ? item.name.slice(0, 6) + '…' : item.name, max: 100 })), axisName: { color: '#64748B', fontSize: 10, width: 72, overflow: 'truncate' }, radius: '58%', splitNumber: 5, splitArea: { areaStyle: { color: ['#fff', '#F8FAFF'] } }, splitLine: { lineStyle: { color: '#E2E8F0', type: 'dashed' } }, axisLine: { lineStyle: { color: '#E2E8F0' } } },
    series: [{ type: 'radar', symbol: 'circle', symbolSize: 5, data: [{ value: groups.map(item => share(item.value)), name: '绝对贡献份额（%）', areaStyle: { color: chartGradient('rgba(239,68,68,.28)', 'rgba(239,68,68,.05)', true) }, lineStyle: { color: RISK_PALETTE.red, width: 2.5 }, itemStyle: { color: RISK_PALETTE.red, borderColor: '#fff', borderWidth: 1.5 } }] }],
  }
}
/** Original unsupported diagrams stay visibly present without fake numeric series. */
export function buildOriginalUnavailableOption(kind: 'bar' | 'gauge' | 'rose' | 'heatmap', reason: string): ChartOption {
  const stroke = '#D7E0E9'
  const fill = '#F1F5F9'
  const decorations: Record<string, unknown>[] = []
  if (kind === 'bar') {
    for (let index = 0; index < 3; index++) decorations.push({ type: 'rect', shape: { x: 0, y: index * 24, width: 150, height: 10 }, style: { fill, stroke, lineWidth: 1 } })
  } else if (kind === 'gauge') {
    decorations.push({ type: 'arc', shape: { cx: 80, cy: 70, r: 62, startAngle: Math.PI, endAngle: 2 * Math.PI, clockwise: true }, style: { fill: null, stroke, lineWidth: 12 } })
  } else if (kind === 'rose') {
    for (let index = 0; index < 6; index++) decorations.push({ type: 'sector', shape: { cx: 75, cy: 45, r: 42, r0: 15, startAngle: index * Math.PI / 3, endAngle: (index + 1) * Math.PI / 3 }, style: { fill, stroke: '#fff', lineWidth: 2 } })
  } else {
    for (let y = 0; y < 5; y++) for (let x = 0; x < 5; x++) decorations.push({ type: 'rect', shape: { x: x * 22, y: y * 15, width: 20, height: 13 }, style: { fill, stroke: '#E2E8F0', lineWidth: 1 } })
  }
  return { animation: false, tooltip: { show: false }, graphic: [{ type: 'group', left: 'center', top: '13%', children: decorations }, { type: 'text', left: 'center', top: '52%', style: { text: '原图保留 · 暂无对应模型输出\n' + reason + '\n灰色图形仅为原图型骨架，不表示0或任何比例', width: 240, overflow: 'break', lineHeight: 19, fontSize: 11, fill: '#91A0B0', align: 'center' } }] }
}
