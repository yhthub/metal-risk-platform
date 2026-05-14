<template>
  <div class="system-layout">
   <Sidebar default-active="3-1" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goBack">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">返回预警控制台</span>
            <span class="divider">|</span>
            <span class="page-title-top">全员风险评估深度报告</span>
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
        <div class="report-paper">
          <div class="report-watermark">RISK ASSESSMENT REPORT</div>
          
          <div class="report-header">
            <div class="rh-left">
              <svg class="report-logo-custom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <div class="rh-text">
                <h1>全员健康风险排查与预测报告</h1>
                <p>提取文件：SZ-102_Profile.csv, LIS_Biomarkers.lst | 生成时间：2026-05-12 15:40</p>
              </div>
            </div>
            <div class="rh-right">
              <div class="risk-seal">
                <span>综合级别</span>
                <strong class="text-danger">WARNING</strong>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="report-section">
            <h3 class="rs-title">一、 高危与中危预警人员排查清单</h3>
            <p class="report-desc">系统基于输入的体检与监测数据，已过滤掉健康状态人员。以下为存在临床器质性病变风险的预警人员名单，按综合风险度降序排列：</p>
            <div class="worker-table">
              <div class="wt-header">
                <span>工号 / 姓名</span>
                <span>所属部门</span>
                <span>暴露工龄</span>
                <span>风险驱动因子</span>
                <span>综合危险指数</span>
              </div>
              <div class="wt-row" v-for="worker in highRiskWorkers" :key="worker.id" :class="worker.level">
                <span class="w-name"><strong>{{ worker.id }}</strong> ({{ worker.name }})</span>
                <span>{{ worker.dept }}</span>
                <span>{{ worker.years }} 年</span>
                <span class="w-factors">{{ worker.factors }}</span>
                <span class="w-score">{{ worker.score }}%</span>
              </div>
            </div>
          </div>

          <div class="report-section highlight">
            <h3 class="rs-title">二、 首要高危人员 (SZ-102) 综合靶器官预测</h3>
            <el-row :gutter="40">
              <el-col :span="10">
                <div class="chart-box-report" ref="reportGaugeRef"></div>
              </el-col>
              <el-col :span="14">
                <div class="disease-list">
                  <div class="d-item" v-for="disease in diseaseRisks" :key="disease.name">
                    <div class="d-info">
                      <span class="d-name">{{ disease.name }}</span>
                      <span class="d-val" :class="disease.status">{{ disease.prob }}%</span>
                    </div>
                    <el-progress :percentage="disease.prob" :color="getDiseaseColor(disease.status)" :stroke-width="10" :show-text="false" class="custom-progress" />
                  </div>
                </div>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[系统洞察]：</strong> XGBoost 多靶器官概率推演显示，该员工患退行性中枢神经系统疾病的概率高达 92%，已越过临床安全红线；同时慢性肾病与尿毒症并发概率亦达到 78%，亟待医学干预。</p>
          </div>

          <div class="report-section">
            <h3 class="rs-title">三、 核心重金属暴露结构与特征归因</h3>
            <el-row :gutter="40">
              <el-col :span="12">
                <div class="chart-box-report" ref="reportRadarRef"></div>
              </el-col>
              <el-col :span="12">
                <div class="shap-chart" style="margin-top: 30px;">
                  <div class="shap-row" v-for="shap in shapData" :key="shap.name">
                    <span class="s-label">{{ shap.name }}</span>
                    <div class="s-track">
                      <div class="zero-line"></div>
                      <div class="s-bar" :class="shap.val > 0 ? 'pos' : 'neg'" :style="{ width: Math.abs(shap.val) * 70 + '%' }">
                        <span class="s-val">{{ shap.val > 0 ? '+' + shap.val : shap.val }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[系统洞察]：</strong> 雷达图与 SHAP 归因模型交叉印证，<strong>铅(Pb) 和 砷(As)</strong> 是驱动本次高危预警的核心正向因子（贡献度分别为 +0.85 和 +0.60）。汞(Hg)等其他元素虽有检出，但对当前疾病图谱起负向或微弱影响。</p>
          </div>

          <div class="report-section highlight">
            <h3 class="rs-title">四、 风险演化时序与靶器官毒性分布</h3>
            <el-row :gutter="40">
              <el-col :span="12">
                <div class="chart-box-report" ref="reportLineRef"></div>
              </el-col>
              <el-col :span="12">
                <div class="chart-box-report" ref="reportHeatmapRef"></div>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[系统洞察]：</strong> 时序图揭示了该评估对象的健康风险自 2024 年起呈现指数级攀升（突破 75% 警戒线）。热力图谱进一步明确：Pb 极度富集于神经与骨骼系统，而 Cd 则精准靶向攻击泌尿系统。</p>
          </div>

          <div class="report-section">
            <h3 class="rs-title">五、 毒理学桑基图与靶向因果网络提取</h3>
            <el-row :gutter="40">
              <el-col :span="10">
                <div class="chart-box-report" ref="reportSankeyRef"></div>
              </el-col>
              <el-col :span="14">
                <div class="causal-graph" style="margin-top: 10px; height: 230px;">
                  <svg class="graph-svg" viewBox="0 0 1000 200">
                    <defs>
                      <marker id="arrowRedRpt" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0, 6 3, 0 6" fill="#EF4444" /></marker>
                      <marker id="arrowGreyRpt" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0, 6 3, 0 6" fill="#9CA3AF" /></marker>
                    </defs>
                    <path d="M 150 150 C 300 150, 300 50, 450 50" stroke="#E5E7EB" stroke-width="2" fill="none" marker-end="url(#arrowGreyRpt)"/>
                    <path class="path-active danger" d="M 150 50 C 300 50, 300 50, 450 50" fill="none" marker-end="url(#arrowRedRpt)"/>
                    <path class="path-active danger delay-1" d="M 450 50 C 600 50, 600 100, 750 100" fill="none" marker-end="url(#arrowRedRpt)"/>
                  </svg>
                  <div class="c-node source danger pulse-glow" style="left: 150px; top: 50px;">Pb 暴露异常</div>
                  <div class="c-node source warn" style="left: 150px; top: 150px;">Cd 暴露临界</div>
                  <div class="c-node mechanism danger" style="left: 450px; top: 50px;">血脑屏障通透性异常</div>
                  <div class="c-node target danger pulse-glow" style="left: 750px; top: 100px;">神经退行性病变</div>
                </div>
              </el-col>
            </el-row>
            <p class="report-desc"><strong>[系统洞察]：</strong> 因果图谱(DAG)最终提炼出一条最短的确定性致病链条：<strong>[Pb 持续暴露] ➔ [血脑屏障通透性破坏] ➔ [不可逆中枢神经退行性病变]</strong>。这为后续智能生成阻断策略提供了唯一核心靶点。</p>
          </div>

          <div class="report-footer">
            <div class="sign-area">
              <p>系统算法流：<span class="sign-system">XGBoost + Bayesian DAG v4.1</span></p>
            </div>
            <div class="report-btns">
              <el-button type="success" size="large" @click="handlePrint"><el-icon><Printer /></el-icon> 打印并存档报告</el-button>
            </div>
          </div>
        </div>
      </div>

    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Coin, DataLine, TrendCharts, Share, DocumentChecked, ArrowLeft, Printer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

const goBack = async () => {
  await navigateTo('/risk')
}

const handlePrint = () => {
  setTimeout(() => { window.print() }, 500)
}

const highRiskWorkers = ref([
  { id: 'SZ-102', name: '张建国', dept: '第一熔炼车间', years: 12, factors: 'Pb, As', score: 92, level: 'danger' },
  { id: 'SZ-089', name: '刘伟', dept: '第一熔炼车间', years: 15, factors: 'Pb, Cd', score: 88, level: 'danger' },
  { id: 'SZ-214', name: '王强', dept: '原矿粉碎区', years: 8, factors: 'As, Ni', score: 75, level: 'warn' },
  { id: 'SZ-156', name: '李明', dept: '尾气处理组', years: 10, factors: 'Pb, Hg', score: 68, level: 'warn' },
  { id: 'SZ-042', name: '赵铁柱', dept: '原矿粉碎区', years: 14, factors: 'Cd', score: 55, level: 'warn' }
])

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

/* ================== ECharts 渲染逻辑 ================== */
const reportGaugeRef = ref(null); const reportRadarRef = ref(null); const reportLineRef = ref(null); 
const reportHeatmapRef = ref(null); const reportSankeyRef = ref(null);
let chartsInstances = []

const clearCharts = () => { chartsInstances.forEach(c => c.dispose()); chartsInstances = [] }

const getGaugeOption = () => ({ series: [{ type: 'gauge', startAngle: 180, endAngle: 0, center: ['50%', '75%'], radius: '100%', axisLine: { lineStyle: { width: 15, color: [[0.5, '#10B981'], [0.8, '#F59E0B'], [1, '#EF4444']] } }, pointer: { show: false }, axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, detail: { fontSize: 36, fontWeight: 'bold', formatter: '{value}%', color: '#EF4444', offsetCenter: [0, '-10%'] }, data: [{ value: 92 }] }] })
const getRadarOption = () => ({ radar: { indicator: [ { name: 'Pb', max: 150 }, { name: 'As', max: 150 }, { name: 'Cd', max: 150 }, { name: 'Hg', max: 150 }, { name: 'Cr', max: 150 }, { name: 'Ni', max: 150 } ], axisName: { color: '#64748B', fontWeight: 'bold' } }, series: [{ type: 'radar', data: [{ value: [124, 105, 89, 24, 34, 65], areaStyle: { color: 'rgba(239, 68, 68, 0.3)' }, lineStyle: { color: '#EF4444' }, itemStyle: { color: '#EF4444' } }] }] })
const getLineOption = () => ({ grid: { left: '10%', right: '5%', top: '10%', bottom: '15%' }, xAxis: { type: 'category', boundaryGap: false, data: ['2021', '2022', '2023', '2024', '2025', '2026'] }, yAxis: { type: 'value' }, series: [{ data: [45, 52, 60, 75, 85, 92], type: 'line', smooth: true, lineStyle: { color: '#EF4444', width: 3 }, areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(239, 68, 68, 0.5)'}, {offset: 1, color: 'rgba(239, 68, 68, 0)'}]) } }] })
const getHeatmapOption = () => ({ grid: { left: '20%', right: '5%', top: '5%', bottom: '15%' }, xAxis: { type: 'category', data: ['Pb', 'As', 'Cd', 'Hg', 'Cr'] }, yAxis: { type: 'category', data: ['神经系统', '泌尿系统', '骨骼系统'] }, visualMap: { min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%', inRange: { color: ['#10B981', '#F59E0B', '#EF4444'] }, show: false }, series: [{ name: 'Damage', type: 'heatmap', data: [[0,0,95], [1,0,80], [2,0,20], [3,0,10], [4,0,15], [0,1,30], [1,1,40], [2,1,85], [3,1,20], [4,1,10], [0,2,60], [1,2,30], [2,2,50], [3,2,10], [4,2,5]], label: { show: true } }] })
const getSankeyOption = () => ({ series: [{ type: 'sankey', layout: 'none', focusNodeAdjacency: true, data: [{name:'Pb暴露'}, {name:'As暴露'}, {name:'Cd暴露'}, {name:'血脑屏障异常'}, {name:'肾小管应激'}, {name:'神经退行性病变'}, {name:'慢性肾病'}], links: [ {source:'Pb暴露', target:'血脑屏障异常', value:5}, {source:'As暴露', target:'血脑屏障异常', value:3}, {source:'Cd暴露', target:'肾小管应激', value:4}, {source:'血脑屏障异常', target:'神经退行性病变', value:8}, {source:'肾小管应激', target:'慢性肾病', value:4} ], lineStyle: { color: 'source', curveness: 0.5, opacity: 0.4 } }] })

const initReportCharts = () => {
  clearCharts()
  if(reportGaugeRef.value) { const c = echarts.init(reportGaugeRef.value); c.setOption(getGaugeOption()); chartsInstances.push(c) }
  if(reportRadarRef.value) { const c = echarts.init(reportRadarRef.value); c.setOption(getRadarOption()); chartsInstances.push(c) }
  if(reportLineRef.value) { const c = echarts.init(reportLineRef.value); c.setOption(getLineOption()); chartsInstances.push(c) }
  if(reportHeatmapRef.value) { const c = echarts.init(reportHeatmapRef.value); c.setOption(getHeatmapOption()); chartsInstances.push(c) }
  if(reportSankeyRef.value) { const c = echarts.init(reportSankeyRef.value); c.setOption(getSankeyOption()); chartsInstances.push(c) }
}

const resizeCharts = () => { chartsInstances.forEach(c => c.resize()) }
onMounted(() => { 
  nextTick(() => { initReportCharts() })
  window.addEventListener('resize', resizeCharts) 
})
onBeforeUnmount(() => { 
  window.removeEventListener('resize', resizeCharts)
  clearCharts()
})
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
</style>