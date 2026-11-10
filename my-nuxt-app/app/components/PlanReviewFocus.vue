<template>
  <section class="review-focus" aria-label="资料核查与下一步">
    <div class="section-head"><div>
      <h3>资料核查与下一步</h3>
      <p>{{ readonly ? '生成报告时的资料核查状态' : '按资料是否齐备安排下一步。本次访问内按对象分别保留。' }}</p>
    </div></div>
    <div class="review-list">
      <div v-for="item in items" :key="item.key" class="review-row">
        <div class="review-material"><strong>{{ item.title }}</strong><span>{{ item.material }}</span></div>
        <span v-if="readonly" class="report-status">{{ labels[statusOf(item.key)] }}</span>
        <select v-else :aria-label="`${item.title}核查状态`" :value="statusOf(item.key)" @change="update(item.key, $event)">
          <option v-for="(label, value) in labels" :key="value" :value="value">{{ label }}</option>
        </select>
      </div>
    </div>
    <div class="next-actions" aria-live="polite">
      <h4>{{ missing.length ? '待补充事项' : outstanding.length ? '优先核查' : '下一步安排' }}</h4>
      <ul v-if="missing.length"><li v-for="item in missing" :key="item.key">{{ item.action }}</li></ul>
      <p v-else-if="outstanding.length">先确认{{ outstanding[0].title }}。{{ outstanding[0].action }}</p>
      <p v-else>三项资料已核对齐备。对照本方案的观察指标整理记录，将仍需判断的项目交职业卫生专业人员复核。</p>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Status = 'pending' | 'available' | 'missing'
type Key = 'exposure' | 'controls' | 'followup'
interface Person { id: string; dept: string; factors: string; outcomes: { label: string }[] }
const props = withDefaults(defineProps<{ person: Person; readonly?: boolean }>(), { readonly: false })
const labels: Record<Status, string> = { pending: '待核对', available: '已齐备', missing: '需补充' }
const records = useState<Record<string, Partial<Record<Key, Status>>>>('intervention:material-review', () => ({}))
const items = computed(() => [
  { key: 'exposure' as const, title: '岗位与接触资料', material: `${props.person.dept} · ${props.person.factors}`, action: `调取${props.person.dept}的作业记录，逐项核对 ${props.person.factors} 的接触工序、采样日期和检测记录。` },
  { key: 'controls' as const, title: '现场防护记录', material: '控制措施、检查记录及整改情况', action: '向现场负责人收集最近一次防护检查记录，注明对应工序及尚待核实的问题。' },
  { key: 'followup' as const, title: '随访资料', material: props.person.outcomes.slice(0, 2).map(item => item.label).join('、') || '既往观察记录', action: '整理已有观察记录，登记日期、来源和缺少的项目，交随访人员安排复核。' },
])
const statusOf = (key: Key): Status => records.value[props.person.id]?.[key] ?? 'pending'
const missing = computed(() => items.value.filter(item => statusOf(item.key) === 'missing'))
const outstanding = computed(() => items.value.filter(item => statusOf(item.key) === 'pending'))
function update(key: Key, event: Event) {
  const status = (event.target as HTMLSelectElement).value
  if (status !== 'pending' && status !== 'available' && status !== 'missing') return
  records.value[props.person.id] = { ...records.value[props.person.id], [key]: status }
}
</script>

<style scoped>
.review-focus { color: #24354e; background: #fff; border: 1px solid #d4dfe8; border-radius: 12px; padding: 21px 24px; }
.section-head h3 { margin: 0; font-size: 18px; font-weight: 700; }
.section-head p { margin: 4px 0 12px; color: #53677a; font-size: 13px; }
.review-row { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 12px 0; border-top: 1px solid #e3e9ef; }
.review-material { display: grid; gap: 3px; font-size: 14px; }
.review-material span, .report-status { color: #53677a; font-size: 12px; }
select { border: 1px solid #aabccc; color: #2a4465; background: #fff; border-radius: 6px; padding: 6px 10px; min-height: 34px; font: inherit; font-size: 13px; }
.next-actions { border-left: 3px solid #37827b; background: #f0f7f6; padding: 10px 14px; margin-top: 4px; }
.next-actions h4 { margin: 0 0 4px; color: #245e58; font-size: 13px; }
.next-actions p, .next-actions ul { margin: 0; line-height: 1.7; color: #344a51; font-size: 13px; }
.next-actions ul { padding-left: 1.25em; list-style: disc; }
@media(max-width: 650px) { .review-focus { padding: 17px 14px; } select { min-height: 44px; } }
@media print { .review-focus { margin: 16px 0; color: #172b42; } .review-row, .next-actions { break-inside: avoid; } }
</style>
