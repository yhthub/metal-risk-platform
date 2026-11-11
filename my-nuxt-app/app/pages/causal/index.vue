<template>
  <div class="system-layout causal-layout">
    <Sidebar default-active="4" />
    <main class="main-content">
      <header class="crumb">
        <NuxtLink :to="riskBack"><el-icon><ArrowLeft /></el-icon>风险分析</NuxtLink>
        <span aria-hidden="true">/</span><strong>因果知识推理</strong>
      </header>
      <div class="workspace">
        <header class="intro">
          <div><h1>职业暴露知识图谱</h1><p>选一种元素，看看它和健康有什么关系，以及工作中可以怎样防护。</p></div>
          <button id="open-atlas" class="search-button" @click="openSearch"><el-icon><Search /></el-icon>查找资料</button>
        </header>
        <nav class="elements" aria-label="选择暴露元素">
          <button v-for="(name, code) in elementNames" :key="code" :data-metal="code" :aria-pressed="focus === code" @click="changeMetal(code)">
            <small aria-hidden="true">{{ code }}</small><strong>{{ name }}</strong>
          </button>
          <button class="joint-tab" data-metal="Pb,Cd" :aria-pressed="focus === 'Pb,Cd'" @click="changeMetal('Pb,Cd')"><el-icon><Connection /></el-icon><strong>铅镉联合</strong></button>
        </nav>
        <div class="browse-context">
          <label class="person"><span>浏览对象</span><select id="causal-person" :value="risk.mode ? 'risk' : selectedPlan?.id || ''" @change="choosePerson(($event.target as HTMLSelectElement).value)">
            <option v-if="risk.mode" value="risk">{{ risk.mode === 'batch' ? '本次群体分析' : '本次单人分析' }}</option>
            <option value="">自由浏览</option><option v-for="plan in interventionPlans" :key="plan.id" :value="plan.id">{{ plan.id }} · {{ plan.dept }}</option>
          </select></label>
          <span v-if="risk.mode">{{ risk.current ? '来自本次风险分析' : '来自风险页的指标选择' }}<template v-if="targetLabel"> · {{ targetLabel }}</template></span>
          <span v-else-if="selectedPlan">档案涉及{{ readElements(selectedPlan.factors).map(code => elementNames[code]).join('、') }}</span>
          <button v-if="topic !== 'all'" class="clear" @click="showAll">当前仅看{{ topicName }} · 查看全部</button>
        </div>

        <section class="explorer" aria-labelledby="graph-heading">
          <div class="graph-column">
            <header class="graph-head">
              <div><h2 id="graph-heading">{{ focusName ? focusName + '的' : '' }}{{ view === 'graph' ? '关系图' : '资料清单' }}</h2>
                <p>已收录 {{ visible.length }} 条关系<span v-if="visible.length">，点选即可查看依据</span>。</p></div>
              <div class="switch" role="group" aria-label="浏览方式">
                <button data-view="graph" :aria-pressed="view === 'graph'" @click="view = 'graph'"><el-icon><Connection /></el-icon>图谱</button>
                <button data-view="list" :aria-pressed="view === 'list'" @click="view = 'list'"><el-icon><List /></el-icon>清单</button>
              </div>
            </header>
            <template v-if="active">
              <CausalPathwayGraph v-if="view === 'graph'" :paths="visible" :selected-id="active.id" :focus-metal="focus" @select="selectPath" />
              <div v-else class="list-view">
                <template v-for="(label, kind) in relationKinds" :key="kind">
                  <section v-if="visible.some(path => path.kind === kind)">
                    <h3>{{ label }}</h3>
                    <button v-for="path in visible.filter(p => p.kind === kind)" :key="path.id" :data-path-id="path.id" :aria-pressed="active.id === path.id" @click="selectPath(path.id)">
                      <span>{{ path.to }}<small>{{ path.from }}</small></span><el-icon><ArrowRight /></el-icon>
                    </button>
                  </section>
                </template>
              </div>
              <button class="mobile-preview" @click="mobileEvidence = true"><span>查看依据 · {{ active.to }}</span><el-icon><ArrowRight /></el-icon></button>
            </template>
            <div v-else class="empty-state" role="status">
              <el-icon><Reading /></el-icon><h3>{{ focusName ? '暂未收录这个组合的资料' : '请选择想了解的元素' }}</h3>
              <p>从上方选择元素，即可查看相应的研究和岗位防护措施。</p>
              <button v-if="focusName && topic !== 'all'" @click="showAll">查看{{ focusName }}的全部资料</button>
            </div>
          </div>
          <aside v-if="active" class="desktop-evidence" aria-label="所选关系的依据" aria-live="polite">
            <CausalEvidenceDetail :path="active" />
          </aside>
        </section>

        <footer v-if="hasPlan" class="continue-row">
          <div><el-icon><FirstAidKit /></el-icon><span>{{ matchedPlan ? '对象 ' + matchedPlan.id : focusName + '相关岗位' }}</span></div>
          <NuxtLink id="causal-plan-link" :to="planRoute">查看干预方案 <el-icon><ArrowRight /></el-icon></NuxtLink>
        </footer>
      </div>
      <el-dialog v-model="searchOpen" title="查找图谱资料" width="min(600px, 94vw)" align-center append-to-body destroy-on-close @opened="searchInput?.focus()">
        <label class="search-field"><el-icon><Search /></el-icon><input ref="searchInput" v-model="search" type="search" aria-label="搜索金属、健康影响或防护措施" placeholder="搜索金属、健康影响或防护措施" /></label>
        <div class="search-results">
          <button v-for="path in searchResults" :key="path.id" :data-atlas-path="path.id" @click="openResult(path)">
            <span><strong>{{ path.to }}</strong><small>{{ path.metals.map(m => elementNames[m]).join('、') }} · {{ relationKinds[path.kind] }} · {{ path.studyType }}</small></span><el-icon><ArrowRight /></el-icon>
          </button>
          <p v-if="!searchResults.length">没有找到匹配资料，试试元素名或“排风”等关键词。</p>
        </div>
      </el-dialog>
      <el-drawer v-model="mobileEvidence" class="mobile-evidence" title="关系依据" direction="btt" size="min(78dvh, 550px)" append-to-body destroy-on-close>
        <CausalEvidenceDetail v-if="active" :path="active" />
      </el-drawer>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { ArrowLeft, ArrowRight, Connection, FirstAidKit, List, Reading, Search } from '@element-plus/icons-vue'
import { knowledgeRelations } from '~/utils/knowledgeCatalog'
import { elementNames, readElements, relationKinds, type KnowledgeRelation } from '~/utils/knowledgeTypes'
import { riskPathContext, riskTargetOptions } from '~/utils/causalNavigation'
import { interventionPlans, getInterventionPlan } from '~/utils/interventionPlans'
import { PRODUCT_SHORT_NAME } from '~/utils/product'

useHead({ title: '职业暴露知识图谱 · ' + PRODUCT_SHORT_NAME })
const route = useRoute()
const router = useRouter()
const state = usePredictionState()
const view = useState<'graph' | 'list'>('causal-reading-view', () => 'graph')
const mobileEvidence = ref(false)
const searchOpen = ref(false)
const search = ref('')
const searchInput = ref<HTMLInputElement | null>(null)
const risk = computed(() => riskPathContext(route.query, state.dashboard.value, state.cohortResult.value))
const riskBack = computed(() => risk.value.mode ? { path: '/risk', query: { mode: risk.value.mode } } : '/risk')
const selectedPlan = computed(() => getInterventionPlan(risk.value.mode ? risk.value.person : route.query.person))
const targetLabel = computed(() => riskTargetOptions.find(item => item.value === risk.value.target)?.label || '')
const explicitEdge = computed(() => knowledgeRelations.find(path => path.id === route.query.edge))
const topic = computed(() => {
  const requested = route.query.outcome
  if (requested === 'all' || requested === 'renal' || requested === 'sbp' || requested === 'other' || requested === 'unsupported') return requested
  if (!risk.value.mode) return 'all'
  if (risk.value.target === 'sbp') return 'sbp'
  return ['uacr_mg_g', 'serum_creatinine_mg_dl'].includes(risk.value.target) ? 'renal' : 'unsupported'
})
const topicName = computed(() => ({ all: '全部资料', renal: '肾脏指标', sbp: '收缩压', other: '其他健康指标', unsupported: '本次风险指标' })[topic.value])
const focus = computed(() => {
  const specified = readElements(route.query.metals)
  if (typeof route.query.metals === 'string' && !specified.length) return ''
  if (specified.length === 1) {
    const linked = explicitEdge.value?.metals
    if (linked?.length === 2 && linked.includes(specified[0])) return linked.join(',')
    return specified[0]
  }
  if (specified.includes('Pb') && specified.includes('Cd') &&
    (!explicitEdge.value || explicitEdge.value.metals.length === 2)) return 'Pb,Cd'
  if (specified.length) return explicitEdge.value?.metals.find(m => specified.includes(m)) || specified[0]
  if (risk.value.mode === 'individual' && risk.value.current) {
    const person = state.dashboard.value?.input?.person
    if (person) return (['Pb', 'Cd', 'Hg'] as const).find(m => typeof person[m.toLowerCase() as 'pb'|'cd'|'hg'] === 'number') || ''
  }
  if (selectedPlan.value) return readElements(selectedPlan.value.factors)[0] || ''
  return 'Pb'
})
const focusName = computed(() => focus.value === 'Pb,Cd' ? '铅镉联合暴露' : elementNames[focus.value] || '')
const visible = computed(() => knowledgeRelations.filter(path => {
  const matches = focus.value === 'Pb,Cd' ? path.metals.includes('Pb') && path.metals.includes('Cd') : path.metals.length === 1 && path.metals[0] === focus.value
  return matches && (topic.value === 'all' || topic.value === path.topic)
}))
const active = computed(() => visible.value.find(path => path.id === route.query.edge)
  || visible.value.find(path => path.metals.length === 1 && path.kind === 'health') || visible.value[0])
const scopeMetals = computed(() => readElements(focus.value))
const planMatches = (factors: string) => scopeMetals.value.length > 0 && scopeMetals.value.every(code => readElements(factors).includes(code))
const hasPlan = computed(() => interventionPlans.some(plan => planMatches(plan.factors)))
const matchedPlan = computed(() => selectedPlan.value && planMatches(selectedPlan.value.factors) ? selectedPlan.value : null)
const planRoute = computed(() => {
  const query: Record<string, string> = { from: 'causal', outcome: topic.value, metals: focus.value }
  if (active.value) query.edge = active.value.id
  if (matchedPlan.value) query.person = matchedPlan.value.id
  else {
    query.view = 'coverage'
    if (selectedPlan.value) query.pathPerson = selectedPlan.value.id
  }
  if (risk.value.mode) { query.sourceMode = risk.value.mode; query.sourceTarget = risk.value.target }
  return { path: '/plan', query }
})
function navigate(metals: string, outcome: string, edge?: string) {
  const query: Record<string, string> = { metals, outcome }
  if (edge) query.edge = edge
  if (risk.value.mode) {
    query.from = 'risk'
    query.mode = risk.value.mode
    if (risk.value.target) query.target = risk.value.target
  } else if (selectedPlan.value) query.person = selectedPlan.value.id
  return router.replace({ path: '/causal', query })
}
const changeMetal = (code: string) => navigate(code, 'all')
const showAll = () => changeMetal(focus.value)
function choosePerson(id: string) {
  const plan = getInterventionPlan(id)
  const query = plan ? { person: plan.id } : { metals: focus.value, outcome: 'all' }
  return router.replace({ path: '/causal', query })
}
function onSmallScreen() { return window.matchMedia('(max-width: 760px)').matches }
async function selectPath(id: string) {
  await navigate(focus.value, topic.value, id)
  if (onSmallScreen()) mobileEvidence.value = true
}
const searchResults = computed(() => {
  const term = search.value.trim().toLowerCase()
  if (!term) return knowledgeRelations
  return knowledgeRelations.filter(p => [p.from, p.to, p.title, p.finding, p.source.title, relationKinds[p.kind], ...p.metals, ...p.metals.map(m => elementNames[m])].join(' ').toLowerCase().includes(term))
})
function openSearch() { search.value = ''; searchOpen.value = true }
async function openResult(path: KnowledgeRelation) {
  searchOpen.value = false
  await navigate(path.metals.join(','), 'all', path.id)
  await nextTick()
  if (onSmallScreen()) mobileEvidence.value = true
}
</script>

<style scoped>
.causal-layout { height:100dvh; width:100%; display:flex; overflow:hidden; background:#f6f9fa; color:#203a44; }
.main-content { min-width:0; flex:1; overflow:auto; background:radial-gradient(ellipse 65% 490px at 94% 5%,#e8f3ef 0%,#eef5f238 63%,transparent 96%),linear-gradient(120deg,#f8fafc,#f7f9f8 60%,#f5f7fa); }
.crumb { min-height:49px; padding:0 clamp(16px,3vw,42px); display:flex; align-items:center; gap:14px; background:#fff; border-bottom:1px solid #e2e9ec; font-size:13px; }
.crumb a,.continue-row a { display:inline-flex; align-items:center; gap:5px; color:#46676d; text-decoration:none; }.crumb > span { color:#9dadb3; }
.workspace { box-sizing:border-box; max-width:1460px; margin:auto; padding:clamp(22px,3.1vw,52px) clamp(16px,2.8vw,44px) 65px; }
.intro,.graph-head,.continue-row,.browse-context { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.intro h1 { margin:0; font-size:clamp(26px,3vw,42px); line-height:1.2; letter-spacing:-.045em; color:#183940; font-weight:720; }
.intro p,.graph-head p { margin:9px 0 0; font-size:14px; color:#506874; line-height:1.7; }
button,select,input { font:inherit; }button,select { cursor:pointer; }
button:focus-visible,select:focus-visible,summary:focus-visible,a:focus-visible { outline:2px solid #297d83; outline-offset:3px; }
.search-button,.switch button,.mobile-preview,.clear,.empty-state button { display:inline-flex; align-items:center; justify-content:center; gap:6px; }
.search-button { flex:none; padding:8px 14px; min-height:39px; border-radius:24px; border:1px solid #bdcfce; background:#ffffffc9; color:#375f65; font-size:13px; }.search-button:hover { background:#fff; border-color:#70a098; }
.elements { display:flex; align-items:center; flex-wrap:wrap; gap:5px 8px; margin:24px 0 0; padding:6px 0 10px; border-bottom:1px solid #dce6e4; }
.elements button { display:inline-flex; align-items:center; gap:8px; justify-content:center; border:1px solid transparent; border-radius:22px; padding:8px 12px; background:transparent; color:#425f66; min-height:39px; }
.elements small { font-size:13px; font-family:ui-monospace,monospace; color:#617c87; }.elements strong { font-size:14px; font-weight:600; }
.elements button:hover,.switch button:hover { background:#e5efed; }.elements button[aria-pressed=true] { background:#255d62; color:white; box-shadow:0 3px 9px #285d661b; }.elements button[aria-pressed=true] small { color:#d1ebe6; }
.elements .joint-tab { background:#eef1f7; color:#52627b; }.joint-tab .el-icon { font-size:16px; }
.browse-context { justify-content:flex-start; flex-wrap:wrap; column-gap:16px; row-gap:5px; margin:10px 0 18px; font-size:12px; color:#5a6d75; }
.person { display:flex; align-items:center; gap:7px; }.person select { max-width:min(215px,60vw); padding:5px 18px 5px 4px; border:0; background:transparent; color:#36535b; font-weight:600; }
.clear { font-size:12px; background:none; padding:4px 0; color:#27656d; border:0; text-decoration:underline; text-underline-offset:3px; }
.explorer { display:grid; grid-template-columns:minmax(0,1.9fr) minmax(260px,.93fr); align-items:start; gap:clamp(12px,1.4vw,22px); }
.graph-column { min-width:0; background:#ffffffde; border:1px solid #dce5e8; border-radius:20px; box-shadow:0 6px 24px #263a4d05; overflow:hidden; }
.graph-head { padding:clamp(14px,1.5vw,23px) clamp(14px,1.6vw,25px) 12px; }
.graph-head h2 { margin:0; font-size:clamp(18px,1.65vw,24px); color:#25474c; line-height:1.4; }.graph-head p { margin-top:2px; font-size:12px; }
.switch { display:inline-flex; gap:2px; flex:none; padding:3px; border:1px solid #e1e8e8; background:#f2f6f5; border-radius:16px; }.switch button { min-height:31px; border:0; border-radius:13px; padding:4px 8px; font-size:12px; color:#516b73; background:transparent; }.switch button[aria-pressed=true] { color:#225e64; background:#fff; box-shadow:0 1px 4px #29464920; }
.graph-column :deep(.metal-map) { border-radius:0 0 18px 18px; }
.desktop-evidence { position:sticky; top:14px; min-width:0; }
.mobile-preview { display:none; }.list-view { padding:0 clamp(14px,1.6vw,25px) 12px; }
.list-view h3 { margin:13px 0 5px; color:#46696c; font-size:13px; }
.list-view button,.search-results button { display:flex; width:100%; align-items:center; justify-content:space-between; gap:10px; border:0; border-bottom:1px solid #e3ebeb; text-align:left; padding:9px 10px; background:transparent; color:#294b57; line-height:1.5; font-size:14px; }
.list-view button[aria-pressed=true],.list-view button:hover,.search-results button:hover { background:#edf5f1; border-radius:9px; }
.list-view small,.search-results small { display:block; color:#60767b; font-size:12px; }
.empty-state { text-align:center; padding:35px 16px 48px; }.empty-state > .el-icon { font-size:28px; color:#748e99; }.empty-state h3 { font-size:16px; }.empty-state p { font-size:13px; color:#536e74; }.empty-state button { border:1px solid #c7d9d7; padding:7px 13px; border-radius:20px; background:white; color:#305f63; }
.continue-row { margin-top:16px; padding:14px 4px 0; border-top:1px solid #dde5e5; font-size:13px; }.continue-row > div { display:flex; align-items:center; gap:7px; color:#506573; }.continue-row a { font-weight:600; color:#285e6a; padding:5px; }
.search-field { display:flex; align-items:center; gap:9px; padding:8px 12px; border:1px solid #c9d9d9; border-radius:10px; }.search-field input { width:100%; min-width:0; outline:none; padding:4px 0; border:0; color:#2a4851; }.search-field:focus-within { border-color:#44837e; }
.search-results { max-height:min(55dvh,490px); margin-top:10px; overflow:auto; }.search-results p { font-size:14px; }
:global(.mobile-evidence.el-drawer) { border-radius:22px 22px 0 0; max-height:calc(100dvh - 20px); }
:global(.mobile-evidence .el-drawer__header) { margin:0; padding:14px 16px 5px; }
:global(.mobile-evidence .el-drawer__body) { padding:8px 12px max(16px,env(safe-area-inset-bottom)); }
@media(max-width:1190px) and (min-width:1025px) { .workspace { padding-inline:18px; }.explorer { grid-template-columns:minmax(0,1.55fr) minmax(246px,.95fr); } }
@media(max-width:760px) {
  .workspace { padding:20px 12px 48px; }.crumb { min-height:40px; padding-inline:13px; }
  .intro { align-items:flex-start; gap:7px; }.intro h1 { font-size:clamp(22px,5.9vw,32px); }.intro p { margin-top:6px; font-size:13px; }.search-button { padding:5px 9px; min-height:32px; font-size:12px; }
  .elements { gap:2px 4px; margin-top:13px; padding:4px 0 8px; }.elements button { min-height:35px; padding:5px 8px; gap:5px; }.elements small { font-size:11px; }.elements strong { font-size:13px; }
  .browse-context { margin:6px 0 12px; }.explorer { display:block; }.desktop-evidence { display:none; }.graph-column { border-radius:16px; }
  .graph-head { padding:13px 10px 8px; }.graph-head p { font-size:11px; }.switch button { padding:4px 7px; }
  .mobile-preview { display:flex; width:100%; justify-content:space-between; padding:12px 15px; background:#eef6f2; color:#315e60; border:0; border-top:1px solid #dae8e3; font-size:13px; }
}
@media(max-width:359px) { .search-button { gap:3px; padding:4px 7px; }.elements button { padding:5px 6px; }.graph-head { gap:4px; }.switch button { padding:4px 5px; } }
</style>
