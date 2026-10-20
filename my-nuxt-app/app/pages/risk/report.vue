<template>
  <div class="system-layout">
    <Sidebar :default-active="isBatchMode ? '3-2' : '3-1'" />
    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goBack">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">返回预测控制台</span>
            <span class="divider">|</span>
            <span class="page-title-top">健康指标估计深度报告</span>
          </div>
          <div class="ep-right-zone">
            <div class="user-profile"><div class="avatar">Dr.</div><span>职业卫生研究视图</span></div>
          </div>
        </div>
      </header>

      <div class="report-view-wrapper">
        <div class="report-paper">
          <div class="report-watermark">RESEARCH ESTIMATION REPORT</div>
          <div class="report-header">
            <div class="rh-left">
              <svg class="report-logo-custom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              <div class="rh-text">
                <h1>{{ isBatchMode ? '全群健康指标估计与分布报告' : '健康指标条件估计与模型响应报告' }}</h1>
                <p>数据来源：{{ sourceLabel }} | 报告查看时间：{{ viewedAt || '—' }}</p>
                <p v-if="cohort" class="model-version">版本：{{ cohort.model_version }} · 全文件：{{ cohort.total_records }} 人 · 已完成全部记录处理</p>
                <p v-else-if="result" class="model-version">版本：{{ result.model_version }} · 当前对象：{{ result.person_id || '未提供编号' }}</p>
              </div>
            </div>
            <div class="rh-right"><div class="risk-seal"><span>研究用途</span><strong>测试版本</strong></div></div>
          </div>

          <el-divider />
          <p class="report-desc scope-note">{{ PREDICTION_SCOPE_NOTE }}</p>
          <div v-if="!hasReport" class="empty-report">
            <h2>暂无本次预测报告</h2>
            <p>{{ isBatchMode ? cohortEmptyReason : '请先在预测控制台完成真实模型计算。本页不读取静态人员名单或模拟图；刷新或关闭会话后需要重新计算。' }}</p>
            <el-button type="primary" plain @click="goBack">返回预测控制台</el-button>
          </div>

          <template v-if="isBatchMode && cohort">
            <div class="report-section">
              <h3 class="rs-title">一、 全文件处理范围与输入质量</h3>
              <el-row :gutter="40">
                <el-col :span="10"><div class="chart-box-report" ref="cohortCoverageRef"></div><p class="chart-caption">全文件有效输入覆盖率；不是高危比例</p></el-col>
                <el-col :span="14">
                  <div class="cohort-facts"><div><span>上传记录总数</span><strong>{{ cohort.total_records }} 人</strong></div><div><span>有效输入</span><strong>{{ cohort.processed_records }} 人</strong></div><div><span>输入不足跳过</span><strong>{{ cohort.skipped_records }} 人</strong></div><div><span>所选结局可估计</span><strong>{{ cohortView?.estimated_count || 0 }} 人</strong></div></div>
                </el-col>
              </el-row>
              <p class="report-desc">全部 {{ cohort.total_records }} 条上传记录均已处理，非先取一页再逐人查看。输入不合格的记录保留跳过原因；符合输入要求但某结局验证不足的对象，不为该结局补造估计值。所有汇总均为本文件未加权描述，不代表 NHANES 总体或职业人群的患病率。</p>
              <details v-if="cohortExcluded.length" class="cohort-excluded"><summary>查看 {{ cohortExcluded.length }} 条输入不足记录的原因</summary><ul><li v-for="row in cohortExcluded" :key="row.row_number">原始行 {{ row.row_number }} · {{ row.person_id }}：{{ row.reason || row.status }}</li></ul></details>
            </div>

            <div class="report-section highlight">
              <h3 class="rs-title">二、 全群 12 项结局描述统计</h3>
              <div class="cohort-table-wrap"><table class="cohort-statistics"><thead><tr><th>结局 / 单位</th><th>估计人数</th><th>暂不出值人数</th><th>均值</th><th>中位数</th><th>Q1</th><th>Q3</th><th>最小值</th><th>最大值</th></tr></thead><tbody><tr v-for="summary in cohort.summary" :key="summary.target"><td><strong>{{ summary.label_zh }}</strong><small>{{ summary.unit }}</small></td><td>{{ summary.estimated_count }}</td><td>{{ summary.withheld_count }}</td><td>{{ formatPredictionNumber(summary.statistics?.mean) }}</td><td>{{ formatPredictionNumber(summary.statistics?.median) }}</td><td>{{ formatPredictionNumber(summary.statistics?.q1) }}</td><td>{{ formatPredictionNumber(summary.statistics?.q3) }}</td><td>{{ formatPredictionNumber(summary.statistics?.min) }}</td><td>{{ formatPredictionNumber(summary.statistics?.max) }}</td></tr></tbody></table></div>
              <p class="report-desc">每项结局在全文件内全部可提供估计值的对象中汇总，分母可能不同。未出值不计为 0；“—”表示没有可汇总的数值。Q1 / Q3 为第 25 / 75 百分位数，不是正常参考界限或置信区间。</p>
            </div>

            <div class="report-section">
              <h3 class="rs-title">三、 综合相对预警与单项排名</h3>
              <RiskCohortWarning :result="cohort" :threshold="cohortWarningThreshold" @update:threshold="cohortWarningThreshold = $event" />
              <h4 class="chart-caption">所选结局单项数值排序 · Top 20 展示（不是综合预警榜）</h4>
              <div class="cohort-target-control"><span>切换结局：</span><el-select v-model="selectedTarget" style="width: 240px"><el-option v-for="summary in cohort.summary" :key="summary.target" :value="summary.target" :label="summary.label_zh + ' / ' + summary.unit" /></el-select></div>
              <div v-if="cohortRankOption" class="chart-box-report" ref="cohortRankRef" :style="{ height: Math.max(280, cohortTopRows.length * 24 + 80) + 'px' }"></div>
              <div v-else class="chart-box-report report-empty">{{ cohortView?.reason || '所选结局暂无可排序的估计值' }}</div>
              <div v-if="cohortTopRows.length" class="worker-table"><div class="wt-header"><span>全群排序 / 对象编号</span><span>原始行号</span><span>年龄 / 岁</span><span>{{ selectedLabel }}</span><span>单位</span></div><div class="wt-row" v-for="row in cohortTopRows" :key="row.row_number"><span class="w-name"><strong>{{ row.rank }} · {{ row.person_id }}</strong></span><span>{{ row.row_number }}</span><span>{{ formatPredictionNumber(row.age, 0) }}</span><span class="w-score">{{ formatPredictionNumber(row.prediction) }}</span><span>{{ cohortView?.unit }}</span></div></div>
              <p class="report-desc">本图从全文件 {{ cohortView?.estimated_count || 0 }} 个有效估计中按数值降序排列，仅图表和表格截取前 20 人；完整排序 CSV 不截断。指标数值排序不是临床危险等级，HDL 等指标的高低方向也不同，不能统称为“高危人员”。</p>
            </div>

            <div class="report-section highlight">
              <h3 class="rs-title">四、 {{ selectedLabel }}全群估计值分布</h3>
              <div v-if="cohortDistributionOption" class="chart-box-report" ref="cohortDistributionRef" style="height: 300px;"></div>
              <div v-else class="chart-box-report report-empty" style="height: 300px;">{{ cohortView?.reason || '本结局暂无完整可用的全群分布数据' }}</div>
              <p class="report-desc">横轴保留指标原单位，纵轴为全文件相应估计区间中的人数。这是模型估计值分布，不是实测患病人数或未来发病率；未出值与输入不足的记录不混入数值分布。</p>
            </div>

            <div class="report-section">
              <h3 class="rs-title">五、 {{ selectedLabel }}的性别与年龄分层</h3>
              <el-row :gutter="40"><el-col :span="12"><div v-if="cohortGenderOption" class="chart-box-report" ref="cohortGenderRef"></div><div v-else class="chart-box-report report-empty">暂无可计算的性别分层</div><p class="chart-caption">按文件中的性别分组显示指标估计均值</p></el-col><el-col :span="12"><div v-if="cohortAgeOption" class="chart-box-report" ref="cohortAgeRef"></div><div v-else class="chart-box-report report-empty">暂无可计算的年龄分层</div><p class="chart-caption">按文件中的年龄组显示指标估计均值</p></el-col></el-row>
              <p class="report-desc">分层均值来自全文件相应分组的有效估计，未调整混杂，不是年龄或性别的因果效应。当前没有全群 SHAP / 暴露干预分析，不以任意一人的局部贡献、敏感性曲线或联合响应替代群体结论。</p>
            </div>
            <div v-if="cohort.warnings?.length" class="report-section"><p class="report-desc"><strong>[全群适用性提示]：</strong><br /><span v-for="warning in cohort.warnings" :key="warning">{{ warning }}<br /></span></p></div>
          </template>

          <template v-else-if="!isBatchMode && hasReport">
          <div class="report-section">
            <h3 class="rs-title">一、 当前对象与当次指标估计</h3>
            <p class="report-desc">保留输入记录与原始单位，展示{{ selectedLabel }}的模型估计；不筛选“高危人员”，不推断临床危险等级。一次单人输入不能推导人群患病率。</p>
            <div v-if="hasReport" class="worker-table">
              <div class="wt-header">
                <span>对象编号</span><span>年龄 / BMI</span><span>全血铅</span><span>全血镉 / 总汞</span><span>{{ selectedLabel }}</span>
              </div>
              <div class="wt-row" v-for="row in reportRows" :key="row.key">
                <span class="w-name"><strong>{{ row.id }}</strong><small>{{ row.recordStatus }}</small></span>
                <span>{{ row.age }} 岁<br />{{ row.bmi }} kg/m²</span>
                <span>{{ row.pb }}</span>
                <span>{{ row.cd }}<br />{{ row.hg }}</span>
                <span class="w-score">{{ row.estimate }}<small>{{ row.reason }}</small></span>
              </div>
            </div>
            <div v-else class="report-empty">尚无本次输入及估计记录</div>
          </div>

          <div class="report-section highlight">
            <h3 class="rs-title">二、 当前对象 12 项健康指标估计</h3>
            <el-row :gutter="40">
              <el-col :span="10">
                <div v-if="hasReport" class="chart-box-report" ref="reportGaugeRef"></div>
                <div v-else class="chart-box-report report-empty">待完成真实模型计算</div>
                <p class="chart-caption">可提供数值的结局占比；不是患病概率</p>
              </el-col>
              <el-col :span="14">
                <div v-if="result && hasReport" class="disease-list">
                  <div class="d-item" v-for="outcome in result.results" :key="outcome.target">
                    <div class="d-info">
                      <span class="d-name">{{ outcome.label_zh }}</span>
                      <span class="d-val" :class="predictionHasValue(outcome) ? 'estimate' : 'withheld'">{{ predictionHasValue(outcome) ? formatPredictionNumber(outcome.prediction) + ' ' + outcome.unit : '暂不出值' }}</span>
                    </div>
                    <el-progress :percentage="predictionHasValue(outcome) ? 100 : 0" color="#3B82F6" :stroke-width="3" :show-text="false" class="custom-progress" />
                    <small class="outcome-note">{{ predictionHasValue(outcome) ? predictionIntervalLabel(outcome) : predictionReason(outcome) }}</small>
                  </div>
                </div>
                <div v-else class="report-empty">不以固定百分比填充结局</div>
                <p class="chart-caption">蓝色条仅标记“已提供估计值”，不是风险概率，也不表示指标数值大小。</p>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[结果说明]：</strong>{{ availableCount }} 项可提供探索性数值。其余项目保留暂不出值的原因；暂不出值既不表示正常，也不表示已经患病。{{ INTERVAL_NOTE }}</p>
          </div>

          <div v-if="radarOption || shapOption" class="report-section">
            <h3 class="rs-title">当前模型局部贡献结构与特征解释</h3>
            <el-row :gutter="40">
              <el-col v-if="radarOption" :span="shapOption ? 12 : 24">
                <div v-if="hasReport && radarOption" class="chart-box-report" ref="reportRadarRef"></div>
                <p class="chart-caption">绝对 SHAP 贡献前 5 项与其他项合计的同尺度份额（%）；不是金属浓度、疾病概率或因果作用</p>
              </el-col>
              <el-col v-if="shapOption" :span="radarOption ? 12 : 24">
                <div v-if="hasReport && shapOption" class="chart-box-report shap-chart" ref="reportShapRef"></div>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[模型解释]：</strong>{{ explanationText }} 带符号的 SHAP 值只解释本次模型输出，包含缺失输入分支；不表示金属的因果效应或人体毒性强弱。</p>
            <div class="report-supplement">
              <h4 class="supplement-title">补充信息：全血原始输入与单位核对</h4>
              <div v-if="hasReport" class="chart-box-report" ref="reportBloodRef"></div>
              <div v-else class="chart-box-report report-empty">待录入全血铅、镉、总汞及原始单位</div>
              <p class="chart-caption">三个独立数值轴，各保留录入单位；条长不可跨金属比较，不用于推断毒性强弱</p>
            </div>
          </div>

          <div v-if="doseOption" class="report-section highlight">
            <h3 class="rs-title">全血铅输入敏感性与模型响应</h3>
            <el-row :gutter="40"><el-col :span="24">
              <div v-if="hasReport && doseOption" class="chart-box-report" ref="reportDoseResponseRef" style="height: 300px;"></div>
            </el-col></el-row>
            <p class="report-desc"><strong>[响应说明]：</strong>{{ charts?.dose_response.note || '固定当前对象其余模型输入，仅改变全血铅，查看当前所选指标的真实模型输出。' }} 横轴为全血铅浓度，纵轴为{{ selectedLabel }}估计值；不能据此认定致病阈值、未来发病率或干预效果。</p>
          </div>

          <div v-if="jointOption" class="report-section">
            <h3 class="rs-title">全血铅 × 镉联合输入响应</h3>
            <el-row :gutter="40"><el-col :span="24">
              <div v-if="hasReport && jointOption" class="chart-box-report" ref="reportJointEffectRef" style="height: 300px;"></div>
            </el-col></el-row>
            <p class="report-desc"><strong>[联合响应说明]：</strong>{{ charts?.joint_response.note || '固定当前对象其余输入，枚举全血铅与镉的组合，以所选指标原单位显示模型估计。' }} 颜色深浅只表示模型输出大小，不能证明协同致毒、独立风险叠加或因果交互作用。</p>
          </div>

          <div class="report-section" v-if="result?.warnings?.length">
            <p class="report-desc"><strong>[输入与适用性提示]：</strong><br /><span v-for="warning in result.warnings" :key="warning">{{ warning }}<br /></span></p>
          </div>
          </template>
          <div class="report-footer">
            <div class="sign-area">
              <p>系统算法流：<span class="sign-system">{{ algorithmLabel }}</span></p>
              <p class="chart-caption">横断面同期指标估计 · 非诊断 · 未完成职业人群外部验证</p>
            </div>
            <div class="report-btns">
              <el-button :disabled="!hasReport" @click="exportJson">下载 JSON</el-button>
              <el-button :disabled="!hasReport" @click="exportCsv">{{ isBatchMode ? '全人 × 12 结局 CSV' : '下载 CSV' }}</el-button>
              <el-button v-if="cohort" @click="exportCompositeWarning">综合预警排序 CSV</el-button>
              <el-button v-if="cohort" @click="exportCohortRanking">所选结局排序 CSV</el-button>
              <el-button v-if="cohort" @click="exportCohortSummary">12 结局汇总 CSV</el-button>
              <el-button type="success" size="large" :disabled="!hasReport" @click="handlePrint"><el-icon><Printer /></el-icon> 打印并存档报告</el-button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onActivated, onDeactivated, nextTick, onBeforeUnmount, watch } from 'vue'
import { ArrowLeft, Printer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { buildGaugeOption, buildRadarOption, buildShapOption, buildDoseOption, buildJointOption, chartReason, selectedOutcome } from '~/utils/riskDashboard'
import { INTERVAL_NOTE, METAL_FIELDS, PREDICTION_SCOPE_NOTE, batchPredictionCsv, downloadPrediction, formatPredictionNumber, predictionCsv, predictionHasValue, predictionIntervalLabel, predictionJson, predictionReason } from '~/utils/riskPrediction'
import type { PredictionRequest, PredictionOutcome } from '~/utils/riskPrediction'
import { cohortResponseError, buildCohortView, buildCohortRankOption, buildCohortDistributionOption, buildCohortGroupOption, buildCohortCoverageOption, cohortSummaryCsv, cohortRankingCsv } from '~/utils/riskCohort'
import type { CohortPredictionResponse } from '~/utils/riskCohort'
import { buildCohortWarning, warningRankingCsv } from '~/utils/cohortWarning'

const route = useRoute()
const { lastResult, lastRequest, dashboard, cohortResult, cohortWarningThreshold, batchIntake, selectedTarget } = usePredictionState()
const isBatchMode = computed(() => route.query.mode === 'batch')
const cohort = computed<CohortPredictionResponse | null>(() => isBatchMode.value && cohortResult.value?.complete === true && !cohortResponseError(cohortResult.value) ? cohortResult.value : null)
const cohortEmptyReason = computed(() => cohortResult.value ? cohortResponseError(cohortResult.value) || '请先完成整份群体文件计算。' : '请在群体预测控制台完成整份上传文件的模型计算。本页不会以单人结果、当前分页或模拟数值替代全群体报告。')
const result = computed(() => isBatchMode.value ? null : dashboard.value?.prediction || lastResult.value)
const request = computed(() => isBatchMode.value ? null : dashboard.value?.input || lastRequest.value)
const charts = computed(() => isBatchMode.value ? undefined : dashboard.value?.charts)
const hasReport = computed(() => isBatchMode.value ? !!cohort.value : !!(result.value && request.value))
const viewedAt = ref('')
const currentTarget = computed(() => isBatchMode.value ? selectedTarget.value : charts.value?.target || selectedTarget.value)
const cohortView = computed(() => cohort.value ? buildCohortView(cohort.value, currentTarget.value) : null)
const compositeWarning = computed(() => cohort.value ? buildCohortWarning(cohort.value, cohortWarningThreshold.value) : null)
const cohortTopRows = computed(() => cohortView.value?.rankings.slice(0, 20) || [])
const cohortExcluded = computed(() => cohortView.value?.excluded || [])
const cohortRankOption = computed(() => cohort.value ? buildCohortRankOption(cohort.value, currentTarget.value, 20) : null)
const cohortDistributionOption = computed(() => cohort.value ? buildCohortDistributionOption(cohort.value, currentTarget.value) : null)
const cohortGenderOption = computed(() => cohort.value ? buildCohortGroupOption(cohort.value, currentTarget.value, 'gender') : null)
const cohortAgeOption = computed(() => cohort.value ? buildCohortGroupOption(cohort.value, currentTarget.value, 'age') : null)
const selectedLabel = computed(() => isBatchMode.value ? cohortView.value?.label_zh || '所选指标' : charts.value?.label_zh || (result.value ? selectedOutcome(result.value, currentTarget.value)?.label_zh : null) || '所选指标')
const sourceLabel = computed(() => isBatchMode.value ? cohort.value ? '全群导入 · ' + (batchIntake.value?.file_id === cohort.value.file_id ? batchIntake.value.filename || cohort.value.file_id : cohort.value.file_id) : '暂无完整群体结果' : hasReport.value ? '本次单人录入' : '暂无本次输入')
const availableCount = computed(() => result.value?.results.filter(predictionHasValue).length || 0)
const activeOutcome = computed(() => selectedOutcome(result.value, currentTarget.value))
const modelChartAllowed = computed(() => !!activeOutcome.value && predictionHasValue(activeOutcome.value))
const radarOption = computed(() => charts.value && modelChartAllowed.value ? buildRadarOption(charts.value) : null)
const shapOption = computed(() => charts.value && modelChartAllowed.value ? buildShapOption(charts.value) : null)
const doseOption = computed(() => charts.value && modelChartAllowed.value ? buildDoseOption(charts.value) : null)
const jointOption = computed(() => charts.value && modelChartAllowed.value ? buildJointOption(charts.value) : null)
const explanationText = computed(() => modelChartAllowed.value && charts.value?.explanation.status === 'AVAILABLE'
  ? '当前所选指标：' + selectedLabel.value + '；贡献尺度：' + (charts.value.explanation.scale_label || '未提供') + '。' + (charts.value.explanation.note || '')
  : activeOutcome.value && !modelChartAllowed.value ? predictionReason(activeOutcome.value) : chartReason(charts.value?.explanation, '本次尚无可用的模型解释结果。'))
const algorithmLabel = computed(() => cohort.value ? 'NHANES 12 结局模型组 · ' + cohort.value.model_version + ' · 全文件计算' : result.value ? Array.from(new Set(result.value.results.flatMap(row => row.model_family))).join(' + ') + ' · ' + result.value.model_version : '等待真实模型响应')

function metalLabel(input: PredictionRequest | undefined | null, key: 'pb' | 'cd' | 'hg'): string {
  const value = input?.person[key]
  const unit = input?.measurements[key]?.unit
  return typeof value === 'number' && Number.isFinite(value) ? formatPredictionNumber(value, 3) + ' ' + (unit || '单位未提供').replace('ug', 'μg') : '未提供'
}
function tableRow(id: string, input: PredictionRequest | null | undefined, outcome: PredictionOutcome | undefined, key: string, recordStatus: string, reason?: string) {
  return { key, id: id || '未提供编号', age: formatPredictionNumber(input?.person.age, 0), bmi: formatPredictionNumber(input?.person.bmi),
    pb: metalLabel(input, 'pb'), cd: metalLabel(input, 'cd'), hg: metalLabel(input, 'hg'), recordStatus,
    estimate: outcome && predictionHasValue(outcome) ? formatPredictionNumber(outcome.prediction) + ' ' + outcome.unit : '暂不出值',
    reason: outcome ? (predictionHasValue(outcome) ? '' : predictionReason(outcome)) : reason || '缺少可用估计结果' }
}
const reportRows = computed(() => {
  if (!result.value || !request.value) return []
  return [tableRow(result.value.person_id, request.value, selectedOutcome(result.value, currentTarget.value), 'current', '本次对象')]
})
const goBack = async () => { await navigateTo({ path: '/risk', query: { mode: isBatchMode.value ? 'batch' : 'individual' } }) }
const handlePrint = () => { if (typeof window !== 'undefined' && hasReport.value) setTimeout(() => window.print(), 500) }
const exportJson = () => {
  if (isBatchMode.value) {
    if (cohort.value) downloadPrediction(JSON.stringify({ exported_at: new Date().toISOString(), selected_target: currentTarget.value, cohort: cohort.value, composite_warning: compositeWarning.value, provenance: cohort.value.provenance, notes: [PREDICTION_SCOPE_NOTE, '全文件全部记录与全部12项结局；按本文件未加权描述，不是群体患病风险或因果作用。'] }, null, 2), 'json', 'NHANES_cohort_complete')
    return
  }
  if (!result.value || !request.value) return
  const content = { ...JSON.parse(predictionJson(request.value, result.value)), dashboard: dashboard.value }
  downloadPrediction(JSON.stringify(content, null, 2), 'json')
}
const exportCsv = () => {
  if (isBatchMode.value) { if (cohort.value) downloadPrediction(batchPredictionCsv(cohort.value), 'csv', 'NHANES_cohort_all_outcomes'); return }
  if (result.value) downloadPrediction(predictionCsv(result.value), 'csv')
}
const exportCohortRanking = () => { if (cohort.value) downloadPrediction(cohortRankingCsv(cohort.value, currentTarget.value), 'csv', 'NHANES_cohort_ranking_' + currentTarget.value) }
const exportCompositeWarning = () => { if (compositeWarning.value) downloadPrediction(warningRankingCsv(compositeWarning.value), 'csv', 'NHANES_cohort_composite_warning') }
const exportCohortSummary = () => { if (cohort.value) downloadPrediction(cohortSummaryCsv(cohort.value), 'csv', 'NHANES_cohort_summary') }

// Separate independent axes: Pb/Cd/Hg retain their original units, not a mixed-unit radar.
function buildBloodInputOption(input: PredictionRequest): echarts.EChartsOption {
  return {
    grid: METAL_FIELDS.map((_, index) => ({ left: 86, right: 60, top: 20 + index * 78, height: 31 })),
    xAxis: METAL_FIELDS.map((metal, index) => ({ type: 'value' as const, gridIndex: index, min: 0, splitNumber: 2,
      name: input.measurements[metal.key].unit.replace('ug', 'μg'), nameTextStyle: { fontSize: 10 }, axisLabel: { fontSize: 9 }, splitLine: { lineStyle: { type: 'dashed' as const } } })),
    yAxis: METAL_FIELDS.map((metal, index) => ({ type: 'category' as const, gridIndex: index, data: [metal.label], axisTick: { show: false }, axisLine: { show: false }, axisLabel: { fontSize: 10 } })),
    series: METAL_FIELDS.map((metal, index) => ({ type: 'bar' as const, xAxisIndex: index, yAxisIndex: index,
      data: [input.person[metal.key]], barMaxWidth: 18, itemStyle: { color: '#3B82F6', borderRadius: [0, 3, 3, 0] }, label: { show: true, position: 'right' as const, formatter: () => formatPredictionNumber(input.person[metal.key], 3), fontSize: 10 } }))
  }
}
const reportGaugeRef = ref<HTMLElement | null>(null)
const reportRadarRef = ref<HTMLElement | null>(null)
const reportBloodRef = ref<HTMLElement | null>(null)
const reportShapRef = ref<HTMLElement | null>(null)
const reportDoseResponseRef = ref<HTMLElement | null>(null)
const reportJointEffectRef = ref<HTMLElement | null>(null)
const cohortCoverageRef = ref<HTMLElement | null>(null)
const cohortRankRef = ref<HTMLElement | null>(null)
const cohortDistributionRef = ref<HTMLElement | null>(null)
const cohortGenderRef = ref<HTMLElement | null>(null)
const cohortAgeRef = ref<HTMLElement | null>(null)
let chartsInstances: echarts.ECharts[] = []
let mounted = false
let active = false
let resizeListening = false
const clearCharts = () => { chartsInstances.forEach(chart => chart.dispose()); chartsInstances = [] }
function initReportCharts() {
  clearCharts()
  if (!hasReport.value || !mounted || !active) return
  let candidates: Array<[HTMLElement | null, unknown]>
  if (isBatchMode.value && cohort.value) candidates = [
    [cohortCoverageRef.value, buildCohortCoverageOption(cohort.value)],
    [cohortRankRef.value, cohortRankOption.value],
    [cohortDistributionRef.value, cohortDistributionOption.value],
    [cohortGenderRef.value, cohortGenderOption.value],
    [cohortAgeRef.value, cohortAgeOption.value]
  ]
  else if (!isBatchMode.value && result.value && request.value) candidates = [
    [reportGaugeRef.value, buildGaugeOption(result.value)],
    [reportRadarRef.value, radarOption.value],
    [reportBloodRef.value, buildBloodInputOption(request.value)],
    [reportShapRef.value, shapOption.value],
    [reportDoseResponseRef.value, doseOption.value],
    [reportJointEffectRef.value, jointOption.value]
  ]
  else return
  for (const [element, option] of candidates) if (element && option) {
    const chart = echarts.init(element); chart.setOption(option as echarts.EChartsOption); chartsInstances.push(chart)
  }
}
const resizeCharts = () => { chartsInstances.forEach(chart => chart.resize()) }
watch([dashboard, lastResult, lastRequest, cohortResult, selectedTarget, isBatchMode], async () => {
  if (!mounted || !active) return
  viewedAt.value = new Date().toLocaleString('zh-CN', { hour12: false })
  await nextTick(); initReportCharts()
}, { deep: true })
async function resumeReport() {
  if (!mounted || active) return
  active = true
  viewedAt.value = new Date().toLocaleString('zh-CN', { hour12: false })
  await nextTick()
  if (!mounted || !active) return
  initReportCharts(); resizeCharts()
  if (!resizeListening) { window.addEventListener('resize', resizeCharts); resizeListening = true }
}
function pauseReport() {
  active = false
  if (resizeListening) { window.removeEventListener('resize', resizeCharts); resizeListening = false }
  clearCharts()
}
onMounted(() => { mounted = true; void resumeReport() })
onActivated(() => { void resumeReport() })
onDeactivated(pauseReport)
onBeforeUnmount(() => { mounted = false; pauseReport() })
</script>

<style lang="scss" scoped>
@use "sass:color";

:deep(.el-icon svg) { max-width: 1em; max-height: 1em; width: 1em; height: 1em; }

$color-primary: #1D4ED8; $color-primary-light: #EFF6FF; $color-bg: #E2E8F0; $text-main: #0F172A; $text-muted: #64748B; $border-color: #E2E8F0;
$color-safe: #10B981; $color-warn: #F59E0B; $color-danger: #EF4444; 

* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', sans-serif; overflow: hidden; }

/* 侧边栏与顶栏 */
.sidebar { width: 280px; background-color: #fff; border-right: 1px solid $border-color; display: flex; flex-direction: column; z-index: 10; flex-shrink: 0; box-shadow: 2px 0 15px rgba(0,0,0,0.03); }
.brand-logo { height: 70px; display: flex; align-items: center; gap: 14px; padding: 0 24px; border-bottom: 1px solid $border-color; svg { width: 30px; height: 30px; color: $color-primary; flex-shrink: 0; } .brand-text { display: flex; flex-direction: column; } .title-en { font-size: 1.1rem; font-weight: 900; color: #1E3A8A; letter-spacing: -0.5px;} .title-cn { font-size: 0.8rem; font-weight: 600; color: #64748B; letter-spacing: 1px; margin-top: 2px;} }
.menu-container { overflow-y: auto; flex: 1; padding: 16px 0; :deep(.custom-el-menu) { border-right: none; .menu-group-title { font-size: 0.85rem; font-weight: 800; color: #94A3B8; padding: 24px 24px 10px 24px; letter-spacing: 1px;} .el-sub-menu__title, .el-menu-item { font-weight: 600; color: #475569; font-size: 1.05rem; margin: 6px 12px; border-radius: 8px; height: 50px; line-height: 50px;} .el-sub-menu__title:hover, .el-menu-item:hover { background-color: #F8FAFC; color: $color-primary; } .el-menu-item.is-active { background-color: $color-primary-light; color: $color-primary; font-weight: 700;} .el-icon { font-size: 1.3rem; margin-right: 12px; color: #64748B; } .is-active > .el-icon { color: $color-primary; } .el-sub-menu .el-menu-item { min-width: auto; padding-left: 55px !important; font-size: 0.95rem; font-weight: 500;} } }

.main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth; }
.ep-header { height: 64px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex !important; justify-content: center; flex-shrink: 0; }
.nav-wrapper { width: 100%; padding: 0 32px; display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; justify-content: space-between !important; align-items: center !important; height: 100%; max-width: none; }
.back-link { display: flex; flex-direction: row; align-items: center; gap: 12px; cursor: pointer; color: $text-main; transition: color 0.2s; &:hover { color: $color-primary; } .back-icon { font-size: 1.2rem; font-weight: bold;} .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px;} .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; } .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-main; } }
.ep-right-zone { display: flex; align-items: center; flex-direction: row; }
.user-profile { display: flex; flex-direction: row; align-items: center; gap: 12px; font-weight: 600; color: $text-main; font-size: 0.95rem; white-space: nowrap; .avatar { width: 32px; height: 32px; border-radius: 50%; background: $color-primary-light; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 0.9rem;} }

/* ==========================================
   报告页面主体
   ========================================== */
.report-view-wrapper { flex: 1 0 auto; padding: 40px 0; display: flex; justify-content: center; align-items: flex-start; animation: fadeIn 0.4s; }
.report-paper { background: #fff; width: 1000px; height: max-content; padding: 80px; position: relative; box-shadow: 0 20px 50px rgba(0,0,0,0.1); border-radius: 2px; }

.report-watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-35deg); font-size: 70px; color: rgba(0,0,0,0.03); font-weight: 900; pointer-events: none; white-space: nowrap; }
.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; .rh-left { display: flex; align-items: center; gap: 12px; } .report-logo-custom { width: 34px; height: 34px; color: $color-primary; margin-bottom: 4px;} h1 { font-size: 26px; color: $text-main; margin: 0 0 10px 0; font-weight: 800; letter-spacing: -1px;} p { font-size: 13px; color: $text-muted; margin: 0; } .risk-seal { border: 3px solid $color-danger; width: 100px; height: 100px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; transform: rotate(15deg); span { font-size: 12px; color: $color-danger; } strong { font-size: 18px; color: $color-danger; } } }
.report-section { margin-top: 40px; .rs-title { font-size: 18px; font-weight: 800; color: $text-main; border-bottom: 2px solid $text-main; padding-bottom: 8px; margin-bottom: 20px; } &.highlight { background: #F8FAFC; padding: 30px; border-radius: 8px; border: 1px dashed $border-color;} .report-desc { font-size: 14px; color: #475569; line-height: 1.6; margin-top: 20px; background: #fff; padding: 12px; border-left: 4px solid $color-primary; border-radius: 4px;} }

/* 花名册表格 */
.worker-table {
  border: 1px solid $border-color; border-radius: 6px; overflow: hidden;
  .wt-header { display: grid; grid-template-columns: 2fr 1.5fr 1fr 1.5fr 1fr; background: #F1F5F9; padding: 12px 16px; font-weight: 700; color: $text-main; font-size: 0.9rem; }
  .wt-row { 
    display: grid; grid-template-columns: 2fr 1.5fr 1fr 1.5fr 1fr; padding: 12px 16px; border-bottom: 1px solid $border-color; font-size: 0.9rem; color: #334155; align-items: center;
    &:last-child { border-bottom: none; }
    &.danger { background: #FEF2F2; .w-score { color: $color-danger; font-weight: 800;} .w-factors { color: $color-danger; font-weight: 600;}}
    &.warn { background: #FFFBEB; .w-score { color: $color-warn; font-weight: 800;} .w-factors { color: $color-warn; font-weight: 600;}}
    .w-name strong { color: $text-main; font-size: 0.95rem; }
  }
}

.chart-box-report { width: 100%; height: 260px; }
.disease-list { display: flex; flex-direction: column; gap: 12px; }
.d-item { display: flex; flex-direction: column; gap: 6px; }
.d-info { display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 600; color: $text-main; .danger{color:$color-danger;} .warn{color:$color-warn;} .safe{color:$color-safe;} }
:deep(.custom-progress .el-progress-bar__outer) { background-color: #F1F5F9 !important; }

/* SHAP 归因图 */
.shap-chart { display: flex; flex-direction: column; gap: 12px; padding: 10px 0; }
.shap-row { display: flex; align-items: center; height: 22px; }
.s-label { width: 85px; text-align: right; padding-right: 12px; font-size: 0.8rem; font-weight: 700; color: $text-main; flex-shrink: 0; white-space: nowrap; z-index: 2;}
.s-track { flex: 1; position: relative; height: 100%; display: flex; align-items: center; }
.zero-line { position: absolute; left: 25%; top: -10px; bottom: -10px; width: 1px; border-left: 2px dashed #9CA3AF; z-index: 0; }
.s-bar { position: absolute; height: 18px; border-radius: 3px; z-index: 1; display: flex; align-items: center;}
.s-bar.pos { left: 25%; background: #EF4444; transform-origin: left; }
.s-bar.neg { right: 75%; background: #10B981; transform-origin: right; }
.s-val { position: absolute; font-size: 0.75rem; font-weight: 700; white-space: nowrap; }
.s-bar.pos .s-val { left: 100%; padding-left: 8px; color: #EF4444; }
.s-bar.neg .s-val { right: 100%; padding-right: 8px; color: #10B981; }

/* 桑基图与DAG图 */
.causal-graph { position: relative; height: 260px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; }
.graph-svg { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; display: block !important; max-height: none !important; max-width: none !important;}
.path-active { stroke: #EF4444; stroke-width: 3; stroke-dasharray: 10; animation: dashMove 1s linear infinite; filter: url(#glowRed); }
.delay-1 { animation-delay: 0.5s; } 
@keyframes dashMove { to { stroke-dashoffset: -20; } }
.c-node { position: absolute; transform: translate(-50%, -50%); padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: 700; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); z-index: 2; border-left: 4px solid; &.source { border-color: #3B82F6; } &.mechanism { border-color: #8B5CF6; } &.target { border-color: #10B981; } &.danger { background: #FEF2F2; border-color: #EF4444; color: #B91C1C; } &.warn { background: #FFFBEB; border-color: #F59E0B; color: #B45309; } }
.pulse-glow { animation: pulseRedShadow 2s infinite; }
@keyframes pulseRedShadow { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

.report-footer { margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end; .sign-system { font-weight: 700; color: #94a3b8; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

@media print { .sidebar, .ep-header, .report-btns { display: none !important; } .main-content { height: auto; overflow: visible; } .report-paper { box-shadow: none; padding: 40px; } }

/* Keep the original paper/report visual system, with true-result and empty states. */
.report-paper { max-width: calc(100% - 64px); overflow: hidden; }
.report-header .model-version { margin-top: 8px; font-size: 11px; overflow-wrap: anywhere; }
.scope-note { font-size: 13px; line-height: 1.8; color: #64748B; }
.empty-report { padding: 28px; text-align: center; background: #F8FAFC; border: 1px dashed #CBD5E1; border-radius: 8px; h2 { font-size: 19px; } p { font-size: 13px; line-height: 1.8; color: #64748B; } }
.report-empty { display: flex; justify-content: center; align-items: center; padding: 24px; color: #94A3B8; font-size: 13px; line-height: 1.8; text-align: center; border: 1px dashed #E2E8F0; border-radius: 6px; min-height: 80px; }
.worker-table .wt-header, .worker-table .wt-row { gap: 10px; }
.worker-table small { display: block; color: #64748B; font-size: 10px; line-height: 1.6; margin-top: 5px; font-weight: normal; }
.worker-table .w-score { color: #2563EB; font-weight: 600; overflow-wrap: anywhere; }
.chart-caption, .outcome-note { font-size: 10px; line-height: 1.7; color: #64748B; }
.chart-caption { margin: 8px 0 0; }
.report-supplement { margin-top: 24px; padding-top: 16px; border-top: 1px dashed #E2E8F0; }
.supplement-title { margin: 0 0 12px; font-size: 13px; color: #64748B; }
.cohort-facts { display: grid; grid-template-columns: 1fr 1fr; gap: 28px 18px; padding-top: 35px; span { display: block; color: #64748B; font-size: 12px; margin-bottom: 10px; } strong { color: #2563EB; font-size: 20px; } }
.cohort-table-wrap { overflow-x: auto; border: 1px solid #E2E8F0; border-radius: 6px; }
.cohort-statistics { width: 100%; border-collapse: collapse; font-size: 11px; th, td { padding: 11px 8px; text-align: right; border-bottom: 1px solid #E2E8F0; white-space: nowrap; } th { background: #EFF6FF; color: #475569; } th:first-child, td:first-child { text-align: left; } small { display: block; margin-top: 5px; color: #64748B; } }
.cohort-target-control { margin-bottom: 16px; color: #64748B; font-size: 12px; display: flex; align-items: center; gap: 10px; }
.cohort-excluded { margin-top: 18px; color: #64748B; font-size: 12px; line-height: 1.8; summary { cursor: pointer; } ul { max-height: 280px; overflow: auto; padding-left: 22px; } }
.outcome-note { display: block; }
.d-info { gap: 10px; .estimate { color: #2563EB; white-space: nowrap; } .withheld { color: #94A3B8; white-space: nowrap; } }
.report-footer { gap: 16px; flex-wrap: wrap; }
.report-btns { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; }
.report-btns :deep(.el-button + .el-button) { margin-left: 0; }
@media print { .system-layout { display: block; height: auto; overflow: visible; background: #fff; } .report-view-wrapper { display: block; padding: 0; } .report-paper { max-width: none; width: 100%; } .report-section, .wt-row { break-inside: avoid; } .report-watermark { position: fixed; } }

</style>
