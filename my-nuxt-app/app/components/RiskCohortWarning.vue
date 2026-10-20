<template>
  <article class="cohort-warning-card" :class="stateClass" aria-label="全群综合相对预警">
    <header class="warning-header">
      <div class="header-copy">
        <div class="eyebrow">COHORT · COMPOSITE SCREENING</div>
        <h4>特异性高危易感人群预警榜 <span class="scope-badge">本批次相对预警 · 非临床诊断</span></h4>
        <p>逐人计算 12 项结局，再将共同可用结局的全群名次转为百分位、等权合成；不再按某一个指标直接排序。</p>
      </div>
      <label class="threshold-control"><span>综合预警阈值 / 100</span><input type="number" :value="warning.threshold ?? ''" min="0" max="100" step="5" aria-label="综合预警阈值" @change="onThresholdChange" /></label>
    </header>

    <div class="warning-body">
      <section class="ranking-pane" aria-label="综合相对预警对象排序">
        <template v-if="warning.status === 'ALERT'">
          <div class="pane-title"><div><h5>综合相对预警对象</h5><p>全部 {{ warning.evaluated_count }} 名可比较对象中，{{ warning.warning_count }} 人达到阈值 {{ thresholdText }}；下图仅截取榜单显示。</p></div><el-select v-model="rankLimit" size="small" style="width: 96px" aria-label="榜单显示人数"><el-option label="Top 10" :value="10" /><el-option label="Top 20" :value="20" /></el-select></div>
          <div ref="rankRef" class="warning-rank-chart" :style="{ height: rankLimit === 20 ? '480px' : '320px' }"></div>
          <p class="chart-caption">纵轴为规范编号 P-000001 等，按原始文件行固定生成；悬停查看原始编号，展开下方明细可查看 12 项名次。</p>
        </template>
        <div v-else-if="warning.status === 'CLEAR'" class="clear-state">
          <div class="clear-icon" aria-hidden="true"><svg viewBox="0 0 56 56" fill="none"><path d="M28 5 46 12v14c0 11-8 19-18 25C18 45 10 37 10 26V12L28 5Z" stroke="currentColor" stroke-width="2.5" /><path d="m19 27 6 6 13-14" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" /></svg></div>
          <span class="clear-kicker">本批次 · 当前阈值</span><h5>暂无相对预警对象</h5><p>本次综合分最高为 <strong>{{ scoreText(warning.max_score) }}</strong>，未达到预警阈值 <strong>{{ thresholdText }}</strong>。</p>
          <div class="clear-metrics"><div><strong>0 <small>/ {{ warning.evaluated_count }} 人</small></strong><span>达到综合阈值</span></div><div><strong>{{ warning.available_outcome_count }} <small>/ 12 项</small></strong><span>共同有效结局</span></div></div>
          <p class="clear-caution">绿色仅表示未达到本次相对排序阈值，不代表健康、无病或没有暴露风险。</p>
        </div>
        <div v-else class="insufficient-state" role="status"><div class="insufficient-icon" aria-hidden="true">!</div><span class="clear-kicker">暂不能形成综合预警</span><h5>可比较数据不足</h5><p>{{ warning.reason }}</p><p class="insufficient-boundary">需要至少 5 名可比较对象、至少 3 项共同有效结局。缺失与暂不出值不补零，也不显示绿色“无预警”。</p></div>
      </section>

      <aside class="share-pane" aria-label="高危预警对象人群占比">
        <h5>高危预警对象人群占比</h5><p class="share-subtitle">按综合分达到当前阈值计算，不是患病率。</p>
        <div v-if="shareOption" ref="shareRef" class="warning-share-chart"></div>
        <div v-else class="share-unavailable"><strong>—</strong><span>暂不计算占比</span></div>
        <div class="share-counts"><div><span>相对预警对象</span><strong>{{ warning.status === 'INSUFFICIENT_DATA' ? '—' : warning.warning_count }}<small> 人</small></strong></div><div><span>可比较对象 · 占比分母</span><strong>{{ warning.evaluated_count }}<small> 人</small></strong></div><div><span>未纳入综合比较</span><strong class="neutral-number">{{ warning.not_evaluated_count }}<small> 人</small></strong></div></div>
        <p class="share-denominator">上传共 {{ warning.total_records }} 人。分母仅为使用相同有效结局完成综合比较的对象；不以全部上传人数或有效输入人数冒充。</p>
      </aside>
    </div>

    <footer class="method-strip"><span><i></i>共同结局 {{ warning.available_outcome_count }} / 12 项</span><span>各项名次百分位等权平均</span><span>HDL 取低值端，其余取高值端</span><span>综合分 ≥ {{ thresholdText }} 进入预警</span></footer>
    <p class="warning-boundary">{{ warning.scope_note }} 此阈值仅用于本文件内的相对筛查，尚无经外部验证的临床高危界值；显示分数保留 1 位小数，阈值判定使用原始精度。修改阈值只更新本页统计，不重新调用模型。</p>
    <details v-if="warning.excluded_targets.length" class="excluded-outcomes"><summary>{{ warning.excluded_targets.length }} 项结局未参与综合评分，查看原因</summary><ul><li v-for="item in warning.excluded_targets" :key="item.target"><strong>{{ item.label_zh }}</strong><span>{{ item.reason }}</span></li></ul></details>

    <details class="ranking-details">
      <summary>查看全部对象综合排名与 12 项结局名次（含原编号溯源）</summary>
      <p class="details-note">单项名次按对应方向由需关注端向另一端排列；同值并列平均名次。表格分页仅用于展示，所有对象均已参与完整计算。</p>
      <div class="ranking-table-scroll"><table><thead><tr><th class="id-column">规范编号 / 原始编号</th><th>综合名次</th><th>综合分 / 100</th><th>状态</th><th v-for="item in outcomeHeaders" :key="item.target">{{ item.label_zh }}<small>{{ item.direction === 'LOW' ? '低值端优先' : '高值端优先' }}</small></th></tr></thead><tbody><tr v-for="row in visibleRows" :key="row.row_number" :class="{ 'warning-row': row.is_warning }"><td class="id-column"><strong>{{ row.display_id }}</strong><small>原 ID：{{ row.person_id }} · 行 {{ row.row_number }}</small></td><td>{{ row.rank ?? '—' }}</td><td class="score-cell">{{ scoreText(row.score) }}</td><td><span class="row-status" :class="row.is_warning ? 'is-warning' : row.status === 'EVALUATED' ? 'is-evaluated' : 'not-evaluated'" :title="row.reason">{{ row.is_warning ? '相对预警' : row.status === 'EVALUATED' ? '未达阈值' : '未评估' }}</span></td><td v-for="item in row.outcomes" :key="item.target" :title="item.reason || item.label_zh"><template v-if="item.rank !== null && item.percentile !== null"><strong>第 {{ scoreText(item.rank) }} 名</strong><small>{{ scoreText(item.value) }} {{ item.unit }}</small><small>百分位 {{ scoreText(item.percentile) }}</small></template><span v-else class="unavailable-value">暂不排名</span></td></tr></tbody></table></div>
      <div class="ranking-pagination"><span>共 {{ warning.total_records }} 人；全部保留原始编号与未评估原因。</span><el-pagination v-model:current-page="tablePage" :page-size="20" :total="orderedRows.length" layout="total, prev, pager, next" /></div>
    </details>
  </article>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { CohortPredictionResponse } from '~/utils/riskCohort'
import { buildCohortWarning, buildWarningRankOption, buildWarningShareOption } from '~/utils/cohortWarning'
import { formatPredictionNumber } from '~/utils/riskPrediction'

const props = withDefaults(defineProps<{ result: CohortPredictionResponse; threshold?: number }>(), { threshold: 80 })
const emit = defineEmits<{ (event: 'update:threshold', value: number): void }>()
const warning = computed(() => buildCohortWarning(props.result, props.threshold))
const stateClass = computed(() => ({ 'state-alert': warning.value.status === 'ALERT', 'state-clear': warning.value.status === 'CLEAR', 'state-insufficient': warning.value.status === 'INSUFFICIENT_DATA' }))
const thresholdText = computed(() => scoreText(warning.value.threshold))
const rankLimit = ref(10)
const rankOption = computed(() => buildWarningRankOption(warning.value, rankLimit.value))
const shareOption = computed(() => buildWarningShareOption(warning.value))
const tablePage = ref(1)
const orderedRows = computed(() => [...warning.value.rows].sort((a, b) => (a.rank ?? Number.MAX_SAFE_INTEGER) - (b.rank ?? Number.MAX_SAFE_INTEGER) || a.row_number - b.row_number))
const visibleRows = computed(() => orderedRows.value.slice((tablePage.value - 1) * 20, tablePage.value * 20))
const outcomeHeaders = computed(() => warning.value.rows[0]?.outcomes || [])
const scoreText = (value: number | null | undefined) => formatPredictionNumber(value, 1)
function setThreshold(value: number | undefined) { if (typeof value === 'number' && Number.isFinite(value) && value >= 0 && value <= 100) emit('update:threshold', value) }
function onThresholdChange(event: Event) {
  const input = event.currentTarget as HTMLInputElement
  const value = input.valueAsNumber
  if (Number.isFinite(value) && value >= 0 && value <= 100) {
    setThreshold(value)
    input.value = String(value)
  } else input.value = Number.isFinite(props.threshold) ? String(props.threshold) : ''
}

const rankRef = ref<HTMLElement | null>(null)
const shareRef = ref<HTMLElement | null>(null)
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
  if (typeof ResizeObserver !== 'undefined') observer = new ResizeObserver(resizeCharts)
  for (const [element, option] of [[rankRef.value, rankOption.value], [shareRef.value, shareOption.value]] as const) if (element && option && element.clientWidth > 0 && element.clientHeight > 0) { const chart = echarts.init(element); chart.setOption(option); instances.push(chart); observer?.observe(element) }
}
function resume() { if (!mounted || active) return; active = true; window.addEventListener('resize', resizeCharts); void renderCharts() }
function pause() { active = false; window.removeEventListener('resize', resizeCharts); clearCharts() }
watch(() => [props.result, props.threshold, rankLimit.value], () => { void renderCharts() }, { deep: false })
watch(() => [props.result.file_id, props.threshold], () => { tablePage.value = 1 })
onMounted(() => { mounted = true; resume() })
onActivated(resume)
onDeactivated(pause)
onBeforeUnmount(() => { pause(); mounted = false })
</script>

<style scoped>
*{box-sizing:border-box}.cohort-warning-card{--state:#ef4444;--state-dark:#991b1b;--state-tint:#fff1f2;grid-column:1/-1;min-width:0;background:#fff;border:1px solid #fecaca;border-top:4px solid var(--state);border-radius:12px;padding:26px 26px 20px;box-shadow:0 5px 18px #0f172a04;color:#0f172a}.warning-header{display:flex;justify-content:space-between;align-items:flex-start;gap:26px;padding-bottom:20px;border-bottom:1px solid #edf2f7}.eyebrow{font-size:10px;font-weight:700;letter-spacing:.14em;color:var(--state);margin-bottom:9px}.warning-header h4{font-size:17px;line-height:1.7;display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:0;color:var(--state-dark)}.scope-badge{font-size:10px;font-weight:500;line-height:1.8;color:#64748b;background:#f8fafc;border:1px solid #e2e8f0;padding:2px 8px;border-radius:4px}.warning-header p{font-size:12px;line-height:1.9;color:#7c8fa6;margin:8px 0 0;max-width:820px}.threshold-control{display:grid;gap:9px;flex:0 0 auto;font-size:11px;color:#60758c}.threshold-control :deep(.el-input-number){width:128px}.warning-body{display:grid;grid-template-columns:minmax(0,2fr) minmax(260px,1fr);gap:28px;padding:24px 0 18px}.ranking-pane{min-width:0}.share-pane{min-width:0;border-left:1px dashed #dbe5ed;padding:0 0 0 28px;display:flex;flex-direction:column}.pane-title{display:flex;justify-content:space-between;gap:14px;align-items:flex-start}.pane-title h5,.share-pane h5{font-size:14px;line-height:1.8;margin:0;color:var(--state-dark)}.pane-title p,.share-subtitle{font-size:11px;line-height:1.9;color:#8394a8;margin:7px 0 0}.warning-rank-chart{width:100%;margin:12px 0 0}.chart-caption{font-size:10px;line-height:1.8;color:#91a0b3;margin:2px 0 0}.warning-share-chart{height:232px;width:100%;flex:0 0 auto}.share-counts{display:grid;gap:12px;margin-top:auto}.share-counts>div{display:flex;justify-content:space-between;align-items:baseline;gap:10px;font-size:11px;color:#7d8fa3}.share-counts strong{font-size:18px;color:var(--state);font-variant-numeric:tabular-nums}.share-counts strong small{font-size:10px;font-weight:400;color:#8da0b4}.share-counts strong.neutral-number{color:#8795a5}.share-denominator{font-size:10px;line-height:1.9;color:#94a3b8;margin:16px 0 0}.method-strip{display:flex;gap:15px 22px;flex-wrap:wrap;align-items:center;padding:13px 16px;border-radius:7px;background:#f8fafc;font-size:10px;line-height:1.8;color:#7c8ea2}.method-strip span{display:flex;align-items:center;gap:6px}.method-strip i{width:6px;height:6px;border-radius:50%;display:inline-block;background:var(--state)}.warning-boundary{font-size:10px;line-height:1.9;color:#97a3b3;margin:12px 0 0}.clear-state,.insufficient-state{min-height:365px;padding:27px 28px 13px;text-align:center;display:flex;flex-direction:column;align-items:center;justify-content:center;background:radial-gradient(ellipse at 50% 35%,#ecfdf5 0,transparent 66%)}.clear-icon{width:70px;height:70px;display:flex;align-items:center;justify-content:center;color:#059669;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:22px;box-shadow:0 7px 24px #10b9810a;margin-bottom:18px}.clear-icon svg{width:48px;height:48px}.clear-kicker{font-size:10px;letter-spacing:.08em;color:#55a68c}.clear-state h5,.insufficient-state h5{font-size:22px;color:#047857;line-height:1.6;margin:8px 0 10px}.clear-state>p{font-size:12px;line-height:1.9;color:#76968a;margin:0}.clear-state>p strong{font-weight:600;color:#078469}.clear-metrics{display:flex;justify-content:center;gap:48px;margin:24px 0 21px}.clear-metrics>div{display:grid;gap:7px}.clear-metrics strong{color:#059669;font-size:26px;line-height:1.3;font-variant-numeric:tabular-nums}.clear-metrics strong small{font-size:12px;font-weight:400;color:#87a799}.clear-metrics span{font-size:10px;color:#8ba398}.clear-state p.clear-caution{font-size:10px;color:#91a29b;max-width:440px}.state-clear{--state:#10b981;--state-dark:#047857;--state-tint:#ecfdf5;border-color:#a7f3d0}.state-clear .method-strip{background:#f2fcf7}.state-insufficient{--state:#d69a31;--state-dark:#956215;--state-tint:#fffaf0;border-color:#eadbbd}.insufficient-state{background:radial-gradient(ellipse at 50% 35%,#fffbeb 0,transparent 66%)}.insufficient-icon{width:57px;height:57px;border-radius:18px;border:1px solid #f7deaa;background:#fffbeb;color:#b78222;display:flex;align-items:center;justify-content:center;font:500 32px Georgia,serif;margin-bottom:18px}.insufficient-state .clear-kicker{color:#ae925d}.insufficient-state h5{color:#956215}.insufficient-state p{font-size:12px;color:#9b8b70;line-height:1.9;margin:0;max-width:490px}.insufficient-state p.insufficient-boundary{font-size:10px;color:#a5a1a0;margin-top:17px}.share-unavailable{height:232px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;color:#b0b9c4}.share-unavailable strong{font-weight:400;font-size:44px}.share-unavailable span{font-size:11px}.excluded-outcomes,.ranking-details{font-size:11px;color:#8a98aa;line-height:1.9;margin-top:14px}.excluded-outcomes summary,.ranking-details summary{cursor:pointer;font-weight:600}.excluded-outcomes ul{padding-left:18px;margin:10px 0}.excluded-outcomes li{margin:5px 0}.excluded-outcomes li strong{font-weight:500;color:#7a8a9e;margin-right:12px}.ranking-details{border-top:1px solid #edf2f7;padding-top:16px}.ranking-details summary{color:#5b7d9d}.details-note{font-size:10px;color:#94a3b8;margin:12px 0}.ranking-table-scroll{overflow-x:auto;border:1px solid #e6edf4;border-radius:6px}.ranking-table-scroll table{width:max-content;min-width:100%;border-collapse:collapse;text-align:left;font-size:11px}.ranking-table-scroll th{font-weight:600;white-space:nowrap;padding:13px 14px;background:#f3f8fc;color:#6a8299;border-bottom:1px solid #e6edf4;min-width:115px}.ranking-table-scroll td{padding:13px 14px;color:#74899d;border-top:1px solid #edf2f7;vertical-align:middle;line-height:1.9}.ranking-table-scroll td strong{font-weight:500}.ranking-table-scroll small{display:block;font-weight:400;font-size:9px;color:#a2afbd;line-height:1.8}.id-column{min-width:175px!important}.id-column strong{color:#4b7091;letter-spacing:.03em}.id-column small{max-width:210px;overflow-wrap:anywhere}.score-cell{font-weight:600;color:#d45f5f!important}.warning-row{background:#fffafa}.row-status{padding:3px 7px;border-radius:4px;white-space:nowrap;font-size:10px}.is-warning{background:#fff0f0;color:#db5656}.is-evaluated{background:#f0faf6;color:#429e7f}.not-evaluated{background:#faf6ed;color:#b19870}.unavailable-value{color:#a8b2be;font-size:10px}.ranking-pagination{display:flex;align-items:center;justify-content:space-between;gap:20px;margin-top:17px;font-size:10px;color:#9ba7b5}@media(min-width:1500px){.warning-body{grid-template-columns:minmax(0,2.3fr) minmax(290px,1fr)}}@media print{.threshold-control,.ranking-pagination{display:none}.cohort-warning-card{box-shadow:none;break-inside:avoid}.warning-body{grid-template-columns:minmax(0,2fr) minmax(240px,1fr)}}
.threshold-control input{width:128px;height:32px;padding:0 10px;background:#fff;color:#60758c;font:inherit;font-size:12px;line-height:30px;border:1px solid #dce4ec;border-radius:4px;outline:none;box-shadow:0 1px 2px #0f172a03;transition:border-color .15s,box-shadow .15s}.threshold-control input:hover{border-color:#b7c8da}.threshold-control input:focus{border-color:#6da5ec;box-shadow:0 0 0 2px #3b82f615}
/* The rank and share remain one desktop card, with a quiet internal separator. */
.cohort-warning-card{border-radius:14px;padding:25px 26px 21px;box-shadow:0 4px 16px #102a4305}
.warning-header{padding-bottom:18px;border-bottom:1px dashed #e8eef7;gap:24px}
.eyebrow{font-size:9px;letter-spacing:.11em;margin-bottom:7px}
.warning-header h4{font-size:17px;font-weight:700;color:#172033;line-height:1.6}
.scope-badge{border-radius:5px;background:#f8fafc;border-color:#e2eaf4;color:#78879c;font-size:10px;padding:2px 7px;font-weight:400}
.warning-header p{font-size:12px;line-height:1.8;color:#7b899e;max-width:800px;margin-top:8px}
.threshold-control{gap:8px;color:#7d8ca0;font-size:10px;background:#f8fafc;padding:10px 12px;border:1px solid #edf2f7;border-radius:8px}
.threshold-control input{height:34px;border-radius:6px;font-size:13px;font-weight:500;color:#475569;background:#fff;width:116px;font-variant-numeric:tabular-nums}
.warning-body{padding-top:23px;gap:26px}
.share-pane{padding-left:26px;border-left-color:#dce5f1}
.pane-title h5,.share-pane h5{font-size:14px;font-weight:700;color:#334155}
.pane-title p,.share-subtitle{color:#8795a8;font-size:11px;line-height:1.8}
.warning-rank-chart{margin-top:13px}
.chart-caption{font-size:10px;line-height:1.8;color:#8796aa;margin-top:3px}
.warning-share-chart{height:240px;margin-top:7px}
.share-counts{gap:0;padding:3px 0;margin-top:11px}
.share-counts>div{padding:10px 0;border-bottom:1px dashed #e8eef7;font-size:11px;color:#8190a4}
.share-counts>div:last-child{border-bottom:0}
.share-counts strong{font-size:19px;font-weight:600}
.share-denominator{color:#8b99ac;font-size:10px;line-height:1.85;margin-top:12px}
.method-strip{background:#f8fafd;border-radius:8px;padding:12px 15px;gap:11px 23px;color:#7c8ba0;border:1px solid #edf2f8}
.warning-boundary{color:#8b99ac;font-size:10px;line-height:1.85;margin-top:13px}
.clear-state{border-radius:12px;background:radial-gradient(ellipse at 50% 35%,#e4faef 0,#f9fefb 45%,#fff 80%);min-height:365px}
.clear-icon{width:74px;height:74px;border-radius:23px;background:linear-gradient(145deg,#ecfdf5,#dcfce7);box-shadow:0 7px 26px #10b98110}
.clear-state h5{font-size:23px;font-weight:600;letter-spacing:.3px}
.clear-metrics{padding:16px 28px;background:#ffffffb3;border:1px solid #def4e9;border-radius:12px;margin:22px 0 18px;gap:40px}
.clear-metrics strong{font-size:28px;font-weight:600}
.state-clear .method-strip{border-color:#e5f4ed;background:#f6fcf9}
.insufficient-state{border-radius:12px}
.ranking-details{border-top:1px dashed #e8eef7;margin-top:17px;padding-top:17px}
.ranking-details summary,.excluded-outcomes summary{font-size:11px;font-weight:500}
.ranking-table-scroll{border-radius:9px;border-color:#e2eaf4}
.ranking-table-scroll th{background:#f6f9fe;color:#596e88}
.ranking-table-scroll td{border-color:#edf2f8}
.ranking-table-scroll tbody tr:nth-child(even):not(.warning-row){background:#fbfdff}
.warning-row{background:#fff8f8}
.row-status{border-radius:5px;padding:4px 8px}
.id-column strong{font-weight:600!important}
@media(max-width:1200px){.warning-body{grid-template-columns:minmax(0,1.8fr) minmax(250px,1fr);gap:22px}.share-pane{padding-left:22px}.warning-header{gap:20px}.warning-header h4{font-size:16px}}
@media print{.cohort-warning-card{box-shadow:none}.warning-share-chart{height:232px}.clear-state{background:#f8fdfb}}
</style>
