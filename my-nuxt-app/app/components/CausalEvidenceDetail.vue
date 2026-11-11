<template>
  <section class="evidence-detail" aria-label="所选关系的证据">
    <div class="detail-head">
      <span class="source-type"><el-icon><Reading /></el-icon>{{ path.sourceType }}</span>
      <span class="year">{{ path.source.year }}</span>
    </div>
    <h3>{{ path.title }}</h3>
    <p class="finding">{{ path.observed }}</p>
    <div class="interpretation">
      <h4>如何理解</h4>
      <p>{{ path.summary }}</p>
      <h4>适用范围</h4>
      <p>{{ path.limits }}</p>
    </div>
    <a class="source-link" :href="path.source.url" target="_blank" rel="noopener noreferrer">
      <span><small>{{ path.source.issuer }} · {{ path.source.locator }}</small><strong>{{ path.source.title }}</strong></span>
      <el-icon aria-label="在新窗口打开原文"><TopRight /></el-icon>
    </a>
  </section>
</template>

<script setup lang="ts">
import { Reading, TopRight } from '@element-plus/icons-vue'
import type { CausalPathway } from '~/utils/causalEvidence'
defineProps<{ path: CausalPathway }>()
</script>

<style scoped>
.evidence-detail { min-width: 0; padding: clamp(18px, 2vw, 28px); border: 1px solid #ccdfe3; border-top: 3px solid #2c817f; border-radius: 14px; color: #283d4b; background: linear-gradient(145deg,#f0f7f6 0%,#fff 49%); }
.detail-head, .source-type { display: flex; align-items: center; }
.detail-head { justify-content: space-between; gap: 10px; color: #41746e; }
.source-type { gap: 7px; font-weight: 650; font-size: 12px; }
.source-type .el-icon { font-size: 17px; }
.year { font-size: 12px; font-variant-numeric: tabular-nums; color: #596c76; }
h3 { font-size: clamp(17px,1.6vw,22px); color: #193846; line-height: 1.55; margin: 15px 0 9px; }
.finding, .interpretation p { margin: 0; font-size: 14px; line-height: 1.85; }
.finding { color: #314d56; }
.interpretation { margin: 17px 0 18px; border-top: 1px solid #e1ecec; }
.interpretation h4 { margin: 14px 0 3px; font-size: 13px; font-weight: 650; color: #36556a; }
.interpretation p { color: #536772; }
.source-link { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid #dce8e8; background: #f5f9f9; border-radius: 9px; color: #245f66; text-decoration: none; overflow-wrap: anywhere; }
.source-link:hover { background: #eaf4f3; border-color: #98c8c2; }
.source-link small, .source-link strong { display: block; }
.source-link small { font-size: 11px; line-height: 1.55; color: #516e74; }
.source-link strong { margin-top: 4px; font-size: 12px; line-height: 1.5; font-weight: 650; }
.source-link .el-icon { flex: none; }
@media (max-width: 760px) { .evidence-detail { padding: 15px; border-radius: 0 0 9px 9px; } }
</style>
