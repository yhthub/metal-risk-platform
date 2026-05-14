<template>
  <div class="system-layout">
    <Sidebar default-active="3-1" />
    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToDatainput">
            <el-icon class="back-icon">
              <ArrowLeft />
            </el-icon>
            <span class="back-text">返回工作台</span>
            <span class="divider">|</span>
            <span class="page-title-top">风险量化与预警</span>
          </div>

          <div class="ep-right-zone">
            <div class="user-profile">
              <div class="avatar">Dr.</div>
              <span>职业卫生评估员</span>
            </div>
          </div>
        </div>
      </header>

      <div class="page-container">
        <div class="pipeline-steps">
          <div class="step active"><span class="step-num">1</span> 数据接入配置</div>
          <div class="step-line active-line"></div>
          <div class="step active"><span class="step-num">2</span> 多维可视化分析</div>
          <div class="step-line active-line"></div>
          <div class="step active"><span class="step-num">3</span> 风险预警模型</div>
        </div>

        <div class="data-source-banner">
          <div class="ds-left">
            <span class="ds-label">当前评估对象 (SZ-102) 挂载特征文件：</span>
            <div class="file-chips">
              <el-tag size="large" effect="plain" round class="custom-tag"><el-icon>
                  <Document />
                </el-icon> SZ-102_Profile.csv</el-tag>
              <el-tag size="large" effect="plain" round class="custom-tag"><el-icon>
                  <Document />
                </el-icon> LIS_Biomarkers.lst</el-tag>
              <el-tag size="large" effect="plain" round class="custom-tag"><el-icon>
                  <Document />
                </el-icon> Smelting_Exposure.csv</el-tag>
            </div>
          </div>
          <div class="ds-right">
            <el-button link type="primary" class="mr-4">查看特征明细</el-button>
            <el-dropdown trigger="hover" placement="bottom-end">
              <el-button type="primary" plain><el-icon>
                  <Plus />
                </el-icon> 追加数据源</el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item :icon="Upload">导入本地文件</el-dropdown-item>
                  <el-dropdown-item :icon="FolderOpened">从历史档案拉取</el-dropdown-item>
                  <el-dropdown-item :icon="Link" divided>API 接口接入</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>

        <div class="model-selector-card">
          <div class="selector-content">
            <label class="s-label">指定风险评估预训练模型：</label>
            <div class="selector-actions">
              <el-select v-model="selectedModel" size="large" placeholder="选择模型" class="custom-el-select"
                style="width: 220px;">
                <el-option v-for="model in availableModels" :key="model.id" :label="model.type" :value="model.id" />
              </el-select>
              <el-button type="primary" size="large" @click="startReasoning" :loading="isReasoning" class="run-btn">
                <span v-if="!isReasoning" style="margin-right: 6px;">✨</span>
                {{ isReasoning ? '模型深度推理中...' : '运行预警评估' }}
              </el-button>
            </div>
          </div>
        </div>

        <div class="gemini-thinking-container" v-if="isReasoning || reasoningComplete">
          <div class="thinking-header" @click="isThinkingExpanded = !isThinkingExpanded">
            <div class="t-left">
              <svg class="sparkle-icon" :class="{ 'spinning': isReasoning }" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" stroke-width="2">
                <path d="M12 2L15 9L22 12L15 15L12 22L9 15L2 12L9 9L12 2Z" fill="currentColor" />
              </svg>
              <span class="t-text">{{ isReasoning ? '模型深度思考与推理中...' : '查看完整推理过程 (Show thinking)' }}</span>
            </div>
            <el-icon class="chevron-icon" :class="{ 'rotated': isThinkingExpanded }">
              <ArrowDown />
            </el-icon>
          </div>
          <div class="thinking-body" v-show="isThinkingExpanded">
            <ul class="think-steps">
              <li class="t-step active">加载特征张量：提取 Pb, Cd, Hg, As 等10项核心暴露维度...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 1 }">调用德尔菲法 (Delphi) 专家库，匹配行业基线阈值...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 2 }">运行层次分析法 (AHP) 分配多金属复合暴露风险权重...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 3 }">计算 SHAP 贡献度，推演靶器官损伤联合概率...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 4 }">构建有向无环图 (DAG)，生成最短致病因果路径...</li>
            </ul>
          </div>
        </div>

        <div class="results-dashboard" v-if="reasoningComplete && !isReasoning">

          <div class="alert-conclusion-banner">
            <div class="a-icon"><el-icon>
                <WarningFilled />
              </el-icon></div>
            <div class="a-content">
              <h4>系统综合预警定级：<span class="level-danger">【三级 - 危险超标】</span></h4>
              <p>结合 <strong>德尔菲法 (Delphi)</strong> 与 <strong>层次分析法 (AHP)</strong>
                筛选核心预警指标，系统已构建金属及其化合物健康风险的三级预警体系。当前评估对象
                (SZ-102) 存在多维高危异常，亟需启动早期干预与决策支持。</p>
            </div>
          </div>

          <div class="results-grid">
            <div class="result-card col-span-2">
              <div class="r-head">
                <h4>风险总览仪表盘 (Risk Score)</h4>
              </div>
              <div class="chart-box" ref="dashGaugeRef"></div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <h4>五大多发病概率预测</h4>
                <el-button link type="primary" :icon="Download" @click="goToReportPage">导出PDF简报</el-button>
              </div>
              <div class="disease-list">
                <div class="d-item" v-for="disease in diseaseRisks" :key="disease.name">
                  <div class="d-info">
                    <span class="d-name">{{ disease.name }}</span>
                    <span class="d-val" :class="disease.status">{{ disease.prob }}%</span>
                  </div>
                  <el-progress :percentage="disease.prob" :color="getDiseaseColor(disease.status)" :stroke-width="10"
                    :show-text="false" class="custom-progress" />
                </div>
              </div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <h4>多金属暴露特征结构雷达</h4>
              </div>
              <div class="chart-box" ref="dashRadarRef"></div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <h4>特征归因优先级贡献 (SHAP Values)</h4>
              </div>
              <div class="shap-chart">
                <div class="shap-row" v-for="shap in shapData" :key="shap.name">
                  <span class="s-label">{{ shap.name }}</span>
                  <div class="s-track">
                    <div class="zero-line"></div>
                    <div class="s-bar" :class="shap.val > 0 ? 'pos' : 'neg'"
                      :style="{ width: Math.abs(shap.val) * 70 + '%' }">
                      <span class="s-val">{{ shap.val > 0 ? '+' + shap.val : shap.val }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <h4>历史健康风险演化趋势 (Trend)</h4>
              </div>
              <div class="chart-box" ref="dashLineRef"></div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <h4>多靶器官毒性分布热力图</h4>
              </div>
              <div class="chart-box" ref="dashHeatmapRef"></div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <h4>毒性传导机制桑基图 (Sankey)</h4>
              </div>
              <div class="chart-box" ref="dashSankeyRef"></div>
            </div>

            <div class="result-card col-span-6">
              <div class="r-head">
                <h4>靶向因果推断网络提取 (DAG)</h4>
              </div>
              <div class="causal-graph">
                <svg class="graph-svg" viewBox="0 0 1000 200">
                  <defs>
                    <marker id="arrowRed" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                      <polygon points="0 0, 6 3, 0 6" fill="#EF4444" />
                    </marker>
                    <marker id="arrowGrey" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto">
                      <polygon points="0 0, 6 3, 0 6" fill="#9CA3AF" />
                    </marker>
                    <filter id="glowRed" x="-20%" y="-20%" width="140%" height="140%">
                      <feGaussianBlur stdDeviation="3" result="blur" />
                      <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                  </defs>
                  <path d="M 150 150 C 350 150, 350 50, 550 50" stroke="#E5E7EB" stroke-width="2" fill="none"
                    marker-end="url(#arrowGrey)" />
                  <path d="M 550 150 C 750 150, 750 100, 900 100" stroke="#E5E7EB" stroke-width="2" fill="none"
                    marker-end="url(#arrowGrey)" />
                  <path class="path-active danger" d="M 150 50 C 350 50, 350 50, 550 50" fill="none"
                    marker-end="url(#arrowRed)" />
                  <path class="path-active danger delay-1" d="M 550 50 C 750 50, 750 100, 900 100" fill="none"
                    marker-end="url(#arrowRed)" />
                </svg>
                <div class="c-node source danger pulse-glow" style="left: 150px; top: 50px;">Pb 暴露异常</div>
                <div class="c-node source warn" style="left: 150px; top: 150px;">Cd 暴露临界</div>
                <div class="c-node mechanism danger" style="left: 550px; top: 50px;">血脑屏障通透性异常</div>
                <div class="c-node mechanism warn" style="left: 550px; top: 150px;">肾近曲小管氧化应激</div>
                <div class="c-node target danger pulse-glow" style="left: 900px; top: 100px;">神经退行性病变</div>
              </div>
            </div>
          </div>

          <div class="bottom-action-bar">
            <el-button type="success" size="large" plain :icon="Download" @click="goToReportPage"
              style="margin-right: 12px;">
              下载风险评估报告 (完整版)
            </el-button>
            <el-button type="primary" size="large" class="final-run-btn" @click="goToPlan">
              生成个体化智能干预与阻断策略 ➔
            </el-button>
          </div>
        </div>
      </div>

      <footer class="model-meta-footer">
        <div class="footer-container">
          <h4>预训练模型字典与说明 (Model Meta Information)</h4>
          <div class="meta-grid">
            <div class="meta-item" v-for="m in availableModels" :key="m.id">
              <strong>{{ m.type }}</strong>
              <p>{{ m.desc }}</p>
            </div>
          </div>
        </div>
      </footer>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Coin, DataLine, TrendCharts, Share, DocumentChecked, ArrowLeft, ArrowDown, Document, Plus, Upload, FolderOpened, Link, WarningFilled, Download, Check } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

const goToInputData = async () => {
  // 注意：如果你的文件名叫 inputdata.vue，这里就是 '/inputdata'
  // 如果叫 datainput.vue，这里请改成 '/datainput'
  await navigateTo('/datainput')
}
const goToPlan = async () => { await navigateTo('/plan') }

// ✨ 核心分离：跳转到全新的独立路由页面
const goToReportPage = async () => {
  ElMessage.success({ message: '正在提取多维数据，生成风险评估长卷...', duration: 2000 })
  setTimeout(async () => {
    await navigateTo('/risk/report')
  }, 600)
}

const availableModels = ref([
  { id: 'm1', type: 'XGBoost', desc: '复合金属-多靶器官综合风险评估模型，融合多组学与环境监测评估全局概率。' },
  { id: 'm2', type: 'DNN', desc: '铅/砷协同-中枢神经疾病网络，专攻重金属突破血脑屏障引起的神经退行性病变。' },
  { id: 'm3', type: 'LightGBM', desc: '镉靶向-慢性肾病与尿毒症预警模型，基于尿镉特征精准预测肾小管及肾小球损伤。' },
  { id: 'm4', type: 'Random Forest', desc: '多金属复合-骨质疏松与骨折风险模型，分析金属对钙磷代谢及成骨细胞活性的干扰。' },
  { id: 'm8', type: 'Bayesian Net', desc: '职业金属中毒机制因果推理贝叶斯网络，提供具有强可解释性的致病传导路径。' }
])

const selectedModel = ref('m1')
const isReasoning = ref(false)
const reasoningComplete = ref(false)
const isThinkingExpanded = ref(false)
const thinkProgress = ref(0)

const diseaseRisks = ref([
  { name: '退行性中枢神经系统疾病', prob: 92, status: 'danger' },
  { name: '慢性肾病与尿毒症', prob: 78, status: 'warn' },
  { name: '骨质疏松与骨折', prob: 45, status: 'safe' },
  { name: '心脑血管病', prob: 32, status: 'safe' }
])

const getDiseaseColor = (status) => {
  if (status === 'danger') return '#EF4444'
  if (status === 'warn') return '#F59E0B'
  return '#10B981'
}

const shapData = ref([
  { name: 'Pb (铅)', val: 0.85 },
  { name: 'As (砷)', val: 0.60 },
  { name: 'Cd (镉)', val: 0.40 },
  { name: 'Ni (镍)', val: 0.15 },
  { name: 'Cr (铬)', val: 0.08 },
  { name: 'Co (钴)', val: 0.02 },
  { name: 'Th (钍)', val: 0.01 },
  { name: 'Li (锂)', val: -0.05 },
  { name: 'Rn (氡)', val: -0.08 },
  { name: 'Hg (汞)', val: -0.15 }
])

const dashGaugeRef = ref(null); const dashRadarRef = ref(null); const dashLineRef = ref(null);
const dashHeatmapRef = ref(null); const dashSankeyRef = ref(null);
let chartsInstances = []

const clearCharts = () => { chartsInstances.forEach(c => c.dispose()); chartsInstances = [] }

const getGaugeOption = () => ({ series: [{ type: 'gauge', startAngle: 180, endAngle: 0, center: ['50%', '75%'], radius: '100%', axisLine: { lineStyle: { width: 15, color: [[0.5, '#10B981'], [0.8, '#F59E0B'], [1, '#EF4444']] } }, pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, detail: { fontSize: 36, fontWeight: 'bold', formatter: '{value}%', color: '#EF4444', offsetCenter: [0, '-10%'] }, data: [{ value: 92 }] }] })
const getRadarOption = () => ({ radar: { indicator: [{ name: 'Pb', max: 150 }, { name: 'As', max: 150 }, { name: 'Cd', max: 150 }, { name: 'Hg', max: 150 }, { name: 'Cr', max: 150 }, { name: 'Ni', max: 150 }], axisName: { color: '#64748B', fontWeight: 'bold' } }, series: [{ type: 'radar', data: [{ value: [124, 105, 89, 24, 34, 65], areaStyle: { color: 'rgba(239, 68, 68, 0.3)' }, lineStyle: { color: '#EF4444' }, itemStyle: { color: '#EF4444' } }] }] })
const getLineOption = () => ({ grid: { left: '10%', right: '5%', top: '10%', bottom: '15%' }, xAxis: { type: 'category', boundaryGap: false, data: ['2021', '2022', '2023', '2024', '2025', '2026'] }, yAxis: { type: 'value' }, series: [{ data: [45, 52, 60, 75, 85, 92], type: 'line', smooth: true, lineStyle: { color: '#EF4444', width: 3 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(239, 68, 68, 0.5)' }, { offset: 1, color: 'rgba(239, 68, 68, 0)' }]) } }] })
const getHeatmapOption = () => ({ grid: { left: '20%', right: '5%', top: '5%', bottom: '15%' }, xAxis: { type: 'category', data: ['Pb', 'As', 'Cd', 'Hg', 'Cr'] }, yAxis: { type: 'category', data: ['神经系统', '泌尿系统', '骨骼系统'] }, visualMap: { min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%', inRange: { color: ['#10B981', '#F59E0B', '#EF4444'] }, show: false }, series: [{ name: 'Damage', type: 'heatmap', data: [[0, 0, 95], [1, 0, 80], [2, 0, 20], [3, 0, 10], [4, 0, 15], [0, 1, 30], [1, 1, 40], [2, 1, 85], [3, 1, 20], [4, 1, 10], [0, 2, 60], [1, 2, 30], [2, 2, 50], [3, 2, 10], [4, 2, 5]], label: { show: true } }] })
const getSankeyOption = () => ({ series: [{ type: 'sankey', layout: 'none', focusNodeAdjacency: true, data: [{ name: 'Pb暴露' }, { name: 'As暴露' }, { name: 'Cd暴露' }, { name: '血脑屏障异常' }, { name: '肾小管应激' }, { name: '神经退行性病变' }, { name: '慢性肾病' }], links: [{ source: 'Pb暴露', target: '血脑屏障异常', value: 5 }, { source: 'As暴露', target: '血脑屏障异常', value: 3 }, { source: 'Cd暴露', target: '肾小管应激', value: 4 }, { source: '血脑屏障异常', target: '神经退行性病变', value: 8 }, { source: '肾小管应激', target: '慢性肾病', value: 4 }], lineStyle: { color: 'source', curveness: 0.5, opacity: 0.4 } }] })

const initDashboardCharts = () => {
  clearCharts()
  if (dashGaugeRef.value) { const c = echarts.init(dashGaugeRef.value); c.setOption(getGaugeOption()); chartsInstances.push(c) }
  if (dashRadarRef.value) { const c = echarts.init(dashRadarRef.value); c.setOption(getRadarOption()); chartsInstances.push(c) }
  if (dashLineRef.value) { const c = echarts.init(dashLineRef.value); c.setOption(getLineOption()); chartsInstances.push(c) }
  if (dashHeatmapRef.value) { const c = echarts.init(dashHeatmapRef.value); c.setOption(getHeatmapOption()); chartsInstances.push(c) }
  if (dashSankeyRef.value) { const c = echarts.init(dashSankeyRef.value); c.setOption(getSankeyOption()); chartsInstances.push(c) }
}

const resizeCharts = () => { chartsInstances.forEach(c => c.resize()) }
onMounted(() => {
  window.addEventListener('resize', resizeCharts)
  const style = document.createElement('style')
  style.innerHTML = `.el-select .el-input__wrapper { background-color: #F9FAFB !important; border: 1px solid #D1D5DB !important; } .el-select .el-input__inner { font-family: 'Inter', sans-serif !important; font-weight: 700 !important; color: #1D4ED8 !important; text-align: center !important; }`
  document.head.appendChild(style)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  clearCharts()
})

const startReasoning = () => {
  isReasoning.value = true; reasoningComplete.value = false; isThinkingExpanded.value = true; thinkProgress.value = 0;
  const interval = setInterval(() => { thinkProgress.value++; if (thinkProgress.value >= 4) clearInterval(interval) }, 600)
  setTimeout(() => {
    isReasoning.value = false; reasoningComplete.value = true;
    nextTick(() => { initDashboardCharts(); setTimeout(() => { window.scrollTo({ top: 600, behavior: 'smooth' }) }, 100) })
  }, 3500)
}
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

  svg {
    width: 30px;
    height: 30px;
    color: $color-primary;
    flex-shrink: 0;
  }

  .brand-text {
    display: flex;
    flex-direction: column;
  }

  .title-en {
    font-size: 1.1rem;
    font-weight: 900;
    color: #1E3A8A;
    letter-spacing: -0.5px;
  }

  .title-cn {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748B;
    letter-spacing: 1px;
    margin-top: 2px;
  }
}

.menu-container {
  overflow-y: auto;
  flex: 1;
  padding: 16px 0;

  :deep(.custom-el-menu) {
    border-right: none;

    .menu-group-title {
      font-size: 0.85rem;
      font-weight: 800;
      color: #94A3B8;
      padding: 24px 24px 10px 24px;
      letter-spacing: 1px;
    }

    .el-sub-menu__title,
    .el-menu-item {
      font-weight: 600;
      color: #475569;
      font-size: 1.05rem;
      margin: 6px 12px;
      border-radius: 8px;
      height: 50px;
      line-height: 50px;
    }

    .el-sub-menu__title:hover,
    .el-menu-item:hover {
      background-color: #F8FAFC;
      color: $color-primary;
    }

    .el-menu-item.is-active {
      background-color: $color-primary-light;
      color: $color-primary;
      font-weight: 700;
    }

    .el-icon {
      font-size: 1.3rem;
      margin-right: 12px;
      color: #64748B;
    }

    .is-active>.el-icon {
      color: $color-primary;
    }

    .el-sub-menu .el-menu-item {
      min-width: auto;
      padding-left: 55px !important;
      font-size: 0.95rem;
      font-weight: 500;
    }
  }
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.ep-header {
  height: 64px;
  background: #fff;
  border-bottom: 1px solid $border-color;
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex !important;
  justify-content: center;
  flex-shrink: 0;
}

.nav-wrapper {
  width: 100%;
  padding: 0 32px;
  display: flex !important;
  flex-direction: row !important;
  flex-wrap: nowrap !important;
  justify-content: space-between !important;
  align-items: center !important;
  height: 100%;
  max-width: none;
}

.back-link {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  color: $text-main;
  transition: color 0.2s;

  &:hover {
    color: $color-primary;
  }

  .back-icon {
    font-size: 1.2rem;
    font-weight: bold;
  }

  .back-text {
    font-size: 1.05rem;
    font-weight: 700;
    letter-spacing: 1px;
  }

  .divider {
    color: #D1D5DB;
    font-weight: 300;
    margin: 0 8px;
  }

  .page-title-top {
    font-size: 1.1rem;
    font-weight: 800;
    color: $text-main;
  }
}

.ep-right-zone {
  display: flex;
  align-items: center;
  flex-direction: row;
}

.user-profile {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: $text-main;
  font-size: 0.95rem;
  white-space: nowrap;

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: $color-primary-light;
    color: $color-primary;
    display: flex;
    justify-content: center;
    align-items: center;
    font-weight: 700;
    font-size: 0.9rem;
  }
}

.page-container {
  flex: 1 0 auto;
  padding: 40px;
  max-width: 1400px;
  margin: 0 auto;
  width: 100%;
  display: flex;
  flex-direction: column;
  padding-bottom: 80px;
}

.pipeline-steps {
  display: flex;
  align-items: center;
  margin-bottom: 30px;
  background: transparent;
  padding: 0;

  .step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.95rem;
    font-weight: 600;
    color: $text-muted;

    .step-num {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: #E5E7EB;
      display: flex;
      justify-content: center;
      align-items: center;
      font-size: 0.85rem;
    }

    &.active {
      color: $color-primary;

      .step-num {
        background: $color-primary;
        color: #FFF;
      }
    }

    &.success {
      color: $color-safe;

      .step-num {
        background: $color-safe;
        color: #FFF;
        font-size: 1rem;
      }
    }
  }

  .step-line {
    flex: 1;
    height: 2px;
    background: #E5E7EB;
    margin: 0 16px;

    &.active-line {
      background: $color-primary;
    }

    &.success-line {
      background: $color-safe;
    }
  }
}

.data-source-banner {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #93C5FD;
  border-left: 4px solid $color-primary;
  margin-bottom: 24px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
  overflow: hidden;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;

  .ds-left {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .ds-label {
    font-size: 0.95rem;
    font-weight: 700;
    color: $text-main;
  }

  .file-chips {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: center;
  }

  .custom-tag {
    font-size: 0.9rem;
    font-weight: 600;
    color: $color-primary;
    background: #EFF6FF;
    border: none;
    padding: 4px 12px;
    height: auto;

    .el-icon {
      margin-right: 6px;
      font-size: 1rem;
      color: $color-primary;
    }
  }

  .ds-right {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 0.9rem;
    color: $text-muted;
    font-weight: 500;
  }
}

.model-selector-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid $border-color;
  padding: 24px;
  margin-bottom: 24px;
  display: flex;
  justify-content: flex-start;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);

  .selector-content {
    display: flex;
    align-items: center;
    gap: 20px;
    width: 100%;
    max-width: 900px;
    flex-wrap: wrap;
  }

  .s-label {
    font-size: 1.05rem;
    font-weight: 700;
    color: $text-main;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .selector-actions {
    display: flex;
    align-items: center;
    gap: 16px;
    margin-left: auto;
    flex-wrap: wrap;
  }

  .run-btn {
    flex-shrink: 0;
    font-weight: 700;
    padding: 0 32px;
  }
}

.gemini-thinking-container {
  background: #EFF6FF;
  border: 1px solid #BFDBFE;
  border-radius: 12px;
  margin-bottom: 30px;
  overflow: hidden;
  transition: all 0.3s ease;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);

  .thinking-header {
    padding: 16px 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
    user-select: none;

    .t-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .sparkle-icon {
      width: 22px;
      height: 22px;
      color: #2563EB;
    }

    .spinning {
      animation: spin 2s linear infinite;
    }

    .t-text {
      font-size: 1.05rem;
      font-weight: 700;
      color: #1E3A8A;
    }

    .chevron-icon {
      color: #60A5FA;
      transition: transform 0.3s;

      &.rotated {
        transform: rotate(180deg);
      }
    }
  }

  .thinking-body {
    padding: 0 24px 24px 60px;
  }

  .think-steps {
    list-style: none;
    padding: 0;
    margin: 0;
    border-left: 2px solid #DBEAFE;
    padding-left: 16px;
  }

  .t-step {
    font-size: 0.95rem;
    color: #64748B;
    margin-bottom: 12px;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      left: -21px;
      top: 6px;
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #DBEAFE;
    }

    &.active {
      color: #1E40AF;
      font-weight: 600;

      &::before {
        background: #3B82F6;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.6);
      }
    }
  }
}

@keyframes spin {
  100% {
    transform: rotate(360deg);
  }
}

.results-dashboard {
  animation: fadeIn 0.6s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.alert-conclusion-banner {
  display: flex;
  gap: 20px;
  background: #FEF2F2;
  border: 1px solid #FCA5A5;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 30px;

  .a-icon {
    font-size: 2rem;
    color: $color-danger;
  }

  .a-content {
    h4 {
      margin: 0 0 10px 0;
      font-size: 1.2rem;
      color: #991B1B;

      .level-danger {
        font-weight: 900;
        color: #DC2626;
      }
    }

    p {
      margin: 0;
      font-size: 0.95rem;
      color: #7F1D1D;
      line-height: 1.6;

      strong {
        background: #FEE2E2;
        padding: 2px 6px;
        border-radius: 4px;
        border: 1px solid #FCA5A5;
      }
    }
  }
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 24px;
  margin-bottom: 30px;
}

.col-span-1 {
  grid-column: span 1;
}

.col-span-2 {
  grid-column: span 2;
}

.col-span-3 {
  grid-column: span 3;
}

.col-span-6 {
  grid-column: span 6;
}

.result-card {
  background: #fff;
  border: 1px solid $border-color;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
}

.r-head {
  margin-bottom: 16px;
  border-bottom: 1px solid #F8FAFC;
  padding-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;

  h4 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: $text-main;
  }
}

.chart-box {
  width: 100%;
  height: 220px;
}

.disease-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.d-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.d-info {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  font-weight: 600;
  color: $text-main;

  .danger {
    color: $color-danger;
  }

  .warn {
    color: $color-warn;
  }

  .safe {
    color: $color-safe;
  }
}

:deep(.custom-progress .el-progress-bar__outer) {
  background-color: #F1F5F9 !important;
}

/* SHAP Chart (带有防挤压优化) */
.shap-chart {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
}

.shap-row {
  display: flex;
  align-items: center;
  height: 22px;
}

.s-label {
  width: 85px;
  text-align: right;
  padding-right: 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: $text-main;
  flex-shrink: 0;
  white-space: nowrap;
  z-index: 2;
}

.s-track {
  flex: 1;
  position: relative;
  height: 100%;
  display: flex;
  align-items: center;
}

.zero-line {
  position: absolute;
  left: 25%;
  top: -10px;
  bottom: -10px;
  width: 1px;
  border-left: 2px dashed #9CA3AF;
  z-index: 0;
}

.s-bar {
  position: absolute;
  height: 18px;
  border-radius: 3px;
  z-index: 1;
  animation: expandBar 1s ease-out forwards;
  display: flex;
  align-items: center;
}

.s-bar.pos {
  left: 25%;
  background: #EF4444;
  transform-origin: left;
}

.s-bar.neg {
  right: 75%;
  background: #10B981;
  transform-origin: right;
}

.s-val {
  position: absolute;
  font-size: 0.75rem;
  font-weight: 700;
  white-space: nowrap;
}

.s-bar.pos .s-val {
  left: 100%;
  padding-left: 8px;
  color: #EF4444;
}

.s-bar.neg .s-val {
  right: 100%;
  padding-right: 8px;
  color: #10B981;
}

@keyframes expandBar {
  from {
    transform: scaleX(0);
  }

  to {
    transform: scaleX(1);
  }
}

.causal-graph {
  position: relative;
  height: 260px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
}

.graph-svg {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
  display: block !important;
  max-height: none !important;
  max-width: none !important;
}

.path-active {
  stroke: #EF4444;
  stroke-width: 3;
  stroke-dasharray: 10;
  animation: dashMove 1s linear infinite;
  filter: url(#glowRed);
}

.delay-1 {
  animation-delay: 0.5s;
}

@keyframes dashMove {
  to {
    stroke-dashoffset: -20;
  }
}

.c-node {
  position: absolute;
  transform: translate(-50%, -50%);
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 700;
  background: #fff;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  z-index: 2;
  border-left: 4px solid;

  &.source {
    border-color: #3B82F6;
  }

  &.mechanism {
    border-color: #8B5CF6;
  }

  &.target {
    border-color: #10B981;
  }

  &.danger {
    background: #FEF2F2;
    border-color: #EF4444;
    color: #B91C1C;
  }

  &.warn {
    background: #FFFBEB;
    border-color: #F59E0B;
    color: #B45309;
  }
}

.pulse-glow {
  animation: pulseRedShadow 2s infinite;
}

@keyframes pulseRedShadow {
  0% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4);
  }

  70% {
    box-shadow: 0 0 0 10px rgba(239, 68, 68, 0);
  }

  100% {
    box-shadow: 0 0 0 0 rgba(239, 68, 68, 0);
  }
}

.bottom-action-bar {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
  padding-bottom: 20px;

  .final-run-btn {
    font-weight: 700;
    padding: 0 32px;
  }
}

.model-meta-footer {
  flex-shrink: 0;
  background: #F1F5F9;
  border-top: 1px solid #E2E8F0;
  padding: 40px;
  margin-top: auto;

  .footer-container {
    max-width: 1400px;
    margin: 0 auto;
  }

  h4 {
    color: $text-main;
    margin: 0 0 24px 0;
    font-size: 1.1rem;
    border-bottom: 1px solid #CBD5E1;
    padding-bottom: 16px;
  }

  .meta-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 24px;
  }

  .meta-item {
    font-size: 0.85rem;
    color: $text-muted;

    strong {
      display: block;
      color: $text-main;
      margin-bottom: 6px;
    }

    p {
      margin: 0;
      line-height: 1.5;
    }
  }
}

@media (max-width: 1200px) {
  .results-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .col-span-2,
  .col-span-3,
  .col-span-6 {
    grid-column: span 2;
  }

  .meta-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>