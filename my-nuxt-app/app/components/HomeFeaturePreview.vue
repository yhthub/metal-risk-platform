<template>
  <section class="preview" :data-feature-preview="kind" :aria-label="previewTitles[kind]">
    <template v-if="kind === 'risk'">
      <header class="preview-head"><h3><el-icon><DataAnalysis /></el-icon>收缩压估计</h3><span>NHANES 2017–2018 公开样本</span></header>
      <div class="risk-stats">
        <div><span>示例对象 020</span><p><b>{{ estimate.toFixed(2) }}</b><span>mmHg</span></p></div>
        <div><span>组内降序排名</span><p><strong>第 5 位</strong><span>/ 20 人</span></p></div>
      </div>
      <figure class="distribution">
        <figcaption><strong>20 人的估计值分布</strong><span><i></i>对象所在区间</span></figcaption>
        <div class="bins" role="list" aria-label="按收缩压估计值分组，每组宽 5 mmHg">
          <div v-for="bin in bins" :key="bin.start" role="listitem" :aria-label="bin.start + ' 至不足 ' + (bin.start + 5) + ' mmHg，' + bin.count + ' 人'"
            :class="{ selected: estimate >= bin.start && estimate < bin.start + 5 }">
            <small aria-hidden="true">{{ bin.count }}</small><i aria-hidden="true" :style="{ height: bin.count / largestBin * 56 + 'px' }"></i>
          </div>
        </div>
        <div class="axis" aria-hidden="true"><span v-for="edge in edges" :key="edge">{{ edge }}</span></div>
        <p class="axis-caption">收缩压估计值（mmHg） · 柱上数字为人数</p>
      </figure>
    </template>
    <template v-else-if="kind === 'cleaning'">
      <header class="preview-head"><h3><el-icon><Grid /></el-icon>表格清洗前后</h3><span>内置合成案例</span></header>
      <div class="file-flow">
        <div><span class="file-type">XLSX</span><strong>12 行 <small>×</small> 21 列</strong></div>
        <el-icon aria-hidden="true"><Right /></el-icon>
        <div><span class="file-type ready">CSV</span><strong>10 行 <small>×</small> 20 列</strong></div>
      </div>
      <p class="changes">去除编号两端空格，删除 1 行空白和 1 行重复记录，保留 20 个必需字段。</p>
      <div class="explanation">
        <div class="subhead"><strong>收缩压模型的局部贡献</strong><span>公开样本 · 对象 020</span></div>
        <div v-for="item in contributions" :key="item.name" class="contribution">
          <span>{{ item.name }}</span><i aria-hidden="true"><b :style="{ width: item.value / 6 * 100 + '%' }"></b></i><strong>+{{ item.value.toFixed(2) }}</strong>
        </div>
        <p class="unit-note">部分特征对本次估计值的贡献，单位为 mmHg。</p>
      </div>
    </template>
    <template v-else>
      <header class="preview-head"><h3><el-icon><ChatLineRound /></el-icon>医学问答示例</h3></header>
      <div class="conversation">
        <img :src="kidneyArt" alt="" width="68" height="50" loading="lazy">
        <div>
          <p class="question">镉暴露与肾损伤有什么关系？</p>
          <p class="answer">一项美国成人调查显示，血镉较高的人群中，肾脏过滤能力偏低更为常见。</p>
        </div>
      </div>
      <a class="paper" href="https://pubmed.ncbi.nlm.nih.gov/19700501/" target="_blank" rel="noopener noreferrer"
        title="Blood Cadmium and Lead and Chronic Kidney Disease in US Adults: A Joint Analysis">
        <el-icon><Reading /></el-icon>查看研究原文 · PubMed，2009 <span aria-hidden="true">↗</span>
      </a>
      <div class="plan-excerpt">
        <div class="subhead"><strong>二级预防方案</strong><span>预设档案 · SZ-105</span></div>
        <ul><li><span>岗位防护</span>核查呼吸防护与局部排风</li><li><span>健康随访</span>跟踪尿镉与肾功能记录</li></ul>
        <NuxtLink :to="{ path: '/plan/specplan', query: { person: 'SZ-105' } }">查看该方案报告 <span aria-hidden="true">→</span></NuxtLink>
      </div>
    </template>
  </section>
</template>

<script setup lang="ts">
import { ChatLineRound, DataAnalysis, Grid, Reading, Right } from '@element-plus/icons-vue'
import kidneyArt from '~/assets/illustrations/prompts/kidney-study.svg?no-inline'

type Feature = 'risk' | 'cleaning' | 'knowledge'
defineProps<{ kind: Feature }>()
const previewTitles: Record<Feature, string> = {
  risk: '公开样本中的单人估计及群体分布',
  cleaning: '合成表格清洗与公开样本模型解释',
  knowledge: '有文献来源的问答与预设干预方案',
}

// Frozen public demo: NHANES-v5-basic, NHANES_2017-2018_risk_demo_20.csv,
// source row 20 (SEQN 93743). The bins aggregate SBP predictions in 5 mmHg intervals.
const estimate = 133.7381286621
const bins = [
  { start: 110, count: 1 }, { start: 115, count: 4 }, { start: 120, count: 0 },
  { start: 125, count: 4 }, { start: 130, count: 10 }, { start: 135, count: 1 },
]
const edges = [...bins.map(bin => bin.start), 140]
const largestBin = Math.max(...bins.map(bin => bin.count))
const contributions = [{ name: '年龄', value: 5.84495 }, { name: '全血铅', value: 0.60754 }]
</script>

<style scoped>
.preview {
  --ink: #214e77; --tint: #edf4fb; --line: #dbe5ee;
  box-sizing: border-box; min-width: 0; color: #22384b; background: #fff;
  border: 1px solid var(--line); border-radius: 16px; padding: clamp(18px,2.1vw,28px);
  box-shadow: 0 12px 32px -18px #334f6852; font-variant-numeric: tabular-nums;
  font-family: "PingFang SC","Microsoft YaHei UI","Microsoft YaHei","Noto Sans CJK SC",system-ui,sans-serif;
}
.preview[data-feature-preview="cleaning"] { --ink:#256965; --tint:#edf6f3; --line:#d8e6e2; }
.preview[data-feature-preview="knowledge"] { --ink:#495b87; --tint:#f0f2f9; --line:#dfe3ee; }
.preview h3,.preview p,.preview figure,.preview ul { margin:0; }
.preview-head,.subhead,.distribution figcaption { display:flex; align-items:baseline; justify-content:space-between; flex-wrap:wrap; gap:4px 12px; }
.preview-head h3 { display:flex; align-items:center; gap:9px; font-size:17px; font-weight:650; color:var(--ink); }
.preview-head > span,.subhead > span,.distribution figcaption > span,.unit-note,.axis-caption { color:#516777; font-size:12px; line-height:1.6; }
.risk-stats,.file-flow { margin:16px 0; padding:14px 18px; border-radius:9px; background:var(--tint); }
.risk-stats { display:grid; grid-template-columns:1.1fr 1fr; align-items:center; gap:12px; }
.risk-stats > div + div { border-inline-start:1px solid #c8d9e7; padding-inline-start:16px; }
.risk-stats span { color:#435c70; font-size:12px; }
.risk-stats p { display:flex; align-items:baseline; flex-wrap:wrap; gap:1px 5px; margin-top:3px; font-size:12px; color:#4b6274; }
.risk-stats p > * { white-space:nowrap; }
.risk-stats b { font-size:clamp(25px,2.5vw,34px); letter-spacing:-.045em; line-height:1.2; color:var(--ink); }
.risk-stats strong { font-size:19px; color:#2f556e; }
.distribution figcaption strong,.subhead strong { font-size:14px; color:#304957; }
.distribution figcaption i { display:inline-block; width:8px; height:8px; margin-right:5px; border-radius:2px; background:#376f9e; }
.bins { display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); align-items:end; gap:3px; height:85px; border-bottom:1px solid #9eafbd; }
.bins > div { display:flex; flex-direction:column; justify-content:end; align-items:stretch; text-align:center; }
.bins small { font-size:12px; line-height:18px; color:#475e70; }
.bins i { background:#b7d1e4; border-radius:3px 3px 0 0; }
.bins .selected i { background:#376f9e; }.bins .selected small { color:var(--ink); font-weight:700; }
.axis { display:flex; justify-content:space-between; margin:3px -8px 0; color:#536578; font-size:11px; }
.axis > span { width:19px; text-align:center; }.preview .axis-caption { margin-top:5px; text-align:center; }
.file-flow { display:grid; grid-template-columns:1fr auto 1fr; align-items:center; gap:12px; margin-bottom:7px; }
.file-flow > div { display:grid; gap:4px; }.file-flow > .el-icon { color:#59867d; }
.file-flow strong { font-size:clamp(16px,1.7vw,21px); color:#224d49; white-space:nowrap; }
.file-flow small { font-size:14px; font-weight:400; color:#637a76; }
.file-type { font-size:11px; font-weight:700; color:#4c6873; letter-spacing:.06em; }.file-type.ready { color:#28716a; }
.changes,.answer { font-size:13px; line-height:1.7; color:#475e6a; }
.explanation,.plan-excerpt { border-top:1px solid var(--line); padding-top:14px; margin-top:15px; }
.subhead { margin-bottom:10px; }
.contribution { display:grid; grid-template-columns:3.2em minmax(0,1fr) 3.5em; gap:8px; align-items:center; margin:6px 0; font-size:12px; }
.contribution i { height:8px; border-radius:3px; background:#f0f4f3; }.contribution b { display:block; height:100%; background:#6ba79b; border-radius:3px; }
.contribution strong { color:#286351; text-align:right; }
.preview .unit-note { margin-top:8px; }
.conversation { display:grid; grid-template-columns:auto minmax(0,1fr); gap:12px; align-items:start; margin:14px 0 6px; }
.conversation img { width:clamp(42px,5vw,68px); height:auto; }
.preview .question { margin-bottom:6px; padding:6px 10px; width:fit-content; max-width:100%; border-radius:9px 9px 9px 2px; background:var(--tint); color:#384c77; font-size:14px; font-weight:600; text-wrap:balance; }
.paper,.plan-excerpt a { display:inline-flex; align-items:baseline; gap:5px; width:fit-content; color:#355e87; font-size:12px; line-height:1.65; text-decoration:underline; text-underline-offset:3px; }
.paper { display:inline; overflow-wrap:anywhere; }.paper .el-icon { margin-right:4px; vertical-align:-1px; }
.preview a:focus-visible { outline:2px solid #387ac2; outline-offset:2px; }
.plan-excerpt ul { padding:0; list-style:none; }.plan-excerpt li { display:flex; gap:10px; align-items:baseline; font-size:13px; line-height:1.8; }
.plan-excerpt li span { flex:none; color:#526675; font-size:12px; }
.plan-excerpt a { margin-top:6px; }
@media (max-width:600px) {
  .preview { padding:16px; }.preview-head h3 { font-size:16px; }
  .risk-stats,.file-flow { padding:11px; gap:9px; }.risk-stats > div + div { padding-inline-start:10px; }
}
</style>
