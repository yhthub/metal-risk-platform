<template>
  <div class="system-layout">
    <Sidebar :default-active="mode === 'batch' ? '3-2' : '3-1'" />
    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToDatainput"><el-icon class="back-icon"><ArrowLeft /></el-icon><span class="back-text">返回工作台</span><span class="divider">|</span><span class="page-title-top">风险量化与预警</span></div>
          <div class="ep-right-zone"><el-tag :type="serviceStatus?.ready ? 'success' : 'info'" effect="plain">{{ serviceStatus?.ready ? '真实模型已就绪' : '模型未就绪' }}</el-tag><div class="user-profile"><div class="avatar">Dr.</div><span>职业卫生评估员</span></div></div>
        </div>
      </header>
      <div class="page-container">
        <div class="pipeline-steps"><div class="step active"><span class="step-num">1</span> 数据接入配置</div><div class="step-line active-line"></div><div class="step active"><span class="step-num">2</span> 多维可视化分析</div><div class="step-line active-line"></div><div class="step active"><span class="step-num">3</span> 风险预警模型</div></div>
        <div class="data-source-banner">
          <div class="ds-left"><span class="ds-label">当前评估对象 / 数据来源：</span><div class="file-chips"><el-tag size="large" effect="plain" round class="custom-tag" :closable="hasSource" @close="handleFileRemove"><el-icon><Document /></el-icon>{{ sourceName }}</el-tag></div></div>
          <div class="ds-right"><el-button link type="primary" @click="goToDatainput">查看特征明细</el-button><el-button type="primary" plain @click="inputDialog = true">核对本次输入</el-button></div>
        </div>
        <div class="model-selector-card">
          <div class="selector-content"><label class="s-label">指定风险评估预训练模型：</label><div class="selector-actions"><el-select v-model="selectedModel" size="large" placeholder="选择模型" class="custom-el-select" style="width: 330px;" filterable><el-option v-for="model in availableModels" :key="model.id" :label="model.type + (model.disabled ? '（原型 · 未接入）' : '')" :value="model.id" :disabled="model.disabled" /></el-select><el-button type="primary" size="large" @click="startReasoning" :loading="isReasoning" :disabled="!serviceStatus?.ready || groupDemoLoading" class="run-btn">{{ isReasoning ? '真实模型计算中…' : mode === 'batch' ? '运行全群体分析' : '运行单人分析' }}</el-button></div></div>
        </div>
        <div class="dashboard-controls">
          <el-button-group><el-button :type="mode === 'individual' ? 'primary' : 'default'" @click="selectMode('individual')">单人分析</el-button><el-button :type="mode === 'batch' ? 'primary' : 'default'" @click="selectMode('batch')">群体分析</el-button></el-button-group>
          <label>目标结局 <el-select v-model="selectedTarget" style="width: 205px"><el-option v-for="target in targetOptions" :key="target.value" :label="target.label" :value="target.value" /></el-select></label>
          <el-button v-if="mode === 'batch' && showIndividualDetail" plain @click="closeIndividualDetail">关闭个人明细 · 返回群体概览</el-button>
          <el-button v-if="mode === 'individual'" plain :loading="demoLoading" @click="fillDemo">一键合成示例</el-button>
          <template v-else>
            <el-button type="primary" plain :loading="groupDemoLoading && groupDemoVariant === 'standard'" :disabled="isReasoning || groupDemoLoading" @click="importGroupDemo('standard')">一键公开数据演示</el-button>
            <el-button type="danger" plain :loading="groupDemoLoading && groupDemoVariant === 'warning'" :disabled="isReasoning || groupDemoLoading" @click="importGroupDemo('warning')">一键预警案例演示</el-button>
          </template>
          <span class="version-note">{{ serviceStatus?.model_version || '尚未连接模型' }}</span>
        </div>
        <p v-if="mode === 'batch'" class="demo-preset-note">两种演示复用同一批 NHANES 公开数据与真实模型：普通演示预设 80 分，预警案例预设 75 分，可在结果中调整。演示阈值不是临床界值，绿色不表示无健康风险。</p>
        <el-alert class="scope-alert" type="info" :closable="false" title="测试版 · 当次指标估计，不是发病概率或临床诊断" :description="PREDICTION_SCOPE_NOTE" show-icon />
        <el-alert v-if="serviceError || predictionError" class="scope-alert" type="error" :closable="false" :title="serviceError || predictionError" show-icon />
        <el-alert v-if="intakeNotice || demoNotice" class="scope-alert" type="info" :closable="false" :title="demoNotice || intakeNotice" />
        <details v-if="mode === 'batch' && batchIntake?.provenance?.id" class="demo-source-details">
          <summary>公开演示来源：{{ batchIntake.provenance.title }} · {{ batchIntake.provenance.rows }}人（查看适用范围）</summary>
          <p>调查周期：{{ batchIntake.provenance.cycle }}。BMI 按同周期参与者编号关联原始身体测量数据；模型结果均在点击后计算。</p>
          <ul><li v-for="note in batchIntake.provenance.limitations" :key="note">{{ note }}</li></ul>
        </details>
        <div class="gemini-thinking-container" v-if="isReasoning || requestLogs.length || reasoningComplete">
          <div class="thinking-header" @click="isThinkingExpanded = !isThinkingExpanded"><div class="t-left"><svg class="sparkle-icon" :class="{ spinning: isReasoning }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2L15 9L22 12L15 15L12 22L9 15L2 12L9 9L12 2Z" fill="currentColor" /></svg><span class="t-text">{{ isReasoning ? '正在请求真实模型计算…' : '查看本次真实请求记录' }}</span></div><el-icon class="chevron-icon" :class="{ rotated: isThinkingExpanded }"><ArrowDown /></el-icon></div>
          <div class="thinking-body" v-show="isThinkingExpanded"><ul class="think-steps"><li v-for="(entry, index) in requestLogs" :key="index" class="t-step active">{{ entry }}</li></ul></div>
        </div>
        <section v-if="mode === 'batch' && cohortResult" class="cohort-results">
          <RiskCohortDashboard :result="cohortResult" :target="selectedTarget" :target-options="targetOptions" :warning-threshold="cohortWarningThreshold" @update:warning-threshold="cohortWarningThreshold = $event" @select-target="selectedTarget = $event" @inspect-person="inspectCohortPerson" />
          <div class="bottom-action-bar cohort-action-bar"><el-button type="success" plain :icon="Download" @click="goToReportPage">群体分析报告</el-button><el-button @click="downloadCompositeWarning">下载综合预警排序</el-button><el-button @click="downloadCohortSummary">下载全群汇总</el-button><el-button @click="downloadCohortRanking">下载所选结局排序</el-button><el-button @click="downloadAllCohortRecords">下载全部对象结果</el-button></div>
        </section>
        <div class="results-dashboard" v-if="(mode === 'individual' || showIndividualDetail) && reasoningComplete && !isReasoning">
          <el-alert v-if="mode === 'batch'" class="scope-alert" type="warning" :closable="false" :title="'个人明细：以下所有曲线和贡献图仅属于' + selectedPersonName + '，不能替代上方全群体统计。'" />
          <div class="alert-conclusion-banner research-banner"><div class="a-icon"><el-icon><WarningFilled /></el-icon></div><div class="a-content"><h4>本次真实模型结果：<span>{{ charts?.label_zh }} · {{ selectedPersonName }}</span></h4><p>共 {{ dashboard!.prediction.results.length }} 项结局，{{ availableCount }} 项提供探索性估计，其余保留未出值原因。图表仅展示本次可计算的指标、输入响应和局部贡献，不代表因果效应、安全阈值或职业病风险等级。</p></div></div>
          <div class="analysis-section-heading"><div><span class="section-eyebrow">INDIVIDUAL INSIGHTS</span><h3>单人健康指标分析</h3></div><span class="live-result-badge"><i></i>本次模型计算</span></div>
          <p v-if="!rankOption" class="calculation-notice">所选结局暂不出值：{{ selectedTargetReason }}。可在下方切换其他结局。</p>
          <details v-if="unavailableChartNotes.length && rankOption" class="calculation-details"><summary>部分分析未展示 · 查看原因</summary><p v-for="note in unavailableChartNotes" :key="note">{{ note }}</p></details>
          <div class="results-grid individual-grid" data-computed-diagrams>
            <div v-if="rankOption" class="result-card col-span-4 estimate-card">
              <div class="r-head"><div class="title-group"><h4>当前对象指标估计 <el-tag size="small" type="primary" effect="plain" round>{{ charts?.label_zh }}</el-tag></h4><span class="sub-desc">根据本次实际输入计算，保留指标原单位；不是患病概率。</span></div></div>
              <div class="chart-box estimate-chart" ref="warningRankRef"></div>
            </div>
            <div class="result-card coverage-card" :class="rankOption ? 'col-span-2' : 'col-span-6'">
              <div class="r-head"><div class="title-group"><h4>结局估计可用性</h4><span class="sub-desc">已提供数值 / 全部结局，不是健康风险比例。</span></div></div>
              <div class="chart-box coverage-chart" ref="dashGaugeRef"></div>
            </div>
            <div v-if="importanceOption" class="result-card col-span-3">
              <div class="r-head"><div class="title-group"><h4>局部特征贡献份额</h4><span class="sub-desc">绝对 SHAP 份额，含协变量和缺失分支；不是 PIP 或因果重要性。</span></div></div>
              <div class="chart-box" ref="toxinWeightRef"></div>
            </div>
            <div v-if="doseOption" class="result-card col-span-3">
              <div class="r-head"><div class="title-group"><h4>全血铅输入敏感性</h4><span class="sub-desc">仅改变铅、其余输入固定的实际模型响应；非因果剂量反应。</span></div></div>
              <div class="chart-box" ref="doseResponseRef"></div>
            </div>
            <div v-if="jointOption" class="result-card col-span-3">
              <div class="r-head"><div class="title-group"><h4>双金属联合输入响应</h4><span class="sub-desc">全血铅 × 全血镉的实际模型网格；颜色仅表示估计值大小，不证明协同致病。</span></div></div>
              <div class="chart-box joint-chart" ref="jointEffectRef"></div>
            </div>
            <div v-if="shapOption" class="result-card col-span-3">
              <div class="r-head"><div class="title-group"><h4>本次对象的局部贡献拆解</h4><span class="sub-desc">带符号 SHAP · {{ charts?.explanation.scale_label || '未取得尺度' }}；不解释为致病或保护作用。</span></div></div>
              <div class="chart-box contribution-chart" ref="shapChartRef" :style="{ height: Math.max(320, shapItems.length * 30 + 76) + 'px' }"></div>
              <p class="chart-note">基准 {{ formatPredictionNumber(charts?.explanation.base_value, 3) }} + 全部贡献 ≈ 原生输出 {{ formatPredictionNumber(charts?.explanation.raw_prediction, 3) }}。{{ charts?.explanation.note }}</p>
            </div>
            <div class="result-card col-span-6 outcomes-card">
              <div class="r-head"><div class="title-group"><h4>多结局指标估计 <span class="heading-count">{{ availableCount }} / {{ dashboard!.prediction.results.length }} 项可估计</span></h4><span class="sub-desc">点击切换目标，联动更新上方图表；各指标使用独立单位，不合成单人风险分数。</span></div></div>
              <div class="actual-outcomes"><button class="outcome-item" :class="{ chosen: row.target === selectedTarget, withheld: !predictionHasValue(row) }" v-for="(row, index) in dashboard!.prediction.results" :key="row.target" @click="selectedTarget = row.target" :style="{ '--outcome-accent': outcomeAccents[index % outcomeAccents.length] }"><div class="outcome-top"><span class="outcome-name">{{ row.label_zh }}</span><span class="outcome-status">{{ predictionHasValue(row) ? '已估计' : '暂不出值' }}</span></div><strong class="outcome-value">{{ predictionHasValue(row) ? formatPredictionNumber(row.prediction) : '—' }}<small v-if="predictionHasValue(row)">{{ row.unit }}</small></strong><small class="outcome-note">{{ predictionHasValue(row) ? '测试集MAE ' + formatPredictionNumber(row.test_metrics.MAE) + ' ' + row.unit : predictionReason(row) }}</small></button></div>
            </div>
          </div>
          <el-alert v-if="dashboard!.prediction.warnings.length" type="info" :closable="false" :title="dashboard!.prediction.warnings.join('；')" />
          <p class="chart-note">{{ INTERVAL_NOTE }}</p>
          <div class="bottom-action-bar"><el-button type="success" size="large" plain :icon="Download" @click="goToReportPage" style="margin-right: 12px;">下载风险评估报告（本次真实结果）</el-button><el-button type="primary" size="large" class="final-run-btn" @click="goToPlan">查看干预策略原型（非本模型建议）➔</el-button></div>
        </div>
        <el-empty v-if="!isReasoning && !requestLogs.length && !cohortResult && !dashboard" description="请核对输入后运行：群体将完成整份文件全部对象预测，默认展示全群统计，而非逐人翻页。" />
      </div>
      <footer class="model-meta-footer"><div class="footer-container"><h4>预训练模型字典与说明 (Model Meta Information)</h4><div class="meta-grid"><div class="meta-item" v-for="model in availableModels" :key="model.id"><strong>{{ model.type }} <small>{{ model.disabled ? '原型 · 未接入' : '真实已训练' }}</small></strong><p>{{ model.disabled ? '保留独立功能原型，未在本页执行；不能作为本次结果依据。' : model.desc }}</p></div></div></div></footer>
    </main>
    <el-dialog v-model="inputDialog" title="核对本次模型输入" width="850px" destroy-on-close>
      <p class="dialog-note">{{ mode === 'batch' ? '批次必须在数据工作台导入含BMI的真实NHANES格式；J周期原始列的铅单位固定为μg/dL，镉和总汞为μg/L（等价ng/mL）。在此核对全血样本、原始单位与分析物，不按列名替你确认。' : '年龄、性别、BMI和三种全血金属为必填。未知保持空，数值0仅用于实际测得为0的情况。' }}</p>
      <div v-if="mode === 'individual'" class="input-grid"><label>对象编号<el-input v-model="draft.person.id" placeholder="可选，避免姓名" /></label><label>年龄 / 岁<el-input v-model.number="draft.person.age" type="number" placeholder="18–80岁整数" /></label><label>生理性别<el-select v-model="draft.person.gender" placeholder="未确认" clearable @clear="draft.person.gender = null" @change="draft.person.gender_confirmed = false"><el-option label="女性" value="female" /><el-option label="男性" value="male" /></el-select></label><label>BMI / kg·m⁻²<el-input v-model.number="draft.person.bmi" type="number" /></label></div>
      <el-checkbox v-if="mode === 'individual'" v-model="draft.person.gender_confirmed" :disabled="!draft.person.gender">已明确核对性别，未沿用未经确认的默认值</el-checkbox>
      <div class="dialog-metals"><section v-for="metal in METAL_FIELDS" :key="metal.key"><h4>{{ metal.label }}</h4><label v-if="mode === 'individual'">实测浓度<el-input v-model.number="draft.person[metal.key]" type="number" placeholder="缺测留空" /></label><label>样本<el-select v-model="draft.measurements[metal.key].sample" @change="draft.measurements[metal.key].confirmed = false"><el-option label="未确认" value="" /><el-option label="全血" value="whole_blood" /><el-option label="血清（不适用）" value="serum" /><el-option label="尿样（不适用）" value="urine" /><el-option label="随机尿（不适用）" value="random_urine" /></el-select></label><label>原始单位<el-select v-model="draft.measurements[metal.key].unit" @change="draft.measurements[metal.key].confirmed = false"><el-option label="未确认" value="" /><el-option v-for="unit in unitsFor(metal.key)" :key="unit" :value="unit" :label="unit.replace('ug', 'μg')" /></el-select></label><label>分析物<el-select v-model="draft.measurements[metal.key].analyte" @change="draft.measurements[metal.key].confirmed = false"><el-option label="未确认" value="" /><el-option :label="metal.key === 'hg' ? '总汞（非甲基汞/无机汞）' : metal.key === 'pb' ? '铅' : '镉'" :value="metal.analyte" /><el-option label="其他（不适用）" value="other" /></el-select></label><el-checkbox v-model="draft.measurements[metal.key].confirmed">已核对样本、单位和分析物</el-checkbox></section></div>
      <details v-if="mode === 'individual'" class="dialog-optional"><summary>可选个人因素（NHANES训练口径；不匹配则未知）</summary><div class="input-grid"><label>教育程度<el-select v-model="draft.covariates.education" placeholder="未知" clearable @clear="draft.covariates.education = null"><el-option v-for="item in EDUCATION_OPTIONS" :key="item.value" :label="item.label" :value="item.value" /></el-select></label><label>婚姻<el-select v-model="draft.covariates.marital" placeholder="未知" clearable @clear="draft.covariates.marital = null"><el-option v-for="item in MARITAL_OPTIONS" :key="item.value" :label="item.label" :value="item.value" /></el-select></label><label>终生100支口径吸烟<el-select v-model="draft.covariates.smoking" placeholder="未知" clearable @clear="draft.covariates.smoking = null"><el-option v-for="item in SMOKING_OPTIONS" :key="item.value" :label="item.label" :value="item.value" /></el-select></label><label>过去一年饮酒<el-select v-model="draft.covariates.alcohol_any_past_year" placeholder="未知" clearable @clear="draft.covariates.alcohol_any_past_year = null"><el-option label="是" :value="true" /><el-option label="否" :value="false" /></el-select></label></div></details>
      <el-alert v-if="inputErrors.length" type="error" :closable="false" :title="inputErrors.join('；')" />
      <p class="dialog-note">仅接受18–80岁成人，80为NHANES顶码。规范输入为铅 μg/dL、镉和总汞 μg/L；仅同全血明确单位可由后端记录换算，不改变原始录入值。</p>
      <template #footer><el-button @click="goToDatainput">返回数据工作台</el-button><el-button type="primary" @click="confirmInputs">完成核对</el-button></template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onActivated, onBeforeUnmount, onDeactivated, onMounted, ref, watch } from 'vue'
import { ArrowLeft, ArrowDown, Document, WarningFilled, Download } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import { EDUCATION_OPTIONS, INTERVAL_NOTE, MARITAL_OPTIONS, METAL_FIELDS, PREDICTION_SCOPE_NOTE, SMOKING_OPTIONS, batchPredictionCsv, buildPredictionRequest, clonePrediction, createPredictionDraft, downloadPrediction, formatPredictionNumber, measurementErrors, predictionHasValue, predictionReason } from '~/utils/riskPrediction'
import { availableShapItems, buildDoseOption, buildGaugeOption, buildImportanceOption, buildJointOption, buildRankOption, buildShapOption, chartReason, selectedOutcome } from '~/utils/riskDashboard'
import { RISK_CHART_COLORS } from '~/utils/riskChartTheme'
import { cohortRankingCsv, cohortResponseError, cohortSummaryCsv } from '~/utils/riskCohort'
import { buildCohortWarning, warningRankingCsv } from '~/utils/cohortWarning'
import type { MetalKey, PredictionRequest, PredictionStatus } from '~/utils/riskPrediction'
import type { DashboardResponse } from '~/utils/riskDashboard'

const router = useRouter()
const route = useRoute()
const api = useApi()
const { draft, intake, batchIntake, lastRequest, lastResult, dashboard, batchResult, cohortResult, cohortWarningThreshold, cohortWarningDemoPreset, selectedTarget, selectedRow, lastDashboardRequest, invalidate, setResult } = usePredictionState()
const showIndividualDetail = ref(false)
function modeFromQuery(value: unknown): 'individual' | 'batch' {
  return value === 'batch' ? 'batch' : 'individual'
}
const mode = ref<'individual' | 'batch'>(modeFromQuery(route.query.mode))
const selectMode = async (next: 'individual' | 'batch') => {
  await router.push({ path: '/risk', query: { ...route.query, mode: next } })
}
const availableModels = ref([
  { id: 'm1', type: 'XGBoost', desc: '复合金属-多靶器官综合风险评估模型，融合多组学与环境监测评估全局概率。' },
  { id: 'm2', type: 'DNN', desc: '铅/砷协同-中枢神经疾病网络，专攻重金属突破血脑屏障引起的神经退行性病变。' },
  { id: 'm3', type: 'LightGBM', desc: '镉靶向-慢性肾病与尿毒症预警模型，基于尿镉特征精准预测肾小管及肾小球损伤。' },
  { id: 'm4', type: 'G-computation', desc: '边际因果效应推断算法，用于模拟如果提升群体暴露水平，谁将受到最大的健康损害。' },
  { id: 'm5', type: 'BKMR', desc: '贝叶斯核机器回归，擅长捕捉重金属混合暴露在复杂交互下的非线性与协同效应。' },
  { id: 'm6', type: 'Random Forest', desc: '随机森林集成模型，通过多棵决策树投票实现稳健的多靶器官风险分层与特征排序。' },
  { id: 'm7', type: 'CatBoost', desc: '梯度提升决策树，内置有序目标编码，适合处理工种、学历等类别型协变量。' },
  { id: 'm8', type: 'Elastic Net', desc: '弹性网络正则化回归，兼顾 L1 稀疏选择与 L2 共线性收缩，适合高维暴露特征筛选。' },
  { id: 'm9', type: 'Cox-PH', desc: 'Cox 比例风险生存模型，量化暴露工龄与职业病发病时间的半参数关联。' },
  { id: 'm10', type: 'Weibull-AFT', desc: 'Weibull 加速失效时间模型，拟合暴露累积剂量与靶器官损伤发生的时序关系。' },
  { id: 'm11', type: 'Bayesian Network', desc: '贝叶斯有向图模型，编码金属→分子机制→疾病的条件概率结构，支持因果推理。' },
  { id: 'm12', type: 'GAM (Generalized Additive)', desc: '广义可加模型，以非参数样条拟合各金属的非线性剂量-反应曲线。' },
  { id: 'm13', type: 'SHAP-Integrated MLP', desc: '多层感知机+SHAP归因一体化，端到端输出个体风险评分与全局特征贡献度。' },
  { id: 'm14', type: 'QG-Comp', desc: '分位型g-计算，在分位数层面估计复合暴露干预的因果效应，适用偏态分布数据。' },
  { id: 'm15', type: 'TMLE', desc: '目标最大似然估计，双稳健因果推断算法，兼顾模型误设与稀疏暴露数据。' },
  { id: 'm16', type: 'DeepSurv', desc: '深度生存网络，以深度学习拟合非线性协变量效应，输出个体化风险轨迹。' },
  { id: 'm17', type: 'AFT-NN', desc: '加速失效时间神经网络，融合生存分析与深度学习预测多金属暴露下的器官衰竭时间。' },
  { id: 'm18', type: 'BKMR-CS', desc: '贝叶斯核机器回归-分层扩展版，支持暴露组内按工种或年龄分层的异质性效应估计。' },
  { id: 'm19', type: 'SuperLearner', desc: '超级学习器集成框架，交叉验证自动加权组合多基学习器，最小化预测风险。' },
  { id: 'm20', type: 'Causal Forest', desc: '因果森林异质性处理效应模型，识别对干预最敏感的亚群体，指导精准干预分配。' }
].map(model => ({ ...model, disabled: model.id !== 'm1', type: model.id === 'm1' ? 'XGBoost / CatBoost（NHANES实训模型组）' : model.type, desc: model.id === 'm1' ? '基于NHANES公开数据的已训练CPU模型组，12项当次指标估计；部分结局因验证不足默认不出值。' : model.desc })))
const selectedModel = ref('m1')
const serviceStatus = ref<PredictionStatus | null>(null)
const serviceError = ref('')
const statusLoading = ref(false)
const inputDialog = ref(false)
const inputErrors = ref<string[]>([])
const predictionError = ref('')
const demoLoading = ref(false)
const groupDemoLoading = ref(false)
const groupDemoVariant = ref<'standard' | 'warning'>('standard')
const demoNotice = ref('')
const intakeNotice = ref('')
const isReasoning = ref(false)
const isThinkingExpanded = ref(true)
const requestLogs = ref<string[]>([])
const reasoningComplete = computed(() => !!dashboard.value)
const charts = computed(() => dashboard.value?.charts)
const availableCount = computed(() => dashboard.value?.prediction.results.filter(predictionHasValue).length || 0)
const selectedPersonName = computed(() => dashboard.value?.prediction.person_id || draft.value.person.id || '本次对象')
const hasSource = computed(() => mode.value === 'batch' ? !!batchIntake.value?.file_id : Object.values(draft.value.person).some(value => value !== null && value !== '' && value !== false))
const sourceName = computed(() => mode.value === 'batch' ? batchIntake.value?.filename || batchIntake.value?.file_id || '尚未导入真实群体文件' : hasSource.value ? '单人：' + (draft.value.person.id || '本次录入对象') : '尚未载入单人数据')
const targetOptions = [
  { value: 'sbp', label: '收缩压 / mmHg' }, { value: 'dbp', label: '舒张压 / mmHg' },
  { value: 'serum_creatinine_mg_dl', label: '血清肌酐 / mg/dL' }, { value: 'bun_mg_dl', label: '血尿素氮 / mg/dL' },
  { value: 'uric_acid_mg_dl', label: '尿酸 / mg/dL' }, { value: 'uacr_mg_g', label: '尿白蛋白肌酐比 / mg/g' },
  { value: 'hba1c_percent', label: '糖化血红蛋白 / %' }, { value: 'total_cholesterol_mg_dl', label: '总胆固醇 / mg/dL' },
  { value: 'hdl_cholesterol_mg_dl', label: '高密度脂蛋白胆固醇 / mg/dL' }, { value: 'alt_u_l', label: 'ALT / U/L' },
  { value: 'ast_u_l', label: 'AST / U/L' }, { value: 'ggt_u_l', label: 'GGT / U/L' }
]
const outcomeAccents = RISK_CHART_COLORS
const rankOption = computed(() => dashboard.value ? buildRankOption(dashboard.value.prediction, selectedTarget.value) : null)
const importanceOption = computed(() => charts.value ? buildImportanceOption(charts.value) : null)
const doseOption = computed(() => charts.value ? buildDoseOption(charts.value) : null)
const jointOption = computed(() => charts.value ? buildJointOption(charts.value) : null)
const shapItems = computed(() => availableShapItems(charts.value))
const shapOption = computed(() => charts.value ? buildShapOption(charts.value) : null)
const unavailableChartNotes = computed(() => [
  !shapOption.value ? '局部特征贡献：' + chartReason(charts.value?.explanation) : '',
  !doseOption.value ? '全血铅输入响应：' + chartReason(charts.value?.dose_response) : '',
  !jointOption.value ? '双金属联合响应：' + chartReason(charts.value?.joint_response) : ''
].filter(Boolean))
const selectedTargetReason = computed(() => { const outcome = selectedOutcome(dashboard.value?.prediction, selectedTarget.value); return outcome && !predictionHasValue(outcome) ? predictionReason(outcome) : chartReason(charts.value) })
const unitsFor = (key: MetalKey) => [...new Set(['ug/L', 'ug/dL', 'ng/mL', draft.value.measurements[key].unit].filter(Boolean))]
const goToDatainput = async () => { await router.push('/datainput') }
const goToPlan = async () => { await router.push('/plan') }
const goToReportPage = async () => { if (dashboard.value || cohortResult.value) await router.push({ path: '/risk/report', query: { mode: mode.value } }) }
const downloadCohortCsv = (content: string, label: string) => {
  if (typeof document === 'undefined') return
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }))
  const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'NHANES_cohort_' + label + '_' + new Date().toISOString().slice(0, 10) + '.csv'; anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
const downloadCohortSummary = () => { if (cohortResult.value) downloadCohortCsv(cohortSummaryCsv(cohortResult.value), 'summary') }
const downloadCohortRanking = () => { if (cohortResult.value) downloadCohortCsv(cohortRankingCsv(cohortResult.value, selectedTarget.value), selectedTarget.value + '_ranking') }
const downloadCompositeWarning = () => { if (cohortResult.value) downloadCohortCsv(warningRankingCsv(buildCohortWarning(cohortResult.value, cohortWarningThreshold.value)), 'composite_warning') }
const downloadAllCohortRecords = () => { if (cohortResult.value) downloadCohortCsv(batchPredictionCsv(cohortResult.value), 'all_records') }
const handleFileRemove = () => { epoch++; if (mode.value === 'individual') draft.value = createPredictionDraft(); intake.value = null; batchIntake.value = null; invalidate(); clearCharts(); requestLogs.value = []; isReasoning.value = false }
const confirmInputs = () => {
  inputErrors.value = mode.value === 'batch' ? measurementErrors(draft.value.measurements) : buildPredictionRequest(draft.value).errors
  if (!inputErrors.value.length) inputDialog.value = false
}

const warningRankRef = ref<HTMLElement | null>(null)
const dashGaugeRef = ref<HTMLElement | null>(null)
const toxinWeightRef = ref<HTMLElement | null>(null)
const doseResponseRef = ref<HTMLElement | null>(null)
const jointEffectRef = ref<HTMLElement | null>(null)
const shapChartRef = ref<HTMLElement | null>(null)
let chartInstances: echarts.ECharts[] = []
let resizeObserver: ResizeObserver | null = null
let active = false
let epoch = 0
let suppressSelection = false
let applyingGroupDemo = false
const clearCharts = () => { resizeObserver?.disconnect(); resizeObserver = null; chartInstances.forEach(chart => chart.dispose()); chartInstances = [] }
const resizeCharts = () => chartInstances.forEach(chart => chart.resize())
async function initDashboardCharts() {
  await nextTick()
  if (!active || !dashboard.value || isReasoning.value) return
  clearCharts()
  const options = [
    [warningRankRef.value, rankOption.value], [dashGaugeRef.value, buildGaugeOption(dashboard.value.prediction)],
    [toxinWeightRef.value, importanceOption.value], [doseResponseRef.value, doseOption.value], [jointEffectRef.value, jointOption.value], [shapChartRef.value, shapOption.value]
  ] as const
  if (typeof ResizeObserver !== 'undefined') resizeObserver = new ResizeObserver(resizeCharts)
  for (const [element, option] of options) {
    if (!element || !option) continue
    const chart = echarts.init(element, undefined, { devicePixelRatio: Math.min(window.devicePixelRatio || 1, 2) })
    chart.setOption(option)
    chartInstances.push(chart)
    resizeObserver?.observe(element)
  }
}
function clearCurrentExplanation() {
  dashboard.value = null
  lastResult.value = null
  lastRequest.value = null
  lastDashboardRequest.value = null
  clearCharts()
}
watch(draft, () => {
  epoch++; invalidate(); clearCharts(); showIndividualDetail.value = false; isReasoning.value = false; requestLogs.value = []; inputErrors.value = []; predictionError.value = ''; demoNotice.value = ''
}, { deep: true, flush: 'sync' })
watch(mode, () => {
  epoch++; invalidate(); clearCharts(); showIndividualDetail.value = false; isReasoning.value = false; requestLogs.value = []; predictionError.value = ''; inputErrors.value = []
  for (const metal of METAL_FIELDS) draft.value.measurements[metal.key].confirmed = false
}, { flush: 'sync' })
watch(() => route.query.mode, value => { if (route.path === '/risk') mode.value = modeFromQuery(value) }, { flush: 'sync' })
watch(batchIntake, () => {
  resetStaleGroupDemoThreshold()
  if (mode.value !== 'batch' || applyingGroupDemo) return
  epoch++; invalidate(); clearCharts(); showIndividualDetail.value = false; isReasoning.value = false; requestLogs.value = []
  for (const metal of METAL_FIELDS) draft.value.measurements[metal.key].confirmed = false
}, { deep: true, flush: 'sync' })
watch([selectedTarget, selectedRow], () => {
  if (!active || suppressSelection) return
  if (mode.value === 'batch' && !showIndividualDetail.value) return
  const input = mode.value === 'batch'
    ? batchResult.value?.records.find(record => record.row_number === selectedRow.value)?.input
    : lastDashboardRequest.value?.input || lastRequest.value
  if (input) refreshSelectedDashboard(clonePrediction(input))
})
watch(dashboard, () => { if (dashboard.value) initDashboardCharts(); else clearCharts() })
async function refreshStatus() {
  if (statusLoading.value) return
  statusLoading.value = true; serviceError.value = ''
  const response: any = await api.getPredictionStatus()
  if (response.success) serviceStatus.value = response.data
  else { serviceStatus.value = null; serviceError.value = response.error || '无法连接本地模型服务。' }
  statusLoading.value = false
}
async function fillDemo() {
  if (mode.value !== 'individual') return
  demoLoading.value = true
  const current = epoch
  const response: any = await api.getPredictionDemo()
  if (current !== epoch || !active) { demoLoading.value = false; return }
  if (response.success && response.data?.payload) {
    batchResult.value = null; selectedRow.value = null; batchIntake.value = null
    draft.value = clonePrediction(response.data.payload)
    demoNotice.value = response.data.notice || '显式合成填表示例；运行后由真实模型计算。'
    intake.value = null
  } else predictionError.value = response.error || '未获取到合成示例，不回退为假数据。'
  demoLoading.value = false
}
// RISK_GROUP_DEMO_START
function resetStaleGroupDemoThreshold() {
  const preset = cohortWarningDemoPreset.value
  if (!preset || applyingGroupDemo || batchIntake.value?.file_id === preset.file_id) return
  if (cohortWarningThreshold.value === preset.threshold) cohortWarningThreshold.value = 80
  cohortWarningDemoPreset.value = null
}
async function importGroupDemo(variant: 'standard' | 'warning' = 'standard') {
  if (groupDemoLoading.value || isReasoning.value || mode.value !== 'batch') return
  groupDemoLoading.value = true
  groupDemoVariant.value = variant
  try {
    if (!active || !serviceStatus.value?.ready) { predictionError.value = '模型尚未就绪，未替换当前数据，也未执行群体演示。'; return }
    const confirmationEpoch = epoch
    if (batchIntake.value?.file_id || batchResult.value) {
      try {
        await ElMessageBox.confirm('将切换到已核验测量口径的真实公开 NHANES 演示数据，并替换当前页面的群体记录与图表。原上传文件不会删除。是否继续？', '替换当前群体数据', { confirmButtonText: '载入公开演示并计算', cancelButtonText: '保留当前数据', type: 'warning' })
      } catch { return }
    }
    if (!active || mode.value !== 'batch' || confirmationEpoch !== epoch) return
    const current = ++epoch
    predictionError.value = ''
    const response: any = await api.importPredictionBatchDemo()
    if (current !== epoch || !active || mode.value !== 'batch') return
    if (!response.success || !/^FILE-[0-9a-f]{8}$/.test(response.data?.import_result?.file_id || '')
      || response.data?.provenance?.id !== 'nhanes_2017_2018_risk_demo_20' || response.data?.provenance?.rows !== 20
      || !response.data?.measurements || METAL_FIELDS.some(metal => !response.data.measurements[metal.key])) {
      predictionError.value = response.error || '公开演示数据导入失败；保留原群体数据，不显示模拟结果。'
      return
    }
    const verifiedMeasurements = clonePrediction(response.data.measurements)
    const errors = measurementErrors(verifiedMeasurements)
    if (errors.length) { predictionError.value = '演示测量口径未通过校验，未替换当前数据：' + errors.join('；'); return }
    applyingGroupDemo = true
    suppressSelection = true
    batchIntake.value = { file_id: response.data.import_result.file_id, filename: response.data.import_result.filename, provenance: clonePrediction(response.data.provenance || {}) }
    draft.value.measurements = verifiedMeasurements
    inputErrors.value = []; inputDialog.value = false; intakeNotice.value = ''
    demoNotice.value = variant === 'warning'
      ? '预警案例演示：复用同一批真实公开 NHANES 数据与真实模型，初始综合阈值设为 75 分，用于体验红色预警界面，不是临床高危判定。只有模型计算成功才显示结果；你仍可调整阈值。'
      : '已载入真实公开 NHANES 演示数据，初始综合阈值设为 80 分；样本与单位来自已核验的演示文件，只有真实模型计算成功后才展示图表。不会把这些确认用于其他上传文件。'
    const stagedEpoch = epoch
    await nextTick()
    applyingGroupDemo = false
    suppressSelection = false
    if (!active || mode.value !== 'batch' || stagedEpoch !== epoch) return
    cohortWarningThreshold.value = variant === 'warning' ? 75 : 80
    cohortWarningDemoPreset.value = variant === 'warning' ? { file_id: batchIntake.value!.file_id, threshold: 75 } : null
    await runBatch()
  } catch (error: any) {
    predictionError.value = error?.message || '公开数据演示未完成；没有生成模拟模型结果。'
  } finally {
    applyingGroupDemo = false
    suppressSelection = false
    groupDemoLoading.value = false
  }
}
// RISK_GROUP_DEMO_END
async function refreshSelectedDashboard(input: PredictionRequest) {
  const target = selectedTarget.value
  const current = ++epoch
  clearCurrentExplanation()
  predictionError.value = ''; isReasoning.value = true; isThinkingExpanded.value = true
  lastDashboardRequest.value = { input: clonePrediction(input), target }
  requestLogs.value = ['已核对本次对象与测量口径：' + (input.person.id || '未提供编号'), '已发送真实模型请求：' + (targetOptions.find(item => item.value === target)?.label || target)]
  const response: any = await api.getPredictionDashboard({ input, target })
  if (current !== epoch || !active || target !== selectedTarget.value) return
  isReasoning.value = false
  if (!response.success || response.data?.charts?.target !== target || !Array.isArray(response.data?.prediction?.results)) {
    predictionError.value = response.error || '未得到符合契约的真实模型响应；没有生成模拟图表。'
    requestLogs.value.push('请求未完成：' + predictionError.value)
    return
  }
  dashboard.value = response.data as DashboardResponse
  setResult(input, dashboard.value.prediction)
  requestLogs.value.push('模型返回12项真实结局，' + dashboard.value.prediction.results.filter(predictionHasValue).length + '项提供探索性估计。')
  requestLogs.value.push('局部解释：' + (dashboard.value.charts.explanation.status === 'AVAILABLE' ? '已由原生模型计算 SHAP' : chartReason(dashboard.value.charts.explanation)))
  requestLogs.value.push('敏感性曲线与双金属网格：' + (dashboard.value.charts.dose_response.status === 'AVAILABLE' && dashboard.value.charts.joint_response.status === 'AVAILABLE' ? '真实输入扰动计算完成' : '部分图表不足，保留原因'))
  await initDashboardCharts()
}
async function startReasoning() {
  if (isReasoning.value || groupDemoLoading.value) return
  predictionError.value = ''
  if (!serviceStatus.value?.ready) { predictionError.value = '模型尚未就绪，请检查本地后端。'; return }
  if (selectedModel.value !== 'm1') { predictionError.value = '所选功能仅为原型，不能执行假计算。'; return }
  if (mode.value === 'batch') { await runBatch(); return }
  const { payload, errors } = buildPredictionRequest(draft.value)
  inputErrors.value = errors
  if (errors.length) { inputDialog.value = true; return }
  suppressSelection = true
  batchResult.value = null; selectedRow.value = null
  await nextTick()
  suppressSelection = false
  await refreshSelectedDashboard(payload)
}
// RISK_COHORT_RUN_START
async function runBatch() {
  if (isReasoning.value) return
  inputErrors.value = measurementErrors(draft.value.measurements)
  predictionError.value = ''
  if (!batchIntake.value?.file_id) { predictionError.value = '请先在数据工作台导入含真实BMI、年龄、性别和三种全血金属的NHANES文件；缺少BMI不能补造。'; return }
  if (inputErrors.value.length) { inputDialog.value = true; return }
  if (!serviceStatus.value?.ready) { predictionError.value = '模型尚未就绪。'; return }
  const current = ++epoch
  const fileId = batchIntake.value.file_id
  suppressSelection = true
  invalidate(); clearCharts(); showIndividualDetail.value = false; isReasoning.value = true; isThinkingExpanded.value = true
  requestLogs.value = ['已核对全文件样本、单位和分析物；正在一次完成全部对象的12项真实指标估计，非分页推理。']
  const response: any = await api.predictCohort({ file_id: fileId, measurements: clonePrediction(draft.value.measurements) })
  if (current !== epoch || !active || mode.value !== 'batch' || batchIntake.value?.file_id !== fileId) { suppressSelection = false; return }
  const completenessError = response.success ? cohortResponseError(response.data) : null
  if (!response.success || completenessError || response.data?.file_id !== fileId) {
    isReasoning.value = false; suppressSelection = false
    predictionError.value = response.error || completenessError || '返回结果不属于当前全群文件，未显示群体结论。'
    requestLogs.value.push('整份文件分析未完成：' + predictionError.value)
    return
  }
  batchResult.value = response.data
  cohortResult.value = response.data
  selectedRow.value = null
  isReasoning.value = false
  requestLogs.value.push('整份文件 ' + response.data.total_records + ' 条已全部处理；有效输入 ' + response.data.processed_records + ' 人，跳过 ' + response.data.skipped_records + ' 人（保留原因）。')
  requestLogs.value.push('默认展示全群综合相对预警、各结局分布与统计；没有自动选取个人代表群体。')
  await nextTick()
  suppressSelection = false
}
// RISK_COHORT_RUN_END
async function inspectCohortPerson(rowNumber: number) {
  const record = cohortResult.value?.records.find(item => item.row_number === rowNumber)
  if (!record?.input || isReasoning.value) return
  const fileId = cohortResult.value!.file_id
  suppressSelection = true
  showIndividualDetail.value = true
  selectedRow.value = rowNumber
  await nextTick()
  suppressSelection = false
  if (!active || mode.value !== 'batch' || !showIndividualDetail.value || cohortResult.value?.file_id !== fileId || selectedRow.value !== rowNumber) return
  await refreshSelectedDashboard(clonePrediction(record.input))
}
function closeIndividualDetail() {
  epoch++; showIndividualDetail.value = false; selectedRow.value = null; isReasoning.value = false; clearCurrentExplanation()
  requestLogs.value = cohortResult.value ? ['整份文件分析已完成，当前展示全部对象的群体视角。'] : []
}
function applyIntakeContext() {
  mode.value = modeFromQuery(route.query.mode)
  if (mode.value === 'individual' && intake.value) {
    intakeNotice.value = '已读取数据工作台本次单人记录；请核对性别、全血测量口径与总汞定义。不匹配的学历和生活方式类别未自动映射。'
    intake.value = null
  }
}
function activateDashboard() {
  resetStaleGroupDemoThreshold()
  active = true; applyIntakeContext()
  if (mode.value === 'batch' && showIndividualDetail.value && dashboard.value?.charts.target !== selectedTarget.value) closeIndividualDetail()
  refreshStatus(); window.addEventListener('resize', resizeCharts); initDashboardCharts()
}
onMounted(activateDashboard)
onActivated(activateDashboard)
onDeactivated(() => { active = false; epoch++; isReasoning.value = false; demoLoading.value = false; window.removeEventListener('resize', resizeCharts); clearCharts() })
onBeforeUnmount(() => { active = false; epoch++; window.removeEventListener('resize', resizeCharts); clearCharts() })
</script>

<style lang="scss" scoped>
@use "sass:color";

:deep(.el-icon svg) {
  max-width: 1em;
  max-height: 1em;
  width: 1em;
  height: 1em;
}

$color-primary: #1D4ED8;
$color-primary-light: #EFF6FF;
$color-bg: #F8FAFC;
$text-main: #0F172A;
$text-muted: #64748B;
$border-color: #E2E8F0;
$color-safe: #10B981;
$color-warn: #F59E0B;
$color-danger: #EF4444;

* {
  box-sizing: border-box;
}

.system-layout {
  display: flex;
  height: 100vh;
  background-color: $color-bg;
  font-family: 'Inter', sans-serif;
  overflow: hidden;
}

/* 侧边栏与顶栏框架样式 */
.sidebar {
  width: 280px;
  background-color: #fff;
  border-right: 1px solid $border-color;
  display: flex;
  flex-direction: column;
  z-index: 10;
  flex-shrink: 0;
  box-shadow: 2px 0 15px rgba(0, 0, 0, 0.03);
}

.brand-logo {
  height: 70px;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 24px;
  border-bottom: 1px solid $border-color;

  svg { width: 30px; height: 30px; color: $color-primary; flex-shrink: 0; }
  .brand-text { display: flex; flex-direction: column; }
  .title-en { font-size: 1.1rem; font-weight: 900; color: #1E3A8A; letter-spacing: -0.5px; }
  .title-cn { font-size: 0.8rem; font-weight: 600; color: #64748B; letter-spacing: 1px; margin-top: 2px; }
}

.menu-container {
  overflow-y: auto;
  flex: 1;
  padding: 16px 0;

  :deep(.custom-el-menu) {
    border-right: none;
    .menu-group-title { font-size: 0.85rem; font-weight: 800; color: #94A3B8; padding: 24px 24px 10px 24px; letter-spacing: 1px; }
    .el-sub-menu__title, .el-menu-item { font-weight: 600; color: #475569; font-size: 1.05rem; margin: 6px 12px; border-radius: 8px; height: 50px; line-height: 50px; }
    .el-sub-menu__title:hover, .el-menu-item:hover { background-color: #F8FAFC; color: $color-primary; }
    .el-menu-item.is-active { background-color: $color-primary-light; color: $color-primary; font-weight: 700; }
    .el-icon { font-size: 1.3rem; margin-right: 12px; color: #64748B; }
    .is-active>.el-icon { color: $color-primary; }
    .el-sub-menu .el-menu-item { min-width: auto; padding-left: 55px !important; font-size: 0.95rem; font-weight: 500; }
  }
}

.main-content {
  flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth;
}

.ep-header {
  height: 64px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex !important; justify-content: center; flex-shrink: 0;
}

.nav-wrapper {
  width: 100%; padding: 0 32px; display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; justify-content: space-between !important; align-items: center !important; height: 100%; max-width: none;
}

.back-link {
  display: flex; flex-direction: row; align-items: center; gap: 12px; cursor: pointer; color: $text-main; transition: color 0.2s;
  &:hover { color: $color-primary; }
  .back-icon { font-size: 1.2rem; font-weight: bold; }
  .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px; }
  .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; }
  .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-main; }
}

.ep-right-zone { display: flex; align-items: center; flex-direction: row; }

.user-profile {
  display: flex; flex-direction: row; align-items: center; gap: 12px; font-weight: 600; color: $text-main; font-size: 0.95rem; white-space: nowrap;
  .avatar { width: 32px; height: 32px; border-radius: 50%; background: $color-primary-light; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 0.9rem; }
}

.page-container {
  flex: 1 0 auto; padding: 40px; max-width: 1400px; margin: 0 auto; width: 100%; display: flex; flex-direction: column; padding-bottom: 80px;
}

.pipeline-steps {
  display: flex; align-items: center; margin-bottom: 30px; background: transparent; padding: 0;
  .step { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; color: $text-muted;
    .step-num { width: 24px; height: 24px; border-radius: 50%; background: #E5E7EB; display: flex; justify-content: center; align-items: center; font-size: 0.85rem; }
    &.active { color: $color-primary; .step-num { background: $color-primary; color: #FFF; } }
    &.success { color: $color-safe; .step-num { background: $color-safe; color: #FFF; font-size: 1rem; } }
  }
  .step-line { flex: 1; height: 2px; background: #E5E7EB; margin: 0 16px;
    &.active-line { background: $color-primary; }
    &.success-line { background: $color-safe; }
  }
}

.data-source-banner {
  background: #fff; border-radius: 12px; border: 1px solid #93C5FD; border-left: 4px solid $color-primary; margin-bottom: 24px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02); overflow: hidden; display: flex; justify-content: space-between; align-items: center; padding: 20px 24px;
  .ds-left { display: flex; align-items: center; gap: 16px; }
  .ds-label { font-size: 0.95rem; font-weight: 700; color: $text-main; }
  .file-chips { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
  .custom-tag { font-size: 0.9rem; font-weight: 600; color: $color-primary; background: #EFF6FF; border: none; padding: 4px 12px; height: auto;
    .el-icon { margin-right: 6px; font-size: 1rem; color: $color-primary; }
  }
  .ds-right { display: flex; align-items: center; gap: 12px; font-size: 0.9rem; color: $text-muted; font-weight: 500; }
}

.model-selector-card {
  background: #fff; border-radius: 12px; border: 1px solid $border-color; padding: 24px; margin-bottom: 24px; display: flex; justify-content: flex-start; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
  .selector-content { display: flex; align-items: center; gap: 20px; width: 100%; max-width: 900px; flex-wrap: wrap; }
  .s-label { font-size: 1.05rem; font-weight: 700; color: $text-main; white-space: nowrap; flex-shrink: 0; }
  .selector-actions { display: flex; align-items: center; gap: 16px; margin-left: auto; flex-wrap: wrap; }
  .run-btn { flex-shrink: 0; font-weight: 700; padding: 0 32px; }
}

.gemini-thinking-container {
  background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; margin-bottom: 30px; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
  .thinking-header { padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none;
    .t-left { display: flex; align-items: center; gap: 12px; }
    .sparkle-icon { width: 22px; height: 22px; color: #2563EB; }
    .spinning { animation: spin 2s linear infinite; }
    .t-text { font-size: 1.05rem; font-weight: 700; color: #1E3A8A; }
    .chevron-icon { color: #60A5FA; transition: transform 0.3s; &.rotated { transform: rotate(180deg); } }
  }
  .thinking-body { padding: 0 24px 24px 60px; }
  .think-steps { list-style: none; padding: 0; margin: 0; border-left: 2px solid #DBEAFE; padding-left: 16px; }
  .t-step { font-size: 0.95rem; color: #64748B; margin-bottom: 12px; position: relative;
    &::before { content: ''; position: absolute; left: -21px; top: 6px; width: 8px; height: 8px; border-radius: 50%; background: #DBEAFE; }
    &.active { color: #1E40AF; font-weight: 600; &::before { background: #3B82F6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.6); } }
  }
}

@keyframes spin { 100% { transform: rotate(360deg); } }

.results-dashboard { animation: fadeIn 0.6s ease-out forwards; }

@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

.alert-conclusion-banner {
  display: flex; gap: 20px; background: #FEF2F2; border: 1px solid #FCA5A5; padding: 24px; border-radius: 12px; margin-bottom: 30px;
  .a-icon { font-size: 2rem; color: $color-danger; }
  .a-content {
    h4 { margin: 0 0 10px 0; font-size: 1.2rem; color: #991B1B; .level-danger { font-weight: 900; color: #DC2626; } }
    p { margin: 0; font-size: 0.95rem; color: #7F1D1D; line-height: 1.6; strong { background: #FEE2E2; padding: 2px 6px; border-radius: 4px; border: 1px solid #FCA5A5; } }
  }
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 24px;
  margin-bottom: 30px;
}

.col-span-1 { grid-column: span 1; }
.col-span-2 { grid-column: span 2; }
.col-span-3 { grid-column: span 3; }
.col-span-4 { grid-column: span 4; }
.col-span-6 { grid-column: span 6; }

.result-card {
  background: #fff; border: 1px solid #DFE7F2; border-radius: 14px; padding: 24px; box-shadow: 0 3px 14px rgba(30, 64, 110, 0.025);
  &.border-danger { border-color: #FCA5A5; border-top: 4px solid #EF4444; }
}

.r-head {
  margin-bottom: 20px; border-bottom: 1px dashed #EAF0F8; padding-bottom: 16px; display: flex; justify-content: space-between; align-items: center;
  .title-group { display: flex; flex-direction: column; gap: 6px; }
  h4 { margin: 0; font-size: 16px; font-weight: 750; color: #172033; display: flex; align-items: center; flex-wrap: wrap; gap: 10px; line-height: 1.6; }
  .sub-desc { font-size: 12px; color: #7B879A; line-height: 1.85; }
}

.chart-box { width: 100%; height: 320px; }
.estimate-chart, .coverage-chart { height: 240px; }
.joint-chart { height: 370px; }
.individual-grid { grid-auto-flow: row dense; align-items: start; }
.estimate-card { background: linear-gradient(120deg, #F8FBFF 0%, #FFFFFF 70%); }
.analysis-section-heading { margin: 30px 0 20px; display: flex; align-items: center; justify-content: space-between; gap: 20px; h3 { margin: 5px 0 0; font-size: 21px; color: #172033; font-weight: 750; } }
.section-eyebrow { color: #8A9AB2; font-size: 10px; letter-spacing: 1.8px; font-weight: 650; }
.live-result-badge { display: inline-flex; align-items: center; gap: 8px; border-radius: 20px; padding: 7px 12px; background: #ECFDF5; color: #059669; font-size: 11px; i { width: 6px; height: 6px; border-radius: 50%; background: #10B981; } }
.calculation-notice, .calculation-details { color: #758399; background: #F1F6FC; border: 1px solid #E2EAF5; border-radius: 9px; padding: 13px 18px; font-size: 12px; line-height: 1.9; margin: 0 0 20px; }
.calculation-details { summary { cursor: pointer; } p { margin: 8px 0 0; } }
.heading-count { font-size: 11px; font-weight: 500; color: #6E809B; background: #F1F5FB; border-radius: 12px; padding: 2px 9px; }

.disease-list { display: flex; flex-direction: column; gap: 12px; }
.d-item { display: flex; flex-direction: column; gap: 6px; }
.d-info { display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 600; color: $text-main;
  .danger { color: $color-danger; } .warn { color: $color-warn; } .safe { color: $color-safe; }
}
:deep(.custom-progress .el-progress-bar__outer) { background-color: #F1F5F9 !important; }

/* SHAP Chart */
.shap-chart { display: flex; flex-direction: column; gap: 12px; padding: 10px 0; }
.shap-row { display: flex; align-items: center; height: 22px; }
.s-label { width: 85px; text-align: right; padding-right: 12px; font-size: 0.8rem; font-weight: 700; color: $text-main; flex-shrink: 0; white-space: nowrap; z-index: 2; }
.s-track { flex: 1; position: relative; height: 100%; display: flex; align-items: center; }
.zero-line { position: absolute; left: 25%; top: -10px; bottom: -10px; width: 1px; border-left: 2px dashed #9CA3AF; z-index: 0; }
.s-bar { position: absolute; height: 18px; border-radius: 3px; z-index: 1; animation: expandBar 1s ease-out forwards; display: flex; align-items: center; }
.s-bar.pos { left: 25%; background: #EF4444; transform-origin: left; }
.s-bar.neg { right: 75%; background: #10B981; transform-origin: right; }
.s-val { position: absolute; font-size: 0.75rem; font-weight: 700; white-space: nowrap; }
.s-bar.pos .s-val { left: 100%; padding-left: 8px; color: #EF4444; }
.s-bar.neg .s-val { right: 100%; padding-right: 8px; color: #10B981; }

@keyframes expandBar { from { transform: scaleX(0); } to { transform: scaleX(1); } }

.causal-graph { position: relative; height: 260px; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; overflow: hidden; }
.graph-svg { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; display: block !important; max-height: none !important; max-width: none !important; }
.path-active { stroke: #EF4444; stroke-width: 3; stroke-dasharray: 10; animation: dashMove 1s linear infinite; filter: url(#glowRed); }
.delay-1 { animation-delay: 0.5s; }
@keyframes dashMove { to { stroke-dashoffset: -20; } }
.c-node { position: absolute; transform: translate(-50%, -50%); padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: 700; background: #fff; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); z-index: 2; border-left: 4px solid;
  &.source { border-color: #3B82F6; } &.mechanism { border-color: #8B5CF6; } &.target { border-color: #10B981; }
  &.danger { background: #FEF2F2; border-color: #EF4444; color: #B91C1C; } &.warn { background: #FFFBEB; border-color: #F59E0B; color: #B45309; }
}

.pulse-glow { animation: pulseRedShadow 2s infinite; }
@keyframes pulseRedShadow { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }

.bottom-action-bar { display: flex; justify-content: flex-end; margin-top: 10px; padding-bottom: 20px;
  .final-run-btn { font-weight: 700; padding: 0 32px; }
}

.model-meta-footer { flex-shrink: 0; background: #F1F5F9; border-top: 1px solid #E2E8F0; padding: 40px; margin-top: 100px;
  .footer-container { max-width: 1400px; margin: 0 auto; }
  h4 { color: $text-main; margin: 0 0 24px 0; font-size: 1.1rem; border-bottom: 1px solid #CBD5E1; padding-bottom: 16px; }
  .meta-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 24px; }
  .meta-item { font-size: 0.85rem; color: $text-muted; strong { display: block; color: $text-main; margin-bottom: 6px; } p { margin: 0; line-height: 1.5; } }
}

@media (max-width: 1200px) {
  .results-grid { grid-template-columns: repeat(2, 1fr); }
  .col-span-2, .col-span-3, .col-span-4, .col-span-6 { grid-column: span 2; }
  .meta-grid { grid-template-columns: repeat(2, 1fr); }
}

/* Data bindings below retain the original dashboard grid and chart placements. */
.ep-right-zone { gap: 16px; }
.dashboard-controls { display:flex; align-items:center; flex-wrap:wrap; gap:16px; margin:-8px 0 24px; label { display:flex; align-items:center; gap:10px; font-size:13px; color:#64748B; } .version-note { margin-left:auto; color:#94A3B8; font-size:11px; } }
.demo-preset-note { margin: -10px 0 22px; color: #8292a6; font-size: 11px; line-height: 1.8; }
.demo-source-details { margin: -4px 0 20px; padding: 12px 16px; border: 1px solid #DBEAFE; border-radius: 8px; color: #64748B; background: #F8FBFF; font-size: 12px; line-height: 1.7; summary { cursor: pointer; color: #315E93; } p, ul { margin: 8px 0 0; } ul { padding-left: 20px; } }
.scope-alert { margin-bottom:18px; }
.data-source-banner .file-chips { max-width:600px; overflow-wrap:anywhere; }
.research-banner { background:#EFF6FF; border-color:#BFDBFE; .a-icon { color:#3B82F6; } .a-content h4 { color:#1E40AF; } .a-content p { color:#475569; } }
.result-card.border-danger { border-color:#BFDBFE; border-top-color:#3B82F6; min-width:0; }
.result-card { min-width:0; }
.chart-frame { position:relative; }
.chart-empty { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; padding:25px; text-align:center; font-size:13px; line-height:1.9; color:#94A3B8; background:#F8FAFC; border:1px dashed #E2E8F0; border-radius:8px; }
.chart-empty.standalone { position:static; min-height:260px; }
.chart-note { font-size:11px; line-height:1.9; color:#94A3B8; margin-top:16px; overflow-wrap:anywhere; }
.actual-outcomes { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
.outcome-item { position: relative; overflow: hidden; min-width: 0; display: flex; flex-direction: column; gap: 10px; padding: 17px 16px; border: 1px solid #E6ECF5; border-radius: 10px; background: #FBFCFE; cursor: pointer; text-align: left; font: inherit; transition: background .18s, border-color .18s; &::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--outcome-accent); opacity: .75; } &:hover { border-color: #AFCBF6; background: #F6FAFF; } &:focus-visible { outline: 2px solid #3B82F6; outline-offset: 2px; } &.chosen { border-color: #93BFFA; background: #F0F6FF; } &.withheld { background: #F9FAFC; &::before { background: #CBD5E1; } .outcome-status { color: #94A3B8; background: #EEF2F6; } .outcome-value { color: #A8B4C5; } } }
.outcome-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 7px; }
.outcome-name { color: #42516A; font-size: 12px; font-weight: 600; line-height: 1.6; }
.outcome-status { flex-shrink: 0; color: #059669; background: #EAF9F2; font-size: 9px; padding: 2px 6px; border-radius: 9px; }
.outcome-value { color: #223A60; font-size: 25px; line-height: 1.3; font-weight: 700; font-variant-numeric: tabular-nums; small { font-size: 10px; font-weight: 500; color: #8290A5; margin-left: 7px; } }
.outcome-note { color: #8A99AD; font-size: 10px; line-height: 1.8; }
.native-scale { min-height:260px; justify-content:center; gap:14px; .s-label { width:130px; overflow:hidden; text-overflow:ellipsis; font-size:11px; } .zero-line { left:50%; border-left-width:1px; } .s-bar.pos { left:50%; } .s-bar.neg { right:50%; } .s-val { font-size:10px; } .s-bar { animation:none; } }
.batch-page-bar { display:flex; align-items:center; flex-wrap:wrap; gap:14px; margin:15px 0 24px; span { color:#64748B; font-size:12px; } }
.meta-item small { font-weight:400; color:#94A3B8; }
.dialog-note { font-size:12px; line-height:1.9; color:#8191A5; }
.input-grid { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); gap:14px; margin:15px 0; label { display:flex; flex-direction:column; gap:7px; font-size:12px; color:#475569; } }
.dialog-metals { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; margin:20px 0; section { min-width:0; padding:16px; border:1px solid #E2E8F0; border-radius:9px; background:#F8FAFC; h4 { margin:0 0 14px; font-size:14px; color:#334155; } label { display:flex; flex-direction:column; gap:6px; margin:12px 0; font-size:12px; color:#64748B; } :deep(.el-checkbox__label) { font-size:11px; white-space:normal; } } }
.dialog-optional { margin:20px 0; summary { font-size:12px; color:#64748B; cursor:pointer; } .input-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.cohort-action-bar { justify-content:flex-end; flex-wrap:wrap; gap:12px; margin:22px 0 30px; }
@media (max-width:1400px) { .data-source-banner { align-items:flex-start; gap:16px; } .data-source-banner .file-chips { max-width:420px; } .native-scale .s-label { width:110px; } }
@media (min-width: 1201px) and (max-width: 1450px) { .actual-outcomes { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
@media (max-width: 1200px) { .individual-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); .col-span-3 { grid-column: span 1; } .col-span-2 { grid-column: span 1; } .col-span-4 { grid-column: span 1; } .col-span-6 { grid-column: span 2; } } .actual-outcomes { grid-template-columns: repeat(3, minmax(0, 1fr)); } .result-card { padding: 20px; } }

</style>
