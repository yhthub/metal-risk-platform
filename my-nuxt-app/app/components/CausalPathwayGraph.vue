<template>
  <div v-if="paths.length" ref="container" class="knowledge-graph" data-path-graph>
    <svg class="network" :viewBox="`0 0 ${width} ${height}`" :style="{ height: height + 'px' }"
      role="group" aria-label="暴露因素、研究指标与原始文献关系图">
      <defs>
        <pattern :id="uid + '-dots'" width="16" height="16" patternUnits="userSpaceOnUse">
          <circle cx="1" cy="1" r=".85" fill="#a9bdc9" opacity=".55" />
        </pattern>
        <linearGradient :id="uid + '-ink'" gradientUnits="userSpaceOnUse" :x1="exposureX" :x2="indicatorX" y1="0" y2="0">
          <stop stop-color="#4764ad" /><stop offset="1" stop-color="#168278" />
        </linearGradient>
      </defs>
      <rect width="100%" height="100%" :fill="`url(#${uid}-dots)`" aria-hidden="true" />
      <g aria-hidden="true" class="headings">
        <text :x="exposureX" y="22">暴露因素</text>
        <text :x="indicatorX" y="22">研究指标</text>
        <text v-if="!compact" :x="studyX" y="22">原始文献</text>
      </g>

      <g aria-hidden="true" class="sources">
        <path v-for="link in sourceLinks" :key="link.id" :d="link.d" class="source-wire" :class="{ marked: link.active }" />
      </g>
      <g v-for="edge in edges" :key="edge.id" class="relationship" :class="{ marked: edge.id === selectedId }"
        :data-graph-edge="edge.id" role="button" tabindex="0" :aria-pressed="edge.id === selectedId"
        :aria-label="edge.title" @click="selectEdge(edge.id)" @keydown.enter.prevent="selectEdge(edge.id)"
        @keydown.space.prevent="selectEdge(edge.id)">
        <title>{{ edge.title }}</title>
        <path :d="edge.d" class="line-halo" aria-hidden="true" />
        <path :d="edge.d" class="line" :stroke="edge.id === selectedId ? `url(#${uid}-ink)` : undefined" aria-hidden="true" />
        <path :d="edge.d" class="line-target" aria-hidden="true" />
      </g>

      <g v-for="node in displayedNodes" :key="node.key" class="concept" :class="[node.type, { marked: node.active }]"
        :transform="`translate(${node.x} ${node.y})`" role="button" tabindex="0"
        :data-graph-node="node.key" :data-graph-study="node.type === 'study' ? node.key : undefined"
        :aria-label="node.label + '，' + node.paths.length + ' 条研究关系'"
        :aria-expanded="node.paths.length > 1 ? focusedKey === node.key : undefined"
        @click="selectNode(node)" @keydown.enter.prevent="selectNode(node)" @keydown.space.prevent="selectNode(node)">
        <title>{{ node.type === 'study' ? node.paths[0].source.title : node.label }}</title>
        <template v-if="node.type === 'exposure'">
          <rect x="-49" y="-29" width="98" height="71" rx="9" class="node-target" />
          <circle v-if="node.active" r="28.5" class="element-halo" />
          <path class="element" d="M -2 -22 Q 0 -23 2 -22 L 18 -13 Q 20 -12 20 -10 V 10 Q 20 12 18 13 L 2 22 Q 0 23 -2 22 L -18 13 Q -20 12 -20 10 V -10 Q -20 -12 -18 -13 Z" />
          <text class="symbol" y="4.5" :class="{ paired: node.symbol.length > 3 }">{{ node.symbol }}</text>
          <text class="exposure-label" y="38">{{ node.label }}</text>
        </template>
        <template v-else-if="node.type === 'indicator'">
          <rect class="metric" :x="-metricWidth / 2" y="-21" :width="metricWidth" height="42" rx="21" />
          <circle class="port" :cx="-metricWidth / 2" r="3.4" /><circle class="port" :cx="metricWidth / 2" r="3.4" />
          <text class="metric-label" :y="node.lines.length > 1 ? -3 : 4.5">
            <tspan v-for="(line, index) in node.lines" :key="line" x="0" :dy="index ? 15 : 0">{{ line }}</tspan>
          </text>
        </template>
        <template v-else>
          <rect class="study-card" :x="-studyWidth/2" y="-25" :width="studyWidth" height="50" rx="9" />
          <g :transform="`translate(${-studyWidth/2 + 13} -8)`" aria-hidden="true" class="paper-icon">
            <path d="M2 0h10l4 4v13H2z M12 0v5h4 M5 9h8 M5 12h6" />
          </g>
          <text class="study-label" :x="-studyWidth/2 + 38" y="-2">{{ node.label }}</text>
          <text class="study-meta" :x="-studyWidth/2 + 38" y="13">{{ node.paths[0].source.year }} · {{ node.paths.length }} 条关系</text>
        </template>
      </g>
    </svg>
    <div class="legend" aria-label="图例">
      <span><i></i>研究关系</span><span><i class="citation"></i>文献出处</span>
      <span class="active-key"><i></i>当前选中</span>
    </div>
    <div v-if="focusNode && focusNode.paths.length > 1" class="node-choices" data-graph-choices>
      <strong>{{ focusNode.label }}关联的研究</strong>
      <button v-for="path in focusNode.paths" :key="path.id" type="button" :data-graph-choice="path.id"
        :aria-pressed="selectedId === path.id" @click="emit('select', path.id)">{{ path.from }} · {{ path.to }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useId, watch } from 'vue'
import type { CausalPathway } from '~/utils/causalEvidence'

const props = defineProps<{ paths: CausalPathway[]; selectedId: string }>()
const emit = defineEmits<{ select: [id: string] }>()
const uid = 'cg-' + useId().replace(/[^\w-]/g, '')
const container = ref<HTMLElement | null>(null)
const width = ref(900)
const focusedKey = ref('')
let observer: ResizeObserver | undefined
watch(container, element => {
  observer?.disconnect()
  if (!element) return
  const measure = () => { width.value = Math.max(1, Math.round(element.getBoundingClientRect().width)) }
  measure()
  observer = new ResizeObserver(measure)
  observer.observe(element)
}, { flush: 'post' })
onBeforeUnmount(() => observer?.disconnect())
watch(() => props.paths.map(path => path.id).join('|'), () => { focusedKey.value = '' })

type Kind = 'exposure' | 'indicator' | 'study'
interface Concept {
  type: Kind
  key: string
  label: string
  symbol: string
  lines: string[]
  paths: CausalPathway[]
  x: number
  y: number
  active: boolean
}
const compact = computed(() => width.value < 580)
const metricWidth = computed(() => compact.value ? Math.min(151, width.value * .42) : Math.min(178, width.value * .24))
const studyWidth = computed(() => compact.value ? Math.min(205, width.value * .64) : Math.min(172, width.value * .235))
const exposureX = computed(() => compact.value ? Math.max(50, width.value * .19) : width.value * .135)
const indicatorX = computed(() => compact.value ? width.value - metricWidth.value / 2 - 23 : width.value * .49)
const studyX = computed(() => compact.value ? width.value / 2 : width.value * .865)

function exposureLabel(path: CausalPathway) {
  if (path.from === '随访中的血镉') return '血镉'
  if (path.from === '培养细胞接触氯化镉') return '氯化镉（细胞）'
  return path.from
}
function keys(path: CausalPathway) {
  return ['e:' + exposureLabel(path), 'i:' + path.to, 's:' + path.source.url]
}
const concepts = computed(() => {
  const all = new Map<string, Concept>()
  for (const path of props.paths) {
    const [exposure, indicator, study] = keys(path)
    function add(type: Kind, key: string, label: string, symbol = '') {
      let node = all.get(key)
      if (!node) {
        const lines = label === '尿 β₂-微球蛋白持续升高' ? ['尿 β₂-微球蛋白', '持续升高'] : [label]
        node = { type, key, label, symbol, lines, paths: [], x: 0, y: 0, active: false }
        all.set(key, node)
      }
      node.paths.push(path)
      if (path.id === props.selectedId) node.active = true
    }
    add('exposure', exposure, exposureLabel(path), path.from === '培养细胞接触氯化镉' ? 'CdCl₂' : path.metals.join('·'))
    add('indicator', indicator, path.to)
    add('study', study, path.sourceType)
  }
  return [...all.values()]
})
const columns = computed(() => ({
  exposure: concepts.value.filter(node => node.type === 'exposure'),
  indicator: concepts.value.filter(node => node.type === 'indicator'),
  study: concepts.value.filter(node => node.type === 'study'),
}))
const rows = computed(() => Math.max(1, columns.value.exposure.length, columns.value.indicator.length, columns.value.study.length))
const bottomRow = computed(() => 66 + (rows.value - 1) * (compact.value ? 74 : 71))
const height = computed(() => bottomRow.value + (compact.value ? 121 : 52))
const positioned = computed(() => {
  const result = new Map<string, Concept>()
  function place(node: Concept, x: number, y: number) { result.set(node.key, { ...node, x, y }) }
  for (const [index, node] of columns.value.indicator.entries()) {
    const span = bottomRow.value - 66
    const n = columns.value.indicator.length
    place(node, indicatorX.value, 66 + (n > 1 ? span * index / (n - 1) : span / 2))
  }
  for (const type of ['exposure', 'study'] as const) {
    const group = columns.value[type]
    const x = type === 'exposure' ? exposureX.value : studyX.value
    const center = (node: Concept) => {
      const ys = [...new Set(node.paths.map(path => result.get(keys(path)[1])!.y))]
      return ys.reduce((sum, y) => sum + y, 0) / ys.length
    }
    const ordered = [...group].sort((a, b) => center(a) - center(b))
    ordered.forEach((node, i) => {
      const y = ordered.length === columns.value.indicator.length || type === 'exposure'
        ? 66 + (ordered.length > 1 ? (bottomRow.value - 66) * i / (ordered.length - 1) : (bottomRow.value - 66) / 2)
        : Math.max(66 + i * 58, Math.min(bottomRow.value - (ordered.length - 1 - i) * 58, center(node)))
      place(node, x, compact.value && type === 'study' ? height.value - 32 : y)
    })
  }
  return result
})
const displayedNodes = computed(() => [...positioned.value.values()].filter(node => !compact.value || node.type !== 'study' || node.active))
const focusNode = computed(() => positioned.value.get(focusedKey.value))

function curve(x1: number, y1: number, x2: number, y2: number) {
  const mid = (x1 + x2) / 2
  return `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`
}
const edges = computed(() => props.paths.map(path => {
  const [exposure, indicator] = keys(path)
  const a = positioned.value.get(exposure)!
  const b = positioned.value.get(indicator)!
  return { id: path.id, title: path.title, d: curve(a.x + 21, a.y, b.x - metricWidth.value / 2, b.y) }
}).sort((a, b) => Number(a.id === props.selectedId) - Number(b.id === props.selectedId)))
const sourceLinks = computed(() => {
  const links = new Map<string, { id: string; d: string; active: boolean }>()
  for (const path of props.paths) {
    const active = path.id === props.selectedId
    if (compact.value && !active) continue
    const [, indicator, source] = keys(path)
    const id = indicator + '|' + source
    const a = positioned.value.get(indicator)!
    const b = positioned.value.get(source)!
    const x1 = a.x + metricWidth.value / 2
    const rail = width.value - 8
    const d = compact.value
      ? `M ${x1} ${a.y} Q ${rail} ${a.y} ${rail} ${a.y+12} V ${b.y-12} Q ${rail} ${b.y} ${rail-12} ${b.y} H ${b.x+studyWidth.value/2}`
      : curve(x1, a.y, b.x - studyWidth.value / 2, b.y)
    links.set(id, { id, d, active: active || Boolean(links.get(id)?.active) })
  }
  return [...links.values()].sort((a, b) => Number(a.active) - Number(b.active))
})
function selectEdge(id: string) {
  focusedKey.value = ''
  emit('select', id)
}
function selectNode(node: Concept) {
  focusedKey.value = node.paths.length > 1 && focusedKey.value !== node.key ? node.key : ''
  if (!node.active || node.paths.length === 1) emit('select', node.paths[0].id)
}
</script>

<style scoped>
.knowledge-graph { overflow: hidden; background: #f6fafc; border: 1px solid #dce6ed; border-radius: 12px; }
.network { width: 100%; display: block; background: radial-gradient(ellipse at 19% 37%,#eaf1ff88,transparent 48%),radial-gradient(ellipse at 68% 47%,#def5ef66,transparent 45%); }
.network text { user-select: none; font-family: inherit; }
.headings { text-anchor: middle; font-size: 12px; font-weight: 650; fill: #577086; }
.relationship, .concept { cursor: pointer; outline: none; }
.line, .line-halo, .line-target, .source-wire { fill: none; stroke-linecap: round; }
.line { stroke-width: 1.8; }.relationship:not(.marked) .line { stroke: #92abba; }.relationship.marked .line { stroke-width: 3.25; }
.line-halo { stroke: #f6fafc; stroke-width: 5.5; }.line-target { stroke: transparent; stroke-width: 15; pointer-events: stroke; }
.relationship:hover .line,.relationship:focus-visible .line { stroke: #315d87; stroke-width: 3.7; }
.relationship:focus-visible .line-halo { stroke: #a8c2d7; stroke-width: 8; }
.source-wire { stroke: #acabc2; stroke-width: 1.5; stroke-dasharray: 3 5; }.source-wire.marked { stroke: #7457a4; stroke-width: 2.3; }
.node-target { fill: transparent; }.element-halo { fill: #4167b116; stroke: #5778b94d; }
.element { stroke: #7e98c4; stroke-width: 1.45; fill: #eaf1fd; }.marked .element { fill: #355a9a; stroke: #355a9a; }
.symbol { text-anchor: middle; fill: #365690; font: 700 15px/1 system-ui,sans-serif !important; }.symbol.paired { font-size: 11px !important; }.marked .symbol { fill: white; }
.exposure-label,.metric-label { text-anchor: middle; font-size: 13px; font-weight: 620; }.exposure-label { fill: #3b5270; }
.metric { fill: #eef8f6; stroke: #8db9af; stroke-width: 1.5; }.port { fill: #f5fbfa; stroke: #78a799; stroke-width: 1.5; }
.metric-label { fill: #2e635b; }.marked .metric { fill: #1c7169; stroke: #19665f; stroke-width: 2; }.marked .metric-label { fill: white; }.marked .port { fill: white; stroke: #18776b; }
.study-card { fill: #fbfaff; stroke: #bdb1d2; stroke-width: 1.15; }.marked .study-card { fill: #f0ebfa; stroke: #8065aa; stroke-width: 1.7; }
.paper-icon { fill: none; stroke: #78619e; stroke-width: 1.5; stroke-linejoin: round; stroke-linecap: round; }
.study-label { fill: #55456f; font-size: 13px; font-weight: 640; }.study-meta { fill: #6f657e; font-size: 11px; }
.concept:hover :is(.element,.study-card,.metric),.concept:focus-visible :is(.element,.study-card,.metric) { stroke: #213e63; stroke-width: 3; }
.legend { display: flex; align-items: center; flex-wrap: wrap; gap: 7px 18px; padding: 9px 16px; border-top: 1px solid #dfe8ee; background: #fcfdfe; color: #526b7d; font-size: 11px; }
.legend span { display: inline-flex; align-items: center; gap: 5px; }.legend i { width: 16px; border-top: 2px solid #8fa7b9; }.legend .citation { border-top: 2px dashed #89779e; }.active-key i { border-color: #217c73; border-width: 3px; }
.node-choices { display: flex; align-items: center; flex-wrap: wrap; gap: 6px; padding: 9px 14px; background: white; border-top: 1px solid #dfe8ee; color: #344e65; font-size: 12px; }
.node-choices strong { margin-right: 5px; }.node-choices button { cursor: pointer; padding: 6px 9px; background: #fff; border: 1px solid #cedae4; border-radius: 6px; color: inherit; font: inherit; }.node-choices button[aria-pressed=true] { background: #e4f2ef; border-color: #79a69f; color: #235b54; }
@media(max-width:580px) { .legend { padding: 8px 10px; gap: 6px 12px; }.metric-label,.exposure-label { font-size: 12px; } }
</style>
