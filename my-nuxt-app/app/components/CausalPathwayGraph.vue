<template>
  <figure v-if="paths.length" class="metal-map" data-orbit-atlas data-path-graph
    :data-layout="compact ? 'tree' : 'radial'" :aria-label="elementLabel + '的证据关系图'">
    <div ref="canvas" class="network-canvas" :class="{ compact, single: paths.length === 1 }">
      <svg class="connections" aria-hidden="true" focusable="false">
        <g v-for="wire in wires" :key="wire.id" :data-graph-edge="wire.id"
          :class="['wire', wire.kind, { current: wire.id === selectedId, hovering: wire.id === hoverId }]"
          :aria-pressed="wire.id === selectedId" @pointerenter="hoverId = wire.id" @pointerleave="hoverId = ''"
          @click="emit('select', wire.id)">
          <path class="ink" :d="wire.d" /><path class="hit" :d="wire.d" />
        </g>
      </svg>

      <div ref="hub" class="element-hub" data-graph-hub :class="{ paired: symbols.length > 1 }">
        <div class="medallion">
          <span class="atomic-number" :title="'原子序数 ' + numbers">{{ numbers }}</span>
          <strong>{{ symbols.join('·') }}</strong>
          <span class="element-name">{{ elementLabel }}</span>
        </div>
      </div>

      <div v-for="bank in banks" :key="bank.side" :class="['bank', bank.side]">
        <button v-for="(item, index) in bank.items" :key="item.id" type="button"
          :class="['leaf', item.kind]" :style="{ '--inset': bendFor(index, bank.items.length) }"
          :data-graph-node="item.id" :data-graph-kind="item.kind" :aria-pressed="selectedId === item.id"
          :aria-label="[categories[item.kind], item.to, item.from, item.studyType, '查看依据'].join('，')"
          @pointerenter="hoverId = item.id" @pointerleave="hoverId = ''"
          @focus="hoverId = item.id" @blur="hoverId = ''" @click="emit('select', item.id)">
          <span class="port" aria-hidden="true">
            <CausalRelationGlyph :path="item" />
            <span v-if="selectedId === item.id" class="selected-mark"><Check /></span>
          </span>
          <span class="leaf-text">
            <strong>{{ item.to }}</strong>
            <span class="citation">{{ item.studyType }}<template v-if="item.source.year"><i>·</i>{{ item.source.year }}</template></span>
          </span>
        </button>
      </div>
    </div>

    <figcaption class="legend">
      <span v-for="kind in presentKinds" :key="kind" :class="kind"><i aria-hidden="true" />{{ categories[kind] }}</span>
    </figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { Check } from '@element-plus/icons-vue'
import { elementNames, relationKinds as categories, type KnowledgeRelation } from '~/utils/knowledgeTypes'

type Kind = KnowledgeRelation['kind']
const props = defineProps<{ paths: KnowledgeRelation[]; selectedId: string; focusMetal?: string }>()
const emit = defineEmits<{ select: [id: string] }>()
const canvas = ref<HTMLElement | null>(null)
const hub = ref<HTMLElement | null>(null)
const compact = ref(false)
const hoverId = ref('')
const atomicNumbers: Record<string, number> = { Pb: 82, Cd: 48, Hg: 80, As: 33, Cr: 24, Ni: 28, Mn: 25, Se: 34 }
const symbols = computed(() => props.focusMetal?.split(',').filter(Boolean) ?? [...new Set(props.paths.flatMap(p => p.metals))])
const numbers = computed(() => symbols.value.map(symbol => atomicNumbers[symbol]).join(' / '))
const elementLabel = computed(() => symbols.value.map(symbol => elementNames[symbol]).join('与'))
const presentKinds = computed(() => (Object.keys(categories) as Kind[]).filter(kind => props.paths.some(p => p.kind === kind)))
const banks = computed(() => {
  const items = presentKinds.value.flatMap(kind => props.paths.filter(p => p.kind === kind))
  const half = items.length / 2
  const boundaries = items.map((item, i) => i && item.kind !== items[i - 1].kind ? i : 0).filter(Boolean)
  const best = boundaries.sort((a, b) => Math.abs(a - half) - Math.abs(b - half))[0]
  const cut = best !== undefined && Math.abs(best - half) <= 1 ? best : Math.floor(half)
  return [{ side: 'west', items: items.slice(0, cut) }, { side: 'east', items: items.slice(cut) }].filter(bank => bank.items.length)
})

// Pull the middle of each bank outwards so the terminals follow a shallow arc.
function bendFor(index: number, count: number) {
  if (count < 3) return '0px'
  const t = index / (count - 1)
  return (Math.sin(Math.PI * t) * 17).toFixed(1) + '%'
}

interface Wire { id: string; kind: Kind; d: string }
const wires = shallowRef<Wire[]>([])
let observer: ResizeObserver | undefined
let frame = 0

function trace() {
  if (!canvas.value || !hub.value) return
  const box = canvas.value.getBoundingClientRect()
  const narrow = box.width < 585
  if (narrow !== compact.value) {
    compact.value = narrow
    nextTick(scheduleTrace)
    return
  }
  const source = hub.value.getBoundingClientRect()
  const cx = source.left + source.width / 2 - box.left
  const cy = source.top + source.height / 2 - box.top
  const points: Wire[] = []
  for (const node of canvas.value.querySelectorAll<HTMLButtonElement>('[data-graph-node]')) {
    const port = node.querySelector<HTMLElement>('.port')!.getBoundingClientRect()
    const x = port.left + port.width / 2 - box.left
    const y = port.top + port.height / 2 - box.top
    const sign = Math.sign(x - cx) || 1
    const angle = Math.atan2((y - cy) * (narrow ? 0.48 : 1), x - cx)
    const r = source.width / 2
    const sx = cx + Math.cos(angle) * r
    const sy = cy + Math.sin(angle) * r
    const reach = Math.abs(x - sx) * 0.46
    const end = x - sign * (port.width / 2)
    const controlX = sx + Math.cos(angle) * reach
    const controlY = sy + Math.sin(angle) * reach
    const d = `M ${sx} ${sy} C ${controlX} ${controlY}, ${end - sign * reach} ${y}, ${end} ${y}`
    points.push({ id: node.dataset.graphNode!, kind: node.dataset.graphKind as Kind, d })
  }
  wires.value = points
}
function scheduleTrace() {
  if (frame) cancelAnimationFrame(frame)
  frame = requestAnimationFrame(() => { frame = 0; trace() })
}
watch(canvas, el => {
  observer?.disconnect()
  if (!el) return
  observer = new ResizeObserver(scheduleTrace)
  observer.observe(el)
  scheduleTrace()
}, { flush: 'post' })
watch(() => props.paths, () => { if (canvas.value) scheduleTrace() }, { flush: 'post' })
onBeforeUnmount(() => { observer?.disconnect(); if (frame) cancelAnimationFrame(frame) })
</script>

<style scoped>
.metal-map {
  margin:0; min-width:0; color:#222d2e; container-type:inline-size;
  background:radial-gradient(ellipse at 51% 47%,#e6efed70,transparent 48%),linear-gradient(123deg,#fafafa,#f8f9f8 62%,#f7f8f9);
}
.network-canvas {
  isolation:isolate; position:relative; display:grid; align-items:center; box-sizing:border-box;
  grid-template-columns:minmax(0,1fr) clamp(128px,22%,248px) minmax(0,1fr);
  grid-template-areas:'west hub east'; gap:0; padding:clamp(24px,3.8cqw,42px) clamp(16px,2.55cqw,36px) clamp(20px,3.2cqw,36px);
  min-height:clamp(282px,29cqw,324px);
}
.health { --ink:#17695d; --tint:#ecf5f1; --line:#a0bcb3; }
.mechanism { --ink:#92542d; --tint:#fbf1e7; --line:#c8ad96; }
.control { --ink:#465c95; --tint:#edf1f9; --line:#acb7cf; }
.connections { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
.wire .ink { fill:none; stroke:var(--line); stroke-width:1.45; stroke-linecap:round; transition:stroke .16s,stroke-width .16s; }
.wire.current .ink,.wire.hovering .ink { stroke:var(--ink); stroke-width:2.35; }
.wire .hit { fill:none; stroke:transparent; stroke-width:12; pointer-events:stroke; cursor:pointer; }
.element-hub {
  grid-area:hub; justify-self:center; position:relative; z-index:1; display:grid; place-items:center;
  width:clamp(84px,9.8cqw,106px); aspect-ratio:1; border-radius:50%; pointer-events:none;
}
.element-hub::before,.element-hub::after {
  content:''; position:absolute; border-radius:50%; pointer-events:none;
}
.element-hub::before { inset:-8px; border:1px solid #648a8035; box-shadow:0 0 0 6px #e2e9e64d; }
.element-hub::after { inset:0; box-shadow:0 12px 17px -9px #253e4480,inset 0 0 0 1px #203e4850; }
.medallion {
  width:100%; height:100%; box-sizing:border-box; border-radius:50%; color:#fff;
  background:radial-gradient(ellipse at 29% 13%,#a1bdaf 0%,#799b94 12%,transparent 42%),
    radial-gradient(ellipse at 78% 86%,#152f38 0%,#34565c 43%,#607f7b 75%,#c3d1c4 100%);
  box-shadow:inset 1px 2px 3px #ebf3e6a3,inset -2px -3px 6px #132b344d;
  display:flex; flex-direction:column; align-items:center; justify-content:center; gap:2px;
}
.atomic-number { font:500 10px/1.1 ui-monospace,monospace; letter-spacing:.04em; color:#fff; }
.medallion strong { font:500 clamp(37px,4.5cqw,52px)/1.02 Georgia,'Times New Roman',serif; letter-spacing:-.065em; text-shadow:0 1px 2px #102b3240; }
.element-name { font-size:12px; font-weight:600; line-height:1.35; color:#f4f7f1; }
.paired .medallion strong { font-size:clamp(23px,2.7cqw,31px); letter-spacing:-.075em; }.paired .element-name { font-size:11px; }
.bank { position:relative; display:grid; min-width:0; row-gap:clamp(18px,2.4cqw,27px); pointer-events:none; }
.west { grid-area:west; justify-items:end; }.east { grid-area:east; justify-items:start; }
.leaf {
  position:relative; display:inline-flex; align-items:center; gap:clamp(7px,1.15cqw,13px);
  width:max-content; max-width:calc(100% - var(--inset)); min-height:52px; box-sizing:border-box; padding:4px 0;
  appearance:none; cursor:pointer; border:0; border-radius:9px; background:transparent; color:inherit; font:inherit; pointer-events:auto;
}
.west .leaf { margin-right:var(--inset); flex-direction:row-reverse; text-align:right; }
.east .leaf { margin-left:var(--inset); text-align:left; }
.port {
  position:relative; display:grid; place-items:center; flex:none; box-sizing:border-box; width:clamp(34px,3.8cqw,43px); aspect-ratio:1;
  border-radius:50%; color:var(--ink); background:var(--tint);
  box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--ink) 21%,transparent),0 2px 3px #263e4108;
  transition:box-shadow .18s,background-color .18s,color .18s;
}
.port > svg { width:50%; height:50%; }
.selected-mark {
  position:absolute; right:-3px; bottom:-1px; display:grid; place-items:center; width:15px; height:15px; border-radius:50%;
  background:#fff; color:var(--ink); border:1px solid color-mix(in srgb,var(--ink) 34%,white);
}
.selected-mark svg { width:10px; height:10px; stroke:currentColor; stroke-width:18; }
.leaf-text { min-width:0; display:grid; gap:4px; }
.leaf strong { font-weight:625; font-size:clamp(15px,1.65cqw,18px); line-height:1.44; letter-spacing:-.025em; overflow-wrap:anywhere; }
.citation { color:#596567; font-size:clamp(12px,1.12cqw,13px); line-height:1.45; overflow-wrap:anywhere; }
.citation i { padding:0 .35em; font-style:normal; }
.leaf[aria-pressed=true] strong { color:var(--ink); }
.leaf[aria-pressed=true] .port { color:white; background:var(--ink); box-shadow:0 0 0 4px color-mix(in srgb,var(--ink) 12%,transparent),0 2px 7px #223e3b19; }
.leaf:hover .port { box-shadow:0 0 0 5px color-mix(in srgb,var(--ink) 13%,transparent); }
.leaf:focus-visible { outline:2px solid var(--ink); outline-offset:4px; }
.legend { margin:0; padding:3px 12px 16px; display:flex; justify-content:center; align-items:center; gap:clamp(12px,2cqw,23px); color:#505f63; font-size:12px; }
.legend span { display:inline-flex; align-items:center; gap:6px; }
.legend i { width:7px; height:7px; border-radius:50%; background:var(--ink); }
.legend .mechanism i { border-radius:1px; transform:rotate(45deg); }.legend .control i { border-radius:2px; }
.single:not(.compact) { grid-template-columns:36% minmax(0,1fr); grid-template-areas:'hub east'; column-gap:10%; }
.network-canvas.compact {
  grid-template-areas:'hub west' 'hub east'; grid-template-columns:clamp(66px,21%,93px) minmax(0,1fr);
  min-height:0; padding:18px 12px 12px; column-gap:clamp(8px,3.2cqw,16px); row-gap:6px;
}
.network-canvas.single.compact { grid-template-areas:'hub east'; }
.compact .element-hub { width:56px; justify-self:start; }.compact .element-hub::before { inset:-3px; box-shadow:none; }
.compact .medallion { gap:0; }.compact .medallion strong { font-size:24px; }
.compact .atomic-number { font-size:8px; }.compact .element-name { font-size:10px; }.compact .paired .medallion strong { font-size:17px; }
.compact .bank { justify-items:stretch; gap:4px; }
.compact .leaf { margin:0; padding:5px 4px 5px 0; width:100%; max-width:none; flex-direction:row; gap:11px; text-align:start; min-height:48px; }
.compact .port { width:32px; }.compact .leaf strong { font-size:14px; }.compact .citation { font-size:11px; }.compact .leaf-text { gap:2px; }
.compact + .legend { justify-content:flex-start; padding:9px 18px 14px; font-size:11px; }
@media(prefers-reduced-motion:reduce) { .wire .ink,.leaf .port { transition:none; } }
</style>
