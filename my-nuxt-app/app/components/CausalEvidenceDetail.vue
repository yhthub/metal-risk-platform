<template>
  <article class="evidence" :class="path.kind" :data-evidence-id="path.id">
    <header>
      <span class="category"><i aria-hidden="true" />{{ relationKinds[path.kind] }}</span>
      <span>{{ path.studyType }}</span>
    </header>
    <h3>{{ path.to }}</h3>
    <p class="subject">{{ path.from }}</p>
    <p class="finding">{{ path.finding }}</p>
    <div class="boundary"><strong>适用范围</strong><p>{{ path.limit }}</p></div>
    <details v-if="path.detail" :key="path.id"><summary>查看研究数据</summary><p>{{ path.detail }}</p></details>
    <a :href="path.source.url" target="_blank" rel="noopener noreferrer" class="source-link">
      <span class="source-caption"><el-icon><Reading /></el-icon>{{ path.source.url.startsWith('https://pubmed.ncbi.nlm.nih.gov/') ? '查看论文摘要与出处' : '查看来源' }} <el-icon><TopRight /></el-icon></span>
      <strong>{{ path.source.title }}</strong>
      <small>{{ path.source.issuer }}<template v-if="path.source.year"> · {{ path.source.year }}</template><br>{{ path.source.locator }}</small>
    </a>
  </article>
</template>
<script setup lang="ts">
import { Reading, TopRight } from '@element-plus/icons-vue'
import { relationKinds, type KnowledgeRelation } from '~/utils/knowledgeTypes'
defineProps<{ path: KnowledgeRelation }>()
</script>
<style scoped>
.evidence { --accent:#257a75; --tint:#eef7f4; min-width:0; overflow-wrap:anywhere; background:linear-gradient(175deg,var(--tint),#fff 45%); border:1px solid #d2dedb; border-top:3px solid var(--accent); border-radius:12px; padding:clamp(16px,1.6vw,25px); color:#283f4b; }
.mechanism { --accent:#926333; --tint:#fbf4e9; }.control { --accent:#695685; --tint:#f5f1fa; }
header { display:flex; flex-wrap:wrap; align-items:center; gap:6px 11px; font-size:12px; color:#536876; }
.category { display:inline-flex; align-items:center; gap:6px; color:var(--accent); font-weight:650; }.category i { width:8px; height:8px; border-radius:50%; background:var(--accent); }
h3 { margin:16px 0 4px; font-size:clamp(19px,1.8vw,25px); line-height:1.4; letter-spacing:-.025em; }
.subject { margin:0; font-size:13px; color:#596d75; }
.finding { margin:16px 0; font-size:15px; line-height:1.85; }
.boundary { border-left:2px solid color-mix(in srgb, var(--accent) 46%, white); padding-left:11px; }
.boundary strong { font-size:12px; color:var(--accent); }.boundary p, details p { margin:3px 0 0; color:#50636c; font-size:13px; line-height:1.75; }
details { margin-top:12px; font-size:13px; }summary { cursor:pointer; color:#3c606d; }
.source-link { display:block; margin-top:18px; padding-top:14px; border-top:1px solid #dbe4e5; text-decoration:none; color:#305568; }
.source-caption { display:flex; align-items:center; gap:6px; font-size:13px; font-weight:650; }
.source-caption .el-icon:last-child { margin-left:auto; }.source-link strong,.source-link small { display:block; margin-top:5px; font-size:12px; line-height:1.55; }.source-link small { color:#5b707b; }
.source-link:hover strong { text-decoration:underline; text-underline-offset:2px; }.source-link:focus-visible,summary:focus-visible { outline:2px solid var(--accent); outline-offset:3px; }
</style>
