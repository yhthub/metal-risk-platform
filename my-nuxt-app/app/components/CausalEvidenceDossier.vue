<template>
  <section class="dossier" data-evidence-dossier aria-labelledby="dossier-heading">
    <header class="dossier-heading">
      <img class="index-art" data-platform-art="source-index" :src="sourceIndexArt" alt="" width="84" height="56" loading="lazy">
      <div><h2 id="dossier-heading">{{ name }}资料索引</h2>
        <p>对照研究对象与观察结果，再按具体工序核查防护措施。</p></div>
      <span class="source-count"><el-icon><Reading /></el-icon>{{ sources }} 份来源</span>
    </header>
    <div class="sheets">
      <section class="study-sheet" aria-labelledby="study-heading">
        <header class="sheet-title"><h3 id="study-heading" tabindex="-1">研究对照</h3><span>{{ studies.length }} 条研究关系</span></header>
        <table v-if="studies.length">
          <thead><tr><th scope="col">研究对象</th><th scope="col">观察指标</th><th scope="col">主要发现</th></tr></thead>
          <tbody>
            <tr v-for="path in studies" :key="path.id" :data-study-row="path.id">
              <th scope="row"><span class="type" :class="path.kind">{{ path.studyType }}<template v-if="path.source.year"> · {{ path.source.year }}</template></span>
                <button class="inspect" :data-inspect-path="path.id" :aria-label="'图中查看：' + path.to" @click="$emit('inspect', path.id)">{{ path.to }} <el-icon><Aim /></el-icon></button>
                <span class="population">{{ path.study.population }}</span></th>
              <td class="measure"><small>观察指标</small>{{ path.study.measure }}</td>
              <td class="finding"><small>主要发现</small>{{ path.study.result }}
                <a :href="path.source.url" rel="noopener noreferrer" target="_blank" :title="path.source.title" :aria-label="'查看研究来源：' + path.source.title">研究来源 <el-icon><TopRight /></el-icon></a></td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty">当前筛选下尚未收录研究资料。</p>
      </section>
      <section class="control-sheet" aria-labelledby="control-heading">
        <header class="sheet-title"><h3 id="control-heading" tabindex="-1">岗位防护核查</h3><span>{{ controls.length }} 项措施</span></header>
        <ol v-if="controls.length">
          <li v-for="path in controls" :key="path.id" :data-control-row="path.id">
            <span class="pin" aria-hidden="true"><el-icon><Operation /></el-icon></span>
            <div class="control-body">
              <span class="work">{{ path.from }}</span>
              <button class="inspect" :data-inspect-path="path.id" :aria-label="'图中查看：' + path.to" @click="$emit('inspect', path.id)">{{ path.to }} <el-icon><Aim /></el-icon></button>
              <p>{{ path.field.verify }}</p>
              <div class="record"><strong>建议留存</strong><span>{{ path.field.record }}</span></div>
              <a :href="path.source.url" rel="noopener noreferrer" target="_blank" :title="path.source.title" :aria-label="'查看防护依据：' + path.source.title">{{ path.studyType }} <el-icon><TopRight /></el-icon></a>
            </div>
          </li>
        </ol>
        <p v-else class="empty">当前筛选下尚未收录岗位措施。<slot name="reset" /></p>
        <slot name="plan" />
      </section>
    </div>
  </section>
</template>
<script setup lang="ts">
import { computed } from 'vue'
import { Aim, Operation, Reading, TopRight } from '@element-plus/icons-vue'
import sourceIndexArt from '~/assets/illustrations/workflow/source-index.svg?no-inline'
import type { FieldCheck, KnowledgeRelation, StudyComparison } from '~/utils/knowledgeTypes'

const props = defineProps<{ paths: KnowledgeRelation[]; name: string }>()
defineEmits<{ inspect: [id: string] }>()
const studies = computed(() => props.paths.filter((p): p is KnowledgeRelation & { study: StudyComparison } => !!p.study))
const controls = computed(() => props.paths.filter((p): p is KnowledgeRelation & { field: FieldCheck } => !!p.field))
const sources = computed(() => new Set(props.paths.map(p => p.source.url.split('#')[0])).size)
</script>
<style scoped>
.dossier { margin-top:clamp(24px,2.4vw,38px); color:#223e48; }
.dossier-heading, .sheet-title { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.dossier-heading { display:grid; grid-template-columns:auto minmax(0,1fr) auto; justify-content:stretch; margin-bottom:15px; }
.index-art { display:block; width:84px; height:auto; }
.dossier h2,.dossier h3,.dossier p { margin:0; }
.dossier h2 { color:#1e4144; font-size:clamp(21px,1.9vw,28px); line-height:1.35; letter-spacing:-.035em; }
.dossier-heading p { margin-top:4px; color:#52666c; font-size:13px; line-height:1.6; }
.source-count,.sheet-title > span,.type,.work { font-size:12px; }
.source-count { display:inline-flex; align-items:center; gap:6px; color:#425d63; white-space:nowrap; }
.sheets { display:grid; grid-template-columns:minmax(0,1.9fr) minmax(275px,.93fr); gap:clamp(14px,1.35vw,22px); align-items:start; }
.study-sheet,.control-sheet { min-width:0; border:1px solid #d4dedb; background:#fff; border-radius:10px; overflow:hidden; }
.sheet-title { background:#eaf2ef; color:#204f4f; padding:15px clamp(13px,1.35vw,22px); border-top:3px solid #316c67; border-bottom:1px solid #d7e3de; }
.sheet-title h3 { font-size:18px; font-weight:700; line-height:1.3; }.sheet-title > span { color:#51676a; }
.sheet-title h3 { scroll-margin-top:18px; }.sheet-title h3:focus-visible { outline:2px solid #32666b; outline-offset:3px; }
@media(max-width:1024px) { .sheet-title h3 { scroll-margin-top:76px; } }
.control-sheet .sheet-title { color:#49405f; background:#f0eff5; border-top-color:#786986; border-bottom-color:#e0dde8; }
table { width:100%; border-collapse:collapse; table-layout:fixed; text-align:left; }
thead th { font-size:12px; color:#52696b; font-weight:650; background:#f7f9f8; padding:9px 14px; }
thead th:first-child { width:34%; }thead th:nth-child(2) { width:25%; }
tbody th,td { padding:15px 14px; border-top:1px solid #e0e8e6; vertical-align:top; overflow-wrap:anywhere; line-height:1.7; font-size:13px; font-weight:400; }
.type,.work { display:block; line-height:1.5; color:#54676d; }
.type { display:flex; align-items:baseline; gap:5px; color:#326661; }
.type::before { content:''; width:6px; height:6px; background:currentColor; border-radius:50%; flex:none; align-self:center; }
.type.mechanism { color:#875c36; }.type.mechanism::before { border-radius:1px; transform:rotate(45deg); }
.inspect { display:block; margin:3px 0 1px; border:0; padding:2px 0; background:transparent; color:#213f45; text-align:left; font:inherit; font-size:15px; font-weight:680; line-height:1.5; cursor:pointer; }
.inspect .el-icon { font-size:12px; color:#6c8584; }.inspect:hover,.dossier a:hover { color:#155e65; text-decoration:underline; text-underline-offset:3px; }
.population { display:block; color:#51666b; }.measure { color:#455c63; }
.measure > small,.finding > small { display:none; }
.dossier a { display:flex; align-items:center; gap:4px; width:fit-content; color:#2b6666; margin-top:7px; font-size:12px; font-weight:600; text-decoration:none; }
.dossier a:focus-visible,.inspect:focus-visible { outline:2px solid #33797c; outline-offset:3px; }
ol { margin:0; padding:3px clamp(13px,1.35vw,22px) 0; list-style:none; }
li { display:grid; grid-template-columns:23px 1fr; gap:9px; padding:16px 0; }
li + li { border-top:1px solid #e2e6e9; }.control-body { min-width:0; }
.pin { margin-top:2px; display:grid; place-items:center; width:23px; height:23px; border:1px solid #dbd6e3; color:#766384; border-radius:6px; background:#f8f6fa; }
.control-body p,.record { font-size:13px; line-height:1.75; }.control-body p { margin:5px 0; }
.record { display:flex; align-items:baseline; gap:7px; color:#56656b; }.record strong { flex:none; color:#63596d; font-size:12px; }
.empty { padding:20px; font-size:13px; color:#52656d; }
@media(max-width:1100px) { .sheets { grid-template-columns:minmax(0,1.65fr) minmax(235px,.95fr); } tbody th,td,thead th { padding-inline:9px; } }
@media(max-width:900px) { .sheets { grid-template-columns:minmax(0,1fr); } }
@media(max-width:620px) {
 .dossier { margin-top:24px; }.dossier-heading { grid-template-columns:minmax(0,1fr) auto; gap:5px 12px; }
 .index-art { grid-column:2; grid-row:1 / 3; align-self:center; width:64px; }.source-count { grid-column:1; }
 .dossier-heading p { font-size:12px; }.sheets { gap:14px; }
 table,tbody,tr,tbody th,td { display:block; width:auto; } thead { position:absolute; width:1px; height:1px; overflow:hidden; clip-path:inset(50%); }
 tbody tr { padding:12px 15px 13px; } tbody tr + tr { border-top:1px solid #dce5e2; }
 tbody th,td { border:0; padding:0; } .population { margin:2px 0 6px; }
 .measure > small,.finding > small { display:inline; margin-right:7px; color:#51676a; font-weight:650; font-size:12px; }
 .finding { margin-top:3px; }.sheet-title { padding:12px 15px; }
}
</style>
