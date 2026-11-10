<template>
  <section class="coverage" aria-label="群体方案总览">
    <section class="distribution" aria-label="岗位与预防层级分布">
      <header class="section-heading">
        <div><h2>岗位与预防层级分布</h2><p>选择表中的人数，可查看对应的干预对象。</p></div>
        <label class="metal-select">暴露因素
          <select v-model="metal"><option value="">全部因素</option><option v-for="symbol in metals" :key="symbol" :value="symbol">{{ metalName(symbol) }}</option></select>
        </label>
      </header>
      <table class="matrix">
        <caption class="visually-hidden">按岗位和预防层级统计方案人数，受暴露因素筛选影响</caption>
        <thead><tr><th scope="col">岗位</th><th v-for="item in levels" :key="item.key" scope="col"><span class="tier" :class="item.key">{{ item.label }}</span></th><th scope="col">合计</th></tr></thead>
        <tbody><tr v-for="row in matrixRows" :key="row.dept">
          <th scope="row">{{ row.dept }}</th>
          <td v-for="item in levels" :key="item.key"><button type="button" class="count" :class="item.key" :aria-pressed="dept === row.dept && level === item.key" :aria-label="`${row.dept}，${item.label}，${row.counts[item.key]}人`" @click="selectScope(row.dept, item.key)">{{ row.counts[item.key] }}</button></td>
          <td><button type="button" class="count" :aria-pressed="dept === row.dept && !level" :aria-label="`${row.dept}，全部层级，${row.total}人`" @click="selectScope(row.dept, '')">{{ row.total }}</button></td>
        </tr></tbody>
        <tfoot><tr><th scope="row">全部岗位</th><td v-for="item in levels" :key="item.key"><button type="button" class="count" :class="item.key" :aria-pressed="!dept && level === item.key" :aria-label="`全部岗位，${item.label}，${levelTotals[item.key]}人`" @click="selectScope('', item.key)">{{ levelTotals[item.key] }}</button></td><td><button type="button" class="count" :aria-pressed="!dept && !level" :aria-label="`全部岗位与层级，${byMetal.length}人`" @click="selectScope('', '')">{{ byMetal.length }}</button></td></tr></tfoot>
      </table>
    </section>

    <section class="directory" aria-label="筛选后的方案目录">
      <header class="section-heading">
        <div><h2>方案目录</h2><p class="filter-status" role="status">{{ dept || '全部岗位' }} · {{ level ? levelLabels[level] : '全部层级' }} · {{ metal ? metalName(metal) : '全部因素' }}，共 {{ visiblePlans.length }} 人</p></div>
        <button v-if="hasFilter" type="button" class="reset" @click="resetFilters">清除筛选</button>
      </header>
      <template v-if="visiblePlans.length">
        <div class="directory-labels" aria-hidden="true"><span>对象与岗位</span><span>暴露因素与方案重点</span><span>措施与观察项目</span><span></span></div>
        <ul class="plan-list"><li v-for="plan in visiblePlans" :key="plan.id" class="plan-row">
          <div class="identity"><strong>{{ plan.id }}</strong><small>{{ plan.dept }} · 接触 {{ plan.years }} 年</small><span class="tier" :class="plan.level">{{ levelLabels[plan.level] }}</span></div>
          <div class="focus"><span class="factor-line">{{ factorCodes(plan.factors).map(metalName).join('、') }}</span><p>{{ plan.recommendationSummary }}</p></div>
          <div class="monitoring"><strong>{{ plan.workflow.length }} 项措施</strong><p><span class="mobile-label">观察项目：</span>{{ plan.outcomes.map(item => item.label).join('、') }}</p></div>
          <button type="button" class="open-plan" :aria-label="`查看 ${plan.id} 的方案`" @click="emit('select', plan.id)">查看方案 <span aria-hidden="true">→</span></button>
        </li></ul>
      </template>
      <div v-else class="empty"><strong>当前条件下没有干预对象</strong><p>可选择其他人数单元格，或清除筛选查看全部方案。</p></div>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { interventionPlans, type PreventionLevel } from '~/utils/interventionPlans'

const emit = defineEmits<{ select: [personId: string] }>()
const levels = [{ key: 'level1', label: '一级预防' }, { key: 'level2', label: '二级预防' }] as const
const levelLabels: Record<PreventionLevel, string> = { level1: '一级预防', level2: '二级预防' }
const metalLabels: Record<string, string> = { Pb: '铅', As: '砷', Cd: '镉', Hg: '汞', Cr: '铬', Ni: '镍' }
const metalName = (code: string) => metalLabels[code] ? `${metalLabels[code]}（${code}）` : code
const factorCodes = (factors: string) => factors.split(/[,，、]/).map(code => code.trim()).filter(Boolean)
const departments = [...new Set(interventionPlans.map(plan => plan.dept))]
const metals = [...new Set(interventionPlans.flatMap(plan => factorCodes(plan.factors)))]
const dept = ref('')
const level = ref<PreventionLevel | ''>('')
const metal = ref('')
const hasFilter = computed(() => Boolean(dept.value || level.value || metal.value))
const byMetal = computed(() => interventionPlans.filter(plan => !metal.value || factorCodes(plan.factors).includes(metal.value)))
const matrixRows = computed(() => departments.map(department => {
  const plans = byMetal.value.filter(plan => plan.dept === department)
  return { dept: department, counts: countByLevel(plans), total: plans.length }
}))
const levelTotals = computed(() => countByLevel(byMetal.value))
const visiblePlans = computed(() => byMetal.value.filter(plan => (!dept.value || plan.dept === dept.value) && (!level.value || plan.level === level.value)))

function countByLevel(plans: { level: PreventionLevel }[]): Record<PreventionLevel, number> {
  const counts = { level1: 0, level2: 0 }
  for (const plan of plans) counts[plan.level]++
  return counts
}
function selectScope(department: string, preventionLevel: PreventionLevel | '') {
  dept.value = department
  level.value = preventionLevel
}
function resetFilters() {
  metal.value = ''
  selectScope('', '')
}
</script>

<style scoped>
.coverage { display: grid; gap: 20px; min-width: 0; color: #263b51; }
.distribution, .directory { min-width: 0; padding: 21px 24px; background: #fff; border: 1px solid #d8e2e9; border-radius: 12px; }
.section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.section-heading h2 { margin: 0; color: #20374c; font-size: 19px; line-height: 1.45; }
.section-heading p { margin: 4px 0 0; color: #556b7c; font-size: 13px; line-height: 1.65; }
.metal-select { display: inline-flex; align-items: center; flex-wrap: wrap; gap: 8px; color: #45596f; font-size: 13px; }
.metal-select select { min-width: 110px; min-height: 38px; border: 1px solid #b4c3d0; border-radius: 6px; background: #fff; color: #273f60; padding: 0 7px; font: inherit; }
.matrix { width: 100%; border-collapse: collapse; font-size: 13px; text-align: center; }
.matrix th, .matrix td { padding: 4px 8px; }
.matrix th:first-child { text-align: left; width: 37%; }
.matrix thead { color: #536576; background: #f5f8fa; }
.matrix thead th { padding-block: 8px; font-weight: 600; }
.matrix tbody th { font-weight: 550; }
.matrix tbody tr, .matrix tfoot { border-top: 1px solid #e2e8ee; }
.matrix tfoot { background: #f8fafc; }
.matrix tfoot th { font-weight: 650; }
.tier { display: inline-flex; width: fit-content; align-items: center; padding: 2px 7px; font-size: 12px; border-radius: 5px; white-space: nowrap; font-weight: 600; }
.tier.level1 { color: #126057; background: #e4f2ee; }
.tier.level2 { color: #874919; background: #f8ebdc; }
.count { min-height: 34px; width: min(80px, 100%); border: 1px solid transparent; background: transparent; border-radius: 5px; font: inherit; font-weight: 650; color: #29466f; cursor: pointer; font-variant-numeric: tabular-nums; }
.count.level1 { color: #176357; }
.count.level2 { color: #98531c; }
.count:hover { background: #edf2f8; border-color: #d1dce6; }
.count[aria-pressed='true'] { background: #2b4267; color: #fff; }
.count.level1[aria-pressed='true'] { background: #25675d; }
.count.level2[aria-pressed='true'] { background: #925522; }
.reset, .open-plan { cursor: pointer; border: 1px solid #bdc9d6; border-radius: 6px; background: #fff; color: #29496c; min-height: 36px; padding: 4px 10px; font: inherit; font-size: 12px; white-space: nowrap; }
.reset:hover, .open-plan:hover { background: #edf3f8; border-color: #8da5bd; }
.directory-labels, .plan-row { display: grid; grid-template-columns: minmax(120px, .76fr) minmax(180px, 1.6fr) minmax(140px, 1fr) 84px; align-items: start; gap: 15px; }
.directory-labels { border-bottom: 1px solid #dbe5eb; background: #f5f8fa; padding: 8px 10px; font-size: 12px; color: #506476; font-weight: 650; }
.plan-list { padding: 0; margin: 0; list-style: none; }
.plan-row { padding: 14px 10px; border-bottom: 1px solid #e2e9ef; }
.plan-row:last-child { border-bottom: 0; padding-bottom: 2px; }
.identity { display: grid; gap: 4px; }
.identity strong { font-size: 15px; font-weight: 750; color: #243e68; font-variant-numeric: tabular-nums; }
.identity small { color: #526678; font-size: 12px; }
.factor-line, .monitoring strong { color: #284763; font-weight: 650; font-size: 13px; }
.plan-row p { margin: 4px 0 0; font-size: 13px; line-height: 1.65; color: #455b6e; overflow-wrap: anywhere; }
.mobile-label { display: none; }
.empty { border-top: 1px solid #dce5ec; padding: 24px 12px 10px; text-align: center; }
.empty strong { color: #354c64; font-size: 15px; }
.empty p { font-size: 13px; color: #5c6e7f; }
.visually-hidden { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
@media (max-width: 900px) {
  .directory-labels { display: none; }
  .plan-row { position: relative; grid-template-columns: minmax(0, 1fr); gap: 7px; padding: 13px 0; }
  .plan-row:first-child { border-top: 1px solid #dce5ec; }
  .identity { padding-right: 90px; grid-template-columns: auto 1fr; align-items: center; }
  .identity small { grid-column: 1 / -1; grid-row: 2; }
  .identity .tier { grid-column: 2; grid-row: 1; }
  .open-plan { position: absolute; right: 0; top: 13px; }
  .monitoring { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0 10px; }
  .monitoring p { margin: 0; }
  .mobile-label { display: inline; }
}
@media (max-width: 600px) {
  .coverage { gap: 14px; }
  .distribution, .directory { padding: 15px 14px; }
  .section-heading { flex-wrap: wrap; align-items: center; }
  .section-heading h2 { font-size: 17px; }
  .metal-select { width: 100%; }
  .metal-select select { flex: 1; min-height: 42px; }
  .matrix { font-size: 12px; }
  .matrix th:first-child { width: 34%; }
  .matrix th, .matrix td { padding: 4px 2px; }
  .matrix .tier { padding-inline: 3px; font-size: 11px; }
  .count { min-height: 38px; }
  .reset, .open-plan { min-height: 42px; }
}
</style>
