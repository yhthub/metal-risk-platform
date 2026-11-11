<template>
  <section ref="workspace" class="plan-work" :aria-labelledby="uid + '-title'">
    <header class="work-head">
      <div>
        <h2 :id="uid + '-title'">实施计划与随访</h2>
        <p>按措施核对执行安排，或查看随访时需要记录的指标。</p>
      </div>
      <div class="view-switch" role="tablist" aria-label="计划工作视图" @keydown="navigateTabs">
        <button v-for="item in views" :id="uid + '-tab-' + item.key" :key="item.key" type="button" role="tab"
          :aria-selected="view === item.key" :aria-controls="uid + '-panel-' + item.key" :tabindex="view === item.key ? 0 : -1"
          @click="view = item.key">
          <el-icon aria-hidden="true"><component :is="item.icon" /></el-icon>{{ item.label }}
        </button>
      </div>
    </header>

    <div v-show="view === 'implementation'" :id="uid + '-panel-implementation'" class="work-view" role="tabpanel" :aria-labelledby="uid + '-tab-implementation'">
      <div class="view-lead">
        <h3>措施安排</h3><span>勾选仅表示已核对内容，不代表措施已实施。</span>
      </div>
      <ol v-if="steps.length" class="step-list">
        <li v-for="(step, i) in steps" :key="stepKey(step, i)" class="step-row" :data-row="i" tabindex="-1">
          <div class="step-order" aria-hidden="true">{{ ordinal(i) }}</div>
          <div class="step-content">
            <div class="step-columns">
              <div class="measure">
                <span v-if="step.tag" class="category" :class="categoryStyle(step)">{{ step.tag }}</span>
                <h4>{{ step.title }}</h4>
                <p v-if="step.desc">{{ step.desc }}</p>
                <dl v-if="step.period || step.owner" class="measure-meta">
                  <div v-if="step.period"><dt><el-icon aria-hidden="true"><Clock /></el-icon>计划时段</dt><dd>{{ step.period }}</dd></div>
                  <div v-if="step.owner"><dt><el-icon aria-hidden="true"><User /></el-icon>建议分工</dt><dd>{{ step.owner }}</dd></div>
                </dl>
              </div>
              <div v-if="step.indicator" class="indicator"><strong>核查要点</strong><p>{{ step.indicator }}</p></div>
            </div>
            <div class="step-tools">
              <button v-if="step.detail" type="button" class="detail-toggle" :aria-expanded="expanded === i" :aria-controls="uid + '-details-' + i" @click="expanded = expanded === i ? null : i">
                <el-icon aria-hidden="true" :class="{ rotated: expanded === i }"><ArrowRight /></el-icon>{{ expanded === i ? '收起实施说明' : '展开实施说明' }}
              </button>
              <label class="check-item" :class="{ checked: isChecked(step, i) }">
                <input type="checkbox" :aria-label="'核对措施：' + step.title" :checked="isChecked(step, i)" @change="toggleCheck(step, i)">
                {{ isChecked(step, i) ? '已核对' : '标记已核对' }}
              </label>
            </div>
            <div v-if="step.detail" v-show="expanded === i" :id="uid + '-details-' + i" class="execution-note">{{ step.detail }}</div>
          </div>
        </li>
      </ol>
      <p v-else class="empty">当前方案暂无实施措施。</p>
    </div>

    <div v-show="view === 'monitoring'" :id="uid + '-panel-monitoring'" class="work-view" role="tabpanel" :aria-labelledby="uid + '-tab-monitoring'">
      <div class="monitoring-heading">
        <img v-if="view === 'monitoring'" data-platform-art="follow-up" :src="followUpArt" alt="" width="69" height="46">
        <div><h3>随访记录要求</h3><p>以下为待采集项目，尚未录入随访结果。</p></div>
      </div>
      <div v-if="person.outcomes?.length" class="record-wrap">
        <table class="records">
          <caption class="sr-only">当前方案的随访指标、记录内容和资料来源</caption>
          <thead><tr><th scope="col">随访指标</th><th scope="col">记录内容</th><th scope="col">资料来源</th></tr></thead>
          <tbody><tr v-for="item in person.outcomes" :key="item.label">
            <th scope="row">{{ item.label }}</th>
            <td><span class="mobile-label" aria-hidden="true">记录内容</span>{{ item.record || '待补充' }}</td>
            <td class="record-source"><span class="mobile-label" aria-hidden="true">资料来源</span>{{ item.source || '待补充' }}</td>
          </tr></tbody>
        </table>
      </div>
      <p v-else class="empty">当前方案尚未列出随访指标。</p>
      <template v-if="steps.some(step => step.indicator)">
        <div class="view-lead review-lead"><h3>措施核查清单</h3></div>
        <ol class="review-list">
          <template v-for="(step, i) in steps" :key="stepKey(step, i)">
            <li v-if="step.indicator">
              <span class="review-number" aria-hidden="true">{{ ordinal(i) }}</span>
              <div><h4>{{ step.title }}</h4><p>{{ step.indicator }}</p></div>
              <button type="button" class="jump" :aria-label="'查看实施措施：' + step.title" @click="openStep(i)">查看措施<el-icon aria-hidden="true"><ArrowRight /></el-icon></button>
            </li>
          </template>
        </ol>
      </template>
    </div>
  </section>
</template>

<script setup lang="ts">
import { planStepKey as stepKey, usePlanChecks } from '~/composables/usePlanChecks'
import { computed, nextTick, ref, useId, watch } from 'vue'
import { ArrowRight, Calendar, Clock, List, User } from '@element-plus/icons-vue'
import followUpArt from '~/assets/illustrations/workflow/follow-up.svg?no-inline'

type Measure = { title: string; tag?: string; type?: string; desc?: string; detail?: string; indicator?: string; period?: string; owner?: string }
type PlanObject = { id: string; workflow?: Measure[]; outcomes?: { label: string; record?: string; source?: string }[] }
type View = 'implementation' | 'monitoring'
const props = defineProps<{ person: PlanObject }>()
const views = [{ key: 'implementation', label: '实施计划', icon: List }, { key: 'monitoring', label: '随访监测', icon: Calendar }] as const
const uid = useId()
const workspace = ref<HTMLElement>()
const view = useState<View>('intervention-work-view', () => 'implementation')
// Only anonymous plan IDs and measure keys remain in this Nuxt session. This is a review aid, not a clinical record.
const { isReviewed, toggleReviewed } = usePlanChecks()
const expanded = ref<number | null>(0)
const steps = computed(() => props.person.workflow || [])
watch(() => props.person.id, () => { expanded.value = 0 })
const ordinal = (i: number) => String(i + 1).padStart(2, '0')
const isChecked = (step: Measure, i: number) => isReviewed(props.person.id, stepKey(step, i))
const toggleCheck = (step: Measure, i: number) => toggleReviewed(props.person.id, stepKey(step, i))
function categoryStyle(step: Measure) {
  if (step.type === 'danger' || step.type === 'warning') return 'category-amber'
  if (step.type === 'safe' || step.type === 'success') return 'category-teal'
  return 'category-indigo'
}
async function navigateTabs(event: KeyboardEvent) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  view.value = event.key === 'Home' ? 'implementation' : event.key === 'End' ? 'monitoring' : view.value === 'implementation' ? 'monitoring' : 'implementation'
  await nextTick()
  workspace.value?.querySelector<HTMLButtonElement>('[role="tab"][aria-selected="true"]')?.focus()
}
async function openStep(i: number) {
  view.value = 'implementation'
  expanded.value = i
  await nextTick()
  const row = workspace.value?.querySelector<HTMLElement>('[data-row="' + i + '"]')
  row?.focus({ preventScroll: true })
  row?.scrollIntoView({ block: 'nearest' })
}
</script>

<style scoped>
.plan-work{container-type:inline-size;min-width:0;color:#172c48;font-size:14px;--work-line:#dce5ed;--work-muted:#4f6377;--work-ink:#243e71;--work-teal:#166254}
.work-head{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:8px 0 17px;border-bottom:2px solid #cddce8}
.work-head h2,.view-lead h3,.measure h4,.review-list h4{margin:0;color:#192f48;line-height:1.45;font-weight:740}
.work-head h2{font-size:clamp(19px,2vw,23px);letter-spacing:.01em}
.work-head p{margin:5px 0 0;color:var(--work-muted);font-size:13px;line-height:1.65}
.view-switch{display:inline-flex;flex-shrink:0;gap:3px;align-items:center;background:#eaf0f6;padding:4px;border:1px solid #d5e0ea;border-radius:11px}
.view-switch button,.step-tools button,.jump{font:inherit;cursor:pointer;border:0}
.view-switch button{display:inline-flex;gap:6px;align-items:center;justify-content:center;min-height:36px;padding:5px 13px;font-size:13px;font-weight:650;background:transparent;color:#465e76;border-radius:7px}
.view-switch button[aria-selected="true"]{color:#fff;background:#294673;box-shadow:0 1px 4px #1b345329}
.view-switch button:not([aria-selected="true"]):hover{background:#f9fbfd}
.view-lead{display:flex;justify-content:space-between;align-items:baseline;gap:6px 16px;flex-wrap:wrap;margin:16px 0 11px}
.view-lead h3{font-size:16px}
.monitoring-heading{display:flex;align-items:center;gap:13px;margin:16px 0 12px}
.monitoring-heading img{flex:none;display:block;width:clamp(54px,5vw,69px);height:auto}
.monitoring-heading h3{margin:0;color:#192f48;font-size:16px;line-height:1.45}
.monitoring-heading p{margin:2px 0 0;font-size:12px;line-height:1.7;color:var(--work-muted)}
.view-lead>span,.empty{font-size:12px;line-height:1.7;color:var(--work-muted)}
.step-list,.review-list{margin:0;padding:0;list-style:none}
.step-list,.record-wrap,.review-list{background:#fff;border:1px solid var(--work-line);border-radius:13px}
.step-row{display:grid;grid-template-columns:30px minmax(0,1fr);gap:14px;padding:19px 20px;scroll-margin:72px;position:relative}
.step-row+.step-row,.review-list li+li{border-top:1px solid var(--work-line)}
.step-order,.review-number{font-variant-numeric:tabular-nums;font-weight:730;line-height:1;font-size:13px}
.step-order{display:grid;place-items:center;width:30px;height:32px;border-radius:8px;background:#edf1fa;color:#334e82;border:1px solid #dce4f3}
.step-content,.measure,.indicator{min-width:0;overflow-wrap:anywhere}
.step-columns{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:20px}
.category{display:inline-block;font-size:11px;line-height:1.55;font-weight:650;padding:2px 7px;border-radius:5px}
.category-indigo{color:#354e86;background:#edf1fb}.category-teal{color:#116251;background:#e6f4ef}.category-amber{color:#874b17;background:#fbefdf}
.measure h4{margin-top:5px;font-size:17px}
.measure p,.indicator p,.execution-note,.review-list p{margin:5px 0 0;color:#44586c;font-size:13px;line-height:1.7}
.measure-meta{display:flex;flex-wrap:wrap;gap:3px 14px;margin:8px 0 0}
.measure-meta div,.measure-meta dt{display:inline-flex;align-items:baseline;gap:4px}
.measure-meta dt,.measure-meta dd{font-size:12px;line-height:1.6;margin:0}
.measure-meta dt{color:var(--work-muted);white-space:nowrap}
.measure-meta dt .el-icon{align-self:center;font-size:13px}
.measure-meta dd{color:#2d455d;font-weight:600}
.indicator{align-self:start;border-left:2px solid #9bcabe;padding:0 0 0 12px;margin-top:2px}
.indicator strong{color:var(--work-teal);font-weight:680;font-size:12px}
.indicator p{margin-top:3px;color:#36564e}
.step-tools{display:flex;align-items:center;gap:8px 16px;flex-wrap:wrap;margin-top:8px}
.detail-toggle,.jump,.check-item{display:inline-flex;align-items:center;gap:4px;min-height:32px;line-height:1.5}
.step-tools .detail-toggle,.jump{padding:2px 0;font-size:12px;font-weight:650;background:transparent;color:var(--work-ink)}
.detail-toggle .el-icon,.jump .el-icon{font-size:12px}.detail-toggle .rotated{transform:rotate(90deg)}
.detail-toggle:hover,.jump:hover{text-decoration:underline;text-underline-offset:3px}
.check-item{margin-inline-start:auto;font-size:12px;color:#465d71;cursor:pointer;white-space:nowrap}
.check-item input{accent-color:#176c58;width:16px;height:16px;margin:0 2px 0 0;cursor:pointer}
.check-item.checked{color:var(--work-teal);font-weight:650}
.execution-note{margin-top:5px;padding:10px 13px;background:#f4f7fa;border-radius:7px;color:#344a61}
.records{width:100%;border-collapse:separate;border-spacing:0;font-size:13px;line-height:1.65;overflow-wrap:anywhere}
.records th,.records td{vertical-align:top;text-align:start;padding:12px 14px}
.records thead th{font-size:12px;color:#466656;font-weight:680;background:#edf5f2}
.records thead th:first-child{border-start-start-radius:12px}
.records thead th:last-child{border-start-end-radius:12px}
.records tbody th{width:24%;font-weight:680;color:#25443d}
.records tbody td{color:#354b5e}.records tbody .record-source{width:26%;color:var(--work-muted);font-size:12px}
.records tbody tr+tr>*{border-top:1px solid var(--work-line)}
.review-lead{margin-top:23px}
.review-list li{display:grid;grid-template-columns:26px minmax(0,1fr) auto;align-items:baseline;gap:10px;padding:12px 17px}
.review-number{color:var(--work-teal);font-size:12px}.review-list h4{font-size:14px}.review-list p{margin:3px 0 0}
.jump{white-space:nowrap}
.sr-only{position:absolute;width:1px;height:1px;padding:0;border:0;overflow:hidden;clip-path:inset(50%);white-space:nowrap}
.mobile-label{display:none}
.plan-work :where(button,input,[tabindex="-1"]):focus-visible{outline:2px solid #366db0;outline-offset:2px}
@container (max-width:690px){
  .work-head{align-items:flex-start;flex-direction:column;gap:12px}
  .step-row{padding:15px 14px;gap:10px}
  .step-columns{gap:14px}
}
@container (max-width:540px){
  .work-head{padding-bottom:12px}.view-switch{display:flex;align-self:stretch}.view-switch button{flex:1;min-height:40px}
  .view-lead{display:block;margin:13px 0 8px}.view-lead>span{display:block;margin-top:3px}
  .step-row{grid-template-columns:24px minmax(0,1fr);gap:8px;padding:14px 11px}
  .step-order{width:24px;height:27px;font-size:12px}
  .step-columns{grid-template-columns:minmax(0,1fr);gap:10px}
  .measure h4{font-size:16px}.indicator{margin:0;padding-left:9px}.detail-toggle,.check-item,.jump{min-height:42px}
  .step-tools{gap:4px 9px;margin-top:3px}.execution-note{margin-top:0}
  .records,.records tbody,.records tr,.records tbody th,.records tbody td{display:block}
  .records thead{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}
  .records tbody tr{padding:10px 13px}.records tbody tr+tr{border-top:1px solid var(--work-line)}.records tbody tr+tr>*{border:0}
  .records tbody th,.records tbody td,.records tbody .record-source{width:auto;padding:2px 0}
  .mobile-label{display:inline-block;margin-right:7px;font-size:11px;font-weight:650;color:var(--work-teal)}
  .review-lead{margin-top:18px}.review-list li{grid-template-columns:18px minmax(0,1fr);gap:1px 6px;padding:10px 12px}
  .jump{grid-column:2;justify-self:start}
}
</style>
