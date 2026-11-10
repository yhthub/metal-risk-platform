<template>
  <nav class="workflow-steps" aria-label="功能流程">
    <ol>
      <li v-for="(label, index) in labels" :key="label"
        :class="{ 'is-current': current === index + 1, 'is-earlier': index + 1 < current, 'is-complete': completed >= index + 1 }"
        :aria-current="current === index + 1 ? 'step' : undefined">
        <span class="workflow-stage">
          <span class="workflow-number" aria-hidden="true">
            <svg v-if="completed >= index + 1" viewBox="0 0 20 20" fill="none"><path d="m5 10 3 3 7-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" /></svg>
            <template v-else>{{ index + 1 }}</template>
          </span>
          <span class="workflow-label">{{ label }}</span>
        </span>
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
.workflow-steps { box-sizing: border-box; width: 100%; margin: 0 0 26px; border: 1px solid #d6e1ea; border-radius: 14px; background: #fff; padding: 10px 14px; }
ol { display: flex; align-items: center; margin: 0; padding: 0; list-style: none; }
li { display: flex; align-items: center; min-width: 0; color: #536779; font-size: 14px; font-weight: 650; }
li:not(:last-child) { flex: 1; }
li:not(:last-child)::after { content: ''; flex: 1; height: 2px; margin: 0 clamp(6px, 1.3vw, 20px); border-radius: 2px; background: #dce4eb; }
.workflow-stage { display: inline-flex; align-items: center; gap: 9px; padding: 6px 10px; border-radius: 8px; }
.workflow-number { display: grid; place-items: center; flex-shrink: 0; width: 24px; height: 24px; border: 1px solid #c8d5df; border-radius: 50%; background: #f3f6f9; font-size: 12px; font-weight: 750; font-variant-numeric: tabular-nums; }
.workflow-number svg { width: 18px; height: 18px; }
.workflow-label { white-space: nowrap; }
.is-earlier .workflow-number { color: #14685f; background: #e5f3ef; border-color: #99cbc1; }
li.is-earlier::after { background: #7ab8ad; }
.is-complete .workflow-number { color: #fff; background: #117b68; border-color: #117b68; }
.is-current .workflow-stage { color: #fff; background: #263f75; box-shadow: 0 2px 4px #192c4517; }
.is-current .workflow-number { color: #233e72; background: white; border-color: white; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
@media (max-width: 680px) {
  .workflow-steps { padding: 6px; margin-bottom: 18px; border-radius: 12px; }
  ol { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }
  li { position: relative; justify-content: center; font-size: 12px; }
  .workflow-stage { flex-direction: column; gap: 4px; min-width: 54px; padding: 5px 3px; }
  li:not(:last-child)::after { position: absolute; left: calc(50% + 20px); right: calc(-50% + 20px); top: 17px; margin: 0; }
  .workflow-stage { position: relative; z-index: 1; }
}
</style>
