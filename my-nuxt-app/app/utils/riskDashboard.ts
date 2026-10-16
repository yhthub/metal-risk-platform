/** Pure ECharts builders for the original risk dashboard and report. */
import { formatPredictionNumber, predictionHasValue } from './riskPrediction'
import type { BatchPredictionResponse, PredictionOutcome, PredictionRequest, PredictionResponse } from './riskPrediction'
import { RISK_PALETTE, chartGradient, featureAccent } from './riskPalette'
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
const blue = '#3B82F6'
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
  return { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: any[]) => params.map(item => html(item.name) + '：' + formatPredictionNumber(item.value) + ' ' + html(current.unit)).join('<br/>') }, grid: { left: '3%', right: '12%', top: '8%', bottom: '15%', containLabel: true }, xAxis: { type: 'value', name: current.unit, splitLine: { lineStyle: { type: 'dashed' } } }, yAxis: { type: 'category', inverse: true, data: valid.map(item => item.id), axisTick: { show: false }, axisLabel: { width: 100, overflow: 'truncate' } }, series: [{ type: 'bar', name: current.label_zh, barMaxWidth: 34, data: valid.map(item => item.row!.prediction), itemStyle: { color: blue, borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', formatter: (item: any) => formatPredictionNumber(item.value), color: '#2563EB' } }] }
}
export function buildGaugeOption(prediction: PredictionResponse, batch?: DashboardBatchResponse | null): ChartOption {
  const numerator = batch ? batch.processed_records : prediction.results.filter(predictionHasValue).length
  const denominator = batch ? batch.records.length : prediction.results.length
  const percentage = denominator > 0 ? numerator / denominator * 100 : 0
  return { tooltip: { formatter: html(batch ? '本页有效记录' : '可估计结局') + '：' + numerator + ' / ' + denominator }, series: [{ type: 'gauge', startAngle: 180, endAngle: 0, center: ['50%', '75%'], radius: '100%', min: 0, max: 100, splitNumber: 4, progress: { show: true, width: 15, itemStyle: { color: blue } }, axisLine: { lineStyle: { width: 15, color: [[1, '#E5EDF7']] } }, pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, detail: { offsetCenter: [0, '10%'], fontSize: 30, color: '#2563EB', formatter: (value: number) => formatPredictionNumber(value, 1) + '%' }, data: [{ value: percentage, name: numerator + ' / ' + denominator + (batch ? ' 条有效记录' : ' 项可估计'), title: { offsetCenter: [0, '38%'], fontSize: 11, color: '#64748B' } }] }] }
}
export function buildImportanceOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts).filter(item => item.value !== 0).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  if (!items.length) return null
  const data = items.slice(0, 5).map(item => ({ name: item.label_zh || item.feature, value: Math.abs(item.value), details: [item], itemStyle: { color: featureAccent(item.feature) } }))
  const remainder = items.slice(5)
  if (remainder.length) data.push({ name: '其他特征（合计）', value: remainder.reduce((sum, item) => sum + Math.abs(item.value), 0), details: remainder, itemStyle: { color: RISK_PALETTE.gray } })
  return {
    tooltip: { trigger: 'item', formatter: (item: any) => html(item.name) + '<br/>绝对贡献份额：' + formatPredictionNumber(item.percent, 1) + '%<br/>原生尺度：' + html(charts.explanation.scale_label) + (item.data?.details?.length ? '<br/>' + item.data.details.map((detail: ShapItem) => html(detail.label_zh || detail.feature) + '：' + (detail.value > 0 ? '+' : '') + formatPredictionNumber(detail.value, 4)).join('<br/>') : '') },
    graphic: [{ type: 'text', left: 'center', bottom: 0, style: { text: '前5项 + 其他合计，保留全部绝对贡献', fill: '#94A3B8', fontSize: 9 } }],
    series: [{ name: '绝对 SHAP 份额（不是 PIP）', type: 'pie', radius: ['20%', '72%'], center: ['50%', '46%'], roseType: 'radius', itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }, label: { formatter: '{b}\n{d}%', fontSize: 10, width: 70, overflow: 'truncate', alignTo: 'edge', edgeDistance: 6, bleedMargin: 2, distanceToLabelLine: 3 }, labelLine: { length: 8, length2: 5 }, labelLayout: { hideOverlap: true, moveOverlap: 'shiftY' }, data }], color: [RISK_PALETTE.red, RISK_PALETTE.orange, RISK_PALETTE.amber, RISK_PALETTE.blue, RISK_PALETTE.purple, RISK_PALETTE.gray]
  }
}
export function buildDoseOption(charts: DashboardCharts): ChartOption | null {
  const block = charts.dose_response
  if (block.status !== 'AVAILABLE') return null
  const values = (block.values || []).filter(item => finite(item.x) && finite(item.prediction))
  if (values.length < 2) return null
  return { tooltip: { trigger: 'axis', formatter: (params: any[]) => params.map(item => '全血铅：' + formatPredictionNumber(item.value[0], 3) + ' ' + html(block.unit) + '<br/>' + html(charts.label_zh) + '估计：' + formatPredictionNumber(item.value[1]) + ' ' + html(charts.unit)).join('<br/>') }, grid: { left: '6%', right: '6%', top: '13%', bottom: '22%', containLabel: true }, xAxis: { type: 'value', name: '全血铅 / ' + block.unit, nameLocation: 'middle', nameGap: 29, splitLine: { show: false } }, yAxis: { type: 'value', name: charts.unit, scale: true, splitLine: { lineStyle: { type: 'dashed' } } }, series: [{ type: 'line', name: charts.label_zh + '模型响应', data: values.map(item => [item.x, item.prediction]), smooth: false, symbol: 'circle', symbolSize: 4, lineStyle: { color: RISK_PALETTE.red, width: 2 }, itemStyle: { color: RISK_PALETTE.red }, areaStyle: { color: chartGradient('rgba(239,68,68,0.28)', 'rgba(239,68,68,0)', true) }, markLine: finite(block.current_value) ? { silent: true, symbol: 'none', label: { formatter: '本次输入', fontSize: 10 }, lineStyle: { color: '#94A3B8', type: 'dashed' }, data: [{ xAxis: block.current_value }] } : undefined }] }
}
export function buildJointOption(charts: DashboardCharts): ChartOption | null {
  const block = charts.joint_response
  if (block.status !== 'AVAILABLE' || !block.x_values?.length || !block.y_values?.length) return null
  const values = (block.values || []).filter(item => item.length === 3 && item.every(finite) && Number.isInteger(item[0]) && Number.isInteger(item[1]) && item[0] >= 0 && item[1] >= 0 && item[0] < block.x_values!.length && item[1] < block.y_values!.length)
  if (!values.length) return null
  const numbers = values.map(item => item[2]); const min = Math.min(...numbers); const max = Math.max(...numbers)
  return { tooltip: { position: 'top', formatter: (item: any) => '全血铅：' + formatPredictionNumber(block.x_values![item.value[0]], 3) + ' ' + html(block.x_unit) + '<br/>全血镉：' + formatPredictionNumber(block.y_values![item.value[1]], 3) + ' ' + html(block.y_unit) + '<br/>' + html(charts.label_zh) + '估计：' + formatPredictionNumber(item.value[2]) + ' ' + html(charts.unit) }, grid: { left: '4%', right: '4%', top: '15%', bottom: '26%', containLabel: true }, xAxis: { type: 'category', data: block.x_values.map(value => formatPredictionNumber(value, 3)), name: '全血铅 / ' + block.x_unit, nameLocation: 'middle', nameGap: 28, axisTick: { show: false } }, yAxis: { type: 'category', data: block.y_values.map(value => formatPredictionNumber(value, 3)), name: '全血镉 / ' + block.y_unit, axisTick: { show: false } }, visualMap: { min, max: max === min ? min + 1 : max, calculable: false, orient: 'horizontal', left: 'center', bottom: 0, itemWidth: 10, itemHeight: 100, precision: 1, text: ['估计值高', '估计值低'], inRange: { color: ['#FFF7ED', '#FED7AA', '#FB923C', RISK_PALETTE.red] } }, series: [{ type: 'heatmap', name: charts.label_zh + '模型响应', data: values, label: { show: true, formatter: (item: any) => formatPredictionNumber(item.value[2], 1), fontSize: 10 }, itemStyle: { borderWidth: 2, borderColor: '#fff' } }] }
}
export function buildShapOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts)
  if (!items.length) return null
  return { tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: (params: any[]) => params.map(item => html(item.name) + '<br/>带符号贡献：' + formatPredictionNumber(item.value, 4) + '<br/>尺度：' + html(charts.explanation.scale_label)).join('<br/>') }, grid: { left: '3%', right: '12%', top: '4%', bottom: '19%', containLabel: true }, xAxis: { type: 'value', name: charts.explanation.scale_label, nameLocation: 'middle', nameGap: 28, nameTextStyle: { fontSize: 10 }, splitLine: { lineStyle: { type: 'dashed' } } }, yAxis: { type: 'category', inverse: true, data: items.map(item => item.label_zh || item.feature), axisLabel: { width: 115, overflow: 'truncate', fontSize: 10 }, axisTick: { show: false } }, series: [{ type: 'bar', barMaxWidth: 17, data: items.map(item => ({ value: item.value, itemStyle: { color: item.value >= 0 ? '#EF4444' : '#10B981' } })), label: { show: true, position: 'right', fontSize: 10, formatter: (item: any) => (item.value > 0 ? '+' : '') + formatPredictionNumber(item.value, 3) }, markLine: { silent: true, symbol: 'none', lineStyle: { color: '#94A3B8', type: 'dashed' }, label: { show: false }, data: [{ xAxis: 0 }] } }] }
}
export function buildRadarOption(charts: DashboardCharts): ChartOption | null {
  const items = availableShapItems(charts).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  const total = items.reduce((sum, item) => sum + Math.abs(item.value), 0)
  if (items.length < 5 || total === 0) return null
  const groups = items.slice(0, 5).map(item => ({ name: item.label_zh || item.feature, value: Math.abs(item.value) }))
  groups.push({ name: '其他特征（合计）', value: items.slice(5).reduce((sum, item) => sum + Math.abs(item.value), 0) })
  const share = (value: number) => value / total * 100
  return { tooltip: { formatter: () => '本次对象绝对 SHAP 份额：前5项 + 其他合计<br/>不是暴露浓度、患病概率或因果重要性<br/>' + groups.map(item => html(item.name) + '：' + formatPredictionNumber(share(item.value), 1) + '%').join('<br/>') }, radar: { indicator: groups.map(item => ({ name: item.name.length > 7 ? item.name.slice(0, 6) + '…' : item.name, max: 100 })), axisName: { color: '#64748B', fontSize: 10, width: 72, overflow: 'truncate' }, radius: '54%' }, series: [{ type: 'radar', data: [{ value: groups.map(item => share(item.value)), name: '绝对贡献份额（%）', areaStyle: { color: '#EF444433' }, lineStyle: { color: RISK_PALETTE.red }, itemStyle: { color: RISK_PALETTE.red } }] }] }
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
