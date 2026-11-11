<template>
  <div class="system-layout">
    <Sidebar default-active="5" />
    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="nav-left">
            <NuxtLink to="/" class="back-link"><el-icon><ArrowLeft /></el-icon> 系统首页</NuxtLink>
            <span class="divider" aria-hidden="true"></span>
            <span class="page-title-top">方案推荐</span>
          </div>
        </div>
      </header>

      <div class="page-container">
        <PipelineSteps :current="4" />
        <header class="plan-heading">
          <div class="plan-intro">
            <img class="plan-art" data-platform-art="intervention-plan" :src="interventionArt" alt="" width="108" height="72">
            <div><h1>干预方案推荐</h1><p>基于预设职业档案，查看岗位防护、健康随访与交接安排。</p></div>
          </div>
          <dl class="scope-counts" aria-label="方案库覆盖范围">
            <div><dt>预设方案</dt><dd>{{ interventionPlans.length }}</dd></div>
            <div><dt>措施安排</dt><dd>{{ totalSteps }}</dd></div>
            <div><dt>暴露因素</dt><dd>{{ metalCount }}</dd></div>
          </dl>
        </header>
        <div v-if="handover" class="handover">
          <span>本次{{ handover === 'batch' ? '群体' : '单人' }}风险分析已完成，可结合分析报告查阅下方预设方案。</span>
          <NuxtLink :to="{ path: '/risk/report', query: { mode: handover } }">查看本次分析报告 →</NuxtLink>
        </div>
        <div v-if="causalOrigin" class="handover">
          <span>当前查阅路径 · {{ causalOrigin.label }}</span>
          <NuxtLink :to="{ path: '/causal', query: causalOrigin.back }">返回路径与依据 →</NuxtLink>
        </div>
        <nav class="workspace-views" aria-label="选择方案视图">
          <NuxtLink :to="{ path: '/plan', query: { ...originQuery, person: selectedPerson.id } }" :aria-current="coverage ? 'false' : 'page'"><el-icon><Document /></el-icon>个人干预方案</NuxtLink>
          <NuxtLink :to="{ path: '/plan', query: { ...originQuery, view: 'coverage' } }" :aria-current="coverage ? 'page' : 'false'"><el-icon><Grid /></el-icon>群体方案总览</NuxtLink>
        </nav>
        <KeepAlive><InterventionCoverage v-if="coverage" :path-metals="causalOrigin?.metals" @select="selectPerson" /></KeepAlive>
        <div v-if="!coverage" class="plan-workspace">
          <aside class="person-picker" aria-label="选择干预对象">
            <h2>干预对象</h2>
            <div class="levels" role="group" aria-label="选择预防层级">
              <button type="button" class="level-secondary" :aria-pressed="selectedLevel === 'level2'" @click="selectPerson(lastPerson.level2)">
                <el-icon><FirstAidKit /></el-icon>二级预防
              </button>
              <button type="button" class="level-primary" :aria-pressed="selectedLevel === 'level1'" @click="selectPerson(lastPerson.level1)">
                <el-icon><Sunny /></el-icon>一级预防
              </button>
            </div>
            <div class="roster" role="group" aria-label="按编号选择干预对象">
              <button v-for="person in currentPersons" :key="person.id" type="button"
                :aria-pressed="selectedPerson.id === person.id" @click="selectPerson(person.id)">
                <span><strong>{{ person.id }}</strong><small>{{ person.dept }}</small></span>
                <el-icon v-if="selectedPerson.id === person.id"><CircleCheck /></el-icon>
              </button>
            </div>
            <label class="mobile-picker"><span>对象编号</span>
              <select :value="selectedPerson.id" @change="selectPerson($event.target.value)">
                <option v-for="person in currentPersons" :key="person.id" :value="person.id">{{ person.id }} · {{ person.dept }}</option>
              </select>
            </label>
          </aside>

          <div class="plan-body" :key="selectedPerson.id">
            <section class="overview" aria-label="当前对象的推荐重点与依据">
              <div class="decision-summary">
                <div class="identification">
                  <span class="level-label" :class="selectedLevel">{{ selectedLevel === 'level2' ? '二级预防' : '一级预防' }}</span>
                  <span class="person-code">{{ selectedPerson.id }}</span>
                  <span>{{ selectedPerson.dept }}</span>
                </div>
                <div class="priority">
                  <div><h2>方案重点</h2><p>{{ selectedPerson.recommendationSummary }}</p></div>
                  <NuxtLink class="report-link" :to="{ path: '/plan/specplan', query: { ...originQuery, person: selectedPerson.id } }">
                    <el-icon><Document /></el-icon>查看方案报告
                  </NuxtLink>
                </div>
                <div class="source-facts"><span><b>暴露因素</b>{{ selectedPerson.factors }}</span><span><b>接触工龄</b>{{ selectedPerson.years }} 年</span></div>
              </div>
              <div class="basis-section">
                <h3>推荐依据</h3>
                <dl class="basis-grid">
                  <div v-for="reason in selectedPerson.basis" :key="reason.label"><dt>{{ reason.label }}</dt><dd>{{ reason.detail }}</dd></div>
                </dl>
              </div>
            </section>

            <nav class="section-jumps" aria-label="本方案内容">
              <button v-for="item in sections" :key="item.id" type="button" @click="goToSection(item.id)">
                <el-icon><component :is="item.icon" /></el-icon>{{ item.label }}
              </button>
            </nav>
            <div id="plan-implementation" class="plan-section" tabindex="-1">
              <InterventionPlanDetails :person="selectedPerson" />
            </div>
            <div id="plan-exposure" class="plan-section" tabindex="-1">
              <ExposureControlReview :factors="selectedPerson.factors" />
            </div>
            <div id="plan-handover" class="plan-section" tabindex="-1">
              <PlanReviewFocus :person="selectedPerson" />
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { ArrowLeft, CircleCheck, Collection, Document, FirstAidKit, Grid, List, Reading, Sunny } from '@element-plus/icons-vue'
import { getInterventionPlan, interventionPlans, plansByLevel } from '~/utils/interventionPlans'
import { causalPlanOrigin } from '~/utils/causalNavigation'
import { PRODUCT_SHORT_NAME } from '~/utils/product'
import interventionArt from '~/assets/illustrations/workflow/intervention-plan.svg?no-inline'

useHead({ title: `方案推荐 · ${PRODUCT_SHORT_NAME}` })
const router = useRouter()
const route = useRoute()
const causalOrigin = computed(() => causalPlanOrigin(route.query))
const coverage = computed(() => route.query.view === 'coverage' || Boolean(causalOrigin.value && !getInterventionPlan(route.query.person)))
const totalSteps = interventionPlans.reduce((sum, plan) => sum + plan.workflow.length, 0)
const metalCount = new Set(interventionPlans.flatMap(plan => plan.factors.split(',').map(f => f.trim()))).size
const { lastResult, dashboard, cohortResult } = usePredictionState()
const handover = computed(() => {
  if (route.query.from !== 'risk') return null
  if (route.query.mode === 'batch' && cohortResult.value?.complete) return 'batch'
  if (route.query.mode === 'individual' && (lastResult.value || dashboard.value?.prediction)) return 'individual'
  return null
})
const originQuery = computed(() => causalOrigin.value?.origin || (handover.value ? { from: 'risk', mode: handover.value } : {}))
const selectedLevel = ref('level2')
const lastPerson = reactive({ level2: plansByLevel.level2[0].id, level1: plansByLevel.level1[0].id })
const currentPersons = computed(() => plansByLevel[selectedLevel.value])
const selectedPerson = computed(() => getInterventionPlan(lastPerson[selectedLevel.value]))
const sections = [
  { id: 'plan-implementation', label: '实施与随访', icon: List },
  { id: 'plan-exposure', label: '现场核查与依据', icon: Reading },
  { id: 'plan-handover', label: '资料与下一步', icon: Collection },
]

function restoreSelection(id) {
  if (typeof id !== 'string') return
  const person = getInterventionPlan(id)
  if (!person) return
  selectedLevel.value = person.level
  lastPerson[person.level] = person.id
}
watch(() => route.query.person, restoreSelection, { immediate: true })
function selectPerson(id) {
  restoreSelection(id)
  if (coverage.value || route.query.person !== id) router.replace({ path: '/plan', query: { ...originQuery.value, person: id } })
}
function goToSection(id) {
  const section = document.getElementById(id)
  if (!section) return
  section.focus({ preventScroll: true })
  section.scrollIntoView({ block: 'start', behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })
}
</script>

<style scoped>
* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; overflow: hidden; background: #f5f7fa; color: #202f47; }
.main-content { position: relative; flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; }
.ep-header { position: sticky; top: 0; z-index: 30; flex-shrink: 0; background: #fff; border-bottom: 1px solid #e5edf4; }
.nav-wrapper { min-height: 64px; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.nav-left { display: flex; align-items: center; gap: 18px; min-width: 0; }
.back-link { display: inline-flex; align-items: center; gap: 8px; color: #647c92; font-size: 13px; text-decoration: none; }
.back-link:hover { color: #287cb9; }
.divider { width: 1px; height: 16px; background: #dfe8f0; }
.page-title-top { font-size: 15px; font-weight: 700; }
.header-caption { color: #8a9caf; font-size: 12px; }
.page-container { flex: 1 0 auto; width: 100%; max-width: 1400px; margin: 0 auto; padding: 30px 36px 48px; min-width: 0; box-sizing: border-box; }
.plan-heading { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px 20px; }
.plan-intro { display: flex; align-items: center; gap: clamp(12px, 1.4vw, 22px); }
.plan-art { display: block; flex: none; width: clamp(74px, 7.5vw, 108px); height: auto; }
.plan-heading h1 { margin: 0; color: #172c46; font-size: 25px; font-weight: 750; }
.plan-heading p { margin: 0; color: #536578; font-size: 12px; line-height: 1.6; }
.scope-counts { display: flex; margin: 0; }
.scope-counts div { display: grid; padding: 0 14px; border-inline-start: 1px solid #d3dfe8; }
.scope-counts dt { color: #556b7c; font-size: 12px; }
.scope-counts dd { order: -1; margin: 0; font-size: 23px; line-height: 1.15; color: #274b66; font-weight: 700; font-variant-numeric: tabular-nums; }
.workspace-views { display: flex; gap: 20px; margin: 12px 0 16px; border-bottom: 1px solid #d4dee9; }
.workspace-views a { display: inline-flex; align-items: center; gap: 6px; text-decoration: none; border-bottom: 3px solid transparent; padding: 9px 1px; color: #546677; font-size: 14px; font-weight: 600; }
.workspace-views a[aria-current="page"] { color: #253f75; border-color: #355892; }
.handover { display: flex; flex-wrap: wrap; gap: 6px 16px; margin: 12px 0 0; padding: 10px 14px; line-height: 1.6; background: #e9f4f0; color: #205f51; font-size: 13px; }
.handover a { font-weight: 650; color: inherit; }
.plan-workspace { display: grid; grid-template-columns: clamp(168px, 15vw, 218px) minmax(0, 1fr); align-items: start; gap: 18px; }
.person-picker { position: sticky; top: 78px; border: 1px solid #d8e1e9; background: #fff; border-radius: 12px; padding: 16px 10px 10px; }
.person-picker h2 { margin: 0 6px 13px; color: #263b55; font-size: 16px; font-weight: 700; }
.levels { display: grid; gap: 5px; padding-bottom: 12px; margin: 0 3px 6px; border-bottom: 1px solid #e0e6ed; }
.levels button { display: flex; align-items: center; gap: 8px; min-height: 36px; padding: 5px 11px; border: 1px solid #e0e5e9; border-inline-start: 3px solid var(--accent); border-radius: 5px; background: #fff; color: var(--accent); font-size: 13px; font-weight: 650; cursor: pointer; }
.levels button[aria-pressed="true"] { background: var(--tint); border-color: var(--accent); }
.levels button[aria-pressed="true"]::after { content: '✓'; margin-left: auto; }
.level-primary { --accent: #14695c; --tint: #eaf6f1; }
.level-secondary { --accent: #975526; --tint: #fbf1e7; }
.roster { display: grid; gap: 3px; }
.roster button { display: flex; align-items: center; justify-content: space-between; text-align: left; min-height: 51px; background: transparent; color: #253a51; padding: 7px 12px; border: 1px solid transparent; border-inline-start: 3px solid transparent; border-radius: 5px; cursor: pointer; }
.roster strong,.roster small { display: block; }
.roster strong,.person-code { font-variant-numeric: tabular-nums; letter-spacing: .045em; }
.roster strong { font-size: 14px; }
.roster small { font-size: 12px; color: #586a7a; margin-top: 2px; }
.roster button[aria-pressed="true"] { background: #edf0fa; border-inline-start-color: #475b95; color: #283e77; }
.roster button:hover { background: #f1f5f9; }
.mobile-picker { display: none; }
.plan-body { min-width: 0; }
.overview { border: 1px solid #cdd9e4; border-radius: 12px; overflow: hidden; background: #fff; }
.decision-summary { padding: 20px 23px 15px; color: white; background: linear-gradient(110deg,#203453 15%,#304d71); }
.identification, .source-facts { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 14px; font-size: 13px; }
.identification { color: #e7eff8; }
.level-label { font-weight: 700; font-size: 12px; padding: 3px 8px; border-radius: 4px; }
.level-label.level2 { color: #6b3e16; background: #ffdfad; }
.level-label.level1 { color: #13564c; background: #c2eee0; }
.person-code { font-weight: 700; color: #fff; }
.priority { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin: 15px 0; }
.priority h2 { font-size: 12px; color: #bed4ee; font-weight: 650; margin: 0 0 5px; }
.priority p { margin: 0; font-size: clamp(18px,1.4vw,23px); line-height: 1.5; font-weight: 650; text-wrap: pretty; }
.report-link { color: #233b59; background: #fff; display: inline-flex; flex: none; align-items: center; gap: 6px; text-decoration: none; font-weight: 650; font-size: 13px; border-radius: 6px; padding: 9px 12px; }
.report-link:hover { background: #e7eff9; }
.source-facts { padding-top: 11px; border-top: 1px solid #ffffff38; }
.source-facts b { margin-right: 6px; color: #bdd2e6; font-size: 12px; font-weight: 500; }
.basis-section { padding: 15px 23px 18px; }
.basis-section h3 { margin: 0 0 10px; color: #233955; font-size: 15px; font-weight: 700; }
.basis-grid { display: grid; grid-template-columns: repeat(auto-fit,minmax(150px,1fr)); gap: 10px 18px; margin: 0; }
.basis-grid div { padding-inline-start: 10px; border-inline-start: 2px solid #9dbeb9; }
.basis-grid dt { color: #2e5755; font-size: 13px; font-weight: 650; }
.basis-grid dd { color: #42576c; font-size: 13px; line-height: 1.65; margin: 3px 0 0; overflow-wrap: anywhere; }
.section-jumps { display: flex; align-items: stretch; gap: 5px; flex-wrap: wrap; margin: 13px 0; }
.section-jumps button { display: inline-flex; align-items: center; gap: 6px; padding: 7px 11px; border-radius: 5px; font-size: 13px; color: #3a506a; background: #e9eff5; cursor: pointer; }
.section-jumps button:hover { background: #dbe6f2; }
.plan-section { scroll-margin-top: 78px; min-width: 0; margin-bottom: 18px; }
@media (max-width: 1100px) { .plan-workspace { grid-template-columns: 164px minmax(0,1fr); gap: 12px; } }
@media (max-width: 760px) {
  .plan-workspace { display: block; }
  .plan-heading { margin-bottom: 12px; }
  .plan-art { width: 68px; }
  .scope-counts { gap: 12px; }
  .scope-counts div { display: flex; align-items: baseline; gap: 4px; padding: 0; border: 0; }
  .scope-counts dd { font-size: 17px; }
  .plan-heading h1 { font-size: 21px; }
  .person-picker { position: static; display: flex; flex-wrap: wrap; gap: 7px 12px; align-items: center; padding: 10px 12px; margin-bottom: 12px; }
  .person-picker h2, .roster { display: none; }
  .levels { grid-template-columns: repeat(2,minmax(0,1fr)); padding: 0; margin: 0; border: 0; flex: 1 1 210px; }
  .levels button { min-height: 38px; padding-inline: 8px; }
  .mobile-picker { display: flex; align-items: center; font-size: 12px; gap: 8px; flex: 1 1 210px; }
  .mobile-picker select { min-width: 0; min-height: 40px; flex: 1; border: 1px solid #afc0cd; border-radius: 5px; background: white; padding: 4px 7px; color: #263f5b; font: inherit; }
  .decision-summary { padding: 15px; }
  .priority { display: grid; gap: 10px; margin: 10px 0; }
  .report-link { justify-self: start; }
  .basis-section { padding: 13px 15px; }
  .basis-grid { grid-template-columns: 1fr; }
  .section-jumps { gap: 4px; }
  .section-jumps button { padding: 8px 6px; font-size: 12px; }
  .plan-section { scroll-margin-top: 72px; }
}
</style>
