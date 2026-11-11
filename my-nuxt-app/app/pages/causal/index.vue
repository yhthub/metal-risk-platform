<template>
  <div class="system-layout causal-layout">
    <Sidebar default-active="4" />
    <main class="main-content">
      <header class="causal-nav">
        <NuxtLink :to="riskBack"><el-icon><ArrowLeft /></el-icon>返回风险分析</NuxtLink>
        <span aria-hidden="true">/</span><strong>因果知识推理</strong>
      </header>
      <div class="causal-workspace">
        <header class="workspace-title">
          <div><h1>暴露路径与干预依据</h1><p>比较单一与联合暴露的研究结果，沿所选关系查看原文和岗位核查事项。</p></div>
          <button id="open-atlas" class="quiet-action" @click="atlasOpen = true"><el-icon><Connection /></el-icon>路径总览</button>
        </header>
        <section class="filters" aria-label="浏览条件">
          <div class="field person-field">
            <label for="causal-person">浏览对象</label>
            <select id="causal-person" :value="personOption" @change="choosePerson(($event.target as HTMLSelectElement).value)">
              <option v-if="risk.mode" value="risk">{{ risk.mode === 'batch' ? '本次群体分析' : '本次单人分析' }}{{ risk.person ? ' · ' + risk.person : '' }}</option>
              <option value="">自由浏览</option>
              <option v-for="plan in interventionPlans" :key="plan.id" :value="plan.id">{{ plan.id }} · {{ plan.dept }}</option>
            </select>
          </div>
          <div class="field"><span id="metals-label">暴露因素 · 可多选</span>
            <div class="pills" role="group" aria-labelledby="metals-label">
              <button v-for="metal in metalOptions" :key="metal" :data-metal="metal" :aria-pressed="metals.includes(metal)" @click="toggleMetal(metal)">{{ metalNames[metal] }} <b>{{ metal }}</b></button>
            </div>
          </div>
          <div class="field"><span id="outcome-label">关注指标</span>
            <div class="pills" role="group" aria-labelledby="outcome-label">
              <button v-for="key in outcomeOptions" :key="key" :data-outcome="key" :aria-pressed="outcome === key" @click="changeOutcome(key)">{{ outcomeNames[key] }}</button>
            </div>
          </div>
        </section>
        <p v-if="risk.mode || selectedPlan" class="context-note">
          <el-icon><InfoFilled /></el-icon>
          <span v-if="risk.mode">{{ risk.current ? '来自本次风险分析' : '来自风险页的指标选择，当前会话没有对应分析记录' }}<template v-if="targetLabel"> · {{ targetLabel }}</template>。以下为相关文献所研究的结局。</span>
          <span v-else-if="selectedPlan">对象 {{ selectedPlan.id }} · {{ selectedPlan.dept }} · 档案记录的暴露因素 {{ selectedPlan.factors }}。</span>
        </p>

        <div class="study-grid">
          <section class="relations" aria-labelledby="relations-title">
            <header class="panel-head"><div><h2 id="relations-title">暴露与健康指标</h2><p>选择一条关系查看研究发现和适用范围。</p></div><span class="count">{{ filtered.length }} 条关系</span></header>
            <div v-if="!filtered.length" class="empty-state" role="status">
              <el-icon><Reading /></el-icon>
              <h3>{{ metals.length || uncoveredProfile ? '当前条件暂无收录关系' : '请选择至少一种暴露因素' }}</h3>
              <p v-if="uncoveredProfile">该对象档案记录的暴露因素为 {{ selectedPlan?.factors }}，当前尚未收录相应研究。可通过路径总览浏览其他暴露因素。</p>
              <p v-else>{{ metals.length ? '可更换指标、调整金属，或查看已收录的全部路径。' : '选择一种金属阅读单项研究，选择多种可同时查看匹配的联合研究。' }}</p>
              <button v-if="metals.length || uncoveredProfile" class="text-action" @click="atlasOpen = true">浏览已收录路径 <span aria-hidden="true">→</span></button>
            </div>
            <template v-else>
              <section v-for="group in groups" :key="group.id" class="path-group">
                <h3><i :class="group.id" aria-hidden="true" />{{ group.title }}<span>{{ group.items.length }}</span></h3>
                <template v-for="path in group.items" :key="path.id">
                  <button class="path-row" :class="{ selected: activePath?.id === path.id }"
                    :data-path-id="path.id" :aria-pressed="activePath?.id === path.id" @click="selectPath(path.id)">
                    <span class="path-flow">
                      <span class="exposure-node">{{ path.from }}</span>
                      <span class="path-arrow" aria-hidden="true"></span>
                      <span class="outcome-node">{{ path.to }}</span>
                    </span>
                    <span class="row-meta"><span>{{ path.relation }}</span><span>{{ path.source.year }} <span aria-hidden="true">›</span></span></span>
                  </button>
                  <div v-if="activePath?.id === path.id" class="mobile-detail"><CausalEvidenceDetail :path="path" /></div>
                </template>
              </section>
              <p v-if="comparisonNote" class="comparison-note">{{ comparisonNote }}</p>
            </template>
          </section>
          <aside class="desktop-detail" aria-label="关系详情">
            <CausalEvidenceDetail v-if="activePath" :path="activePath" />
            <div v-else class="no-evidence"><el-icon><Document /></el-icon><p>选中已收录的关系后，可在这里阅读原文依据。</p></div>
          </aside>
        </div>

        <section class="application" aria-labelledby="actions-title">
          <header class="panel-head">
            <div><h2 id="actions-title">岗位核查与方案</h2><p>{{ matchedPlan ? '可继续查看该对象已有方案的责任人、实施安排和核查指标。' : '按所选暴露因素查看可核查的现场措施。' }}</p></div>
            <NuxtLink v-if="metals.length || matchedPlan" id="causal-plan-link" class="primary-action" :to="planRoute">{{ matchedPlan ? '查看 ' + matchedPlan.id + ' 的方案' : '查看相关方案' }} <span aria-hidden="true">→</span></NuxtLink>
          </header>
          <div v-if="controls.length" class="control-list">
            <article v-for="control in controls" :key="control.id" class="control-item">
              <div class="control-icon"><el-icon><Finished /></el-icon></div>
              <div><h3>{{ control.label }}</h3><p>{{ control.text }}</p>
                <a :href="control.source.url" target="_blank" rel="noopener noreferrer">{{ control.source.issuer }} · {{ control.source.locator }} <el-icon><TopRight /></el-icon></a></div>
            </article>
          </div>
          <p v-else class="control-empty">当前选择暂无已核查的岗位措施来源。</p>
        </section>
      </div>
      <el-dialog v-model="atlasOpen" title="已收录路径总览" width="min(660px, 94vw)" append-to-body destroy-on-close>
        <p class="atlas-intro">按健康指标浏览，选择一条即可定位到对应研究。</p>
        <section v-for="group in atlasGroups" :key="group.id" class="atlas-group">
          <h3>{{ outcomeNames[group.id] }}</h3>
          <button v-for="path in group.items" :key="path.id" :data-atlas-path="path.id" @click="openFromAtlas(path)">
            <span><strong>{{ path.from }} → {{ path.to }}</strong><small>{{ path.sourceType }} · {{ path.source.year }}</small></span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </section>
      </el-dialog>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowLeft, ArrowRight, Connection, Document, Finished, InfoFilled, Reading, TopRight } from '@element-plus/icons-vue'
import { controlSources, metalNames, outcomeNames, pathways, selectPathways } from '~/utils/causalEvidence'
import type { CausalMetal, CausalOutcome, CausalPathway } from '~/utils/causalEvidence'
import { riskPathContext } from '~/utils/causalNavigation'
import { interventionPlans, getInterventionPlan } from '~/utils/interventionPlans'
import { COHORT_WARNING_TARGETS } from '~/utils/cohortWarning'
import { PRODUCT_SHORT_NAME } from '~/utils/product'

useHead({ title: '因果知识推理 · ' + PRODUCT_SHORT_NAME })
const route = useRoute()
const router = useRouter()
const state = usePredictionState()
const atlasOpen = ref(false)
const metalOptions: CausalMetal[] = ['Pb', 'Cd', 'Hg']
const risk = computed(() => riskPathContext(route.query, state.dashboard.value, state.cohortResult.value))
const riskBack = computed(() => risk.value.mode ? { path: '/risk', query: { mode: risk.value.mode } } : '/risk')
const selectedPlan = computed(() => getInterventionPlan(risk.value.mode ? risk.value.person : route.query.person))
const personOption = computed(() => risk.value.mode ? 'risk' : selectedPlan.value?.id || '')
const targetLabel = computed(() => COHORT_WARNING_TARGETS.find(t => t.target === risk.value.target)?.label_zh || '')
const riskOutcome = computed<CausalOutcome>(() => {
  if (!risk.value.mode) return 'renal'
  if (risk.value.target === 'sbp') return 'sbp'
  if (['uacr_mg_g', 'serum_creatinine_mg_dl'].includes(risk.value.target)) return 'renal'
  return 'unsupported'
})
const outcome = computed<CausalOutcome>(() => {
  const key = route.query.outcome
  return key === 'renal' || key === 'sbp' || key === 'unsupported' ? key : riskOutcome.value
})
const outcomeOptions = computed<CausalOutcome[]>(() => riskOutcome.value === 'unsupported' || outcome.value === 'unsupported'
  ? ['renal', 'sbp', 'unsupported'] : ['renal', 'sbp'])
const metals = computed<CausalMetal[]>(() => {
  if (typeof route.query.metals === 'string') {
    const values = route.query.metals.split(',')
    return metalOptions.filter(m => values.includes(m))
  }
  if (risk.value.mode === 'individual' && risk.value.current && state.dashboard.value) {
    const input = state.dashboard.value.input?.person
    return metalOptions.filter(m => typeof input?.[m.toLowerCase() as 'pb'|'cd'|'hg'] === 'number')
  }
  if (selectedPlan.value) return planMetals(selectedPlan.value.factors)
  return ['Pb', 'Cd']
})
const uncoveredProfile = computed(() => !risk.value.mode && selectedPlan.value && !route.query.metals &&
  !planMetals(selectedPlan.value.factors).length)
const filtered = computed(() => selectPathways(metals.value, outcome.value))
const activePath = computed(() => filtered.value.find(p => p.id === route.query.edge)
  || filtered.value.find(p => p.kind === 'joint') || filtered.value[0])
const groups = computed(() => [
  { id: 'joint', title: '联合暴露研究' }, { id: 'single', title: '单一金属研究' }, { id: 'mechanism', title: '实验机制研究' },
].map(g => ({ ...g, items: filtered.value.filter(p => p.kind === g.id) })).filter(g => g.items.length))
const comparisonNote = computed(() => {
  if (metals.value.length < 2) return ''
  const exactJoint = filtered.value.some(p => p.kind === 'joint' && p.metals.length === metals.value.length)
  return exactJoint ? '' : '本页尚未收录同时研究所选全部金属与该指标的资料。各金属的研究结果不能直接相加。'
})
const atlasGroups = computed(() => (['renal', 'sbp'] as const).map(id => ({ id, items: pathways.filter(p => p.outcome === id) })))
const controls = computed(() => controlSources.filter(c => c.metals.some(m => metals.value.includes(m))))
const matchedPlan = computed(() => selectedPlan.value && metals.value.length &&
  metals.value.every(m => planMetals(selectedPlan.value!.factors).includes(m)) ? selectedPlan.value : null)

function planMetals(factors: string) {
  const values = factors.split(',').map(m => m.trim())
  return metalOptions.filter(m => values.includes(m))
}
function selectionQuery(values = metals.value, topic = outcome.value, path = ''): Record<string,string> {
  const query: Record<string,string> = { metals: values.join(',') || 'none', outcome: topic }
  if (risk.value.mode) {
    query.from = 'risk'
    query.mode = risk.value.mode
    if (risk.value.target) query.target = risk.value.target
  } else if (selectedPlan.value) query.person = selectedPlan.value.id
  if (path) query.edge = path
  return query
}
function toggleMetal(metal: CausalMetal) {
  const values = metalOptions.filter(m => m === metal ? !metals.value.includes(m) : metals.value.includes(m))
  return router.replace({ path: '/causal', query: selectionQuery(values) })
}
function changeOutcome(topic: CausalOutcome) {
  return router.replace({ path: '/causal', query: selectionQuery(metals.value, topic) })
}
function selectPath(id: string) {
  return router.replace({ path: '/causal', query: selectionQuery(metals.value, outcome.value, id) })
}
function choosePerson(id: string) {
  const plan = getInterventionPlan(id)
  const query: Record<string,string> = { outcome: outcome.value === 'unsupported' ? 'renal' : outcome.value }
  if (plan) query.person = plan.id
  else query.metals = metals.value.join(',') || 'none'
  return router.replace({ path: '/causal', query })
}
function openFromAtlas(path: CausalPathway) {
  atlasOpen.value = false
  return router.replace({ path: '/causal', query: selectionQuery(path.metals, path.outcome, path.id) })
}
const planRoute = computed(() => {
  const query: Record<string,string> = { from: 'causal', metals: metals.value.join(','), outcome: outcome.value }
  if (activePath.value) query.edge = activePath.value.id
  if (matchedPlan.value) query.person = matchedPlan.value.id
  else {
    query.view = 'coverage'
    if (selectedPlan.value) query.pathPerson = selectedPlan.value.id
  }
  if (risk.value.mode) { query.sourceMode = risk.value.mode; query.sourceTarget = risk.value.target }
  return { path: '/plan', query }
})
</script>

<style scoped>
.causal-layout { display: flex; width: 100%; height: 100dvh; overflow: hidden; box-sizing: border-box; color: #253b50; background: #f5f8fb; font-family: inherit; }
.main-content { flex: 1; min-width: 0; min-height: 0; overflow-y: auto; }
.causal-nav { display: flex; align-items: center; gap: 15px; padding: 0 clamp(18px,3vw,44px); min-height: 54px; border-bottom: 1px solid #dfe7ee; background: #fff; font-size: 13px; }
.causal-nav a, .primary-action, .quiet-action, .text-action { display: inline-flex; align-items: center; justify-content: center; gap: 7px; text-decoration: none; }
.causal-nav a { color: #526b7e; }.causal-nav > span { color: #b4c2cf; }.causal-nav strong { font-weight: 650; }
.causal-workspace { box-sizing: border-box; max-width: 1340px; margin: 0 auto; padding: clamp(20px,3vw,44px) clamp(16px,3vw,42px) 60px; }
.workspace-title, .panel-head { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.workspace-title { margin-bottom: 20px; }
.workspace-title h1 { margin: 0; color: #193649; font-size: clamp(23px,2.3vw,34px); font-weight: 680; letter-spacing: -.035em; line-height: 1.3; }
.workspace-title p, .panel-head p { margin: 6px 0 0; color: #64778a; font-size: 13px; line-height: 1.7; }
button, select { font: inherit; }
button { cursor: pointer; }
.quiet-action { flex: none; border: 1px solid #cbd9e4; background: white; color: #365570; border-radius: 8px; min-height: 38px; padding: 0 12px; font-size: 13px; }
.quiet-action:hover { background: #eef4f8; }
.filters { display: flex; flex-wrap: wrap; align-items: flex-end; column-gap: clamp(18px,3vw,40px); row-gap: 14px; padding: 15px 20px; background: #edf2f6; border: 1px solid #dce5ec; border-radius: 12px; }
.field { display: grid; gap: 6px; min-width: 0; }
.field > label, .field > span { color: #526879; font-size: 12px; font-weight: 600; }
.person-field { min-width: min(190px,100%); }
.person-field select { width: 100%; max-width: 240px; min-height: 36px; border: 1px solid #c8d5df; border-radius: 7px; padding: 4px 7px; background: #fff; color: #283e50; font-size: 13px; cursor: pointer; }
.pills { display: flex; flex-wrap: wrap; gap: 6px; }
.pills button { min-height: 36px; border: 1px solid #ccd9e3; border-radius: 7px; padding: 4px 11px; color: #526879; font-size: 13px; background: #fff; }
.pills b { font-size: 11px; font-weight: 550; opacity: .85; }
.pills button[aria-pressed=true] { background: #254b6b; border-color: #254b6b; color: #fff; }
.pills button:hover { box-shadow: inset 0 0 0 1px #7b99aa; }
.context-note { margin: 10px 0 0; display: flex; align-items: baseline; gap: 7px; font-size: 12px; line-height: 1.7; color: #4e6678; }.context-note .el-icon { flex: none; }
.study-grid { display: grid; grid-template-columns: minmax(0,1.22fr) minmax(0,1fr); align-items: start; gap: 16px; margin: 18px 0; }
.relations, .application { min-width: 0; background: #fff; border: 1px solid #dce5ed; border-radius: 14px; }
.relations, .application { padding: clamp(16px,1.9vw,25px); }
.panel-head { align-items: flex-start; }
.panel-head h2 { margin: 0; font-size: clamp(17px,1.6vw,21px); font-weight: 670; line-height: 1.5; color: #203e53; }
.panel-head p { font-size: 12px; margin-top: 2px; }.count { flex: none; margin-top: 5px; font-size: 12px; color: #596f81; }
.path-group { margin-top: 19px; }
.path-group > h3 { display: flex; align-items: center; gap: 7px; margin: 0 0 7px; color: #4a6274; font-size: 12px; font-weight: 650; }
.path-group h3 i { width: 8px; height: 8px; border: 2px solid #6f95b7; border-radius: 2px; box-sizing: border-box; }
.path-group h3 i.joint { background: #399b91; border-color: #399b91; }.path-group h3 i.mechanism { border-color: #ac8358; border-radius: 100%; }
.path-group h3 span { margin-left: auto; font-weight: 450; color: #688092; }
.path-row { display: block; width: 100%; box-sizing: border-box; padding: 12px 14px 9px; margin-top: 6px; border: 1px solid #dce6ed; border-radius: 9px; color: #34536a; background: #fafcfe; text-align: start; }
.path-row:hover { border-color: #8db4c2; background: #f3f9f9; }
.path-row.selected { background: #edf7f5; border-color: #70aba3; box-shadow: inset 3px 0 #39847e; }
.path-flow { display: grid; grid-template-columns: minmax(0,auto) minmax(16px,1fr) minmax(0,auto); align-items: center; gap: 12px; font-size: 14px; font-weight: 600; line-height: 1.6; }
.exposure-node { color: #305371; }.outcome-node { color: #285d60; }
.path-arrow { position: relative; height: 1px; background: #a5bdc7; }.path-arrow::after { position: absolute; content: ''; right: 0; top: -2px; width: 5px; height: 5px; border-top: 1px solid #7a9ca9; border-right: 1px solid #7a9ca9; transform: rotate(45deg); }
.row-meta { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; margin-top: 4px; font-size: 11px; color: #627784; line-height: 1.6; }
.row-meta > span:last-child { white-space: nowrap; }.row-meta > span:last-child span { margin-left: 5px; font-size: 14px; }
.comparison-note { margin: 14px 0 0; padding: 9px 12px; border-radius: 7px; background: #f3f6f9; color: #586b79; font-size: 12px; line-height: 1.7; }
.desktop-detail { min-width: 0; position: sticky; top: 14px; }.mobile-detail { display: none; }
.empty-state, .no-evidence { padding: 35px 18px; text-align: center; border-radius: 9px; }
.empty-state { margin-top: 16px; border: 1px dashed #c9d8e3; }.empty-state > .el-icon, .no-evidence > .el-icon { font-size: 23px; color: #6c8ca3; }
.empty-state h3 { margin: 9px 0 4px; font-size: 15px; }.empty-state p, .no-evidence p, .control-empty { margin: 5px 0; color: #637787; font-size: 13px; line-height: 1.75; }
.no-evidence { background: #edf2f5; }.text-action { margin-top: 8px; padding: 5px; border: 0; color: #27697a; background: none; font-size: 13px; }
.application .panel-head { align-items: center; }.primary-action { flex: none; min-height: 38px; padding: 0 14px; background: #235875; color: #fff; border-radius: 8px; font-size: 13px; }.primary-action:hover { background: #174259; }
.control-list { display: grid; grid-template-columns: repeat(auto-fit,minmax(min(280px,100%),1fr)); gap: 14px 24px; margin-top: 15px; border-top: 1px solid #e3ebef; padding-top: 15px; }
.control-item { display: flex; align-items: flex-start; gap: 12px; min-width: 0; }
.control-icon { display: grid; flex: none; place-items: center; width: 32px; height: 32px; border-radius: 8px; background: #eef4f8; color: #497693; }
.control-item h3 { margin: 0; font-size: 14px; line-height: 1.6; }.control-item p { margin: 3px 0 5px; font-size: 13px; line-height: 1.7; color: #586d7d; }.control-item a { color: #316979; font-size: 12px; text-decoration: underline; text-underline-offset: 3px; }.control-item .el-icon { vertical-align: middle; }
.control-empty { margin-top: 14px; }
.atlas-intro { margin: 0 0 16px; font-size: 13px; color: #657786; }.atlas-group + .atlas-group { margin-top: 18px; }.atlas-group h3 { margin: 0 0 8px; color: #285a68; font-size: 14px; }
.atlas-group button { display: flex; align-items: center; justify-content: space-between; gap: 10px; width: 100%; padding: 9px 12px; border: 1px solid #dfe7eb; border-radius: 7px; margin: 4px 0; background: #fafcfd; color: #304e60; text-align: left; }
.atlas-group button:hover { background: #edf6f4; }.atlas-group small, .atlas-group strong { display: block; line-height: 1.55; }.atlas-group small { color: #647987; font-size: 11px; }.atlas-group strong { font-size: 13px; }
@media (max-width: 1100px) and (min-width: 1025px) { .study-grid { grid-template-columns: 1fr 1fr; }.causal-workspace { padding-inline: 16px; }.filters { column-gap: 14px; } }
@media (max-width: 760px) {
  .causal-workspace { padding: 18px 12px 38px; }.causal-nav { min-height: 40px; padding-inline: 14px; font-size: 12px; }
  .workspace-title { flex-wrap: wrap; align-items: flex-start; margin-bottom: 13px; gap: 7px; }.workspace-title > div { flex: 1 1 230px; }.workspace-title p { font-size: 12px; }
  .filters { gap: 12px 16px; padding: 12px; }.person-field { flex: 1 1 100%; }.person-field select { max-width: 100%; }
  .study-grid { display: block; margin: 12px 0; }.desktop-detail { display: none; }.mobile-detail { display: block; }
  .path-row.selected { border-bottom-left-radius: 0; border-bottom-right-radius: 0; }.path-flow { gap: 8px; font-size: 13px; }
  .application .panel-head { align-items: flex-start; flex-wrap: wrap; }.panel-head p { font-size: 12px; }
}
@media (max-width: 380px) { .workspace-title > div { flex: 1 1 100%; }.quiet-action { min-height: 32px; }.relations,.application { padding: 13px; } }
</style>
