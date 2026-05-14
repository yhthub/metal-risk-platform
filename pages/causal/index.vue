<template>
  <div class="system-layout">
   <Sidebar default-active="4" />

    <main class="main-content">
     <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToWorkspace">
            <el-icon class="back-icon">
              <ArrowLeft />
            </el-icon>
            <span class="back-text">返回工作台</span>
            <span class="divider">|</span>
            <span class="page-title-top">因果知识推理</span>
          </div>

          <div class="ep-right-zone">
            <div class="user-profile">
              <div class="avatar">Dr.</div>
              <span>职业流行病学研究员</span>
            </div>
          </div>
        </div>
      </header>

      <div class="page-container">
        <div class="global-control-bar animate-on-scroll">
          <div class="control-group">
            <span class="control-label">暴露因子选择</span>
            <el-select v-model="selectedMetals" multiple placeholder="请选择重金属" size="large" clearable>
              <el-option v-for="m in metalOptions" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </div>
          
          <div class="control-group">
            <span class="control-label">目标疾病靶点</span>
            <el-select v-model="selectedDiseases" multiple placeholder="请选择疾病" size="large" clearable>
              <el-option v-for="d in diseaseOptions" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
          </div>
          
          <div class="control-group">
            <span class="control-label">群体暴露年限</span>
            <div class="slider-row">
              <el-slider v-model="exposureYears" :min="1" :max="30" :show-tooltip="false" class="control-slider" />
              <span class="slider-value">{{ exposureYears }}年</span>
            </div>
          </div>
          
          <div class="control-group">
            <span class="control-label">人群分组</span>
            <el-radio-group v-model="populationGroup" size="large">
              <el-radio-button value="adult">成人</el-radio-button>
              <el-radio-button value="child">儿童</el-radio-button>
              <el-radio-button value="elder">老人</el-radio-button>
            </el-radio-group>
          </div>

          <div class="control-actions">
            <el-button type="primary" size="large" @click="applyFilter">应用筛选</el-button>
            <el-button size="large" @click="resetFilter">重置</el-button>
          </div>
        </div>

        <div class="research-kpi-grid animate-on-scroll delay-1">
          <div class="r-kpi-card danger-level">
            <div class="kpi-icon danger">
               <el-icon><Warning /></el-icon>
            </div>
            <div class="kpi-info">
              <span class="kpi-tag">综合因果风险评分</span>
              <div class="flex-align">
                <strong class="kpi-val">{{ animatedRiskScore }}<small>%</small></strong>
                <el-tag effect="dark" :type="kpiData.riskTagType" size="small" class="ml-2">{{ kpiData.riskLevel }}</el-tag>
              </div>
              <span class="kpi-delta text-danger"><el-icon><TopRight /></el-icon> {{ kpiData.riskDesc }}</span>
            </div>
          </div>
          <div class="r-kpi-card">
            <div class="kpi-icon primary">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="kpi-info">
              <span class="kpi-tag">主导致病因子</span>
              <strong class="kpi-val">{{ kpiData.mainFactor }}</strong>
              <span class="kpi-delta text-muted">{{ kpiData.factorDesc }}</span>
            </div>
          </div>
          <div class="r-kpi-card">
            <div class="kpi-icon success">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="kpi-info">
              <span class="kpi-tag">推断置信度</span>
              <strong class="kpi-val text-primary">{{ kpiData.confidence }}<small>%</small></strong>
              <span class="kpi-delta text-safe"><el-icon><Select /></el-icon> {{ kpiData.confidenceDesc }}</span>
            </div>
          </div>
          <div class="r-kpi-card">
            <div class="kpi-icon warning">
              <el-icon><Timer /></el-icon>
            </div>
             <div class="kpi-info">
              <span class="kpi-tag">最优干预优先级</span>
              <strong class="kpi-val text-safe">{{ kpiData.interventionTier }}</strong>
              <span class="kpi-delta text-muted">{{ kpiData.interventionDesc }}</span>
            </div>
          </div>
        </div>

        <section class="core-dag-section animate-on-scroll delay-2">
          <div class="section-header">
            <div class="header-left">
              <div class="title-badge">核心分析</div>
              <h2 class="section-title">全景多模态复合暴露有向无环图</h2>
              <p class="section-desc">
                可视化10种重金属如何从日常接触，一步步影响身体器官，最终导致疾病的完整路径。<br>
                鼠标悬停查看详情，点击节点查看完整机制说明。
              </p>
            </div>
            <div class="header-info">
              <div class="info-card">
                <div class="info-icon"><el-icon><Document /></el-icon></div>
                <div class="info-text">
                  <div class="info-label">数据来源</div>
                  <div class="info-value">权威毒理研究数据库</div>
                </div>
              </div>
              <div class="info-card">
                <div class="info-icon"><el-icon><Clock /></el-icon></div>
                <div class="info-text">
                  <div class="info-label">更新时间</div>
                  <div class="info-value">2026-05-12</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="dag-viewport" 
               @wheel.prevent="handleZoom" 
               @mousedown="startPan" 
               @mousemove="doPan" 
               @mouseup="endPan" 
               @mouseleave="endPan"
               :class="{ 'is-panning': isPanning }">
            
            <div class="grid-bg"></div>
            
            <div class="floating-particles">
              <div v-for="i in 35" :key="i" class="particle" :style="particleStyle(i)"></div>
            </div>
            
            <div class="dag-canvas" ref="causalGraphRef" :style="{ transform: `translate(${panX}px, ${panY}px) scale(${zoom})` }"></div>
            
            <div class="floating-legend">
              <div class="legend-title">图例说明</div>
              <div class="l-row"><i class="node-dot exp"></i> 重金属暴露</div>
              <div class="l-row"><i class="node-dot mol"></i> 分子/病理机制</div>
              <div class="l-row"><i class="node-dot bio"></i> 生物组织损伤</div>
              <div class="l-row"><i class="node-dot dis"></i> 临床终末疾病</div>
              <div class="l-row"><i class="node-dot int"></i> 医疗干预措施</div>
            </div>
            
            <div class="zoom-controls">
              <el-button size="small" circle @click="zoomIn">
                <el-icon><ZoomIn /></el-icon>
              </el-button>
              <div class="zoom-level">{{ Math.round(zoom * 100) }}%</div>
              <el-button size="small" circle @click="zoomOut">
                <el-icon><ZoomOut /></el-icon>
              </el-button>
              <el-button size="small" circle @click="resetView">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </div>
        </section>

      <div class="single-chart-container animate-on-scroll delay-3">
          <div class="chart-card full-width-card">
            <div class="chart-header">
              <div class="header-left">
                <h3 class="chart-title">反事实因果推演沙盘</h3>
                <span class="chart-tag">数字孪生</span>
              </div>
              <p class="chart-desc">
                通过模拟降低特定金属暴露、开启抗氧化/螯合治疗，实时预测干预措施对健康风险的降低效果。
              </p>
            </div>

            <div class="what-if-panel">
              <div class="what-if-body">
                <div class="control-grid two-column">
                  <div class="ctrl-row">
                    <span class="c-label">Pb 铅暴露降低</span>
                    <div class="c-action"><el-slider v-model="simPb" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simPb }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">As 砷暴露降低</span>
                    <div class="c-action"><el-slider v-model="simAs" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simAs }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Cd 镉暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCd" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simCd }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Hg 汞暴露降低</span>
                    <div class="c-action"><el-slider v-model="simHg" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simHg }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Cr 铬暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCr" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simCr }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Ni 镍暴露降低</span>
                    <div class="c-action"><el-slider v-model="simNi" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simNi }}%</span>
                  </div>

                  <div class="ctrl-row">
                    <span class="c-label">Co 钴暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCo" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simCo }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Li 锂暴露降低</span>
                    <div class="c-action"><el-slider v-model="simLi" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simLi }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Al 铝暴露降低</span>
                    <div class="c-action"><el-slider v-model="simAl" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simAl }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Mn 锰暴露降低</span>
                    <div class="c-action"><el-slider v-model="simMn" :min="0" :max="100" class="sci-slider primary"
                        :show-tooltip="false" /></div>
                    <span class="c-val">{{ simMn }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">抗氧化干预治疗</span>
                    <div class="c-action"><el-switch v-model="simMed" active-color="#10B981" /></div>
                    <span class="c-val">{{ simMed ? '开启' : '关闭' }}</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">螯合治疗</span>
                    <div class="c-action"><el-switch v-model="simEDTA" active-color="#6366F1" /></div>
                    <span class="c-val">{{ simEDTA ? '开启' : '关闭' }}</span>
                  </div>
                </div>

                <div class="simulation-result enhanced">
                  <div class="sr-item base">
                    <span class="sr-label">当前基线风险</span>
                    <span class="sr-val">92.4<small>%</small></span>
                  </div>
                  <div class="sr-divider">
                    <el-icon>
                      <ArrowRight />
                    </el-icon>
                  </div>
                  <div class="sr-item pred">
                    <span class="sr-label">干预期望风险</span>
                    <span class="sr-val" :class="{ 'safe-text': simulatedRisk < 50 }">{{ simulatedRisk
                      }}<small>%</small></span>
                  </div>
                </div>

                <div class="gain-indicator enhanced">
                  量化干预收益: <strong class="gain-value">-{{ (92.4 - simulatedRisk).toFixed(1) }}%</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-action-bar animate-on-scroll delay-4">
          <el-button type="info" size="large" plain @click="goToWorkspace">
            <el-icon><ArrowLeft /></el-icon>
            返回数据流总览
          </el-button>
          <el-button type="primary" size="large" class="final-run-btn" @click="goToPlan">
            基于因果机制生成精准干预策略
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </main>

    <el-drawer v-model="drawerVisible" title="节点详细机制说明" direction="right" size="400px" :close-on-click-modal="true">
      <div v-if="selectedNode" class="node-detail-content">
        <div class="node-header">
          <div class="node-badge" :style="{backgroundColor: selectedNode.itemStyle.color}">{{ selectedNode.name }}</div>
          <el-tag :type="getNodeCategoryTag(selectedNode.category)" size="large">{{ getNodeCategoryName(selectedNode.category) }}</el-tag>
        </div>
        
        <div class="detail-section">
          <h4 class="section-title">核心机制说明</h4>
          <p class="detail-text">{{ selectedNode.tooltip }}</p>
        </div>

        <div class="detail-section">
          <h4 class="section-title">上游影响因素</h4>
          <div class="relation-list">
            <el-tag v-for="item in getUpstreamNodes(selectedNode.id)" :key="item.id" class="relation-tag" size="large">
               {{ item.name }}
            </el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">下游影响路径</h4>
          <div class="relation-list">
            <el-tag v-for="item in getDownstreamNodes(selectedNode.id)" :key="item.id" class="relation-tag" size="large" type="danger">
               {{ item.name }}
            </el-tag>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">SHAP 贡献度</h4>
          <div class="shap-bar">
            <div class="shap-bar-fill" :style="{width: `${selectedNode.shapValue * 100}%`}"></div>
            <span class="shap-value">{{ (selectedNode.shapValue * 100).toFixed(1) }}%</span>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title">相关文献</h4>
          <div class="reference-list">
            <div class="reference-item">
              <span class="ref-title">《重金属毒理学与健康风险评估》</span>
              <span class="ref-source">人民卫生出版社, 2025</span>
            </div>
            <div class="reference-item">
              <span class="ref-title">Environmental Health Perspectives</span>
              <span class="ref-source">Vol.133, No.5, 2025</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Coin, Share, DocumentChecked, ArrowLeft, TopRight, Select, Right, 
  DataLine, TrendCharts, Warning, CircleCheck, Timer, ZoomIn, ZoomOut, ArrowRight, Refresh,
  Document, Clock
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

const handleMenuSelect = (index) => {
  const routeMap = {
    '1-1': '/datainput',
    '3-1': '/risk',
    '4': '/causal',
    '5': '/plan'
  }
  if (routeMap[index]) {
    router.push(routeMap[index])
  } else {
    ElMessage.info('该功能正在开发中，敬请期待')
  }
}
const goToWorkspace = async () => { await router.push('/datainput') }
const goToPlan = async () => { await router.push('/plan') }

// ==================== 功能点1+2：全局控制变量 ====================
const selectedMetals = ref([])
const selectedDiseases = ref([])
const exposureYears = ref(10)
const populationGroup = ref('adult')

const metalOptions = [
  { label: 'Pb 铅', value: 'Pb' },
  { label: 'Cd 镉', value: 'Cd' },
  { label: 'As 砷', value: 'As' },
  { label: 'Hg 汞', value: 'Hg' },
  { label: 'Cr 铬', value: 'Cr' },
  { label: 'Ni 镍', value: 'Ni' },
  { label: 'Co 钴', value: 'Co' },
  { label: 'Li 锂', value: 'Li' },
  { label: 'Al 铝', value: 'Al' },
  { label: 'Mn 锰', value: 'Mn' }
]

const diseaseOptions = [
  { label: '慢性肾病', value: 'CKD' },
  { label: '神经疾病', value: 'Neuro' },
  { label: '肝纤维化', value: 'LiverDis' },
  { label: '骨质疏松', value: 'Osteo' },
  { label: '多器官癌变', value: 'Cancer' }
]

// ==================== KPI动态数据 ====================
const kpiBaseData = [
  {
    id: 'full',
    riskScore: 92.4,
    riskLevel: 'Level 3 高危',
    riskTagType: 'danger',
    riskDesc: '10种重金属协同暴露',
    mainFactor: 'Pb ⊕ As',
    factorDesc: '强协同致病效应',
    confidence: 96.8,
    confidenceDesc: '贝叶斯后验概率极高',
    interventionTier: 'Tier 1',
    interventionDesc: '推荐启动临床螯合阻断'
  },
  {
    id: 'pb-as-ckd',
    riskScore: 94.4,
    riskLevel: 'Level 3 高危',
    riskTagType: 'danger',
    riskDesc: 'Pb+As协同肾毒性',
    mainFactor: 'Pb ⊕ As',
    factorDesc: '强协同肾损伤效应',
    confidence: 95.2,
    confidenceDesc: '肾脏通路推断置信度高',
    interventionTier: 'Tier 1',
    interventionDesc: '优先启动肾脏保护治疗'
  },
  {
    id: 'cd-bone',
    riskScore: 78.5,
    riskLevel: 'Level 2 中危',
    riskTagType: 'warning',
    riskDesc: 'Cd慢性骨代谢损伤',
    mainFactor: 'Cd',
    factorDesc: '骨骼蓄积导致骨流失',
    confidence: 92.1,
    confidenceDesc: '骨代谢通路推断可靠',
    interventionTier: 'Tier 2',
    interventionDesc: '建议补充钙+维生素D干预'
  },
  {
    id: 'hg-neuro',
    riskScore: 88.3,
    riskLevel: 'Level 3 高危',
    riskTagType: 'danger',
    riskDesc: 'Hg中枢神经毒性',
    mainFactor: 'Hg',
    factorDesc: '血脑屏障穿透导致神经损伤',
    confidence: 97.5,
    confidenceDesc: '神经通路推断置信度极高',
    interventionTier: 'Tier 1',
    interventionDesc: '优先启动神经保护治疗'
  },
  {
    id: 'low-risk',
    riskScore: 45.2,
    riskLevel: 'Level 1 低危',
    riskTagType: 'success',
    riskDesc: '单金属低剂量暴露',
    mainFactor: 'Cr',
    factorDesc: '低剂量暴露影响有限',
    confidence: 88.6,
    confidenceDesc: '数据有限，置信度中等',
    interventionTier: 'Tier 3',
    interventionDesc: '建议定期监测，暂无需干预'
  }
]

// 当前KPI数据
const kpiData = ref({ ...kpiBaseData[0] })

// ==================== 功能点3：节点详情抽屉 ====================
const drawerVisible = ref(false)
const selectedNode = ref(null)

// ==================== 原有变量 ====================
const animatedRiskScore = ref(0)
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
let startX = 0, startY = 0

// ==================== 功能点4：反事实推演增强 ====================
const simPb = ref(15)
const simAs = ref(10)
const simCd = ref(5)
const simHg = ref(0)
const simCr = ref(0)
const simNi = ref(0)
const simCo = ref(0)
const simLi = ref(0)
const simAl = ref(0)
const simMn = ref(0)
const simMed = ref(false)
const simEDTA = ref(false)
const baseRisk = 92.4
const simulatedRisk = computed(() => {
  let reduction = (simPb.value * 0.4) + (simAs.value * 0.25) + (simCd.value * 0.2) + (simHg.value * 0.1)
  if (simMed.value) reduction += 20
  if (simEDTA.value) reduction += 35
  return Math.max(baseRisk - reduction, 12.0).toFixed(1)
})

// ==================== ECharts 实例管理 ====================
const causalGraphRef = ref(null)
const shapChartRef = ref(null)
const sankeyChartRef = ref(null)
const timeChartRef = ref(null)
let chartsInstances = []
let causalChartInstance = null

const clearCharts = () => { 
  chartsInstances.forEach(c => c.dispose())
  chartsInstances = [] 
}

// ==================== 核心因果图谱数据 ====================
const baseNodes = [
  // 10种重金属
  { id: 'Pb', name: 'Pb 铅', category: 0, x: 80, y: 60, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：冶炼、废旧电池、含铅管道、含铅涂料、烟草烟雾等', shapValue: 0.92 },
  { id: 'Cd', name: 'Cd 镉', category: 0, x: 80, y: 140, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：电镀、电池、颜料、PVC塑料稳定剂、土壤/水污染', shapValue: 0.56 },
  { id: 'As', name: 'As 砷', category: 0, x: 80, y: 220, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：农药、木材防腐剂、冶炼、地下水/饮用水污染', shapValue: 0.68 },
  { id: 'Hg', name: 'Hg 汞', category: 0, x: 80, y: 300, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：氯碱工业、采矿、电池、温度计、荧光灯、燃煤', shapValue: 0.44 },
  { id: 'Cr', name: 'Cr 铬', category: 0, x: 80, y: 380, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：电镀、皮革鞣制、颜料、不锈钢、水泥粉尘', shapValue: 0.38 },
  { id: 'Ni', name: 'Ni 镍', category: 0, x: 80, y: 460, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：电镀、电池、合金、不锈钢、煤燃烧、粉尘', shapValue: 0.32 },
  { id: 'Co', name: 'Co 钴', category: 0, x: 80, y: 540, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：合金、锂电池、磁铁、颜料、硬质合金', shapValue: 0.24 },
  { id: 'Li', name: 'Li 锂', category: 0, x: 80, y: 620, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：锂电池、陶瓷、玻璃、空调制冷剂', shapValue: 0.08 },
  { id: 'Al', name: 'Al 铝', category: 0, x: 80, y: 700, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：铝冶炼、加工粉尘、饮用水处理剂、食品添加剂', shapValue: 0.12 },
  { id: 'Mn', name: 'Mn 锰', category: 0, x: 80, y: 780, symbolSize: 52, itemStyle: { color: '#4D80F0' }, tooltip: '主要来源：冶金、焊接、电池、化肥、农药、汽车尾气', shapValue: 0.18 },

  // 分子机制层
  { id: 'ROS', name: '氧化应激', category: 1, x: 220, y: 100, symbolSize: 52, itemStyle: { color: '#42A5F5' }, tooltip: '重金属诱导ROS过量生成，破坏抗氧化系统，引发脂质过氧化与DNA损伤', shapValue: 0.75 },
  { id: 'DNA', name: 'DNA损伤', category: 1, x: 220, y: 220, symbolSize: 52, itemStyle: { color: '#42A5F5' }, tooltip: '重金属直接与DNA结合或通过ROS间接攻击，导致链断裂、突变和表观遗传改变', shapValue: 0.82 },
  { id: 'Mito', name: '线粒体紊乱', category: 1, x: 220, y: 340, symbolSize: 52, itemStyle: { color: '#42A5F5' }, tooltip: '重金属抑制线粒体呼吸链，导致ATP生成障碍和ROS爆发', shapValue: 0.65 },
  { id: 'Endo', name: '内皮损伤', category: 1, x: 220, y: 460, symbolSize: 52, itemStyle: { color: '#42A5F5' }, tooltip: '重金属破坏血管内皮屏障，导致通透性增加和炎症反应', shapValue: 0.58 },
  { id: 'Infla', name: '神经炎症', category: 1, x: 220, y: 580, symbolSize: 52, itemStyle: { color: '#42A5F5' }, tooltip: '重金属激活小胶质细胞和星形胶质细胞，释放促炎因子，引发神经毒性', shapValue: 0.70 },

  // 组织损伤层
  { id: 'Kidney', name: '肾损伤', category: 2, x: 360, y: 160, symbolSize: 52, itemStyle: { color: '#26A69A' }, tooltip: '重金属在肾小管蓄积，直接损伤近端小管上皮细胞，导致肾功能下降', shapValue: 0.88 },
  { id: 'Liver', name: '肝损伤', category: 2, x: 360, y: 280, symbolSize: 52, itemStyle: { color: '#26A69A' }, tooltip: '重金属在肝脏蓄积，引发肝细胞坏死、纤维化和肝功能障碍', shapValue: 0.72 },
  { id: 'BBB', name: '血脑屏障', category: 2, x: 360, y: 400, symbolSize: 52, itemStyle: { color: '#26A69A' }, tooltip: '重金属破坏血脑屏障完整性，导致神经毒性物质进入中枢神经系统', shapValue: 0.85 },
  { id: 'Bone', name: '骨骼蓄积', category: 2, x: 360, y: 520, symbolSize: 52, itemStyle: { color: '#26A69A' }, tooltip: '重金属替代骨骼中的钙，长期蓄积导致骨质疏松和骨代谢紊乱', shapValue: 0.62 },
  { id: 'Blood', name: '造血障碍', category: 2, x: 360, y: 640, symbolSize: 52, itemStyle: { color: '#26A69A' }, tooltip: '重金属抑制骨髓造血功能，导致贫血和免疫功能下降', shapValue: 0.55 },

  // 临床疾病层
  { id: 'Neuro', name: '神经疾病', category: 3, x: 500, y: 160, symbolSize: 52, itemStyle: { color: '#EF5350' }, tooltip: '重金属诱导的神经炎症和氧化应激，导致认知障碍、帕金森样症状和神经退行性疾病', shapValue: 0.90 },
  { id: 'CKD', name: '慢性肾病', category: 3, x: 500, y: 280, symbolSize: 52, itemStyle: { color: '#EF5350' }, tooltip: '长期重金属暴露导致肾小管不可逆损伤，进展为慢性肾病和肾功能衰竭', shapValue: 0.95 },
  { id: 'LiverDis', name: '肝纤维化', category: 3, x: 500, y: 400, symbolSize: 52, itemStyle: { color: '#EF5350' }, tooltip: '重金属诱导的慢性肝损伤，进展为肝纤维化、肝硬化甚至肝癌', shapValue: 0.78 },
  { id: 'Osteo', name: '骨质疏松', category: 3, x: 500, y: 520, symbolSize: 52, itemStyle: { color: '#EF5350' }, tooltip: '重金属在骨骼蓄积，破坏骨代谢平衡，导致骨质疏松和骨折风险增加', shapValue: 0.68 },
  { id: 'Cancer', name: '多器官癌变', category: 3, x: 500, y: 640, symbolSize: 52, itemStyle: { color: '#EF5350' }, tooltip: '重金属的DNA损伤和突变作用，导致多种器官癌变风险显著升高', shapValue: 0.88 },

  // 医疗干预层
  { id: 'EDTA', name: '螯合治疗', category: 4, x: 640, y: 220, symbolSize: 52, itemStyle: { color: '#66BB6A' }, tooltip: 'EDTA等螯合剂可与重金属形成稳定复合物，促进其从体内排出', shapValue: 0.0 },
  { id: 'Antiox', name: '抗氧化治疗', category: 4, x: 640, y: 380, symbolSize: 52, itemStyle: { color: '#66BB6A' }, tooltip: '补充维生素C/E、N-乙酰半胱氨酸等，清除自由基，减轻氧化应激损伤', shapValue: 0.0 },
  { id: 'Protect', name: '靶器官保护', category: 4, x: 640, y: 540, symbolSize: 52, itemStyle: { color: '#66BB6A' }, tooltip: '针对肝肾等靶器官进行保护治疗，减轻重金属造成的损伤', shapValue: 0.0 },
]

const rawLinks = [
  // Pb
  { source: 'Pb', target: 'ROS', lineStyle: { color: '#4D80F0' }, curveness: 0.1, tooltip: 'Pb²⁺可替代Ca²⁺干扰细胞信号通路，诱导氧化应激和表观遗传变化；与硫醇(-SH)结合损伤蛋白质。', strength: 0.9, confidence: 0.95 },
  { source: 'Pb', target: 'Kidney', lineStyle: { color: '#4D80F0' }, curveness: 0.1, tooltip: 'Pb在肾小管蓄积，直接损伤近端小管上皮细胞，导致肾功能下降。', strength: 0.85, confidence: 0.92 },
  { source: 'Pb', target: 'BBB', lineStyle: { color: '#4D80F0' }, curveness: 0.1, tooltip: 'Pb破坏血脑屏障完整性，进入中枢神经系统，引发神经毒性。', strength: 0.88, confidence: 0.90 },
  
  // Cd
  { source: 'Cd', target: 'Kidney', lineStyle: { color: '#AB47BC' }, tooltip: 'Cd²⁺主要在肾脏蓄积，通过氧化应激和细胞凋亡导致肾小管损伤，是Cd中毒最主要的靶器官。', strength: 0.95, confidence: 0.98 },
  { source: 'Cd', target: 'Bone', lineStyle: { color: '#AB47BC' }, tooltip: 'Cd替代骨骼中的钙，长期蓄积导致骨代谢紊乱和骨质疏松。', strength: 0.75, confidence: 0.85 },
  
  // As
  { source: 'As', target: 'DNA', lineStyle: { color: '#FF9800' }, curveness: -0.1, tooltip: 'As诱导DNA链断裂和基因突变，是明确的致癌物，可导致多种器官癌变。', strength: 0.92, confidence: 0.99 },
  { source: 'As', target: 'Liver', lineStyle: { color: '#FF9800' }, curveness: -0.1, tooltip: 'As在肝脏蓄积，引发肝细胞损伤和肝纤维化，是肝损伤的重要诱因。', strength: 0.80, confidence: 0.88 },
  
  // Hg
  { source: 'Hg', target: 'Infla', lineStyle: { color: '#E91E63' }, curveness: -0.2, tooltip: 'Hg激活小胶质细胞和星形胶质细胞，释放促炎因子，引发神经炎症反应。', strength: 0.88, confidence: 0.92 },
  { source: 'Hg', target: 'BBB', lineStyle: { color: '#E91E63' }, curveness: -0.2, tooltip: 'Hg极易通过血脑屏障，在中枢神经系统蓄积，导致不可逆的神经损伤。', strength: 0.95, confidence: 0.97 },
  
  // Cr
  { source: 'Cr', target: 'DNA', lineStyle: { color: '#9C27B0' }, curveness: 0.15, tooltip: '六价铬是强致癌物，可直接攻击DNA，导致链断裂和突变，引发肺癌等多种癌症。', strength: 0.90, confidence: 0.98 },
  
  // Ni
  { source: 'Ni', target: 'DNA', lineStyle: { color: '#3F51B5' }, curveness: -0.1, tooltip: 'Ni诱导DNA损伤和染色体畸变，是明确的致癌物，可导致肺癌和鼻咽癌。', strength: 0.85, confidence: 0.95 },
  { source: 'Ni', target: 'Infla', lineStyle: { color: '#3F51B5' }, curveness: -0.1, tooltip: 'Ni可引发慢性炎症反应，促进肿瘤发生和进展。', strength: 0.70, confidence: 0.82 },
  
  // Co
  { source: 'Co', target: 'Mito', lineStyle: { color: '#00BCD4' }, tooltip: 'Co抑制线粒体呼吸链功能，导致ATP生成障碍和ROS爆发，引发细胞损伤。', strength: 0.75, confidence: 0.85 },
  
  // Li
  { source: 'Li', target: 'Endo', lineStyle: { color: '#8BC34A' }, tooltip: 'Li破坏血管内皮屏障，导致通透性增加和炎症反应，影响肾功能。', strength: 0.60, confidence: 0.78 },
  
  // Al
  { source: 'Al', target: 'BBB', lineStyle: { color: '#FF5722' }, curveness: 0.2, tooltip: 'Al可通过受损的血脑屏障进入中枢神经系统，与神经退行性疾病相关。', strength: 0.65, confidence: 0.75 },
  
  // Mn
  { source: 'Mn', target: 'Infla', lineStyle: { color: '#CDDC39' }, curveness: -0.3, tooltip: 'Mn诱导小胶质细胞激活和促炎因子释放，引发神经炎症和多巴胺能神经元损伤。', strength: 0.80, confidence: 0.88 },
  { source: 'Mn', target: 'BBB', lineStyle: { color: '#CDDC39' }, curveness: -0.3, tooltip: 'Mn极易通过血脑屏障，在纹状体蓄积，导致帕金森样症状。', strength: 0.85, confidence: 0.90 },

  // 分子→组织
  { source: 'ROS', target: 'Kidney', lineStyle: { color: '#42A5F5' }, tooltip: 'ROS过量生成导致肾小管上皮细胞氧化损伤和凋亡，加重肾损伤。', strength: 0.85, confidence: 0.92 },
  { source: 'ROS', target: 'Liver', lineStyle: { color: '#42A5F5' }, tooltip: 'ROS引发肝细胞脂质过氧化和氧化损伤，导致肝功能障碍。', strength: 0.78, confidence: 0.88 },
  { source: 'ROS', target: 'BBB', lineStyle: { color: '#42A5F5' }, tooltip: 'ROS破坏血脑屏障的完整性，导致神经毒性物质进入中枢神经系统。', strength: 0.82, confidence: 0.90 },
  { source: 'DNA', target: 'Cancer', lineStyle: { color: '#42A5F5' }, tooltip: 'DNA损伤和突变是重金属致癌的核心机制，可导致多种器官癌变。', strength: 0.95, confidence: 0.99 },
  { source: 'Mito', target: 'Liver', lineStyle: { color: '#42A5F5' }, tooltip: '线粒体功能障碍导致肝细胞能量代谢紊乱和ROS生成，加重肝损伤。', strength: 0.72, confidence: 0.85 },
  { source: 'Endo', target: 'Kidney', lineStyle: { color: '#42A5F5' }, tooltip: '内皮损伤导致肾血流量下降和肾功能障碍，加重肾损伤。', strength: 0.70, confidence: 0.82 },
  { source: 'Infla', target: 'BBB', lineStyle: { color: '#42A5F5' }, tooltip: '神经炎症反应破坏血脑屏障，进一步加重中枢神经系统损伤。', strength: 0.78, confidence: 0.88 },

  // 组织→疾病
  { source: 'Kidney', target: 'CKD', lineStyle: { color: '#26A69A' }, tooltip: '长期肾损伤进展为慢性肾病，最终导致肾功能衰竭。', strength: 0.98, confidence: 0.99 },
  { source: 'Liver', target: 'LiverDis', lineStyle: { color: '#26A69A' }, tooltip: '慢性肝损伤进展为肝纤维化、肝硬化，甚至肝癌。', strength: 0.85, confidence: 0.92 },
  { source: 'BBB', target: 'Neuro', lineStyle: { color: '#26A69A' }, tooltip: '血脑屏障破坏导致神经毒性物质进入中枢神经系统，引发神经退行性疾病。', strength: 0.92, confidence: 0.95 },
  { source: 'Bone', target: 'Osteo', lineStyle: { color: '#26A69A' }, tooltip: '骨骼中重金属蓄积导致骨代谢紊乱，引发骨质疏松和骨折风险增加。', strength: 0.80, confidence: 0.88 },
  { source: 'Blood', target: 'Cancer', lineStyle: { color: '#26A69A' }, tooltip: '造血系统损伤和免疫功能下降，增加肿瘤发生风险。', strength: 0.65, confidence: 0.75 },

  // 干预措施
  { source: 'EDTA', target: 'Pb', lineStyle: { color: '#69F0AE' }, curveness: 0.6, tooltip: 'EDTA与Pb形成稳定复合物，促进其从体内排出，降低体内蓄积水平。', strength: 0.90, confidence: 0.95 },
  { source: 'EDTA', target: 'Cd', lineStyle: { color: '#69F0AE' }, curveness: 0.6, tooltip: 'EDTA可与Cd结合，减少其在体内的蓄积，减轻肾毒性。', strength: 0.85, confidence: 0.92 },
  { source: 'Antiox', target: 'ROS', lineStyle: { color: '#76FF03' }, curveness: -0.4, tooltip: '抗氧化剂可清除自由基，减轻重金属诱导的氧化应激损伤。', strength: 0.80, confidence: 0.88 },
  { source: 'Protect', target: 'Kidney', lineStyle: { color: '#00E676' }, curveness: -0.4, tooltip: '肾保护治疗可减轻重金属对肾小管的损伤，延缓肾功能下降。', strength: 0.75, confidence: 0.85 }
]

// ==================== 功能点辅助方法 ====================
// 获取节点上下游
const getUpstreamNodes = (nodeId) => {
  return rawLinks.filter(l => l.target === nodeId).map(l => baseNodes.find(n => n.id === l.source)).filter(Boolean)
}

const getDownstreamNodes = (nodeId) => {
  return rawLinks.filter(l => l.source === nodeId).map(l => baseNodes.find(n => n.id === l.target)).filter(Boolean)
}

// 获取节点分类名称
const getNodeCategoryName = (category) => {
  const categories = ['重金属暴露', '分子机制', '组织损伤', '临床疾病', '干预措施']
  return categories[category]
}

const getNodeCategoryTag = (category) => {
  const tags = ['primary', 'info', 'success', 'danger', 'success']
  return tags[category]
}

// 应用筛选（功能点1+2）
const applyFilter = () => {
  // 1. 更新KPI数据（根据选择的金属和疾病匹配模拟数据）
  let matchedKpi = kpiBaseData[0] // 默认全量数据
  
  if (selectedMetals.value.length > 0 || selectedDiseases.value.length > 0) {
    // 匹配预设场景
    if (selectedMetals.value.includes('Pb') && selectedMetals.value.includes('As') && selectedDiseases.value.includes('CKD')) {
      matchedKpi = kpiBaseData[1] // Pb+As+肾病场景
    } else if (selectedMetals.value.includes('Cd') && selectedDiseases.value.includes('Osteo')) {
      matchedKpi = kpiBaseData[2] // Cd+骨质疏松场景
    } else if (selectedMetals.value.includes('Hg') && selectedDiseases.value.includes('Neuro')) {
      matchedKpi = kpiBaseData[3] // Hg+神经疾病场景
    } else if (selectedMetals.value.length === 1 && selectedMetals.value[0] === 'Cr') {
      matchedKpi = kpiBaseData[4] // 单Cr低风险场景
    } else {
      // 通用场景：根据选择数量动态调整
      const riskAdjustment = (selectedMetals.value.length * 5) + (selectedDiseases.value.length * 3) + (exposureYears.value - 10) * 1.5
      matchedKpi = {
        ...kpiBaseData[0],
        riskScore: Math.min(98, 75 + riskAdjustment),
        riskDesc: `${selectedMetals.value.join('+')}协同暴露`,
        mainFactor: selectedMetals.value.slice(0, 2).join(' ⊕ ') || '多金属协同',
        factorDesc: '基于当前筛选的主要致病路径',
        confidence: Math.max(85, 96.8 - (selectedMetals.value.length * 1.5))
      }
    }
  }
  
  // 人群和年限调整
  if (populationGroup.value === 'child') {
    matchedKpi.riskScore = Math.min(99, matchedKpi.riskScore * 1.08)
    matchedKpi.riskLevel = 'Level 3 高危'
    matchedKpi.riskTagType = 'danger'
  } else if (populationGroup.value === 'elder') {
    matchedKpi.riskScore = Math.min(99, matchedKpi.riskScore * 1.05)
  }
  
  kpiData.value = matchedKpi
  
  // 2. 更新风险评分动画
  animateNumber(matchedKpi.riskScore)
  
  // 3. 更新图谱（只显示选中的节点和连线）
  updateCausalGraph()
}

// 重置筛选
const resetFilter = () => {
  selectedMetals.value = []
  selectedDiseases.value = []
  exposureYears.value = 10
  populationGroup.value = 'adult'
  
  // 恢复默认KPI数据
  kpiData.value = { ...kpiBaseData[0] }
  animateNumber(kpiBaseData[0].riskScore)
  
  // 恢复图谱视图
  resetView()
  updateCausalGraph()
}

// ==================== 核心图谱渲染（已修复：只显示选中的节点和连线） ====================
const getKnowledgeGraphOption = () => {
  // 深拷贝基础数据
  let nodes = JSON.parse(JSON.stringify(baseNodes))
  let links = JSON.parse(JSON.stringify(rawLinks))

  // ✅ 已修复：选择参数后，只显示相关的节点和连线，完全移除不相关的
  if (selectedMetals.value.length > 0 || selectedDiseases.value.length > 0) {
    // 找出所有相关节点
    let relevantNodeIds = new Set()
    
    // 添加选中的金属
    selectedMetals.value.forEach(id => relevantNodeIds.add(id))
    // 添加选中的疾病
    selectedDiseases.value.forEach(id => relevantNodeIds.add(id))
    
    // 递归添加上下游节点（完整因果链）
    const addRelatedNodes = (nodeId) => {
      // 添加上游
      getUpstreamNodes(nodeId).forEach(n => {
        if (!relevantNodeIds.has(n.id)) {
          relevantNodeIds.add(n.id)
          addRelatedNodes(n.id)
        }
      })
      // 添加下游
      getDownstreamNodes(nodeId).forEach(n => {
        if (!relevantNodeIds.has(n.id)) {
          relevantNodeIds.add(n.id)
          addRelatedNodes(n.id)
        }
      })
    }
    
    // 遍历所有选中的节点，添加完整因果链
    relevantNodeIds.forEach(id => addRelatedNodes(id))
   
    // ✅ 关键修复：只保留相关节点和连线，完全删除不相关的
    nodes = nodes.filter(n => relevantNodeIds.has(n.id))
    links = links.filter(l => relevantNodeIds.has(l.source) && relevantNodeIds.has(l.target))
  }

  // 功能点2：根据暴露年限和人群调整节点大小和颜色
  const yearMultiplier = 1 + (exposureYears.value - 10) * 0.02
  const populationMultiplier = populationGroup.value === 'child' ? 1.3 : populationGroup.value === 'elder' ? 1.2 : 1.0
  
  nodes.forEach(n => {
    if (n.category !== 4) { // 干预措施不调整
      n.symbolSize = Math.round(n.symbolSize * yearMultiplier * populationMultiplier)
    }
  })

  // 功能点4：根据反事实干预调整连线
  if (simPb.value > 0) {
    links.forEach(l => {
      if (l.source === 'Pb') l.lineStyle.opacity = Math.max(0.2, 1 - simPb.value / 100)
    })
  }
  if (simAs.value > 0) {
    links.forEach(l => {
      if (l.source === 'As') l.lineStyle.opacity = Math.max(0.2, 1 - simAs.value / 100)
    })
  }
  if (simCd.value > 0) {
    links.forEach(l => {
      if (l.source === 'Cd') l.lineStyle.opacity = Math.max(0.2, 1 - simCd.value / 100)
    })
  }
  if (simMed.value) {
    links.forEach(l => {
      if (l.target === 'ROS') l.lineStyle.opacity = 0.3
    })
  }
  if (simEDTA.value) {
    links.forEach(l => {
      if (l.source === 'Pb' || l.source === 'Cd') l.lineStyle.opacity = 0.2
    })
  }

  // 构建ECharts配置
  const nodeMap = new Map()
  nodes.forEach(n => { n.value = [n.x, n.y]; nodeMap.set(n.id, [n.x, n.y]) })

  const echartsLinks = links.map(edge => ({
    source: edge.source, target: edge.target,
    lineStyle: { 
      width: 2 + edge.strength * 3, // 连线粗细代表因果强度
      opacity: edge.lineStyle.opacity || 0.5, 
      curveness: edge.curveness || 0.15, 
      color: edge.lineStyle.color 
    },
    tooltip: { formatter: edge.tooltip }
  }))

  const linesData = links.filter(l => l.lineStyle.opacity > 0.3).map(edge => ({
    coords: [nodeMap.get(edge.source), nodeMap.get(edge.target)],
    lineStyle: { curveness: edge.curveness || 0.15 },
    effect: { color: edge.lineStyle.color } 
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'item',
      backgroundColor: 'rgba(255,255,255,0.95)', 
      borderColor: '#E2E8F0', 
      textStyle: { color: '#0F172A' },
      padding: [12, 16],
      borderRadius: 8,
      boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
      formatter: function(params) {
        if (params.data && params.data.tooltip) {
          return `<div style="font-weight:bold;margin-bottom:4px;">${params.data.name}</div>${params.data.tooltip}`
        }
        if (params.data && params.data.source && params.data.target) {
          const linkInfo = rawLinks.find(l => l.source === params.data.source && l.target === params.data.target)
          if (linkInfo && linkInfo.tooltip) {
            return `<div style="font-weight:bold;margin-bottom:4px;">${params.data.source} → ${params.data.target}</div>
                     <div>${linkInfo.tooltip}</div>
                    <div style="margin-top:8px;font-size:12px;color:#64748B;">
                      因果强度: ${(linkInfo.strength * 100).toFixed(0)}% | 置信度: ${(linkInfo.confidence * 100).toFixed(0)}%
                    </div>`
          }
        }
        return params.name
      }
    },
    xAxis: { type: 'value', show: false, min: 0, max: 750 },
    yAxis: { type: 'value', show: false, min: 0, max: 850, inverse: true },
    grid: { top: 10, bottom: 10, left: 10, right: 10 },
    series: [
      {
        type: 'effectScatter', 
        coordinateSystem: 'cartesian2d', 
        zlevel: 1,
        data: nodes.map(n => ({ 
          value: n.value, 
          symbolSize: n.symbolSize * 0.95, 
          itemStyle: { 
            color: n.itemStyle.color,
            shadowBlur: 25,
            shadowColor: n.itemStyle.color,
            opacity: n.itemStyle.opacity || 1
          },
          tooltip: { formatter: n.tooltip }
        })),
        rippleEffect: { 
          brushType: 'fill', 
          scale: 1.8, 
          period: 3 
        },
        label: { show: false }
      },
      {
        type: 'graph', 
        coordinateSystem: 'cartesian2d', 
        layout: 'none', 
        zlevel: 2,
        data: nodes, 
        links: echartsLinks, 
        roam: false,
        label: { 
          show: true, 
          position: 'inside', 
          fontSize: 11, 
          fontWeight: 700, 
          color: '#fff',
          textShadow: '0 1px 2px rgba(0,0,0,0.3)'
        },
        itemStyle: { 
          borderWidth: 3, 
          borderColor: '#fff', 
          shadowBlur: 25, 
          shadowOffsetY: 6, 
          shadowColor: 'rgba(0,0,0,0.25)', 
          borderRadius: 12 
        },
        edgeSymbol: ['none', 'arrow'], 
        edgeSymbolSize: [0, 10]
      },
      {
        type: 'lines', 
        coordinateSystem: 'cartesian2d', 
        zlevel: 3,
        effect: { 
          show: true, 
          period: 4, 
          trailLength: 0.5, 
          symbol: 'circle', 
          symbolSize: 7 
        },
        lineStyle: { width: 0, opacity: 0 },
        data: linesData.map(d => ({ 
          coords: d.coords, 
          lineStyle: { curveness: d.lineStyle.curveness }, 
          effect: { color: d.effect.color } 
        }))
      }
    ]
  }
}

// 更新因果图谱
const updateCausalGraph = () => {
  if (causalChartInstance) {
    causalChartInstance.setOption(getKnowledgeGraphOption(), true) // true表示完全替换配置
  }
}

const initAllCharts = () => {
  clearCharts()
  if(causalGraphRef.value) { 
    causalChartInstance = echarts.init(causalGraphRef.value, null, { devicePixelRatio: 3 });
    causalChartInstance.setOption(getKnowledgeGraphOption()); 
    chartsInstances.push(causalChartInstance)
    
    // 功能点3：节点点击事件（保留）
    causalChartInstance.on('click', (params) => {
      if (params.componentType === 'series' && params.seriesType === 'graph') {
        selectedNode.value = baseNodes.find(n => n.id === params.data.id)
        drawerVisible.value = true
      }
    })
  }
}

// 数字滚动动画
const animateNumber = (target, duration = 2000) => {
  const start = animatedRiskScore.value
  const startTime = Date.now()
  const timer = setInterval(() => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    animatedRiskScore.value = Math.round((start + (target - start) * progress) * 10) / 10
    if (progress >= 1) clearInterval(timer)
  }, 16)
}

// 缩放与拖拽控制
const handleZoom = (e) => {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  zoom.value = Math.max(0.4, Math.min(zoom.value + delta, 3.5))
}

const startPan = (e) => {
  isPanning.value = true
  startX = e.clientX - panX.value
  startY = e.clientY - panY.value
}

const doPan = (e) => {
  if (!isPanning.value) return
  panX.value = e.clientX - startX
  panY.value = e.clientY - startY
}

const endPan = () => { isPanning.value = false }

const resetView = () => {
  zoom.value = 1
  panX.value = 0
  panY.value = 0
}

const zoomIn = () => {
  zoom.value = Math.min(zoom.value + 0.2, 3.5)
}

const zoomOut = () => {
  zoom.value = Math.max(zoom.value - 0.2, 0.4)
}

// 完全恢复你原来的浮动粒子样式
const particleStyle = (i) => {
  return {
    left: `${5 + Math.random() * 90}%`,
    top: `${5 + Math.random() * 90}%`,
    animationDelay: `${Math.random() * 5}s`,
    animationDuration: `${6 + Math.random() * 6}s`
  }
}

// 监听反事实参数变化，实时更新图谱
watch([simPb, simAs, simCd, simHg, simCr, simNi, simCo, simLi, simAl, simMn, simMed, simEDTA], () => {
  updateCausalGraph()
}, { deep: true })

onMounted(() => { 
  nextTick(() => { 
    initAllCharts()
    animateNumber(92.4)
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => { 
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible')
        } 
      })
    }, { threshold: 0.1 })
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el))
  })
  
  window.addEventListener('resize', () => chartsInstances.forEach(c => c.resize())) 
})

onBeforeUnmount(() => { 
  window.removeEventListener('resize', () => {})
  clearCharts()
})
</script>

<style scoped>
/* 🛡️ 针对 Tailwind CSS 的 SVG 无限放大防御补丁 */
:deep(.el-icon svg) {
  max-width: 1em;
  max-height: 1em;
  width: 1em;
  height: 1em;
}
:root {
  --primary: #1f77b4;
  --primary-light: #EFF6FF;
  --success: #10B981;
  --warning: #F59E0B;
  --danger: #EF4444;
  --gray-50: #F8FAFC;
  --gray-100: #F1F5F9;
  --gray-200: #E2E8F0;
  --gray-300: #CBD5E1;
  --gray-400: #94A3B8;
  --gray-500: #64748B;
  --gray-600: #475569;
  --gray-700: #334155;
  --gray-900: #0F172A;
}
* { box-sizing: border-box; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
.system-layout { 
  display: flex; 
  height: 100vh; 
  background-color: var(--gray-50);
  overflow: hidden; 
}
/* 主内容区 */
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
  background: rgba(255,255,255,0.85); 
  backdrop-filter: blur(12px); 
  border-bottom: 1px solid var(--gray-200); 
  position: sticky; 
  top: 0;
  z-index: 50; 
  display: flex; 
  justify-content: center; 
}
.nav-wrapper { 
  width: 100%; 
  padding: 0 32px; 
  display: flex; 
  flex-direction: row;
  flex-wrap: nowrap; 
  justify-content: space-between; 
  align-items: center; 
  height: 100%; 
}
.back-link { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  cursor: pointer;
  color: var(--gray-900); 
  transition: color 0.2s ease;
}
.back-link:hover { color: var(--primary); }
.back-link .back-text { font-size: 1.05rem; font-weight: 700; }
.back-link .divider { color: var(--gray-300); margin: 0 8px; }
.back-link .page-title-top { font-size: 1.1rem; font-weight: 800; }
.user-profile { 
  display: flex; 
  align-items: center; 
  gap: 12px; 
  font-weight: 600; 
  font-size: 0.95rem;
}
.user-profile .avatar { 
  width: 36px; 
  height: 36px; 
  border-radius: 50%; 
  background: linear-gradient(135deg, var(--primary-light), #fff); 
  color: var(--primary); 
  display: flex;
  justify-content: center; 
  align-items: center; 
  font-weight: 700; 
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.2);
}
.page-container { 
  padding: 40px;
  max-width: 100%; 
  margin: 0 auto; 
  width: 100%; 
  display: flex; 
  flex-direction: column; 
}
/* =========================================================
   ✅ 全局控制栏 (完全对齐 datainput 高端表单质感)
   ========================================================= */
.global-control-bar {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 16px;
  padding: 24px 32px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between; /* 充分利用右侧空间 */
  gap: 24px;
  flex-wrap: nowrap;
  overflow-x: auto;
  box-shadow: 0 8px 32px #147fe214, 0 2px 8px rgba(16, 101, 230, 0.04);
}
.global-control-bar::-webkit-scrollbar {
  height: 4px;
}
.global-control-bar::-webkit-scrollbar-thumb {
  background: var(--gray-200);
  border-radius: 4px;
}
.control-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex-shrink: 0;
}
.slider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 40px; /* 强制高度与输入框对齐 */
}
.control-label {
  font-weight: 800;
  color: var(--gray-900);
  white-space: nowrap;
  font-size: 0.95rem;
}
.control-actions {
  display: flex;
  gap: 12px;
  margin-left: auto; /* 靠右对齐 */
  align-items: flex-end; /* 与输入框底部对齐 */
  padding-top: 28px; /* 占位以对齐有label的项 */
}
/* 优化输入框和滑块宽度 */
.control-slider {
  width: 160px;
}
.slider-value {
  font-weight: 800;
  color: var(--primary);
  min-width: 48px;
  text-align: right;
  font-size: 1.05rem;
}
.global-control-bar :deep(.el-select) {
  width: 240px; /* 加长选择框，防止文字截断 */
}
.global-control-bar :deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--gray-300) inset !important;
  background: #fff;
}
.global-control-bar :deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--primary) inset !important;
}
/* =========================================================
   ✅ 修复 1：人群分组单选按钮 终极优先级修复
   ========================================================= */
/* =========================================================
   ✅ 人群分组单选按钮 终极强制修复 (100%覆盖Element Plus默认样式)
   ========================================================= */
.global-control-bar :deep(div.el-radio-button > label.el-radio-button__inner) {
  padding: 10px 24px !important;
  font-weight: 600 !important;
  color: var(--gray-600) !important;
  border-color: var(--gray-300) !important;
  background-color: #ffffff !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}

.global-control-bar :deep(div.el-radio-button > label.el-radio-button__inner:hover) {
  color: var(--primary) !important;
  border-color: var(--primary) !important;
  background-color: var(--primary-light) !important;
}

.global-control-bar :deep(div.el-radio-button.is-active > label.el-radio-button__inner) {
  background-color: var(--primary) !important;
  border-color: var(--primary) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 8px rgba(31, 119, 180, 0.2) !important;
}

/* 修复相邻按钮边框重叠问题 */
.global-control-bar :deep(div.el-radio-button.is-active + div.el-radio-button > label.el-radio-button__inner) {
  border-left-color: var(--primary) !important;
}
/* KPI卡片（保留causal原有样式） */
.research-kpi-grid { 
  display: grid;
  grid-template-columns: repeat(4, 1fr); 
  gap: 24px; 
  margin-bottom: 40px; 
}
.r-kpi-card { 
  background: #fff; 
  border: 1px solid var(--gray-200); 
  border-radius: 16px;
  padding: 24px; 
  display: flex; 
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.r-kpi-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.08);
}
.r-kpi-card.danger-level { 
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, rgba(254,242,242,0.5), #fff); 
}
.kpi-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}
.kpi-icon.danger { background: linear-gradient(135deg, #FEE2E2, #FECACA); color: var(--danger); }
.kpi-icon.primary { background: linear-gradient(135deg, #E0F2FE, #BAE6FD); color: var(--primary); }
.kpi-icon.success { background: linear-gradient(135deg, #D1FAE5, #A7F3D0); color: var(--success); }
.kpi-icon.warning { background: linear-gradient(135deg, #FEF3C7, #FDE68A); color: var(--warning); }
.r-kpi-card .kpi-info { 
  display: flex; 
  flex-direction: column; 
  gap: 4px; 
  flex: 1;
}
.r-kpi-card .kpi-tag { 
  font-size: 0.7rem;
  font-weight: 800; 
  color: var(--gray-500); 
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.r-kpi-card .kpi-val { 
  font-size: 2.2rem; 
  font-weight: 900; 
  color: var(--gray-900);
  line-height: 1.1; 
  letter-spacing: -0.02em;
}
.r-kpi-card .kpi-val small { 
  font-size: 1rem; 
  color: var(--gray-500);
}
.r-kpi-card .kpi-delta { font-size: 0.8rem; font-weight: 600; }
.r-kpi-card .text-danger { color: var(--danger); }
.r-kpi-card .text-primary { color: var(--primary); }
.r-kpi-card .text-safe { color: var(--success); }
.r-kpi-card .text-muted { color: var(--gray-500); }
.r-kpi-card .flex-align { display: flex; align-items: center; }
.r-kpi-card .ml-2 { margin-left: 8px; }
/* 核心大屏 */
.core-dag-section { 
  width: 90%;
  margin: 0 auto;
  background: #fff; 
  border: 1px solid var(--gray-200); 
  border-radius: 20px; 
  padding: 32px; 
  margin-bottom: 40px; 
  position: relative;
  box-shadow: 0 4px 20px rgba(0,0,0,0.05);
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.header-left { flex: 1; }
.title-badge {
  display: inline-block;
  background: linear-gradient(135deg, var(--primary), #6366F1);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.section-title {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--gray-900);
  margin: 0 0 8px 0;
  letter-spacing: -0.02em;
}
.section-desc {
  font-size: 0.95rem;
  color: var(--gray-600);
  line-height: 1.6;
  margin: 0;
}
.header-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--gray-50);
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid var(--gray-200);
}
.info-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(14, 165, 233, 0.1);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
}
.info-text { display: flex; flex-direction: column; }
.info-label { font-size: 0.75rem; color: var(--gray-500); font-weight: 600; }
.info-value { font-size: 0.9rem; color: var(--gray-700); font-weight: 700; }
.dag-viewport {
  width: 100%;
  height: 850px;
  background: linear-gradient(135deg, #F0FDF4 0%, #E6F7ED 50%, #EFF6FF 100%);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
  cursor: grab;
  border: 1px solid #DCFCE7;
  margin-top: 15px;
}
.dag-viewport.is-panning { cursor: grabbing; }
.grid-bg {
  position: absolute; width: 100%; height: 100%; top: 0; left: 0;
  background-image: 
    linear-gradient(rgba(16, 185, 129, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none; z-index: 0;
}
.floating-particles {
  position: absolute; width: 100%; height: 100%; top: 0; left: 0;
  overflow: hidden; pointer-events: none; z-index: 1;
}
.particle {
  position: absolute; width: 6px; height: 6px; border-radius: 50%;
  background: rgba(14, 165, 233, 0.5);
  animation: floatBounce 7s infinite ease-in-out;
}
@keyframes floatBounce {
  0% { transform: translate(0, 0); opacity: 0; }
  25% { transform: translate(25px, -35px); opacity: 1; }
  50% { transform: translate(-20px, 25px); opacity: 1; }
  75% { transform: translate(30px, 15px); opacity: 1; }
  100% { transform: translate(0, 0); opacity: 0; }
}
.dag-canvas { 
  width: 100%; height: 100%; transform-origin: center center;
  transition: transform 0.05s linear; z-index: 5; position: relative;
}
.floating-legend {
  position: absolute; top: 20px; right: 20px;
  background: rgba(255, 255, 255, 0.7); backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.8); border-radius: 16px; 
  padding: 18px; box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  z-index: 10; pointer-events: none; font-size: 0.85rem; 
  font-weight: 600; color: var(--gray-700); min-width: 180px;
}
.legend-title {
  font-size: 0.9rem; font-weight: 800; color: var(--gray-900);
  margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--gray-200);
}
.floating-legend .l-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.floating-legend .l-row:last-child { margin-bottom: 0; }
.floating-legend .node-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; box-shadow: 0 0 0 2px rgba(255,255,255,0.8); }
.floating-legend .exp { background: #4D80F0; }
.floating-legend .mol { background: #42A5F5; }
.floating-legend .bio { background: #26A69A; }
.floating-legend .dis { background: #EF5350; }
.floating-legend .int { background: #66BB6A; }
.zoom-controls {
  position: absolute; bottom: 20px; right: 20px;
  background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px);
  border-radius: 12px; padding: 10px 8px; box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  z-index: 10; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 10px;
}
.zoom-controls :deep(.el-button) {
  width: 32px; height: 32px; padding: 0 !important; margin: 0 !important;
  display: flex; align-items: center; justify-content: center;
}
.zoom-controls :deep(.el-icon) {
  display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;
}
.zoom-level {
  font-size: 0.75rem; font-weight: 700; color: var(--gray-700); text-align: center; width: 100%;
}
/* =========================================================
   ✅ 修复 2：滑动条 终极修复 (适配Element Plus 2.7+ 新类名)
   ========================================================= */
.single-chart-container {
  width: 100%;
  margin-bottom: 40px;
}
.full-width-card {
  width: 100%;
  padding: 32px;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 16px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.chart-title {
  font-size: 1.4rem;
  font-weight: 900;
  color: var(--gray-900);
  margin: 0;
}
.chart-tag {
  background: linear-gradient(135deg, var(--primary), #6366F1);
  color: #fff;
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 700;
}
.chart-desc {
  font-size: 1rem;
  color: var(--gray-600);
  line-height: 1.5;
  margin: 0;
  max-width: 60%;
}
.what-if-panel { 
  background: #F8FAFC; 
  border: 1px solid var(--gray-200);
  border-radius: 12px;
  padding: 28px;
}
.what-if-panel .what-if-body { 
  display: flex; 
  flex-direction: column; 
  gap: 24px; 
}
.what-if-panel .control-grid.two-column { 
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px 40px;
  background: #fff;
  border: 1px solid var(--gray-200); 
  border-radius: 12px; 
  padding: 24px; 
}
.what-if-panel .ctrl-row { 
  display: flex; 
  align-items: center; 
  justify-content: space-between;
  gap: 16px;
}
.what-if-panel .c-label { 
  width: 160px; 
  font-size: 0.95rem; 
  font-weight: 700; 
  color: var(--gray-700);
  flex-shrink: 0;
}
.what-if-panel .c-action { 
  flex: 1;
}
.what-if-panel .c-val { 
  width: 50px; 
  text-align: right; 
  font-family: 'JetBrains Mono', monospace; 
  font-weight: 800; 
  color: var(--primary);
  font-size: 1rem;
}
/* ✅ 核心修复：使用Element Plus最新类名 el-slider__track */
:deep(.el-slider) { 
  flex: 1; 
  margin: 0 8px;
}
:deep(.el-slider__runway) { 
  background-color: #E5E7EB !important; /* 标准浅灰色底轨 */
  height: 8px !important; /* 加粗轨道 */
  border-radius: 4px !important; 
}
:deep(.el-slider__track) { 
  background: var(--primary) !important; /* 纯正蓝色激活轨道 */
  height: 8px !important; 
  border-radius: 4px !important; 
}
:deep(.el-slider__button) { 
  border: 3px solid var(--primary) !important; /* 加粗蓝色边框 */
  background-color: #ffffff !important; /* 纯白内心 */
  width: 22px !important; /* 放大滑块 */
  height: 22px !important; 
  box-shadow: 0 2px 8px rgba(31, 119, 180, 0.25) !important;
  margin-top: 0 !important;
  transition: all 0.2s ease;
}
:deep(.el-slider__button:hover) {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(31, 119, 180, 0.35) !important;
}
/* 强化结果比对区域 */
.simulation-result.enhanced {
  background: #ffffff !important;
  border-radius: 12px;
  padding: 24px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
  border: 1px solid var(--gray-200);
  position: relative;
  overflow: hidden;
}
.simulation-result.enhanced::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 4px;
  background: linear-gradient(90deg, var(--primary), var(--success));
}
.sr-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-align: center;
}
.simulation-result.enhanced .sr-val {
  font-size: 3.5rem;
  font-weight: 900;
  font-family: 'JetBrains Mono', monospace;
  line-height: 1;
  color: var(--gray-900) !important;
  text-shadow: none !important;
}
.simulation-result.enhanced .sr-label {
  font-size: 0.9rem;
  color: var(--gray-500) !important;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 700;
}
.simulation-result.enhanced .sr-val small {
  font-size: 1.5rem;
  color: var(--gray-400) !important;
  margin-left: 4px;
}
.simulation-result.enhanced .sr-divider {
  font-size: 2rem;
  color: var(--gray-300) !important;
}
.simulation-result.enhanced .safe-text {
  color: var(--success) !important;
  text-shadow: none !important;
}
.gain-indicator.enhanced {
  text-align: right;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--gray-700);
  margin-top: 8px;
  padding-right: 16px;
}
.gain-indicator.enhanced .gain-value {
  font-size: 1.8rem;
  color: var(--success);
  font-weight: 900;
  text-shadow: none !important;
}
/* 节点详情抽屉样式 */
.node-detail-content { padding: 10px 0; }
.node-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
.node-badge { width: 60px; height: 60px; border-radius: 12px; color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.2rem; }
.detail-section { margin-bottom: 24px; }
.section-title { font-size: 1rem; font-weight: 800; color: var(--gray-900); margin-bottom: 12px; }
.detail-text { color: var(--gray-700); line-height: 1.6; }
.relation-list { display: flex; flex-wrap: wrap; gap: 8px; }
.relation-tag { margin: 0 !important; }
.shap-bar { height: 24px; background: var(--gray-100); border-radius: 12px; overflow: hidden; position: relative; }
.shap-bar-fill { height: 100%; background: linear-gradient(90deg, var(--primary), #6366F1); border-radius: 12px; transition: width 0.5s ease; }
.shap-value { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-weight: 700; color: var(--gray-900); }
.reference-list { display: flex; flex-direction: column; gap: 12px; }
.reference-item { display: flex; flex-direction: column; gap: 4px; }
.ref-title { font-weight: 600; color: var(--gray-900); }
.ref-source { font-size: 0.85rem; color: var(--gray-600); }
/* 底部操作栏 */
.bottom-action-bar { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 24px 32px; border-radius: 16px; border: 1px solid var(--gray-200); margin-top: 40px; box-shadow: 0 10px 30px -5px rgba(0,0,0,0.08); }
.bottom-action-bar .final-run-btn { background: linear-gradient(135deg, var(--primary), #6366F1); border: none; font-weight: 700; color: #fff; padding: 12px 24px; transition: all 0.3s ease; }
.bottom-action-bar .final-run-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 25px rgba(14, 165, 233, 0.3); }
/* 滚动动画 */
.animate-on-scroll { opacity: 0; transform: translateY(30px); transition: 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
.animate-on-scroll.is-visible { opacity: 1; transform: translateY(0); }
.delay-1 { transition-delay: 0.1s; } .delay-2 { transition-delay: 0.2s; } .delay-3 { transition-delay: 0.3s; } .delay-4 { transition-delay: 0.4s; }
</style>