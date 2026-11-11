<template>
  <figure v-if="paths.length" class="metal-map" :data-layout="compact ? 'tree' : 'radial'"
    data-path-graph :aria-label="elementLabel + '的证据关系图'">
    <div ref="canvas" class="network-canvas" :class="{ compact, single: paths.length === 1 }">
      <svg class="connections" aria-hidden="true" focusable="false">
        <g v-for="wire in wires" :key="wire.id" :class="['wire', wire.kind, { current: wire.id === selectedId, hovering: wire.id === hoverId }]"
          :data-graph-edge="wire.id" :aria-pressed="wire.id === selectedId"
          @pointerenter="hoverId = wire.id" @pointerleave="hoverId = ''" @click="emit('select', wire.id)">
          <path class="ink" :d="wire.d" /><path class="hit" :d="wire.d" />
        </g>
      </svg>

      <div ref="hub" data-graph-hub class="specimen" :class="{ paired: elements.length > 1 }">
        <div v-for="symbol in elements" :key="symbol" class="element-tile"
          :aria-label="(names[symbol] || symbol) + (atomicNumbers[symbol] ? '，原子序数 ' + atomicNumbers[symbol] : '')">
          <small :title="'原子序数 ' + atomicNumbers[symbol]">{{ atomicNumbers[symbol] }}</small>
          <b>{{ symbol }}</b><span>{{ names[symbol] || symbol }}</span>
        </div>
      </div>

      <div v-for="bank in banks" :key="bank.side" :class="['bank',bank.side]">
        <button v-for="item in bank.items" :key="item.id" type="button" class="leaf" :class="item.kind"
          :data-graph-node="item.id" :data-graph-kind="item.kind" :aria-pressed="selectedId === item.id"
          :aria-label="[categoryNames[item.kind], item.from, item.to, item.studyType, '查看依据'].join('，')"
          @pointerenter="hoverId = item.id" @pointerleave="hoverId = ''"
          @focus="hoverId = item.id" @blur="hoverId = ''" @click="emit('select', item.id)">
          <span class="leaf-meta"><i aria-hidden="true" />{{ categoryNames[item.kind] }}
            <time v-if="item.source.year" :datetime="String(item.source.year)">{{ item.source.year }}</time>
          </span>
          <strong>{{ item.to }}</strong>
          <small>{{ item.from }}<span aria-hidden="true"> · </span>{{ item.studyType }}</small>
          <span class="port" aria-hidden="true" />
        </button>
      </div>
    </div>
  </figure>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { elementNames as names, relationKinds as categoryNames, type KnowledgeRelation } from '~/utils/knowledgeTypes'

const props = defineProps<{ paths: KnowledgeRelation[]; selectedId: string; focusMetal?: string }>()
const emit = defineEmits<{ select: [id: string] }>()
const canvas = ref<HTMLElement | null>(null)
const hub = ref<HTMLElement | null>(null)
const compact = ref(false)
const hoverId = ref('')
const atomicNumbers: Record<string, number> = { Pb: 82, Cd: 48, Hg: 80, As: 33, Cr: 24, Ni: 28, Mn: 25, Se: 34 }
const elements = computed(() => {
  const focus = props.focusMetal?.split(',').map(s => s.trim()).filter(Boolean)
  return focus?.length ? focus : [...new Set(props.paths.flatMap(p => p.metals))]
})
const elementLabel = computed(() => elements.value.map(symbol => names[symbol] || symbol).join('与'))
const ordered = computed(() => (Object.keys(categoryNames) as KnowledgeRelation['kind'][])
  .flatMap(kind => props.paths.filter(item => item.kind === kind)))

const banks = computed(() => {
  const items = ordered.value
  // Keep whole categories on the same side when there is room to balance the two columns.
  const cuts = items.map((_, i) => i).filter(i => i > 0 && items[i].kind !== items[i - 1].kind)
  const balanced = [...cuts].sort((a, b) => Math.abs(items.length / 2 - a) - Math.abs(items.length / 2 - b))[0]
  const split = balanced !== undefined && Math.abs(items.length / 2 - balanced) <= 1
    ? balanced : Math.floor(items.length / 2)
  return [{ side: 'west', items: items.slice(0, split) }, { side: 'east', items: items.slice(split) }].filter(bank => bank.items.length)
})

interface Wire { id: string; kind: string; d: string }
const wires = shallowRef<Wire[]>([])
let observer: ResizeObserver | undefined
let raf = 0

// Measure the real labels. Chinese line wrapping, browser zoom and font changes can all move ports.
function traceConnections() {
  if (!canvas.value || !hub.value) return
  const plate = canvas.value.getBoundingClientRect()
  const narrow = plate.width < 558
  if (narrow !== compact.value) {
    compact.value = narrow
    nextTick(scheduleTrace)
    return
  }
  const origin = hub.value.getBoundingClientRect()
  const cx = origin.left + origin.width / 2 - plate.left
  const cy = origin.top + origin.height / 2 - plate.top
  const links: Wire[] = []
  for (const leaf of canvas.value.querySelectorAll<HTMLElement>('[data-graph-node]')) {
    const port = leaf.querySelector('.port')!.getBoundingClientRect()
    const x = port.left + port.width / 2 - plate.left
    const y = port.top + port.height / 2 - plate.top
    let d: string
    if (narrow) {
      const rail = 24
      const start = origin.bottom - plate.top
      d = `M ${rail} ${start} V ${y - 10} Q ${rail} ${y} ${rail + 10} ${y} H ${x}`
    } else {
      const sign = x < cx ? -1 : 1
      const startX = cx + sign * origin.width / 2
      const spread = Math.abs(x - startX) * .48
      d = `M ${startX} ${cy} C ${startX + sign * spread} ${cy}, ${x - sign * spread} ${y}, ${x} ${y}`
    }
    links.push({ id: leaf.dataset.graphNode!, kind: leaf.dataset.graphKind!, d })
  }
  wires.value = links
}
function scheduleTrace() {
  if (raf) cancelAnimationFrame(raf)
  raf = requestAnimationFrame(() => { raf = 0; traceConnections() })
}
watch(canvas, el => {
  observer?.disconnect()
  if (!el) return
  observer = new ResizeObserver(scheduleTrace)
  observer.observe(el)
  scheduleTrace()
}, { flush: 'post' })
watch(() => props.paths, () => { if (canvas.value) scheduleTrace() }, { flush: 'post' })
onBeforeUnmount(() => { observer?.disconnect(); if (raf) cancelAnimationFrame(raf) })
</script>

<style scoped>
.metal-map {
  margin: 0; min-width: 0; color: #193c45; background-color: #f5f5ef;
  background-image: radial-gradient(#a9b1a64f .72px,transparent .8px); background-size: 14px 14px;
}
.network-canvas {
  position: relative; isolation: isolate; display: grid; align-items: center; box-sizing: border-box;
  grid-template-columns: minmax(0,1fr) clamp(148px,23%,244px) minmax(0,1fr);
  grid-template-areas: 'west hub east'; padding: clamp(18px,2.1vw,32px) clamp(12px,1.65vw,26px); min-height: 240px;
}
.connections { position:absolute; inset:0; width:100%; height:100%; z-index:0; overflow:visible; pointer-events:none; }
.health { --ink:#236a68; --wire:#78a39c; --border:#b6cdc6; --tint:#eaf2eb; }
.mechanism { --ink:#88552e; --wire:#bf9670; --border:#d8c5ab; --tint:#f7efe0; }
.control { --ink:#4f628c; --wire:#93a0bd; --border:#c2cadd; --tint:#edf0f7; }
.wire .ink { stroke:var(--wire); stroke-width:1.5; stroke-linecap:round; fill:none; }
.wire.current .ink,.wire.hovering .ink { stroke:var(--ink); stroke-width:2.8; }
.wire .hit { pointer-events:stroke; fill:none; stroke:transparent; stroke-width:15; cursor:pointer; }
.specimen {
  position:relative; grid-area:hub; justify-self:center; display:flex; gap:3px; align-items:center; pointer-events:none;
  padding:3px; border:1px solid #1e4148; color:#f8f8ef; background:#f5f5ef; z-index:1;
}
.element-tile {
  display:grid; align-content:space-between; box-sizing:border-box; width:76px; min-height:88px; padding:6px 8px;
  background:#24464c; border-bottom:3px solid #9ebfae;
}
.element-tile small { font:550 10px/1.15 ui-monospace,monospace; color:#ccdad4; }
.element-tile b { font-family:Cambria,Georgia,'Times New Roman',serif; font-size:34px; font-weight:550; line-height:1; letter-spacing:-.045em; }
.element-tile span { color:#e1e9df; font-size:12px; line-height:1.15; }
.paired .element-tile { width:49px; min-height:71px; padding:5px 7px; }.paired .element-tile b { font-size:25px; }
.bank { position:relative; display:grid; gap:12px; z-index:1; min-width:0; pointer-events:none; }
.bank.west { grid-area:west; }.bank.east { grid-area:east; }
.leaf {
  display:block; min-width:0; width:100%; box-sizing:border-box; position:relative; padding:9px 12px;
  background:#fffefa; color:#213c43; border:1px solid var(--border); border-inline-start:3px solid var(--wire);
  border-radius:3px 10px 10px 3px; text-align:start; font:inherit; cursor:pointer; pointer-events:auto;
  transition:background .15s,box-shadow .15s,border-color .15s;
}
.leaf-meta { display:flex; align-items:center; gap:6px; color:var(--ink); font-size:11px; line-height:1.45; font-weight:650; }
.leaf-meta i { box-sizing:border-box; display:block; width:7px; height:7px; border:1.5px solid currentColor; border-radius:50%; }
.mechanism .leaf-meta i { border-radius:0; transform:rotate(45deg); }.control .leaf-meta i { border-radius:1px; background:currentColor; }
.leaf-meta time { margin-inline-start:auto; color:#556968; font:500 11px/1.4 ui-monospace,monospace; }
.leaf strong,.leaf small { display:block; overflow-wrap:anywhere; }
.leaf strong { margin:3px 0; font-size:clamp(14px,1.1vw,17px); line-height:1.4; font-weight:660; }
.leaf small { color:#576b6e; font-size:11px; line-height:1.5; }.leaf small span { padding-inline:1px; }
.leaf .port { box-sizing:border-box; position:absolute; top:50%; width:8px; height:8px; border-radius:50%; border:1.5px solid var(--wire); background:#fffefa; transform:translateY(-50%); }
.west .port { right:-5px; }.east .port { left:-6px; }
.leaf:hover { background:var(--tint); border-color:var(--ink); }
.leaf[aria-pressed=true] { color:white; background:var(--ink); border-color:var(--ink); box-shadow:0 2px 5px #193c4517; }
.leaf[aria-pressed=true] :is(.leaf-meta,.leaf-meta time,.leaf-caption,small) { color:#fffffff0; }
.leaf[aria-pressed=true] .port { background:var(--ink); border-color:#fff; }
.leaf:focus-visible { outline:2px solid var(--ink); outline-offset:3px; }
.network-canvas.single:not(.compact) { grid-template-areas:'hub east'; grid-template-columns:minmax(110px,36%) minmax(0,1fr); }
.network-canvas.compact {
  grid-template-areas:'hub hub' '. west' '. east'; grid-template-columns:26px minmax(0,1fr);
  padding:14px 12px; gap:8px 3px; align-items:start; min-height:auto;
}
.compact .bank { gap:8px; }.compact .port { left:-6px; right:auto; }.compact .leaf { padding:7px 10px; }.compact .leaf strong { font-size:14px; }
.compact .specimen { justify-self:start; }
.compact .element-tile { width:auto; min-width:94px; min-height:32px; display:flex; align-items:baseline; gap:6px; padding:4px 8px; border:0; }
.compact .element-tile b { font-size:22px; }.compact .element-tile small { align-self:flex-start; font-size:9px; }.compact .element-tile span { font-size:13px; }
.compact .paired .element-tile { min-width:0; }
@media(prefers-reduced-motion:reduce) { .leaf { transition:none; } }
</style>
