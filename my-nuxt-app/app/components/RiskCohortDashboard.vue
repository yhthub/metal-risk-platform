<template>
  <section class="cohort-dashboard" aria-label="整份文件群体分析">
    <div class="cohort-banner"><div><h3>整份文件 · 群体分析已完成</h3><p>全部 {{ result.total_records }} 个对象均已处理；有效输入 {{ result.processed_records }} 人，跳过 {{ result.skipped_records }} 人。默认展示全群体，不自动选择个人代表群体。</p></div><el-tag type="success" effect="plain">全量完成 · 非分页推理</el-tag></div>
    <RiskCohortProfile :profile="result.demographic_profile" :total-records="result.total_records" :processed-records="result.processed_records" :skipped-records="result.skipped_records" />
    <details v-if="skippedReasons.length" class="cohort-exclusions"><summary>查看 {{ result.skipped_records }} 名对象未进入模型计算的原因（仍纳入上方基本资料统计）</summary><dl class="reason-list"><div v-for="item in skippedReasons" :key="item.reason"><dt>{{ item.reason }}</dt><dd>{{ item.count }} 人</dd></div></dl></details>
    <div class="model-results-heading"><h3>模型计算结果与群体指标分析</h3><span>以下内容来自实际模型估计，与上方原始人群基本资料分开展示。</span></div>
    <div class="cohort-controls"><label>群体目标结局 <el-select :model-value="target" style="width: 240px" @update:model-value="emit('select-target', $event)"><el-option v-for="item in targetOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></label><span>切换指标只重绘全群图表，无需重新计算全部对象。</span></div>
    <p class="cohort-boundary">“全群”仅指本文件全部对象，并非总体人群代表性估计。汇总未加抽样权重或调整混杂；指标值降序不是疾病风险或干预优先级，数值越大不等于越危险。</p>
    <div class="results-grid">
      <RiskCohortWarning class="col-span-6" :result="result" :threshold="warningThreshold ?? 80" @update:threshold="emit('update:warningThreshold', $event)" />
      <article class="result-card col-span-3 accent-orange"><div class="r-head"><div class="title-group"><h4>全群指标估计分布</h4><span class="sub-desc">{{ view.label_zh }} / {{ view.unit }} · 汇总全部 {{ view.estimated_count }} 个有效估计。</span></div></div><div class="chart-frame"><div class="chart-box" ref="distributionRef"></div><div v-if="!distributionOption" class="chart-empty">{{ view.reason || '暂无完整的全群估计值分布，不以零值代替缺测。' }}</div></div></article>
      <article class="result-card col-span-3 accent-blue"><div class="r-head"><div class="title-group"><h4>12 项结局 · 全群概览</h4><span class="sub-desc">不同单位分别呈现；色条仅区分指标类别，不表示疾病风险。点击切换全群图表。</span></div></div><div class="outcome-list"><button v-for="item in result.summary" :key="item.target" class="outcome-row" :class="[{ selected: item.target === target, 'outcome-withheld': item.estimated_count === 0 }, 'outcome-' + item.target]" @click="emit('select-target', item.target)"><div><strong>{{ item.label_zh }}</strong><span>{{ item.estimated_count > 0 ? '全群均值 ' + formatPredictionNumber(item.mean_prediction) + ' ' + item.unit : '暂不出值' }}</span></div><small>{{ item.estimated_count }} 人有估计 · {{ item.withheld_count }} 人因模型准确性不足暂不出值</small></button></div></article>
      <article class="result-card col-span-6 accent-amber"><div class="r-head"><div class="title-group"><h4>全群估计统计概览</h4><span class="sub-desc">{{ view.label_zh }} / {{ view.unit }} · 仅汇总当前结局的实际模型估计值。</span></div></div><div class="stat-grid"><div class="stat-estimated"><span>均值 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.mean) }}</strong></div><div class="stat-neutral"><span>中位数 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.median) }}</strong></div><div class="stat-neutral"><span>下四分位数 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.q1) }}</strong></div><div class="stat-neutral"><span>上四分位数 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.q3) }}</strong></div><div class="stat-neutral"><span>最小值–最大值 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.min) }}–{{ formatPredictionNumber(view.statistics?.max) }}</strong></div><div class="stat-neutral"><span>标准差 / {{ view.unit }}</span><strong>{{ formatPredictionNumber(view.statistics?.std) }}</strong></div></div><p v-if="view.reason" class="small-note">{{ view.reason }}</p><p class="small-note">这是模型估计的未加权描述性汇总，不是实测检查结论。暂不出值与输入不合格的对象不会补零进入统计；原始人群构成与模型输入状态见上方基本信息。</p></article>
    </div>
    <section class="result-card all-records">
      <div class="r-head"><div class="title-group"><h4>完整全群记录与排序</h4><span class="sub-desc">共 {{ result.total_records }} 条均已完成处理。下方仅显示分页，不限制模型计算人群；未出值和跳过的对象仍保留。本表为所选结局的单项排序，综合预警与12项名次见上方合并卡片。</span></div><el-select v-model="tableOrder" size="small" style="width: 160px"><el-option value="rank" label="所选指标估计降序" /><el-option value="source" label="原始文件行顺序" /></el-select></div>
      <div class="table-scroll"><table><thead><tr><th>单项排序</th><th>规范编号</th><th>原始编号</th><th>原始行号</th><th>年龄 / 性别</th><th>{{ view.label_zh }} / {{ view.unit }}</th><th>状态与原因</th><th>可选个人明细</th></tr></thead><tbody>
        <tr v-for="row in visibleRows" :key="row.record.row_number"><td>{{ row.rank ?? '—' }}</td><td>{{ cohortDisplayId(row.record.row_number) }}</td><td>{{ row.record.person_id }}</td><td>{{ row.record.row_number }}</td><td>{{ row.record.input?.person.age ?? '—' }} 岁 / {{ row.record.input?.person.gender === 'female' ? '女性' : row.record.input?.person.gender === 'male' ? '男性' : '未知' }}</td><td>{{ row.outcome && predictionHasValue(row.outcome) ? formatPredictionNumber(row.outcome.prediction) : '—' }}</td><td :class="!row.record.input ? 'status-skipped' : row.outcome && predictionHasValue(row.outcome) ? 'status-estimated' : 'status-withheld'">{{ recordStatus(row.record, row.outcome) }}</td><td><el-button link type="primary" :disabled="!row.record.input" @click="emit('inspect-person', row.record.row_number)">查看个人明细</el-button></td></tr>
      </tbody></table></div>
      <div class="table-pagination"><span>模型已处理全部 {{ result.total_records }} 条；当前表格显示 {{ pageStart }}–{{ pageEnd }} 条。</span><el-pagination v-model:current-page="tablePage" v-model:page-size="pageSize" :page-sizes="[20, 50, 100]" :total="tableRows.length" layout="total, sizes, prev, pager, next" /></div>
    </section>
    <el-collapse class="prototype-fold" @change="renderCharts"><el-collapse-item title="原图与功能边界（折叠保留，不冒充全群风险模型）" name="original-prototypes"><div class="prototype-grid"><article class="result-card"><h4>致病元凶权重榜</h4><div class="chart-box" ref="prototypeImportanceRef"></div></article><article class="result-card"><h4>高发职业病靶向预测</h4><div class="prototype-empty">没有对应的疾病概率或纵向发病模型。连续指标回归不能给出患病概率，不能把全群覆盖率当成高危比例。</div></article><article class="result-card"><h4>毒物剂量-致病突变曲线</h4><div class="prototype-empty">尚无全群因果剂量反应模型。可选个人明细中的铅响应仅属于选中对象，不代表全群体致病效应。</div></article><article class="result-card"><h4>双毒物“狼狈为奸”协同放大效应</h4><div class="chart-box" ref="prototypeJointRef"></div></article><article class="result-card"><h4>风险推手与保护因素拆解</h4><div class="prototype-empty">没有为全群计算群体归因或因果贡献。不以首个对象的 SHAP 代替全群结论；个人局部贡献仅在主动查看个人明细后提供。</div></article></div></el-collapse-item></el-collapse>
    <p class="small-note">模型版本 {{ result.model_version }} · 本文件有效输入 {{ result.processed_records }} 人，跳过 {{ result.skipped_records }} 人 · 当次指标估计，非临床诊断或未来发病概率。</p>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { buildCohortDistributionOption, buildCohortView } from '~/utils/riskCohort'
import { cohortDisplayId } from '~/utils/cohortWarning'
import { buildOriginalUnavailableOption } from '~/utils/riskDashboard'
import { formatPredictionNumber, predictionHasValue, predictionReason } from '~/utils/riskPrediction'
import type { CohortPredictionResponse } from '~/utils/riskCohort'
import type { BatchPredictionOutcome } from '~/utils/riskPrediction'
const props = defineProps<{ result: CohortPredictionResponse; target: string; targetOptions: ReadonlyArray<{ value: string; label: string }>; warningThreshold?: number }>()
const emit = defineEmits<{ (event: 'select-target', target: string): void; (event: 'inspect-person', rowNumber: number): void; (event: 'update:warningThreshold', value: number): void }>()
const view = computed(() => buildCohortView(props.result, props.target))
const distributionOption = computed(() => buildCohortDistributionOption(props.result, props.target))
const skippedReasons = computed(() => {
  const counts = new Map<string, number>()
  for (const record of props.result.records) if (!record.input) counts.set(record.reason || '必需输入不满足模型条件', (counts.get(record.reason || '必需输入不满足模型条件') || 0) + 1)
  return [...counts].map(([reason, count]) => ({ reason, count })).sort((a, b) => b.count - a.count)
})
const tableOrder = ref('rank')
const tablePage = ref(1)
const pageSize = ref(20)
const tableRows = computed(() => {
  const ranks = new Map(view.value.rankings.map(row => [row.row_number, row.rank]))
  const rows = props.result.records.map(record => ({ record, rank: ranks.get(record.row_number), outcome: record.results?.find(item => item.target === props.target) }))
  return tableOrder.value === 'source' ? rows : [...rows].sort((a, b) => (a.rank ?? Number.MAX_SAFE_INTEGER) - (b.rank ?? Number.MAX_SAFE_INTEGER) || a.record.row_number - b.record.row_number)
})
const visibleRows = computed(() => tableRows.value.slice((tablePage.value - 1) * pageSize.value, tablePage.value * pageSize.value))
const pageStart = computed(() => tableRows.value.length ? (tablePage.value - 1) * pageSize.value + 1 : 0)
const pageEnd = computed(() => Math.min(tableRows.value.length, tablePage.value * pageSize.value))
function recordStatus(record: CohortPredictionResponse['records'][number], outcome?: BatchPredictionOutcome) {
  return !record.input ? '输入不满足：' + (record.reason || '必需字段不足') : outcome && predictionHasValue(outcome) ? '已估计 · 非诊断' : outcome ? '暂不出值：' + predictionReason(outcome) : '没有该结局结果'
}
const distributionRef = ref<HTMLElement | null>(null)
const prototypeImportanceRef = ref<HTMLElement | null>(null)
const prototypeJointRef = ref<HTMLElement | null>(null)
let instances: echarts.ECharts[] = []
let observer: ResizeObserver | null = null
let active = false
let mounted = false
const resizeCharts = () => instances.forEach(chart => chart.resize())
function clearCharts() { observer?.disconnect(); observer = null; instances.forEach(chart => chart.dispose()); instances = [] }
async function renderCharts() {
  await nextTick()
  if (!active || !mounted) return
  clearCharts()
  const options = [[distributionRef.value, distributionOption.value], [prototypeImportanceRef.value, buildOriginalUnavailableOption('rose', '未接入BKMR/PIP模型，不把个体SHAP当成群体致病权重')], [prototypeJointRef.value, buildOriginalUnavailableOption('heatmap', '没有砷输入或全群Pb×As因果协同模型')]] as const
  if (typeof ResizeObserver !== 'undefined') observer = new ResizeObserver(resizeCharts)
  for (const [element, option] of options) if (element && option && element.clientWidth > 0 && element.clientHeight > 0) { const chart = echarts.init(element); chart.setOption(option); instances.push(chart); observer?.observe(element) }
}
function resume() { if (!mounted || active) return; active = true; window.addEventListener('resize', resizeCharts); void renderCharts() }
function pause() { active = false; window.removeEventListener('resize', resizeCharts); clearCharts() }
watch(() => [props.result, props.target], () => { void renderCharts() }, { deep: false })
watch(() => [props.result.file_id, props.target, tableOrder.value, pageSize.value], () => { tablePage.value = 1 })
onMounted(() => { mounted = true; resume() })
onActivated(resume)
onDeactivated(pause)
onBeforeUnmount(() => { pause(); mounted = false })
</script>

<style scoped>
*{box-sizing:border-box}.cohort-dashboard{color:#0f172a}.cohort-banner{display:flex;align-items:center;justify-content:space-between;gap:20px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:24px;margin:24px 0 20px}.cohort-banner h3{margin:0 0 12px;font-size:20px;color:#1e40af}.cohort-banner p{margin:0;font-size:13px;color:#506682;line-height:1.9}.cohort-controls{display:flex;align-items:center;gap:18px;flex-wrap:wrap;margin-bottom:16px}.cohort-controls label{display:flex;align-items:center;gap:12px;font-size:13px;font-weight:600;color:#475569}.cohort-controls>span{color:#94a3b8;font-size:12px}.cohort-boundary{font-size:12px;color:#8191a5;line-height:1.9;margin:0 0 24px}.results-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:24px;margin-bottom:28px}.col-span-2{grid-column:span 2}.col-span-3{grid-column:span 3}.col-span-4{grid-column:span 4}.result-card{background:white;border:1px solid #e2e8f0;border-radius:12px;padding:24px;box-shadow:0 4px 10px #00000005;min-width:0}.border-primary{border-color:#bfdbfe;border-top:4px solid #3b82f6}.r-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px;border-bottom:1px solid #f8fafc;padding-bottom:12px}.title-group{display:flex;flex-direction:column;gap:7px}.r-head h4,.prototype-grid h4{display:flex;align-items:center;flex-wrap:wrap;gap:8px;margin:0;font-size:16px;font-weight:800;color:#0f172a;line-height:1.7}.sub-desc{font-size:12px;color:#64748b;line-height:1.9}.chart-frame{position:relative}.chart-box{width:100%;height:260px}.chart-box.tall{height:320px}.chart-empty{position:absolute;inset:0;padding:28px;display:flex;align-items:center;justify-content:center;text-align:center;line-height:1.9;color:#94a3b8;background:#f8fafc;border:1px dashed #e2e8f0;border-radius:8px;font-size:12px}.outcome-list{max-height:310px;overflow-y:auto;display:grid;gap:8px}.outcome-row{font:inherit;border:0;background:#f8fafc;border-radius:7px;padding:11px;text-align:left;cursor:pointer}.outcome-row.selected{background:#eff6ff}.outcome-row>div{display:flex;justify-content:space-between;gap:10px;font-size:12px;line-height:1.7}.outcome-row strong{font-weight:600;color:#475569}.outcome-row span{color:#2563eb;white-space:nowrap}.outcome-row small{font-size:10px;color:#94a3b8;display:block;margin-top:6px;line-height:1.8}.stat-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin:4px 0 20px}.stat-grid>div{display:grid;gap:8px}.stat-grid span{font-size:11px;color:#94a3b8}.stat-grid strong{font-size:19px;color:#3f6d92}.reason-list{max-height:160px;overflow-y:auto;margin:0}.reason-list>div{display:flex;justify-content:space-between;gap:14px;padding:10px 0;border-top:1px dashed #e2e8f0;font-size:11px;line-height:1.8;color:#8b9caf}.reason-list dd{white-space:nowrap;margin:0;color:#607f9a}.small-note{font-size:11px;line-height:1.9;color:#94a3b8}.table-scroll{overflow-x:auto;border:1px solid #e2e8f0;border-radius:7px}table{border-collapse:collapse;width:100%;font-size:12px;text-align:left}th{padding:13px 12px;background:#f1f7fc;color:#587895;white-space:nowrap;font-weight:600}td{padding:14px 12px;border-top:1px solid #e8eff5;color:#627f97;line-height:1.9}td:nth-child(6){max-width:280px;font-size:11px}.table-pagination{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap;margin-top:22px}.table-pagination>span{font-size:11px;color:#94a3b8}.prototype-fold{margin-top:25px}.prototype-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:20px;padding-top:15px}.prototype-empty{height:260px;display:flex;align-items:center;justify-content:center;text-align:center;padding:25px;font-size:12px;line-height:1.9;color:#94a3b8;background:#f8fafc;border:1px dashed #e2e8f0;border-radius:8px;margin-top:18px}@media(max-width:1200px){.results-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.col-span-2,.col-span-3,.col-span-4{grid-column:span 2}.prototype-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media print{.cohort-controls,.table-pagination,.prototype-fold{display:none}.results-grid{break-inside:auto}.result-card{break-inside:avoid;box-shadow:none}}

/* Original risk palette: colors distinguish sections and model status, not clinical risk. */
.col-span-6{grid-column:1/-1}
.stat-grid{grid-template-columns:repeat(3,minmax(0,1fr))}
.model-results-heading{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin:28px 0 20px}
.model-results-heading h3{margin:0;font-size:18px;color:#1e40af;border-left:4px solid #3B82F6;padding-left:12px}
.model-results-heading span{font-size:12px;color:#8191a5;line-height:1.8}
.cohort-exclusions{margin:16px 0 22px;padding:12px 18px;border:1px solid #fcdba4;border-radius:9px;background:#fffbf5;color:#996211;font-size:12px;line-height:1.9}
.cohort-exclusions summary{cursor:pointer;font-weight:600}.cohort-exclusions .reason-list{margin-top:8px}
.border-danger{border-color:#FCA5A5;border-top:4px solid #EF4444}
.border-danger .r-head h4{color:#991B1B}
.accent-blue{--section-accent:#3B82F6}.accent-green{--section-accent:#10B981}.accent-orange{--section-accent:#F97316}.accent-amber{--section-accent:#F59E0B}
.accent-blue .r-head h4,.accent-green .r-head h4,.accent-orange .r-head h4,.accent-amber .r-head h4{border-left:3px solid var(--section-accent);padding-left:10px}
.accent-green .r-head h4{color:#078469}
.outcome-row{--outcome-accent:#3B82F6;--outcome-tint:#EFF6FF;border-left:3px solid var(--outcome-accent);background:#fff}
.outcome-row.outcome-sbp,.outcome-row.outcome-dbp{--outcome-accent:#EF4444;--outcome-tint:#FFF1F2}
.outcome-row.outcome-serum_creatinine_mg_dl,.outcome-row.outcome-bun_mg_dl,.outcome-row.outcome-uric_acid_mg_dl,.outcome-row.outcome-uacr_mg_g{--outcome-accent:#3B82F6;--outcome-tint:#EFF6FF}
.outcome-row.outcome-hba1c_percent,.outcome-row.outcome-total_cholesterol_mg_dl,.outcome-row.outcome-hdl_cholesterol_mg_dl{--outcome-accent:#F97316;--outcome-tint:#FFF7ED}
.outcome-row.outcome-alt_u_l,.outcome-row.outcome-ast_u_l,.outcome-row.outcome-ggt_u_l{--outcome-accent:#10B981;--outcome-tint:#ECFDF5}
.outcome-row.selected{background:var(--outcome-tint)}
.outcome-row strong,.outcome-row span{color:var(--outcome-accent)}
.outcome-row.outcome-withheld span{color:#B7790C}
.stat-estimated strong,.status-estimated{color:#10B981}
.stat-withheld strong,.status-withheld{color:#B7790C}
.stat-skipped strong,.status-skipped,.stat-neutral strong,.reason-list dd{color:#64748B}
.prototype-grid .result-card{border-color:#E2E8F0;background:#fff}

</style>
