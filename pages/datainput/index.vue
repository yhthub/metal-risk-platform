<template>
  <div class="system-layout">

  <Sidebar default-active="1-1" />

    <main class="main-content">
     <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToHome">
            <el-icon class="back-icon">
              <ArrowLeft />
            </el-icon>
            <span class="back-text">系统首页</span>
            <span class="divider">|</span>
            <span class="page-title-top">职业暴露数据接入与特征工程</span>
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
          <div class="step" :class="{ 'active': currentStep >= 1 }"><span class="step-num">1</span> 数据接入配置</div>
          <div class="step-line" :class="{ 'active-line': currentStep >= 2 }"></div>
          <div class="step" :class="{ 'active': currentStep >= 2 }"><span class="step-num">2</span> 多维可视化分析</div>
          <div class="step-line" :class="{ 'active-line': currentStep >= 3 }"></div>
          <div class="step pending"><span class="step-num">3</span> 风险推理模型</div>
        </div>

        <div class="input-dashboard">
          <div class="panel-card clean-clinical-card">
            <div class="card-layout-grid">
              <div class="form-entry-area">
                <div class="config-row">
                  <div class="config-group flex-2">
                    <label>目标监测工种</label>
                    <div class="radio-cards">
                      <div class="radio-card" :class="{'selected': formData.job === 'smelting'}" @click="formData.job = 'smelting'">冶炼工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'mining'}" @click="formData.job = 'mining'">采矿工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'welding'}" @click="formData.job = 'welding'">电焊工</div>
                      <div class="radio-card" :class="{'selected': formData.job === 'other'}" @click="formData.job = 'other'">其他</div>
                    </div>
                  </div>
                  <div class="config-group flex-1">
                    <label>数据录入模式</label>
                    <div class="mode-switch">
                      <button :class="{'active': formData.mode === 'single'}" @click="handleModeChange('single')">单人录入</button>
                      <button :class="{'active': formData.mode === 'batch'}" @click="handleModeChange('batch')">群体导入</button>
                    </div>
                  </div>
                </div>

                <div class="clinical-divider"></div>

                <div class="input-mode-section" v-if="formData.mode === 'single'">
                  <div class="form-section">
                    <h4 class="section-title">基础个体档案</h4>
                    <div class="clinical-input-grid cols-4">
                      <div class="clinical-input-item"><span class="label">Name / ID</span><div class="input-wrap"><input type="text" v-model="formData.singleData.name" placeholder="ID: SZ-102" /></div></div>
                      <div class="clinical-input-item"><span class="label">Gender</span><div class="input-wrap select-wrap"><select v-model="formData.singleData.gender"><option value="male">Male</option><option value="female">Female</option></select></div></div>
                      <div class="clinical-input-item"><span class="label">Age</span><div class="input-wrap"><input type="number" v-model="formData.singleData.age" placeholder="0" /><span class="unit">Y</span></div></div>
                      <div class="clinical-input-item"><span class="label">Exposure Years</span><div class="input-wrap"><input type="number" v-model="formData.singleData.workYears" placeholder="0" /><span class="unit">Y</span></div></div>
                    </div>
                  </div>

                  <div class="form-section">
                    <h4 class="section-title">核心重金属暴露指标 (8种)</h4>
                    <div class="clinical-input-grid cols-4">
                      <div class="clinical-input-item"><span class="label">Pb (铅)</span><div class="input-wrap" :class="{'is-error': formData.singleData.pb > 400}"><input type="number" v-model="formData.singleData.pb" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Cd (镉)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.cd" placeholder="0.00" /><span class="unit">μg/g</span></div></div>
                      <div class="clinical-input-item"><span class="label">Hg (汞)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.hg" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Th (钍)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.th" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Li (锂)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.li" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Cr (铬)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.cr" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Ni (镍)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.ni" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                      <div class="clinical-input-item"><span class="label">Co (钴)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.co" placeholder="0.00" /><span class="unit">μg/L</span></div></div>
                    </div>
                  </div>

                  <div class="form-section">
                    <h4 class="section-title">伴生非金属与标志物</h4>
                    <div class="clinical-input-grid cols-3">
                      <div class="clinical-input-item"><span class="label">As (砷)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.as" placeholder="0.00" /><span class="unit">μg/g</span></div></div>
                      <div class="clinical-input-item"><span class="label">Rn (氡)</span><div class="input-wrap"><input type="number" v-model="formData.singleData.rn" placeholder="0.00" /><span class="unit">Bq/m³</span></div></div>
                      <div class="clinical-input-item upload-addon">
                        <span class="label">Attachment</span>
                        <button class="btn-mini-upload"><el-icon><Upload /></el-icon> 导入LIS体检报告</button>
                      </div>
                    </div>
                  </div>
                </div>

                <div class="input-mode-section" v-if="formData.mode === 'batch'">
                  <div class="upload-dragger" :class="{'has-file': hasFile}">
                    <el-icon class="upload-icon"><DocumentAdd /></el-icon>
                    <div v-if="!hasFile">
                      <div class="upload-text">拖拽群体监测数据至此 (支持 .csv / .xlsx)</div>
                      <div class="upload-hint">需包含：工号及 Pb, Cd, Hg, Th, Li, Cr, Ni, Co, As, Rn 等暴露特征列</div>
                      <button class="btn-upload" @click="simulateFileUpload">选择本地文件</button>
                    </div>
                    <div v-else class="file-success">
                      <div class="upload-text"><el-icon style="vertical-align: middle; margin-right: 6px;"><DocumentChecked/></el-icon> 第一熔炼车间_全体环境与生物监测表.csv</div>
                      <div class="upload-hint success-text">成功解析 1,245 条样本特征数据，特征维度完整。</div>
                      <button class="btn-upload btn-reupload" @click="hasFile = false">重新上传</button>
                    </div>
                  </div>
                </div>
              </div>

              <div class="reference-sidebar">
                <div class="ref-card">
                  <h4><el-icon><InfoFilled /></el-icon> 临床监测基线参考</h4>
                  <p class="ref-desc">基于职业卫生标准的安全阈值区间，为特征评估提供基线依据：</p>
                  <ul class="ref-list">
                    <li><span class="metal">Pb (铅)</span><span class="range">&lt; 100 μg/L</span></li>
                    <li><span class="metal">Cd (镉)</span><span class="range">&lt; 5.0 μg/g</span></li>
                    <li><span class="metal">Hg (汞)</span><span class="range">&lt; 10.0 μg/L</span></li>
                    <li><span class="metal">Th (钍)</span><span class="range">&lt; 0.1 μg/L</span></li>
                    <li><span class="metal">Li (锂)</span><span class="range">&lt; 1.0 μg/L</span></li>
                    <li><span class="metal">Cr (铬)</span><span class="range">&lt; 5.0 μg/L</span></li>
                    <li><span class="metal">Ni (镍)</span><span class="range">&lt; 3.0 μg/L</span></li>
                    <li><span class="metal">Co (钴)</span><span class="range">&lt; 2.0 μg/L</span></li>
                    <li><span class="metal">As (砷)</span><span class="range">&lt; 35.0 μg/g</span></li>
                    <li><span class="metal">Rn (氡)</span><span class="range">&lt; 50 Bq/m³</span></li>
                  </ul>
                </div>
                
                <div class="action-card">
                  <h4>生成评估画像</h4>
                  <p>将录入特征推入后端模型，执行清洗、标准化与特征分析。</p>
                  <button class="btn-analyze" :class="{'is-loading': isAnalyzing}" @click="runAnalysis">
                    <span v-if="!isAnalyzing">启动特征可视化分析 ➔</span>
                    <span v-else>数据提取与处理中...</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="visualization-dashboard" v-if="showDashboard">
          
          <div v-if="formData.mode === 'batch'" class="batch-dashboard-container animate-on-scroll is-visible">
            
            <div class="kpi-row">
              <div class="kpi-card total"><el-icon class="kpi-icon"><Avatar /></el-icon><div class="kpi-info"><span>总提取解析人数</span><strong>1,245<small> 人</small></strong></div></div>
              <div class="kpi-card male"><el-icon class="kpi-icon"><Male /></el-icon><div class="kpi-info"><span>男性占比</span><strong>856<small> 人 (68.7%)</small></strong></div></div>
              <div class="kpi-card female"><el-icon class="kpi-icon"><Female /></el-icon><div class="kpi-info"><span>女性占比</span><strong>389<small> 人 (31.3%)</small></strong></div></div>
              <div class="kpi-card risk"><el-icon class="kpi-icon"><WarningFilled /></el-icon><div class="kpi-info"><span>触发高危预警人数</span><strong class="text-danger">142<small> 人</small></strong></div></div>
            </div>

            <div class="batch-charts-grid">
              <div class="b-chart-card col-span-2">
                <div class="b-c-header"><h4>群体样本暴露工龄序列特征分析</h4><span class="sub-title">按个体暴露时间(年)升序排列，展示体内核心重金属蓄积趋势</span></div>
                <div id="batchChartSeq" class="b-c-canvas"></div>
              </div>
              <div class="b-chart-card col-span-1">
                <div class="b-c-header"><h4>群体综合靶器官风险评级占比</h4><span class="sub-title">系统 AHP 模型自动定级分布</span></div>
                <div id="batchChartRiskPie" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header"><h4>人群年龄结构与性别分布</h4><span class="sub-title">多维度劳动力画像</span></div>
                <div id="batchChartAgeRose" class="b-c-canvas"></div>
              </div>
              <div class="b-chart-card col-span-1">
                <div class="b-c-header"><h4>车间特征均值 vs 国家基线</h4><span class="sub-title">雷达图覆盖暴露面</span></div>
                <div id="batchChartRadar" class="b-c-canvas"></div>
              </div>
              <div class="b-chart-card col-span-1">
                <div class="b-c-header"><h4>致病因子超标率排行 (%)</h4><span class="sub-title">车间核心危险源溯源</span></div>
                <div id="batchChartExceed" class="b-c-canvas"></div>
              </div>
            </div>
          </div>

          <div v-else class="single-dashboard-container">
            <div class="chart-card main-master-chart animate-on-scroll is-visible">
              <div class="chart-title-wrap">
                <div class="title-left">
                  <h4>个体多金属暴露综合评估画像</h4>
                  <p>各项指标绝对浓度已转换为基于临床安全阈值的相对暴露指数 (%)</p>
                </div>
                <div class="filter-legend">
                  <span :class="{'active': activeFilter === 'all' || activeFilter === 'safe', 'dimmed': activeFilter !== 'all' && activeFilter !== 'safe'}" @click="toggleFilter('safe')"><i class="dot safe"></i>正常 (&lt;50%)</span>
                  <span :class="{'active': activeFilter === 'all' || activeFilter === 'warn', 'dimmed': activeFilter !== 'all' && activeFilter !== 'warn'}" @click="toggleFilter('warn')"><i class="dot warn"></i>预警 (50%-100%)</span>
                  <span :class="{'active': activeFilter === 'all' || activeFilter === 'danger', 'dimmed': activeFilter !== 'all' && activeFilter !== 'danger'}" @click="toggleFilter('danger')"><i class="dot danger"></i>危险超标 (&gt;100%)</span>
                  <span class="reset-filter" v-if="activeFilter !== 'all'" @click="activeFilter = 'all'">[重置]</span>
                </div>
              </div>
              
              <div class="chart-content master-bar-chart">
                <div class="axis-y-label">相对暴露指数 (%)</div>
                <div class="axis-y"><span>150%</span><span>100%</span><span>50%</span><span>0</span></div>
                <div class="threshold-line danger-line" style="bottom: 66.6%"><span>100% 危险超标线</span></div>
                <div class="threshold-line warn-line" style="bottom: 33.3%"><span>50% 早期预警线</span></div>
                
                <div class="bars-container">
                  <div class="master-bar-item" v-for="m in metalsData" :key="m.id" :class="['status-' + m.status, {'dimmed-bar': activeFilter !== 'all' && activeFilter !== m.status}]">
                    <div class="bar-val-static">{{ m.value }}%</div>
                    <div class="bar-track"><div class="bar-fill" :style="{ height: Math.min((m.value / 150 * 100), 100) + '%' }"></div></div>
                    <span class="bar-label">{{ m.symbol }}<span class="cn">{{ m.name }}</span></span>
                    
                    <div class="hover-detail-box">
                      <div class="h-head" :class="'bg-' + m.status">
                        <strong>{{ m.symbol }} ({{ m.name }})</strong>
                        <span class="badge">{{ m.status === 'danger' ? '危险超标' : m.status === 'warn' ? '临界预警' : '健康正常' }}</span>
                      </div>
                      <div class="h-body">
                        <p>相对指数：<strong>{{ m.value }}%</strong></p>
                        <p>实际浓度：{{ m.raw }}{{ m.unit }}</p>
                        <p class="h-risk">临床风险：{{ m.risk }}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="sub-charts-grid animate-on-scroll is-visible">
              <div class="chart-card col-span-1">
                <h4>核心元素密度分布图</h4>
                <div class="chart-content distribution-chart">
                  <div class="dist-layer layer-pb"></div><div class="dist-layer layer-cd"></div><div class="dist-layer layer-hg"></div>
                  <div class="axis-x"></div>
                  <div class="chart-legend"><span class="c-pb">Pb</span><span class="c-cd">Cd</span><span class="c-hg">Hg</span></div>
                </div>
              </div>
              <div class="chart-card col-span-1" style="min-width: 0; overflow: hidden;">
                <h4>历史监测时间序列趋势</h4>
                <div class="chart-content line-trend-chart" style="display: block; width: 100%; height: 220px; padding-top: 15px;">
                  <svg width="100%" height="100%" viewBox="0 0 600 200" preserveAspectRatio="none" style="display: block; overflow: visible;">
                    <path class="trend-line line-danger" d="M10,180 Q100,140 200,90 T400,60 T580,20" fill="none" stroke="#F87171" stroke-width="3"/>
                    <path class="trend-line line-safe" d="M10,190 Q100,150 200,130 T400,110 T580,120" fill="none" stroke="#34D399" stroke-width="3"/>
                    <circle cx="200" cy="90" r="5" fill="#F87171"/><circle cx="400" cy="60" r="5" fill="#F87171"/><circle cx="580" cy="20" r="5" fill="#F87171"/>
                  </svg>
                </div>
              </div>
              <div class="chart-card col-span-1">
                <h4>特征相关性 (Pearson)</h4>
                <div class="chart-content heatmap-chart">
                  <div class="hm-grid">
                    <div class="hm-cell bg-high">Pb</div><div class="hm-cell bg-med">0.68</div><div class="hm-cell bg-low">0.21</div>
                    <div class="hm-cell bg-med">0.68</div><div class="hm-cell bg-high">Cd</div><div class="hm-cell bg-med-low">0.45</div>
                    <div class="hm-cell bg-low">0.21</div><div class="hm-cell bg-med-low">0.45</div><div class="hm-cell bg-high">Hg</div>
                  </div>
                </div>
              </div>
              <div class="chart-card col-span-1">
                <h4>总风险贡献结构占比</h4>
                <div class="chart-content pie-chart-area">
                  <div class="donut-chart"></div>
                  <div class="donut-center"><span class="val">高危</span><span class="lbl">综合评级</span></div>
                  <div class="pie-legend">
                    <div><span class="dot d-pb"></span>Pb (45%)</div>
                    <div><span class="dot d-as"></span>As (35%)</div>
                    <div><span class="dot d-cd"></span>Cd (20%)</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bottom-action-bar">
            <div class="tips">
              <el-icon><CircleCheckFilled /></el-icon>
              数据特征提取完毕，核心因子存在超标预警。请将特征矩阵推入 <strong>复合风险量化模型</strong> 获取具体报告。
            </div>
            <button class="btn-next-step" @click="goToRiskWarning">
              进入风险预警与因果推理控制台 ➔
            </button>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Coin, DataLine, TrendCharts, Share, DocumentChecked, Upload, DocumentAdd, 
  CircleCheckFilled, InfoFilled, ArrowLeft, Male, Female, Avatar, WarningFilled 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const currentStep = ref(1)

const formData = ref({
  job: 'smelting', mode: 'batch', 
  singleData: { 
    name: '', gender: 'male', age: null, workYears: null, 
    pb: 1.24, cd: 0.89, hg: 0.12, th: 0.05, li: 0.18, cr: 0.34, ni: 0.45, co: 0.11, as: 1.05, rn: 15.0 
  }
})

const hasFile = ref(true)
const isAnalyzing = ref(false)
const showDashboard = ref(false)

const activeFilter = ref('all')
const toggleFilter = (status) => { activeFilter.value = activeFilter.value === status ? 'all' : status }
const metalsData = ref([
  { id: 'pb', symbol: 'Pb', name: '铅', value: 124, raw: 1.24, unit: 'μg/L', status: 'danger', risk: '神经系统风险' },
  { id: 'cd', symbol: 'Cd', name: '镉', value: 89, raw: 0.89, unit: 'μg/g', status: 'warn', risk: '肾小管预警' },
  { id: 'hg', symbol: 'Hg', name: '汞', value: 24, raw: 0.12, unit: 'μg/L', status: 'safe', risk: '正常' },
  { id: 'th', symbol: 'Th', name: '钍', value: 12, raw: 0.05, unit: 'μg/L', status: 'safe', risk: '正常' },
  { id: 'li', symbol: 'Li', name: '锂', value: 18, raw: 0.18, unit: 'μg/L', status: 'safe', risk: '正常' },
  { id: 'cr', symbol: 'Cr', name: '铬', value: 34, raw: 0.34, unit: 'μg/L', status: 'safe', risk: '正常' },
  { id: 'ni', symbol: 'Ni', name: '镍', value: 65, raw: 0.45, unit: 'μg/L', status: 'warn', risk: '呼吸道预警' },
  { id: 'co', symbol: 'Co', name: '钴', value: 40, raw: 0.11, unit: 'μg/L', status: 'safe', risk: '正常' },
  { id: 'as', symbol: 'As', name: '砷', value: 105, raw: 1.05, unit: 'μg/g', status: 'danger', risk: '致癌风险' },
  { id: 'rn', symbol: 'Rn', name: '氡', value: 30, raw: 15.0, unit: 'Bq/m³', status: 'safe', risk: '正常' }
])

const handleModeChange = (mode) => {
  formData.value.mode = mode
  showDashboard.value = false 
}

const simulateFileUpload = () => { hasFile.value = true }

const runAnalysis = () => {
  if (formData.value.mode === 'batch' && !hasFile.value) {
    alert("请先上传群体数据文件！")
    return
  }
  isAnalyzing.value = true
  setTimeout(() => {
    isAnalyzing.value = false
    showDashboard.value = true
    currentStep.value = 2
    
    if (formData.value.mode === 'batch') {
      nextTick(() => {
        initBatchECharts()
        window.scrollTo({ top: 800, behavior: 'smooth' })
      })
    } else {
      setTimeout(() => { window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' }) }, 100)
    }
  }, 1200)
}

// ✨ 跳转到风险控制台
const goToRiskWarning = async () => { 
  currentStep.value = 3 
  await navigateTo('/risk') 
}

const goToHome = async () => {
  await navigateTo('/')
}

/* ==============================================
   初始化群体大盘 ECharts
   ============================================== */
let batchCharts = []

const initBatchECharts = () => {
  batchCharts.forEach(c => c.dispose())
  batchCharts = []

  const domSeq = document.getElementById('batchChartSeq')
  if (domSeq) {
    const chartSeq = echarts.init(domSeq)
    let xAxisData = []; let yearData = []; let pbData = []; let asData = [];
    for(let i=1; i<=100; i++) {
      xAxisData.push(`ID-${Math.floor(Math.random()*9000)+1000}`);
      yearData.push((i/100 * 25).toFixed(1)); 
      pbData.push((Math.pow(i/100, 1.5) * 180 + Math.random()*30).toFixed(1)); 
      asData.push((i/100 * 100 + Math.random()*20).toFixed(1));
    }

    chartSeq.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
      legend: { data: ['暴露工龄 (年)', 'Pb 浓度 (μg/L)', 'As 浓度 (μg/g)'], top: 0 },
      grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
      xAxis: { type: 'category', data: xAxisData, axisLabel: { show: false }, axisTick: { show: false } },
      yAxis: [
        { type: 'value', name: '重金属浓度', position: 'left', axisLine: {show: true} },
        { type: 'value', name: '暴露工龄', position: 'right', axisLine: {show: true}, max: 30, splitLine: {show: false} }
      ],
      series: [
        { name: '暴露工龄 (年)', type: 'line', yAxisIndex: 1, data: yearData, smooth: true, itemStyle: { color: '#9CA3AF' }, areaStyle: { color: 'rgba(156,163,175,0.1)'} },
        { name: 'Pb 浓度 (μg/L)', type: 'scatter', symbolSize: 6, data: pbData, itemStyle: { color: '#EF4444' } },
        { name: 'As 浓度 (μg/g)', type: 'scatter', symbolSize: 5, data: asData, itemStyle: { color: '#F59E0B' } }
      ]
    })
    batchCharts.push(chartSeq)
  }

  const domRisk = document.getElementById('batchChartRiskPie')
  if (domRisk) {
    const chartRisk = echarts.init(domRisk)
    chartRisk.setOption({
      tooltip: { trigger: 'item' },
      legend: { bottom: '0', left: 'center' },
      color: ['#10B981', '#F59E0B', '#EF4444'],
      series: [{
        name: '风险评级', type: 'pie', radius: ['45%', '75%'], center: ['50%', '42%'],
        itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
        label: { show: true, formatter: '{b}\n{d}%' },
        data: [ { value: 748, name: '健康安全' }, { value: 355, name: '临界预警' }, { value: 142, name: '危险超标' } ]
      }]
    })
    batchCharts.push(chartRisk)
  }

  const domAge = document.getElementById('batchChartAgeRose')
  if (domAge) {
    const chartAge = echarts.init(domAge)
    chartAge.setOption({
      tooltip: { trigger: 'item' },
      legend: { top: '5%', left: 'center' },
      series: [{
        name: '年龄分布', type: 'pie', radius: [20, 110], center: ['50%', '55%'], roseType: 'area',
        itemStyle: { borderRadius: 4 },
        data: [
          { value: 120, name: '18-25 男', itemStyle: {color: '#93C5FD'} },
          { value: 280, name: '26-35 男', itemStyle: {color: '#3B82F6'} },
          { value: 300, name: '36-45 男', itemStyle: {color: '#1D4ED8'} },
          { value: 156, name: '46+ 男', itemStyle: {color: '#1E3A8A'} },
          { value: 150, name: '26-35 女', itemStyle: {color: '#F472B6'} },
          { value: 239, name: '36-45 女', itemStyle: {color: '#DB2777'} }
        ]
      }]
    })
    batchCharts.push(chartAge)
  }

  const domRadar = document.getElementById('batchChartRadar')
  if (domRadar) {
    const chartRadar = echarts.init(domRadar)
    chartRadar.setOption({
      tooltip: {},
      legend: { bottom: 0 },
      radar: {
        indicator: [
          { name: 'Pb 均值', max: 150 }, { name: 'As 均值', max: 100 }, { name: 'Cd 均值', max: 10 },
          { name: 'Hg 均值', max: 20 }, { name: 'Cr 均值', max: 10 }, { name: 'Ni 均值', max: 10 }
        ]
      },
      series: [{
        name: '均值对比', type: 'radar',
        data: [
          { value: [85, 45, 6, 8, 4, 5], name: '群体样本均值', areaStyle: { color: 'rgba(59, 130, 246, 0.3)'}, lineStyle: {color: '#3B82F6'} },
          { value: [100, 35, 5, 10, 5, 3], name: '国家医学限值', lineStyle: {color: '#10B981', type: 'dashed'} }
        ]
      }]
    })
    batchCharts.push(chartRadar)
  }

  const domExceed = document.getElementById('batchChartExceed')
  if (domExceed) {
    const chartExceed = echarts.init(domExceed)
    chartExceed.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '10%', bottom: '5%', top: '5%', containLabel: true },
      xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' } },
      yAxis: { type: 'category', data: ['Hg(汞)', 'Ni(镍)', 'Cd(镉)', 'As(砷)', 'Pb(铅)'], axisLabel: {fontWeight: 'bold', fontSize: 13} },
      series: [{
        name: '群体超标率', type: 'bar', barWidth: '40%',
        label: { show: true, position: 'right', formatter: '{c}%', fontWeight: 'bold' },
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#EF4444' }, { offset: 1, color: '#FCA5A5' }
          ]),
          borderRadius: [0, 4, 4, 0]
        },
        data: [4.5, 12.3, 28.5, 41.2, 56.8]
      }]
    })
    batchCharts.push(chartExceed)
  }
}

onMounted(() => {
  window.addEventListener('resize', () => { batchCharts.forEach(c => c.resize()) })
})
</script>

<style lang="scss" scoped>
@use "sass:color";
/* 🛡️ 针对 Tailwind CSS 的 SVG 无限放大防御补丁，去掉原生 svg，防止误伤折线图 */
:deep(.el-icon svg) {
  max-width: 1em;
  max-height: 1em;
  width: 1em;
  height: 1em;
}
$color-primary: #1f77b4;
$color-primary-light: #EFF6FF;
$color-bg: #F1F5F9; 
$text-main: #111827;
$text-muted: #6B7280;
$border-color: #E2E8F0;

$color-safe: #34D399;   
$color-warn: #FBBF24;   
$color-danger: #F87171; 
* { box-sizing: border-box; }

.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }

/* ==========================================
   全新优化的侧边栏
   ========================================== */
.sidebar { 
  width: 280px; background-color: #fff; border-right: 1px solid $border-color; 
  display: flex; flex-direction: column; z-index: 10; flex-shrink: 0; box-shadow: 2px 0 15px rgba(0,0,0,0.03);
}
.brand-logo { 
  height: 70px; display: flex; align-items: center; gap: 14px; padding: 0 24px; border-bottom: 1px solid $border-color; 
  svg { width: 30px; height: 30px; color: $color-primary; flex-shrink: 0; }
  .brand-text { display: flex; flex-direction: column; }
  .title-en { font-size: 1.1rem; font-weight: 900; color: #1E3A8A; letter-spacing: -0.5px;}
  .title-cn { font-size: 0.8rem; font-weight: 600; color: #64748B; letter-spacing: 1px; margin-top: 2px;}
}
.menu-container { 
  overflow-y: auto; flex: 1; padding: 16px 0;
  :deep(.custom-el-menu) {
    border-right: none;
    .menu-group-title { font-size: 0.85rem; font-weight: 800; color: #94A3B8; padding: 24px 24px 10px 24px; letter-spacing: 1px;}
    .el-sub-menu__title, .el-menu-item { font-weight: 600; color: #475569; font-size: 1.05rem; margin: 6px 12px; border-radius: 8px; height: 50px; line-height: 50px;}
    .el-sub-menu__title:hover, .el-menu-item:hover { background-color: #F8FAFC; color: $color-primary; }
    .el-menu-item.is-active { background-color: $color-primary-light; color: $color-primary; font-weight: 700;}
    .el-icon { font-size: 1.3rem; margin-right: 12px; color: #64748B; }
    .is-active > .el-icon { color: $color-primary; }
    .el-sub-menu .el-menu-item { min-width: auto; padding-left: 55px !important; font-size: 0.95rem; font-weight: 500;}
  }
}

.main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; scroll-behavior: smooth; background: #F8FAFC;}

/* ✨ 修复：强化顶部导航的横向不换行布局 */
.ep-header { 
  height: 64px; /* 稍微增加高度增加呼吸感 */
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
  flex-direction: row !important; /* 强制横向 */
  flex-wrap: nowrap !important; /* 强制不换行 */
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
  &:hover { color: $color-primary; } 
  .back-icon { font-size: 1.2rem; font-weight: bold;} 
  .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px;} 
  .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; } 
  .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-main; } 
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
  white-space: nowrap; /* 绝对禁止换行 */
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

.page-container { padding: 40px; max-width: 1400px; margin: 0 auto; width: 100%; padding-bottom: 100px; }

/* 进度条 */
.pipeline-steps { display: flex; align-items: center; margin-bottom: 30px; background: transparent; padding: 0; border: none; .step { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; color: $text-muted; .step-num { width: 24px; height: 24px; border-radius: 50%; background: #E5E7EB; display: flex; justify-content: center; align-items: center; font-size: 0.85rem; } &.active { color: $color-primary; .step-num { background: $color-primary; color: #FFF; } } } .step-line { flex: 1; height: 2px; background: #E5E7EB; margin: 0 16px; position: relative; transition: 0.3s; &.active-line { background: $color-primary; } } }

/* 表单区域 */
.clean-clinical-card { background: #fff; border-radius: 12px; border: 1px solid $border-color; box-shadow: 0 4px 15px rgba(0,0,0,0.03); overflow: hidden; margin-bottom: 40px; }
.card-layout-grid { display: flex; min-height: 400px; }
.form-entry-area { flex: 2.2; padding: 40px; border-right: 1px solid $border-color; }
.reference-sidebar { flex: 1; background: #F8FAFC; padding: 40px 30px; display: flex; flex-direction: column; justify-content: space-between; }

.config-row { display: flex; gap: 40px; label { display: block; font-size: 0.95rem; font-weight: 700; color: $text-main; margin-bottom: 12px; } }
.flex-2 { flex: 2; } .flex-1 { flex: 1; }
.radio-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.radio-card { background: #fff; border: 1px solid #D1D5DB; padding: 10px; text-align: center; border-radius: 6px; font-weight: 600; color: $text-main; cursor: pointer; transition: all 0.2s; &:hover { border-color: $color-primary; } &.selected { background: #EFF6FF; border-color: $color-primary; color: $color-primary; } }
.mode-switch { display: flex; background: #F1F5F9; border-radius: 6px; padding: 4px; button { flex: 1; padding: 8px; border: none; background: transparent; border-radius: 4px; font-weight: 600; color: $text-muted; cursor: pointer; transition: 0.3s; &.active { background: #fff; color: $color-primary; box-shadow: 0 2px 4px rgba(0,0,0,0.05); } } }
.clinical-divider { border: 0; height: 1px; background: $border-color; margin: 30px 0; }

.form-section { margin-bottom: 30px; }
.section-title { font-size: 1.05rem; font-weight: 700; color: $text-main; border-left: 4px solid $color-primary; padding-left: 10px; margin-bottom: 20px; }
.clinical-input-grid { display: grid; gap: 16px; }
.cols-4 { grid-template-columns: repeat(4, 1fr); } 
.cols-3 { grid-template-columns: repeat(3, 1fr); } 

.clinical-input-item { 
  display: flex; flex-direction: column; gap: 8px; 
  .label { font-size: 0.9rem; font-weight: 600; color: $text-main; } 
  .input-wrap { 
    display: flex; align-items: center; border: 1px solid #D1D5DB; border-radius: 6px; background: #fff; transition: 0.2s;
    &:focus-within { border-color: $color-primary; box-shadow: 0 0 0 2px #EFF6FF; }
    &.is-error { border-color: $color-danger; background: #FEF2F2; color: $color-danger;}
    input, select { flex: 1; width: 100%; padding: 8px 12px; border: none; font-size: 0.95rem; outline: none; background: transparent; color: $text-main; font-weight: 500;}
    .unit { padding: 0 10px; color: #9CA3AF; font-size: 0.85rem; font-weight: 500; background: #F8FAFC; border-left: 1px solid $border-color; height: 100%; display: flex; align-items: center; }
  }
}

.upload-addon .btn-mini-upload { 
  height: 100%; width: 100%; background: #EFF6FF; border: 1px dashed #60A5FA; border-radius: 6px; 
  color: $color-primary; font-weight: 600; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;
  &:hover { border-color: $color-primary; background: $color-primary; color: #fff;} 
}

.upload-dragger { border: 2px dashed #CBD5E1; border-radius: 12px; padding: 60px; text-align: center; background: #F8FAFC; cursor: pointer; transition: all 0.3s; &:hover { border-color: $color-primary; background: #EFF6FF; } &.has-file { border-color: $color-safe; background: #ecfdf5; } .upload-icon { font-size: 2.5rem; color: #94A3B8; margin-bottom: 16px; } .upload-text { font-size: 1.1rem; font-weight: 700; color: $text-main; margin-bottom: 8px; } .upload-hint { font-size: 0.95rem; color: $text-muted; margin-bottom: 24px; &.success-text { color: #059669; } } .btn-upload { background: #fff; border: 1px solid $border-color; padding: 10px 24px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.95rem; color: $text-main; &.btn-reupload{ border-color: $color-safe; color: #059669;} } }

.reference-sidebar {
  .ref-card {
    h4 { margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px; font-size: 1.05rem; font-weight: 800; color: $text-main; .el-icon { color: $color-primary; } }
    .ref-desc { font-size: 0.85rem; color: $text-muted; line-height: 1.5; margin-bottom: 16px; }
    .ref-list { list-style: none; padding: 0; margin: 0; li { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px dashed #E2E8F0; font-size: 0.9rem; } .metal { font-weight: 700; color: $text-main; } .range { color: $color-safe; font-weight: 700; font-family: monospace; } }
  }
  .action-card {
    background: #fff; padding: 24px; border-radius: 12px; border: 1px solid $border-color; margin-top: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    h4 { margin: 0 0 8px 0; font-size: 1.05rem; font-weight: 800; color: $text-main;}
    p { font-size: 0.9rem; color: $text-muted; margin: 0 0 20px 0; line-height: 1.5;}
    .btn-analyze { width: 100%; background: $text-main; color: #fff; border: none; padding: 14px; border-radius: 8px; font-size: 1.05rem; font-weight: 700; cursor: pointer; transition: 0.3s; &:hover { background: $color-primary; transform: translateY(-2px); box-shadow: 0 8px 16px rgba(31,119,180,0.2); } &.is-loading { background: #9CA3AF; cursor: wait; transform: none; box-shadow: none; } }
  }
}

.visualization-dashboard { animation: slideUp 0.5s ease-out forwards; margin-top: 20px;}
@keyframes slideUp { from { opacity: 0; transform: translateY(40px); } to { opacity: 1; transform: translateY(0); } }

.kpi-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px; }
.kpi-card { 
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 20px; display: flex; align-items: center; gap: 16px; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  .kpi-icon { font-size: 2.5rem; padding: 12px; border-radius: 12px; }
  &.total .kpi-icon { background: #EFF6FF; color: #3B82F6; }
  &.male .kpi-icon { background: #F0FDF4; color: #10B981; }
  &.female .kpi-icon { background: #FDF2F8; color: #EC4899; }
  &.risk .kpi-icon { background: #FEF2F2; color: #EF4444; }
  .kpi-info { display: flex; flex-direction: column; span { font-size: 0.85rem; color: $text-muted; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;} strong { font-size: 1.8rem; font-weight: 900; color: $text-main; small { font-size: 0.9rem; color: #94A3B8; font-weight: 600;}} .text-danger { color: #EF4444; } }
}

.batch-charts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 40px; }
.b-chart-card { 
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column;
  .b-c-header { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #F1F5F9; h4 { margin: 0; font-size: 1.05rem; font-weight: 800; color: $text-main; } .sub-title { font-size: 0.85rem; color: $text-muted; margin-top: 6px; display: block;} }
  .b-c-canvas { flex: 1; min-height: 280px; width: 100%; }
}
.col-span-2 { grid-column: span 2; }
.col-span-1 { grid-column: span 1; }

.chart-card { background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); h4 { margin: 0 0 16px 0; font-size: 1.05rem; font-weight: 700; color: $text-main; } }

.main-master-chart { 
  margin-bottom: 30px; width: 100%; padding: 40px; box-sizing: border-box;
  .chart-title-wrap { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 50px; .title-left h4 { margin: 0 0 8px 0; font-size: 1.5rem; font-weight: 800; color: $text-main;} p { margin: 0; font-size: 0.95rem; color: $text-muted; line-height: 1.5;} }
  .filter-legend { display: flex; gap: 16px; font-size: 0.9rem; font-weight: 600; span { display: flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 20px; cursor: pointer; transition: 0.2s; &:hover { background: #F3F4F6; } &.dimmed { opacity: 0.4; } } .dot { width: 10px; height: 10px; border-radius: 50%; } .safe{background:$color-safe;} .warn{background:$color-warn;} .danger{background:$color-danger;} .reset-filter { color: $color-primary; font-weight: 700; background: transparent; &:hover { background: transparent; text-decoration: underline; } } }
}

.master-bar-chart {
  height: 500px; width: 100%; display: flex; align-items: flex-end; padding-left: 60px; position: relative; box-sizing: border-box;
  .axis-y-label { position: absolute; left: 0; top: -30px; font-size: 0.9rem; font-weight: 600; color: $text-muted;}
  .axis-y { position: absolute; left: 10px; top: 0; height: 100%; width: 40px; display: flex; flex-direction: column; justify-content: space-between; align-items: flex-end; color: #9CA3AF; font-size: 0.9rem; font-weight: 600; font-family: monospace; padding-bottom: 25px; }
  .threshold-line { position: absolute; left: 50px; right: 0; height: 1px; border-top: 2px dashed; z-index: 0; pointer-events: none; span { position: absolute; right: 0; top: -26px; font-size: 0.85rem; font-weight: 700; padding: 4px 10px; border-radius: 4px; } }
  .danger-line { border-color: $color-danger; span { background: #FEF2F2; color: $color-danger; } }
  .warn-line { border-color: $color-warn; span { background: #FFFBEB; color: $color-warn; } }

  .bars-container { width: 100%; height: 100%; display: flex; justify-content: space-around; align-items: flex-end; border-bottom: 2px solid #D1D5DB; position: relative; z-index: 1; padding: 0 20px;}
  .master-bar-item {
    display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end; width: 6.5%; position: relative; transition: opacity 0.3s;
    &.dimmed-bar { opacity: 0.15; }
    .bar-val-static { font-size: 1rem; font-weight: 800; margin-bottom: 8px; transition: transform 0.3s; }
    .bar-track { width: 100%; height: 100%; display: flex; align-items: flex-end; background: transparent; border-radius: 6px 6px 0 0;}
    .bar-fill { width: 100%; border-radius: 6px 6px 0 0; transition: height 1s cubic-bezier(0.16, 1, 0.3, 1); }
    .bar-label { margin-top: 12px; font-weight: 800; font-size: 1.1rem; color: $text-main; display: flex; flex-direction: column; align-items: center; .cn { font-size: 0.8rem; font-weight: 500; color: $text-muted; margin-top: 2px;} }
    
    &.status-safe { .bar-val-static{color: $color-safe;} .bar-fill { background: linear-gradient(to top, #6EE7B7, #34D399); border: 1px solid #10B981; border-bottom: none;} }
    &.status-warn { .bar-val-static{color: $color-warn;} .bar-fill { background: linear-gradient(to top, #FCD34D, #FBBF24); border: 1px solid #F59E0B; border-bottom: none;} }
    &.status-danger { .bar-val-static{color: $color-danger;} .bar-fill { background: linear-gradient(to top, #FCA5A5, #F87171); border: 1px solid #EF4444; border-bottom: none; box-shadow: 0 -4px 15px rgba(239, 68, 68, 0.25); } }

    .hover-detail-box {
      position: absolute; bottom: calc(100% + 15px); left: 50%; transform: translateX(-50%) translateY(10px);
      width: 200px; background: #fff; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.15); opacity: 0; visibility: hidden; transition: all 0.2s; z-index: 100; pointer-events: none;
      .h-head { padding: 10px 12px; border-radius: 8px 8px 0 0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem; color: #fff; .badge{ background: rgba(255,255,255,0.2); padding: 2px 6px; border-radius: 4px; font-size: 0.75rem;} }
      .bg-safe { background: $color-safe; } .bg-warn { background: $color-warn; } .bg-danger { background: $color-danger; }
      .h-body { padding: 12px; p { margin: 0 0 6px 0; font-size: 0.85rem; color: $text-muted; } strong { color: $text-main; font-size: 1rem;} .h-risk { margin-top: 8px; padding-top: 8px; border-top: 1px dashed #E5E7EB; line-height: 1.4; color: $text-main; font-weight: 500;} }
      &::after { content:''; position: absolute; bottom: -6px; left: 50%; transform: translateX(-50%); border-left: 6px solid transparent; border-right: 6px solid transparent; border-top: 6px solid #fff; }
    }
    &:hover .hover-detail-box { opacity: 1; visibility: visible; transform: translateX(-50%) translateY(0); }
    &:hover .bar-val-static { transform: translateY(-5px); }
  }
}

.sub-charts-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 24px; margin-bottom: 40px; }
.chart-content { height: 280px; position: relative; display: flex; justify-content: center; align-items: center;}

.distribution-chart { width: 100%; align-items: flex-end; overflow: hidden; padding-bottom: 20px; }
.dist-layer { position: absolute; bottom: 20px; width: 120%; height: 100px; border-radius: 50% 50% 0 0 / 100% 100% 0 0; mix-blend-mode: multiply; }
.layer-pb { left: -10%; background: rgba(248, 113, 113, 0.4); height: 180px; transform: scaleX(0.6); }
.layer-cd { left: 10%; background: rgba(251, 191, 36, 0.4); height: 200px; transform: scaleX(0.7); }
.layer-hg { left: 30%; background: rgba(52, 211, 153, 0.4); height: 150px; transform: scaleX(0.8); }
.axis-x { position: absolute; bottom: 18px; width: 100%; height: 2px; background: $border-color; }
.chart-legend { position: absolute; top: 10px; right: 20px; display: flex; gap: 12px; font-size: 0.85rem; font-weight: 600; span { display: flex; align-items: center; gap: 4px; &::before { content:''; width:12px; height:12px; border-radius:2px;} } .c-pb::before{background:rgba(248,113,113,0.6);} .c-cd::before{background:rgba(251,191,36,0.6);} .c-hg::before{background:rgba(52,211,153,0.6);} }

.line-trend-chart { 
  display: block !important;
  width: 100%; 
  height: 100%;
  padding: 15px 20px 0 20px;
  svg { 
    display: block !important;
    width: 100% !important; 
    height: 220px !important;
    min-height: 220px !important;
    max-height: none !important; 
    max-width: none !important;
    overflow: visible;
  } 
  
  .trend-line { 
    stroke-dasharray: 800; 
    stroke-dashoffset: 0; 
    animation: lineGrow 2s ease-out forwards;
  } 
} 

@keyframes lineGrow { 
  from { stroke-dashoffset: 800; } 
  to { stroke-dashoffset: 0; } 
}

.heatmap-chart { width: 100%; padding: 10px; } .hm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 2px; width: 100%; height: 100%; } .hm-cell { display: flex; justify-content: center; align-items: center; font-size: 0.85rem; font-weight: 700; color: #fff; border-radius: 4px; } .bg-high { background: #3B82F6; } .bg-med { background: #93C5FD; } .bg-low { background: #DBEAFE; color: #1E3A8A; } .bg-med-low { background: #BFDBFE; color: #1E3A8A; }

.pie-chart-area { display: flex; justify-content: space-around; align-items: center; width: 100%; padding: 0 20px; }
.donut-chart { width: 180px; height: 180px; border-radius: 50%; background: conic-gradient(#F87171 0% 45%, #FBBF24 45% 80%, #34D399 80% 100%); position: relative; }
.donut-center { position: absolute; left: 50%; top: 50%; width: 130px; height: 130px; background: #fff; border-radius: 50%; transform: translate(-50%, -50%); display: flex; flex-direction: column; justify-content: center; align-items: center; .val { font-size: 1.5rem; font-weight: 800; color: $color-danger; } .lbl { font-size: 0.85rem; color: $text-muted; font-weight: 600;} }
.pie-legend { display: flex; flex-direction: column; gap: 14px; font-size: 1rem; font-weight: 600; color: $text-main; div { display: flex; align-items: center; gap: 8px; } .dot { width: 14px; height: 14px; border-radius: 50%; } .d-pb { background: #F87171; } .d-as { background: #FBBF24; } .d-cd { background: #34D399; } }


/* 底部操作条 */
.bottom-action-bar { display: flex; justify-content: space-between; align-items: center; background: #FFFFFF; padding: 24px 32px; border-radius: 12px; border: 1px solid $border-color; box-shadow: 0 4px 20px -5px rgba(0,0,0,0.05); .tips { display: flex; align-items: center; gap: 8px; color: $text-muted; font-size: 1rem; .el-icon { color: $color-primary; font-size: 1.4rem; } strong { color: $text-main; } } .btn-next-step { background: $color-primary; color: #FFFFFF; border: none; padding: 16px 32px; border-radius: 8px; font-size: 1.1rem; font-weight: 700; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3); &:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(31, 119, 180, 0.4); background: color.adjust($color-primary, $lightness: -5%); } } }

@media (max-width: 1200px) { .batch-charts-grid { grid-template-columns: 1fr 1fr; } .kpi-row { grid-template-columns: 1fr 1fr; } .sub-charts-grid { grid-template-columns: 1fr; } .card-layout-grid { flex-direction: column; } .form-entry-area { border-right: none; border-bottom: 1px solid $border-color; } .clinical-input-grid { grid-template-columns: repeat(2, 1fr); } .bottom-action-bar { flex-direction: column; gap: 20px; align-items: stretch; .btn-next-step{ width: 100%; } } }
</style>