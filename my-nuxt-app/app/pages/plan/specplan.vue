<template>
  <div class="system-layout">
    <Sidebar default-active="5" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="workspace-heading">
            <button type="button" class="back-link" @click="goBack"><el-icon class="back-icon"><ArrowLeft /></el-icon><span class="back-text">返回方案推荐</span></button>
            <span class="divider" aria-hidden="true">|</span>
            <span class="page-title-top">干预方案报告</span>
          </div>
          <div class="ep-right-zone">
            <div class="user-profile">
              <div class="avatar">Dr.</div>
              <span>职业卫生评估员</span>
            </div>
          </div>
        </div>
      </header>

      <div class="report-view-wrapper">
        <div v-if="person" class="report-paper" :class="{ 'secondary-prevention': person.level === 'level2' }">
          <div class="report-header">
            <div class="rh-left">
              <svg class="report-logo-custom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <div class="rh-text">
                <h1>{{ person.id }} · 干预方案报告</h1>
                <p>{{ person.dept }}</p>
              </div>
            </div>
            <div class="rh-right">
              <div class="prevention-level">
                <span>预防层级</span>
                <strong>{{ person.level === 'level2' ? '二级预防' : '一级预防' }}</strong>
              </div>
            </div>
          </div>

          <p class="report-source">本报告依据预设岗位档案整理干预事项。具体作业安排由岗位负责人确认，个体诊疗与复查项目由职业医师评估。</p>

          <!-- 一、干预对象信息 -->
          <div class="report-section">
            <h3 class="rs-title">一、干预对象</h3>
            <el-descriptions :column="2" border class="custom-descriptions">
              <el-descriptions-item label="对象编号">{{ person.id }}</el-descriptions-item>
              <el-descriptions-item label="所属部门">{{ person.dept }}</el-descriptions-item>
              <el-descriptions-item label="暴露工龄">{{ person.years }} 年</el-descriptions-item>
              <el-descriptions-item label="暴露因素">{{ person.factors }}</el-descriptions-item>
              <el-descriptions-item label="干预措施">{{ person.workflow.length }} 项</el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 方案依据 -->
          <div class="report-section">
            <h3 class="rs-title">二、方案依据</h3>

            <!-- 核心结论（置顶突出） -->
            <div class="recommendation-hero">
              <div class="rh-badge">方案重点</div>
              <p class="rh-text">{{ person.recommendationSummary }}</p>
            </div>

            <dl class="basis-list">
              <div v-for="basis in person.basis" :key="basis.label">
                <dt>{{ basis.label }}</dt>
                <dd>{{ basis.detail }}</dd>
              </div>
            </dl>
            <div class="background-factors">
              <h4>档案背景</h4>
              <span v-for="item in person.confounders" :key="item.factor">{{ item.factor }}</span>
            </div>
          </div>

          <section class="report-section">
            <h3 class="rs-title">三、本次执行重点</h3>
            <PlanReviewFocus :person="person" readonly />
          </section>

          <!-- 四、干预流程 -->
          <div class="report-section">
            <h3 class="rs-title">四、干预实施流程（共 {{ person.workflow.length }} 步）</h3>
            <div class="workflow-report">
              <div class="wr-step" v-for="(step, idx) in person.workflow" :key="idx">
                <div class="wr-header">
                  <div class="wr-num" :class="step.type">步骤 {{ idx + 1 }}</div>
                  <div class="wr-title">
                    <h4>{{ step.title }}</h4>
                    <el-tag size="small" :type="getTagType(step.type)" effect="light">{{ step.tag }}</el-tag>
                  </div>
                </div>
                <div class="wr-body">
                  <p class="wr-desc">{{ step.desc }}</p>
                  <div class="wr-detail" v-if="step.detail">
                    <strong>具体操作：</strong>{{ step.detail }}
                  </div>
                  <div class="wr-indicator" v-if="step.indicator">
                    <strong>记录要求：</strong>{{ step.indicator }}
                  </div>
                  <div class="wr-meta">
                    <el-tag size="small" type="info" effect="light">{{ step.period }}</el-tag>
                    <span>建议分工 · {{ step.owner }}</span>
                    <span v-if="isReviewed(person.id, planStepKey(step, idx))" class="reviewed-step">措施内容已核对</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <section class="report-section">
            <h3 class="rs-title">五、随访观察与记录</h3>
            <p class="section-note">按对象编号归集实际资料，保留原单位、日期和专业意见。</p>
            <table class="observation-table">
              <thead><tr><th scope="col">观察项目</th><th scope="col">资料来源</th><th scope="col">登记内容</th></tr></thead>
              <tbody>
                <tr v-for="item in person.outcomes" :key="item.label">
                  <th scope="row">{{ item.label }}</th>
                  <td>{{ item.source }}</td>
                  <td>{{ item.record }}</td>
                </tr>
              </tbody>
            </table>
          </section>

          <section class="report-section"><h3 class="rs-title">六、现场核查与资料依据</h3>
            <ExposureControlReview :factors="person.factors" />
          </section>

          <div class="report-footer">
            <div class="report-btns">
              <el-button type="success" size="large" @click="handlePrint"><el-icon><Printer /></el-icon> 打印 / 保存 PDF</el-button>
              <el-button type="info" size="large" plain @click="goBack">返回方案推荐</el-button>
            </div>
          </div>
        </div>
        <section v-else class="report-empty" aria-live="polite"><el-icon><Document /></el-icon><h1>未找到干预对象</h1><p>请返回方案推荐页选择对象，再查看对应报告。</p><el-button type="primary" @click="goBack">返回方案推荐</el-button></section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { ArrowLeft, Document, Printer } from '@element-plus/icons-vue'
import { PRODUCT_SHORT_NAME } from '~/utils/product'
import { planStepKey, usePlanChecks } from '~/composables/usePlanChecks'
import { getInterventionPlan } from '~/utils/interventionPlans'
import { causalPlanOrigin } from '~/utils/causalNavigation'

const router = useRouter()
const route = useRoute()

const { isReviewed } = usePlanChecks()
const goBack = () => {
  const query = person.value ? { person: person.value.id } : {}
  const causal = causalPlanOrigin(route.query)
  if (causal) {
    Object.assign(query, causal.origin)
  } else if (route.query.from === 'risk' && ['individual', 'batch'].includes(route.query.mode)) {
    Object.assign(query, { from: 'risk', mode: route.query.mode })
  }
  return router.push({ path: '/plan', query })
}
const handlePrint = () => window.print()

const getTagType = (type) => {
  if (type === 'danger') return 'danger'
  if (type === 'warning') return 'warning'
  if (type === 'primary') return 'primary'
  return 'success'
}

const person = computed(() => {
  if (route.query.person == null && route.query.from !== 'causal') return getInterventionPlan('SZ-284')
  return getInterventionPlan(route.query.person)
})
useHead(() => ({
  title: `${person.value ? person.value.id + ' · ' : ''}干预方案报告 · ${PRODUCT_SHORT_NAME}`,
}))

</script>

<style lang="scss" scoped>
.reviewed-step { color: #216a58; font-weight: 650; }
@media print { .report-section :deep(.review-row) { break-inside: avoid; } }
$color-primary: #1D4ED8;
$color-bg: #F8FAFC;
$text-main: #0F172A;
$text-muted: #64748B;
$border-color: #E2E8F0;
$color-danger: #EF4444;
$color-warn: #F59E0B;

* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }

.main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth; }
.ep-header { height: 60px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex; justify-content: center; flex-shrink: 0; }
.nav-wrapper { width: 100%; padding: 0 40px; display: flex; justify-content: space-between; align-items: center; }
.back-link { display: flex; align-items: center; gap: 12px; cursor: pointer; color: $text-main; &:hover { color: $color-primary; } .back-text { font-size: 1.05rem; font-weight: 600; } .divider { color: #D1D5DB; margin: 0 4px; } .page-title-top { font-size: 1.1rem; font-weight: 800; } }
.user-profile { display: flex; align-items: center; gap: 12px; font-weight: 500; font-size: 0.95rem; .avatar { width: 32px; height: 32px; border-radius: 50%; background: #EFF6FF; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; } }

.report-view-wrapper { flex: 1 0 auto; background: #E2E8F0; padding: 40px 0; display: flex; justify-content: center; align-items: flex-start; }
.report-paper { background: #fff; width: 1000px; height: max-content; padding: 80px; position: relative; box-shadow: 0 20px 50px rgba(0,0,0,0.1); border-radius: 2px; }


.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
  .rh-left { display: flex; align-items: center; gap: 12px; }
  .report-logo-custom { width: 32px; height: 32px; color: $color-primary; margin-bottom: 4px; }
  h1 { font-size: 24px; color: $text-main; margin: 0 0 10px 0; font-weight: 800; letter-spacing: -1px; } p { font-size: 13px; color: $text-muted; margin: 0; }
}

.report-section { margin-top: 40px; .rs-title { font-size: 18px; font-weight: 800; color: $text-main; border-bottom: 2px solid $text-main; padding-bottom: 8px; margin-bottom: 20px; } &.highlight { background: #F1F5F9; padding: 30px; border-radius: 8px; } }

/* 干预流程样式 */
.workflow-report { display: flex; flex-direction: column; gap: 16px; }
.wr-step { border: 1px solid $border-color; border-radius: 8px; padding: 20px; &:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); } }
.wr-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
.wr-num { width: 72px; height: 32px; border-radius: 6px; display: flex; justify-content: center; align-items: center; font-weight: 800; font-size: 0.8rem; flex-shrink: 0;
  &.danger { background: #FEF2F2; color: #EF4444; border: 1px solid #FECACA; }
  &.primary { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
  &.warning { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
  &.safe { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
}
.wr-title { flex: 1; display: flex; align-items: center; gap: 10px; h4 { margin: 0; font-size: 1rem; font-weight: 700; color: $text-main; } }
.wr-body { padding-left: 86px;
  .wr-desc { margin: 0 0 10px 0; font-size: 0.9rem; color: #475569; line-height: 1.6; }
  .wr-detail, .wr-indicator { font-size: 0.85rem; color: #64748B; margin-bottom: 8px; line-height: 1.5; strong { color: $text-main; } }
  .wr-detail { padding: 10px 12px; background: #F8FAFC; border-radius: 6px; border: 1px solid #F1F5F9; }
  .wr-indicator { padding: 10px 12px; background: #FFFBEB; border-radius: 6px; border: 1px solid #FDE68A; strong { color: #92400E; } }
  .wr-meta { display: flex; gap: 8px; margin-top: 10px; }
}

/* 推荐依据模块 */
.recommendation-hero { background: #ECFDF5; color: #064E3B; border: 1px solid #A7F3D0; border-radius: 10px; padding: 24px 28px; margin-bottom: 24px;
  .rh-badge { display: inline-block; background: #D1FAE5; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; margin-bottom: 12px; letter-spacing: 1px; color: #047857; }
  .rh-text { font-size: 15px; line-height: 1.8; margin: 0 0 16px 0; color: #064E3B; }
  .rh-meta { display: flex; gap: 20px; font-size: 12px; color: #047857; border-top: 1px solid #A7F3D0; padding-top: 12px; }
}

.report-footer { margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end; .sign { font-family: 'Brush Script MT', cursive; font-size: 24px; margin-left: 10px; text-decoration: underline; color: #1e293b; } .sign-system { font-weight: 700; color: #94a3b8; } }

@media print { .sidebar, .ep-header, .report-btns { display: none !important; } .main-content { height: auto; overflow: visible; } .report-paper { box-shadow: none; padding: 40px; } }

@media screen {
  .main-content, .report-view-wrapper, .report-paper, .rh-left, .rh-text,
  .wr-title, .recommendation-hero { min-width: 0; }
  .report-paper { width: min(1000px, calc(100% - 48px)); }
}
@media screen and (max-width: 1280px) {
  .report-paper { padding: 40px; }

  .report-header { gap: 20px; }
  .report-header .rh-left { flex: 1; }
  .report-header .report-logo-custom { flex-shrink: 0; }
  .report-header h1 { font-size: 21px; line-height: 1.5; }
  .report-header p { line-height: 1.8; }
  .report-footer { gap: 24px; flex-wrap: wrap; }
  .report-btns { display: flex; gap: 12px; flex-wrap: wrap; }
  .report-btns :deep(.el-button) { margin-left: 0; }
  .recommendation-hero .rh-meta { flex-wrap: wrap; gap: 8px 16px; }
}
@media screen and (max-width: 700px) {
  .ep-header { height: auto; min-height: 58px; }
  .nav-wrapper { padding: 12px 16px; }
  .back-link { gap: 7px; min-width: 0; flex-wrap: wrap; }
  .back-link .back-text, .back-link .page-title-top { font-size: 13px; }
  .back-link .divider { margin: 0 2px; }
  .ep-right-zone { display: none; }
  .report-view-wrapper { padding: 12px; }
  .report-paper { width: 100%; padding: 20px 16px; border-radius: 10px; }

  .report-header { align-items: flex-start; flex-wrap: wrap; gap: 16px; }
  .report-header .rh-left { flex-basis: 100%; gap: 8px; align-items: flex-start; }
  .report-header .report-logo-custom { width: 26px; height: 26px; }
  .report-header h1 { font-size: 18px; }
  .report-header p { font-size: 11px; }
  .report-header .rh-right { margin-left: auto; padding: 0 8px 6px; }


  .report-section { margin-top: 28px; }
  .report-section .rs-title { font-size: 16px; line-height: 1.7; margin-bottom: 16px; }
  .custom-descriptions :deep(.el-descriptions__table) { table-layout: fixed; }
  .custom-descriptions :deep(.el-descriptions__body tr) { display: grid; grid-template-columns: minmax(85px, .9fr) minmax(0, 1.5fr); }
  .custom-descriptions :deep(.el-descriptions__cell) { display: block; min-width: 0; width: auto; padding: 10px; font-size: 12px; line-height: 1.7; overflow-wrap: anywhere; }
  .recommendation-hero { padding: 16px; margin-bottom: 16px; }
  .recommendation-hero .rh-text { font-size: 13px; line-height: 1.9; overflow-wrap: anywhere; }
  .recommendation-hero .rh-meta { font-size: 11px; gap: 8px; }
  .wr-step { padding: 14px; }
  .wr-header { gap: 8px; align-items: flex-start; }
  .wr-num { width: 62px; font-size: 11px; }
  .wr-title { flex-wrap: wrap; gap: 5px; }
  .wr-title h4 { font-size: 14px; line-height: 1.7; }
  .wr-body { padding-left: 0; }
  .wr-body .wr-desc, .wr-body .wr-detail, .wr-body .wr-indicator { font-size: 12px; line-height: 1.8; overflow-wrap: anywhere; }
  .wr-body .wr-meta { flex-wrap: wrap; }
  .report-footer { margin-top: 32px; gap: 20px; }
  .report-footer .sign-area { font-size: 12px; line-height: 1.8; }
  .report-footer .sign { font-size: 21px; }
  .report-btns { width: 100%; gap: 10px; }
  .report-btns :deep(.el-button) { width: 100%; min-height: 44px; height: auto; padding: 12px; font-size: 13px; white-space: normal; }
  .report-btns :deep(.el-button > span) { white-space: normal; }
}

/* Screen and print share the same source note and prevention level. */
.workspace-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 14px; }
.workspace-heading .back-link { font: inherit; font-size: 13px; background: none; border: 0; padding: 4px 0; color: #68859b; }
.workspace-heading .page-title-top { font-size: 15px; font-weight: 700; }
.workspace-heading .divider { color: #c9d6e1; }
.report-view-wrapper { background: #f3f7fb; }
.report-paper { border: 1px solid #e3ebf3; border-radius: 12px; box-shadow: 0 8px 30px rgba(57, 91, 119, .06); padding: 48px 56px; }





/* Prevention level is indicated by its name, color and left border. */
.report-paper { --level-ink: #15675d; --level-tint: #eef8f4; --level-rule: #55a899; border-top: 4px solid var(--level-rule); }
.report-paper.secondary-prevention { --level-ink: #8b461b; --level-tint: #fff3e7; --level-rule: #c67a42; }
.prevention-level { display: grid; gap: 3px; padding: 9px 16px; border-left: 3px solid var(--level-rule); background: var(--level-tint); color: var(--level-ink); }
.prevention-level span { font-size: 12px; }
.prevention-level strong { font-size: 17px; line-height: 1.4; white-space: nowrap; }
.report-source { margin: 14px 0 0; padding: 12px 0; border-block: 1px solid #dce3ea; font-size: 12px; line-height: 1.75; color: #516375; }
.report-footer { justify-content: flex-end; }
.recommendation-hero { background: #f5f7fd; color: #27354c; border-color: #dce3f0; }
.recommendation-hero .rh-text { color: #27354c; margin: 0; }
.recommendation-hero .rh-badge { background: #e8ecf7; color: #384b72; }
@media screen and (max-width: 700px) {
  .report-header { gap: 10px; }
  .report-header .rh-right { margin: 0; padding: 0; }
  .prevention-level { display: inline-flex; align-items: center; gap: 8px; padding: 4px 10px; }
  .prevention-level strong { font-size: 13px; }
}
@media print {
  .system-layout, .main-content { display: block; height: auto; overflow: visible; }
  .report-view-wrapper { display: block; background: white; padding: 0; }
  .report-view-wrapper .report-paper { width: 100%; }
  .report-header, .report-source, .wr-step { break-inside: avoid; }
  .report-section .rs-title { break-after: avoid; }
  .report-source { color: #333e4c; }
}
.report-section .rs-title { border-bottom: 1px solid #e3ecf4; color: #35546c; font-size: 17px; padding-bottom: 12px; }
.section-note { color: #899eaf; font-size: 12px; line-height: 1.7; }
.report-empty { width: min(520px, calc(100% - 32px)); background: #fff; border: 1px solid #e2eaf2; border-radius: 12px; padding: 48px 24px; text-align: center; color: #58758b; }
.report-empty > .el-icon { font-size: 38px; color: #7db3d6; }
.report-empty h1 { font-size: 22px; margin-top: 20px; }
.report-empty p { font-size: 13px; line-height: 1.8; color: #899baa; margin-bottom: 22px; }
@media (max-width: 700px) { .report-paper { padding: 22px 18px; } .report-header h1 { font-size: 21px; } .report-section .rs-title { font-size: 16px; } .workspace-heading { gap: 10px; } .report-section { margin-top: 28px; } .or-item .or-delta { white-space: normal; font-size: 11px; } }
@media print { .report-paper { border: none; border-radius: 0; box-shadow: none; padding: 20px; } }
.basis-list { margin: 0; }
.basis-list > div { padding: 12px 0; border-bottom: 1px solid #e2e9f0; }
.basis-list dt { margin: 0 0 4px; font-weight: 650; color: #29455e; }
.basis-list dd { margin: 0; line-height: 1.75; color: #40566c; }
.background-factors { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; margin: 16px 0 0; font-size: 13px; }
.background-factors h4 { margin: 0; font-weight: 700; }
.background-factors span { color: #4a6176; }
.wr-meta { flex-wrap: wrap; align-items: center; color: #4b6278; font-size: 12px; }
.observation-table { width: 100%; table-layout: fixed; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
.observation-table th, .observation-table td { padding: 10px; text-align: left; line-height: 1.65; vertical-align: top; border-bottom: 1px solid #dce4eb; overflow-wrap: anywhere; }
.observation-table thead th { color: #345266; background: #eef5f7; }
.observation-table thead th:first-child { width: 24%; }
.observation-table thead th:nth-child(2) { width: 29%; }
.observation-table tbody th { color: #20364d; font-weight: 650; }
@media screen and (max-width: 700px) {
  .observation-table th, .observation-table td { padding: 8px 5px; font-size: 12px; }
}
@media print {
  .basis-list > div, .observation-table tr { break-inside: avoid; }
  .observation-table thead { display: table-header-group; }
  .report-paper { border: 0; border-radius: 0; padding: 0; box-shadow: none; }
}
</style>
