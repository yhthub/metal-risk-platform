<template>
  <figure v-if="paths.length" ref="frame" class="metal-map" data-path-graph
    :data-layout="compact ? 'tree' : 'radial'" :aria-label="hub.name + '的研究与防护关系'">
    <div class="network-canvas" :style="{ height: height + 'px' }">
      <svg class="branches" :viewBox="`0 0 ${width} ${height}`" aria-hidden="true" focusable="false">
        <circle v-if="!compact" class="orbit" :cx="hubX" :cy="hubY" r="65" />
        <g v-for="node in painted" :key="node.item.id" :class="['branch', node.item.kind, { current: selectedId === node.item.id, hovering: hoverId === node.item.id }]"
          :data-graph-edge="node.item.id" :aria-pressed="selectedId === node.item.id"
          @pointerenter="hoverId = node.item.id" @pointerleave="hoverId = ''" @click="emit('select', node.item.id)">
          <path class="stroke-glow" :d="node.d" /><path class="stroke" :d="node.d" /><path class="stroke-hit" :d="node.d" />
        </g>
      </svg>
      <div class="hub" :class="{ compact, compound: hub.symbol.length > 3 }" :style="{ left: hubX + 'px', top: hubY + 'px' }" data-graph-hub>
        <div class="hub-disc">
          <strong>{{ hub.symbol }}</strong>
          <span v-if="!compact">{{ hub.name }}</span>
        </div>
        <span v-if="compact" class="hub-caption">{{ hub.name }}</span>
      </div>
      <button v-for="node in nodes" :key="node.item.id" type="button" :data-graph-node="node.item.id"
        :data-graph-kind="node.item.kind" :aria-pressed="selectedId === node.item.id"
        :aria-label="[categoryNames[node.item.kind], node.item.from, node.item.to, '查看依据'].join('，')"
        class="leaf" :class="[node.item.kind, node.side, { current: selectedId === node.item.id }]"
        :style="{ left: node.left + 'px', width: node.boxWidth + 'px', top: node.y + 'px' }"
        @pointerenter="hoverId = node.item.id" @pointerleave="hoverId = ''"
        @focus="hoverId = node.item.id" @blur="hoverId = ''" @click="emit('select', node.item.id)">
        <span class="leaf-sign" aria-hidden="true">
          <svg viewBox="0 0 24 24"><path :d="icons[node.item.kind]" /></svg>
        </span>
        <span class="leaf-copy">
          <span class="leaf-label">{{ node.item.to }}</span>
          <span v-if="node.caption" class="leaf-caption">{{ node.caption }}</span>
        </span>
      </button>
    </div>
    <figcaption class="map-legend" aria-label="关系类别图例">
      <span v-for="kind in presentKinds" :key="kind" :class="kind">
        <svg aria-hidden="true" viewBox="0 0 24 24"><path :d="icons[kind]" /></svg>{{ categoryNames[kind] }}
      </span>
    </figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { elementNames as names, relationKinds as categoryNames } from '~/utils/knowledgeTypes'
import type { KnowledgeRelation } from '~/utils/knowledgeTypes'

const props = defineProps<{ paths: KnowledgeRelation[]; selectedId: string; focusMetal?: string }>()
const emit = defineEmits<{ select: [id: string] }>()
const frame = ref<HTMLElement | null>(null)
const width = ref(680)
const hoverId = ref('')
let observer: ResizeObserver | undefined
watch(frame, element => {
  observer?.disconnect()
  if (!element) return
  const resize = () => { width.value = Math.max(1, element.clientWidth) }
  resize()
  observer = new ResizeObserver(resize)
  observer.observe(element)
}, { flush: 'post' })
onBeforeUnmount(() => observer?.disconnect())

type Kind = KnowledgeRelation['kind']
const icons: Record<Kind, string> = {
  health: 'M2 12h5l3-7 4 14 3-7h5',
  mechanism: 'M8 6.2a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 1 1 5.4 0Zm13 4.5a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 1 1 5.4 0Zm-11.2 7.6a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 1 1 5.4 0ZM8 7l7.5 2.6M9.4 16.9l6.7-4.6',
  control: 'M12 2.5c2.8 2 5.5 3 8.2 3.4v5.3c0 4.8-3.5 8.3-8.2 10.5-4.7-2.2-8.2-5.7-8.2-10.5V5.9c2.7-.4 5.4-1.4 8.2-3.4Zm-3.5 9.3 2.3 2.3 4.7-4.8',
}
const presentKinds = computed(() => (Object.keys(categoryNames) as Kind[]).filter(kind => props.paths.some(path => path.kind === kind)))
const hub = computed(() => {
  const focus = props.focusMetal?.split(',').map(s => s.trim()).filter(Boolean)
  const common = props.paths[0]?.metals.filter(m => props.paths.every(path => path.metals.includes(m))) || []
  const metals = focus?.length ? focus : common
  return metals.length
    ? { name: metals.map(m => names[m] || m).join('与'), symbol: metals.join(' + ') }
    : { name: '相关暴露', symbol: '金属' }
})

// Place related topics together. A single relation always owns one terminal and one wire.
const ordered = computed(() => presentKinds.value.flatMap(kind => props.paths.filter(path => path.kind === kind)))
const compact = computed(() => width.value < 490)
const rowCount = computed(() => Math.ceil(ordered.value.length / 2))
const height = computed(() => compact.value ? 99 + ordered.value.length * 64 : Math.max(224, 44 + rowCount.value * 82))
const hubX = computed(() => compact.value ? 43 : width.value * (ordered.value.length === 1 ? .31 : .5))
const hubY = computed(() => compact.value ? 46 : height.value * .5)

function qualifier(item: KnowledgeRelation) {
  const source = item.from.trim()
  // Preserve forms, combined exposures and experimental context even with a single metal selected.
  if (item.metals.length > 1 && !item.metals.every(m => source.includes(names[m] || m))) {
    return item.metals.map(m => names[m] || m).join('＋') + (source ? ' · ' + source : '')
  }
  return source === hub.value.name || source === hub.value.name + '暴露' ? '' : source
}

const nodes = computed(() => {
  const cx = hubX.value, cy = hubY.value, w = width.value
  const count = ordered.value.length
  const leftCount = count === 1 ? 0 : rowCount.value
  return ordered.value.map((item, index) => {
    if (compact.value) {
      const x = w < 310 ? 77 : 89, y = 110 + index * 64
      const d = `M ${cx} ${cy + 24} C ${cx} ${y - 11} ${cx} ${y} ${x} ${y}`
      return { item, side: 'right', y, left: x - 17, boxWidth: w - x + 9, d, caption: qualifier(item) }
    }
    const left = index < leftCount
    const n = left ? leftCount : count - leftCount
    const pos = left ? index : index - leftCount
    const sector = pos - (n - 1) / 2
    const y = cy + sector * 82 + (n === 1 && count > 2 ? -7 : 0)
    const sign = left ? -1 : 1
    const reach = Math.min(w * .215, 164) - Math.min(23, Math.abs(sector) * 12)
    const x = cx + sign * reach
    const startAngle = Math.atan2(y - cy, x - cx)
    const startX = cx + Math.cos(startAngle) * 39
    const startY = cy + Math.sin(startAngle) * 39
    const endX = x - sign * 14
    const d = `M ${startX} ${startY} C ${startX + sign * reach * .36} ${startY}, ${endX - sign * reach * .32} ${y}, ${endX} ${y}`
    return { item, side: left ? 'left' : 'right', y, left: left ? 12 : x - 17,
      boxWidth: left ? x + 17 - 12 : w - x + 17 - 12, d, caption: qualifier(item) }
  })
})
const painted = computed(() => [
  ...nodes.value.filter(n => n.item.id !== props.selectedId),
  ...nodes.value.filter(n => n.item.id === props.selectedId),
])
</script>

<style scoped>
.metal-map { margin: 0; min-width: 0; overflow: hidden; border-radius: 18px; background: radial-gradient(ellipse at 49% 50%, #e9f4f3 0%, transparent 57%), linear-gradient(125deg,#f1f5fb,#f8faf8 62%,#faf7ef); color: #24465c; }
.network-canvas { position: relative; isolation: isolate; width: 100%; }
.branches { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.orbit { fill: none; stroke: #a2b9be; stroke-width: .9; stroke-dasharray: 2 7; opacity: .6; }
.health { --ink: #23786e; --tint: #dceee8; --wire: #75a99e; }
.mechanism { --ink: #9b5c2e; --tint: #f5e8d7; --wire: #c6a180; }
.control { --ink: #62548a; --tint: #eae5f2; --wire: #a395b9; }
.branch path { fill: none; stroke-linecap: round; }
.branch .stroke { stroke: var(--wire); stroke-width: 1.55; transition: stroke .16s,stroke-width .16s; pointer-events: none; }
.branch .stroke-glow { stroke: transparent; stroke-width: 7; pointer-events: none; }
.branch.current .stroke-glow { stroke: var(--tint); }
.branch.current .stroke, .branch.hovering .stroke { stroke: var(--ink); stroke-width: 2.8; }
.branch .stroke-hit { stroke: transparent; stroke-width: 16; cursor: pointer; pointer-events: stroke; }
.hub { position: absolute; z-index: 1; transform: translate(-50%,-50%); pointer-events: none; }
.hub-disc { width: 80px; height: 80px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; box-sizing: border-box; background: radial-gradient(ellipse at 25% 16%,#568998,#2e6378 52%,#234c65); color: #fff; box-shadow: 0 0 0 6px #f4faf9b3,0 0 0 7px #c9dcdb,0 7px 19px #2d596827; }
.hub-disc strong { font: 550 32px/1.1 Georgia, 'Times New Roman', serif; letter-spacing: -.045em; }
.hub-disc span { font-weight: 550; font-size: 13px; line-height: 1.5; }
.compound .hub-disc strong { font-size: 20px; }
.leaf { position: absolute; display: flex; align-items: center; gap: 7px; min-height: 50px; box-sizing: border-box; transform: translateY(-50%); padding: 2px 0; text-align: start; border: 0; border-radius: 12px; background: transparent; color: #2b424b; cursor: pointer; font: inherit; }
.leaf.left { flex-direction: row-reverse; text-align: end; }
.leaf-sign { display: grid; flex: 0 0 34px; height: 34px; place-items: center; border-radius: 50%; color: var(--ink); background: var(--tint); border: 1px solid color-mix(in srgb,var(--ink) 25%,transparent); box-sizing: border-box; transition: transform .18s,background .18s; }
.leaf-sign svg, .map-legend svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.65; stroke-linecap: round; stroke-linejoin: round; }
.mechanism .leaf-sign { border-radius: 11px 15px 11px 15px; }
.control .leaf-sign { border-radius: 12px 12px 16px 16px; }
.leaf.current .leaf-sign { color: #fff; background: var(--ink); border-color: var(--ink); box-shadow: 0 0 0 3px #ffffffbe,0 0 0 4px var(--wire); }
.leaf:hover .leaf-sign, .leaf:focus-visible .leaf-sign { transform: scale(1.075); }
.leaf:focus-visible { outline: 2px solid var(--ink); outline-offset: 1px; }
.leaf-copy { min-width: 0; display: grid; gap: 3px; }
.leaf-label, .leaf-caption { overflow-wrap: anywhere; }
.leaf-label { font-size: 14px; line-height: 1.42; font-weight: 640; }
.leaf.current .leaf-label { color: var(--ink); }
.leaf-caption { font-size: 11px; line-height: 1.36; color: #536977; }
.map-legend { display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 7px 15px; padding: 8px 10px 13px; font-size: 11px; color: #526675; }
.map-legend span { display: inline-flex; align-items: center; gap: 4px; }
.map-legend svg { width: 13px; height: 13px; color: var(--ink); }
.compact .hub-disc { width: 50px; height: 50px; box-shadow: 0 0 0 4px #f4faf9b3,0 0 0 5px #c9dcdb; }
.compact .hub-disc strong { font-size: 24px; }
.compound.compact .hub-disc strong { font-size: 14px; }
.hub-caption { position: absolute; left: 66px; top: 50%; transform: translateY(-50%); white-space: nowrap; font-size: 17px; font-weight: 600; color: #315564; }
.metal-map[data-layout=tree] .leaf { gap: 6px; }.metal-map[data-layout=tree] .leaf-caption { font-size: 11px; }
@media (prefers-reduced-motion: reduce) { .leaf-sign, .branch .stroke { transition: none; } }
</style>
