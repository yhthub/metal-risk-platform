<template>
  <nav class="workflow-steps" aria-label="功能流程">
    <ol>
      <li v-for="(label, index) in labels" :key="label"
        :class="{ 'is-current': current === index + 1, 'is-complete': completed >= index + 1 }"
        :aria-current="current === index + 1 ? 'step' : undefined">
        <span class="workflow-number" aria-hidden="true">
          <svg v-if="completed >= index + 1" viewBox="0 0 20 20" fill="none"><path d="m5 10 3 3 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
          <template v-else>{{ index + 1 }}</template>
        </span>
        <span class="workflow-label">{{ label }}</span>
        <span v-if="completed >= index + 1" class="sr-only">已完成</span>
      </li>
    </ol>
  </nav>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ current: number; completed?: number }>(), { completed: 0 })
const labels = ['数据接入', '数据分析', '风险分析', '方案推荐']
</script>

<style scoped>
.workflow-steps { width: 100%; margin-bottom: 28px; }
ol { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); list-style: none; margin: 0; padding: 0; }
li { position: relative; display: flex; align-items: center; gap: 9px; min-width: 0; color: #8996a8; font-size: 14px; font-weight: 600; }
li:not(:last-child)::after { content: ''; flex: 1; height: 1px; background: #dfe7ef; margin: 0 18px; }
.workflow-number { display: grid; place-items: center; width: 28px; height: 28px; flex-shrink: 0; border-radius: 50%; color: #7b8da3; background: #eaf0f6; font-size: 12px; }
.workflow-number svg { width: 18px; height: 18px; }
.workflow-label { white-space: nowrap; }
.is-current { color: #247cb7; }
.is-current .workflow-number { background: #247cb7; color: white; box-shadow: 0 0 0 4px #eaf4fc; }
.is-complete { color: #32847a; }
.is-complete .workflow-number { background: #e2f3ee; color: #32847a; }
.is-complete::after { background: #b7ded5 !important; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
@media (max-width: 680px) {
  .workflow-steps { margin-bottom: 22px; }
  li { flex-direction: column; gap: 8px; font-size: 12px; text-align: center; }
  li:not(:last-child)::after { position: absolute; top: 14px; left: calc(50% + 21px); right: calc(-50% + 21px); margin: 0; }
  .workflow-number { width: 28px; height: 28px; }
}
</style>
