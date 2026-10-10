<template>
  <div class="system-layout flex w-full h-screen overflow-hidden bg-[#F8FAFC] font-sans text-slate-800">
    <div class="fixed top-0 left-0 right-0 h-0.75 bg-liner-to-r from-[#0F172A] via-[#3B82F6] to-[#10B981] z-100"></div>

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

      <div class="page-container px-10 py-8 max-w-400 mx-auto w-full pb-24 flex flex-col gap-6">
        
        <div class="global-control-bar animate-on-scroll">
          <div class="control-group">
            <span class="control-label">暴露因子选择</span>
            <el-select v-model="selectedMetals" multiple placeholder="选择重金属" size="large" clearable collapse-tags collapse-tags-tooltip>
              <el-option v-for="m in metalOptions" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </div>
          
          <div class="control-group">
            <span class="control-label">目标疾病靶点</span>
            <el-select v-model="selectedDiseases" multiple placeholder="选择目标疾病" size="large" clearable collapse-tags collapse-tags-tooltip>
              <el-option v-for="d in diseaseOptions" :key="d.value" :label="d.label" :value="d.value" />
            </el-select>
          </div>
          
          <div class="control-group">
            <span class="control-label">群体暴露年限</span>
            <div class="slider-row">
              <el-slider v-model="exposureYears" :min="1" :max="30" :show-tooltip="false" class="control-slider" />
              <span class="slider-value font-mono font-black">{{ exposureYears }}<small class="text-xs font-sans font-bold text-slate-400 ml-0.5">年</small></span>
            </div>
          </div>
          
          <!-- ✅ 修改4：人群分组UI完全还原为causal原始样式，移除自定义类 -->
          <div class="control-group">
            <span class="control-label">人群分组</span>
            <el-radio-group v-model="populationGroup" size="large">
              <el-radio-button value="adult">成人</el-radio-button>
              <el-radio-button value="child">儿童</el-radio-button>
              <el-radio-button value="elder">老人</el-radio-button>
            </el-radio-group>
          </div>

          <div class="control-actions">
            <el-button type="primary" size="large" class="shadow-md shadow-blue-500/10 font-bold" @click="applyFilter">应用筛选</el-button>
            <el-button size="large" class="font-bold border-slate-300 text-slate-600" @click="resetFilter">重置</el-button>
          </div>
        </div>

        <div class="research-kpi-grid animate-on-scroll delay-1">
          <div class="r-kpi-card danger-level">
            <div class="kpi-icon danger"><el-icon><Warning /></el-icon></div>
            <div class="kpi-info">
              <span class="kpi-tag">综合因果风险评分</span>
              <div class="flex items-center gap-2 mt-0.5">
                <strong class="kpi-val font-mono tracking-tight">{{ animatedRiskScore }}<small class="text-lg font-bold text-slate-400">%</small></strong>
                <el-tag effect="dark" :type="kpiData.riskTagType" size="small" class="font-bold rounded-md uppercase tracking-wider shadow-sm">{{ kpiData.riskLevel }}</el-tag>
              </div>
              <span class="kpi-delta text-danger flex items-center gap-1 text-[0.78rem] font-bold mt-1">
                <el-icon><TopRight /></el-icon> {{ kpiData.riskDesc }}
              </span>
            </div>
          </div>
          
          <div class="r-kpi-card">
            <div class="kpi-icon primary"><el-icon><TrendCharts /></el-icon></div>
            <div class="kpi-info">
              <span class="kpi-tag">主导致病因子</span>
              <strong class="kpi-val tracking-tight text-slate-900 mt-0.5">{{ kpiData.mainFactor }}</strong>
              <span class="kpi-delta text-slate-400 text-[0.78rem] font-semibold mt-1">{{ kpiData.factorDesc }}</span>
            </div>
          </div>

          <div class="r-kpi-card">
            <div class="kpi-icon success"><el-icon><CircleCheck /></el-icon></div>
            <div class="kpi-info">
              <span class="kpi-tag">推断置信度</span>
              <strong class="kpi-val tracking-tight text-blue-600 font-mono mt-0.5">{{ kpiData.confidence }}<small class="text-lg font-bold text-slate-400">%</small></strong>
              <span class="kpi-delta text-emerald-500 flex items-center gap-1 text-[0.78rem] font-bold mt-1">
                <el-icon><Select /></el-icon> {{ kpiData.confidenceDesc }}
              </span>
            </div>
          </div>

          <div class="r-kpi-card">
            <div class="kpi-icon warning"><el-icon><Timer /></el-icon></div>
            <div class="kpi-info">
              <span class="kpi-tag">最优干预优先级</span>
              <strong class="kpi-val tracking-tight text-amber-500 font-mono mt-0.5">{{ kpiData.interventionTier }}</strong>
              <span class="kpi-delta text-slate-400 text-[0.78rem] font-semibold mt-1">{{ kpiData.interventionDesc }}</span>
            </div>
          </div>
        </div>

        <section class="core-dag-section animate-on-scroll delay-2">
          <div class="section-header">
            <div class="header-left">
              <div class="title-badge shadow-sm">核心分析引擎</div>
              <h2 class="section-title">全景多模态复合暴露有向无环图 (DAG)</h2>
              <p class="section-desc">
                数字解析10种重金属在生物体内积蓄的完整链路，呈现从日常接触、病理分子触发到终末组织器官病变的发展进程。<br>
                <span class="text-blue-500 font-semibold">互动提示：</span>鼠标悬停查看因果强度，点击任一机制节点激活三维 SHAP 归因及权威文献网络。
              </p>
            </div>
            <div class="header-info">
              <div class="info-card shadow-sm">
                <div class="info-icon"><el-icon><Document /></el-icon></div>
                <div class="info-text">
                  <div class="info-label">知识图谱基线来源</div>
                  <div class="info-value">权威毒理研究联合数据库</div>
                </div>
              </div>
              <div class="info-card shadow-sm">
                <div class="info-icon"><el-icon><Clock /></el-icon></div>
                <div class="info-text">
                  <div class="info-label">模型推理引擎更新</div>
                  <div class="info-value font-mono">2026-05-12</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="dag-viewport shadow-inner" 
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
            
            <div class="floating-legend border border-slate-200/80 shadow-xl">
              <div class="legend-title">图层节点说明</div>
              <div class="l-row"><i class="node-dot exp"></i> 重金属暴露层</div>
              <div class="l-row"><i class="node-dot mol"></i> 分子/病理机制层</div>
              <div class="l-row"><i class="node-dot bio"></i> 生物组织损伤层</div>
              <div class="l-row"><i class="node-dot dis"></i> 临床终末疾病层</div>
              <div class="l-row"><i class="node-dot int"></i> 医疗干预屏障层</div>
            </div>
            
            <!-- ✅ 修改3：缩放控件（图三）移至右下角 -->
            <div class="zoom-controls border border-slate-200/80 shadow-lg">
              <el-button size="small" circle @click="zoomIn" class="hover:bg-slate-100"><el-icon><ZoomIn /></el-icon></el-button>
              <div class="zoom-level font-mono font-black text-slate-700">{{ Math.round(zoom * 100) }}%</div>
              <el-button size="small" circle @click="zoomOut" class="hover:bg-slate-100"><el-icon><ZoomOut /></el-icon></el-button>
              <el-button size="small" circle @click="resetView" class="hover:bg-slate-100"><el-icon><Refresh /></el-icon></el-button>
            </div>
          </div>
        </section>

        <div class="single-chart-container animate-on-scroll delay-3">
          <div class="chart-card full-width-card border border-slate-200 shadow-xl">
            <div class="chart-header">
              <div class="header-left">
                <h3 class="chart-title">反事实因果模拟推演沙盘</h3>
                <span class="chart-tag shadow-sm">数字孪生系统</span>
              </div>
              <p class="chart-desc text-slate-500">
                通过模拟削减特定重金属暴露或提前部署抗氧化/螯合屏障，实时评估由于“反事实消除”引发的整体健康危险系数缩减额度。
              </p>
            </div>

            <div class="what-if-panel bg-slate-50 border border-slate-200 rounded-2xl p-7">
              <div class="what-if-body">
                <div class="control-grid two-column bg-white border border-slate-200 rounded-xl p-6 shadow-sm">
                  <div class="ctrl-row">
                    <span class="c-label">Pb (铅) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simPb" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simPb }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">As (砷) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simAs" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simAs }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Cd (镉) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCd" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simCd }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Hg (汞) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simHg" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simHg }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Cr (铬) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCr" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simCr }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Ni (镍) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simNi" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simNi }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Co (钴) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simCo" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simCo }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Li (锂) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simLi" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simLi }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Al (铝) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simAl" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simAl }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">Mn (锰) 暴露降低</span>
                    <div class="c-action"><el-slider v-model="simMn" :min="0" :max="100" class="sci-slider primary" :show-tooltip="false" /></div>
                    <span class="c-val font-mono">{{ simMn }}%</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">抗氧化干预治疗开关</span>
                    <div class="c-action flex items-center"><el-switch v-model="simMed" active-color="#10B981" /></div>
                    <span :class="['c-val font-bold text-[0.88rem]', simMed ? 'text-emerald-500' : 'text-slate-400']">{{ simMed ? '开启' : '关闭' }}</span>
                  </div>
                  <div class="ctrl-row">
                    <span class="c-label">临床螯合清除疗法</span>
                    <div class="c-action flex items-center"><el-switch v-model="simEDTA" active-color="#6366F1" /></div>
                    <span :class="['c-val font-bold text-[0.88rem]', simEDTA ? 'text-indigo-500' : 'text-slate-400']">{{ simEDTA ? '开启' : '关闭' }}</span>
                  </div>
                </div>

                <div class="simulation-result enhanced border border-slate-200/80">
                  <div class="sr-box source-baseline">
                    <div class="sr-header-tag">Baseline</div>
                    <span class="sr-label">历史当前基线风险</span>
                    <span class="sr-val text-slate-700">{{ baseRisk }}<small>%</small></span>
                  </div>
                  
                  <!-- ✅ 修改2：箭头位置向右调整，虚线延长并右移 -->
                  <div class="sr-arrow-wrapper">
                    <div class="sr-arrow-line"></div>
                    <el-icon class="text-slate-400 text-xl"><ArrowRight /></el-icon>
                  </div>
                  
                  <div class="sr-box target-prediction" :class="{ 'is-safe-mode': simulatedRisk < 50 }">
                    <div class="sr-header-tag">Counterfactual</div>
                    <span class="sr-label">干预期望预测风险</span>
                    <span class="sr-val font-black">{{ simulatedRisk }}<small>%</small></span>
                  </div>
                </div>

                <div class="gain-indicator enhanced text-right font-bold text-slate-600">
                  量化预期干预总收益: <strong class="gain-value font-mono font-black text-2xl text-emerald-500 ml-1">-{{ (92.4 - simulatedRisk).toFixed(1) }}%</strong>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="bottom-action-bar animate-on-scroll delay-4 border border-slate-200 shadow-xl bg-white/90 backdrop-blur-md">
          <el-button type="info" size="large" plain class="border-slate-300 text-slate-600 font-bold" @click="goToWorkspace">
            <el-icon class="mr-1"><ArrowLeft /></el-icon> 返回数据流总览
          </el-button>
          <el-button type="primary" size="large" class="final-run-btn font-bold shadow-lg shadow-blue-500/20" @click="goToPlan">
            基于上述因果路由生成精准干预策略
            <el-icon class="ml-1"><ArrowRight /></el-icon>
          </el-button>
        </div>
      </div>
    </main>

    <el-drawer v-model="drawerVisible" title="节点多维度精细机制说明" direction="rtl" size="440px" :close-on-click-modal="true" custom-class="scientific-drawer">
      <div v-if="selectedNode" class="node-detail-content px-1 flex flex-col gap-6">
        <div class="node-header flex items-center justify-between border-b border-slate-100 pb-4">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 rounded-xl text-white flex items-center justify-center font-black text-lg shadow-md" :style="{backgroundColor: selectedNode.itemStyle.color, boxShadow: `0 4px 14px ${selectedNode.itemStyle.color}40`}">
              {{ selectedNode.name.split(' ')[0] }}
            </div>
            <div class="flex flex-col">
              <span class="text-base font-black text-slate-900">{{ selectedNode.name }}</span>
              <span class="text-xs text-slate-400 font-semibold font-mono">ID: {{ selectedNode.id }}</span>
            </div>
          </div>
          <el-tag :type="getNodeCategoryTag(selectedNode.category)" size="large" class="font-bold rounded-md shadow-sm">{{ getNodeCategoryName(selectedNode.category) }}</el-tag>
        </div>
        
        <div class="detail-section bg-slate-50 border border-slate-200/60 rounded-xl p-4">
          <h4 class="section-title text-slate-900 flex items-center gap-1.5"><span class="w-1.5 h-3.5 bg-blue-500 rounded-sm"></span>科学机制描述</h4>
          <p class="detail-text text-slate-600 text-sm leading-relaxed mt-2">{{ selectedNode.tooltip }}</p>
        </div>

        <div class="detail-section">
          <h4 class="section-title text-slate-900 flex items-center gap-1.5"><span class="w-1.5 h-3.5 bg-sky-500 rounded-sm"></span>上游暴露/触发因素</h4>
          <div class="relation-list mt-2 flex flex-wrap gap-1.5">
            <el-tag v-for="item in getUpstreamNodes(selectedNode.id)" :key="item.id" class="relation-tag font-semibold rounded-md border-slate-200 bg-white" size="large" type="info">
               {{ item.name }}
            </el-tag>
            <span v-if="getUpstreamNodes(selectedNode.id).length === 0" class="text-xs text-slate-400 font-medium italic pl-1">暂无直击上游通路</span>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title text-slate-900 flex items-center gap-1.5"><span class="w-1.5 h-3.5 bg-red-400 rounded-sm"></span>下游级联影响路径</h4>
          <div class="relation-list mt-2 flex flex-wrap gap-1.5">
            <el-tag v-for="item in getDownstreamNodes(selectedNode.id)" :key="item.id" class="relation-tag font-semibold rounded-md border-red-100 bg-red-50/50" size="large" type="danger">
               {{ item.name }}
            </el-tag>
            <span v-if="getDownstreamNodes(selectedNode.id).length === 0" class="text-xs text-slate-400 font-medium italic pl-1">已达临床或末端终点</span>
          </div>
        </div>

        <div class="detail-section">
          <h4 class="section-title text-slate-900 flex items-center gap-1.5"><span class="w-1.5 h-3.5 bg-indigo-500 rounded-sm"></span>SHAP 独立贡献度占比</h4>
          <div class="shap-container mt-2.5">
            <div class="shap-bar border border-slate-200">
              <div class="shap-bar-fill" :style="{width: `${selectedNode.shapValue * 100}%`}"></div>
              <span class="shap-value font-mono font-black text-xs text-slate-700">{{ (selectedNode.shapValue * 100).toFixed(1) }}%</span>
            </div>
          </div>
        </div>

        <div class="detail-section border-t border-slate-100 pt-4">
          <h4 class="section-title text-slate-900 flex items-center gap-1.5 mb-2.5"><span class="w-1.5 h-3.5 bg-emerald-500 rounded-sm"></span>支撑性权威文献</h4>
          <div class="reference-list flex flex-col gap-3">
            <div class="reference-item bg-slate-50/50 hover:bg-slate-50 border border-slate-200/40 p-3 rounded-lg transition-colors flex flex-col gap-1">
              <span class="ref-title text-sm font-bold text-slate-800">《重金属毒理学与健康风险评估》</span>
              <span class="ref-source text-xs text-slate-400 font-medium">人民卫生出版社, 2025</span>
            </div>
            <div class="reference-item bg-slate-50/50 hover:bg-slate-50 border border-slate-200/40 p-3 rounded-lg transition-colors flex flex-col gap-1">
              <span class="ref-title text-sm font-bold text-slate-800">Environmental Health Perspectives</span>
              <span class="ref-source text-xs text-slate-400 font-medium font-mono">Vol.133, No.5, 2025</span>
            </div>
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, onBeforeUnmount, watch } from 'vue'
import { 
  ArrowLeft, TopRight, Select, TrendCharts, Warning, CircleCheck, Timer, ZoomIn, ZoomOut, ArrowRight, Refresh, Document, Clock
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

// 全局控制变量
const selectedMetals = ref([])
const selectedDiseases = ref([])
const exposureYears = ref(10)
const populationGroup = ref('adult')

const metalOptions = [
  { label: 'Pb (铅)', value: 'Pb' },
  { label: 'Cd (镉)', value: 'Cd' },
  { label: 'As (砷)', value: 'As' },
  { label: 'Hg (汞)', value: 'Hg' },
  { label: 'Cr (铬)', value: 'Cr' },
  { label: 'Ni (镍)', value: 'Ni' },
  { label: 'Co (钴)', value: 'Co' },
  { label: 'Li (锂)', value: 'Li' },
  { label: 'Al (铝)', value: 'Al' },
  { label: 'Mn (锰)', value: 'Mn' }
]

const diseaseOptions = [
  { label: '慢性肾病', value: 'CKD' },
  { label: '神经疾病', value: 'Neuro' },
  { label: '肝纤维化', value: 'LiverDis' },
  { label: '骨质疏松', value: 'Osteo' },
  { label: '多器官癌变', value: 'Cancer' }
]

// KPI场景映射表
const kpiBaseData = [
  {
    id: 'full', riskScore: 92.4, riskLevel: 'Level 3 高危', riskTagType: 'danger', riskDesc: '10种重金属协同暴露',
    mainFactor: 'Pb (铅) ⊕ As (砷)', factorDesc: '强协同致病效应', confidence: 96.8, confidenceDesc: '贝叶斯后验概率极高',
    interventionTier: 'Tier 1', interventionDesc: '推荐启动临床螯合阻断'
  },
  {
    id: 'pb-as-ckd', riskScore: 94.4, riskLevel: 'Level 3 高危', riskTagType: 'danger', riskDesc: 'Pb+As协同肾毒性',
    mainFactor: 'Pb (铅) ⊕ As (砷)', factorDesc: '强协同肾损伤效应', confidence: 95.2, confidenceDesc: '肾脏通路推断置信度高',
    interventionTier: 'Tier 1', interventionDesc: '优先启动肾脏保护治疗'
  },
  {
    id: 'cd-bone', riskScore: 78.5, riskLevel: 'Level 2 中危', riskTagType: 'warning', riskDesc: 'Cd慢性骨代谢损伤',
    mainFactor: 'Cd (镉)', factorDesc: '骨骼蓄积导致骨流失', confidence: 92.1, confidenceDesc: '骨代谢通路推断可靠',
    interventionTier: 'Tier 2', interventionDesc: '建议补充钙+维生素D干预'
  },
  {
    id: 'hg-neuro', riskScore: 88.3, riskLevel: 'Level 3 高危', riskTagType: 'danger', riskDesc: 'Hg中枢神经毒性',
    mainFactor: 'Hg (汞)', factorDesc: '血脑屏障穿透导致神经损伤', confidence: 97.5, confidenceDesc: '神经通路推断置信度极高',
    interventionTier: 'Tier 1', interventionDesc: '优先启动神经保护治疗'
  },
  {
    id: 'low-risk', riskScore: 45.2, riskLevel: 'Level 1 低危', riskTagType: 'success', riskDesc: '单金属低剂量暴露',
    mainFactor: 'Cr (铬)', factorDesc: '低剂量暴露影响有限', confidence: 88.6, confidenceDesc: '数据有限，置信度中等',
    interventionTier: 'Tier 3', interventionDesc: '建议定期监测，暂无需干预'
  }
]

const kpiData = ref({ ...kpiBaseData[0] })

// 节点详情抽屉控制
const drawerVisible = ref(false)
const selectedNode = ref(null)

// 拓扑视图底座参数
const animatedRiskScore = ref(0)
const zoom = ref(1)
const panX = ref(0)
const panY = ref(0)
const isPanning = ref(false)
let startX = 0, startY = 0

// 反事实 sandbox 初始值
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

const causalGraphRef = ref(null)
let chartsInstances = []
let causalChartInstance = null

const clearCharts = () => { 
  chartsInstances.forEach(c => c.dispose())
  chartsInstances = [] 
}

// 核心拓扑图骨架数据定义
const baseNodes = [
  { id: 'Pb', name: 'Pb (铅)', category: 0, x: 80, y: 60, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：冶炼、废旧电池、含铅管道、含铅涂料等', shapValue: 0.92 },
  { id: 'Cd', name: 'Cd (镉)', category: 0, x: 80, y: 140, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：电镀、电池、颜料、PVC塑料稳定剂、工业废水', shapValue: 0.56 },
  { id: 'As', name: 'As (砷)', category: 0, x: 80, y: 220, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：木材防腐剂、有色金属冶炼、地下水污染', shapValue: 0.68 },
  { id: 'Hg', name: 'Hg (汞)', category: 0, x: 80, y: 300, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：氯碱工业、采矿、荧光灯、燃煤排放污染', shapValue: 0.44 },
  { id: 'Cr', name: 'Cr (铬)', category: 0, x: 80, y: 380, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：电镀铬、皮革鞣制、铬黄颜料、合金制造', shapValue: 0.38 },
  { id: 'Ni', name: 'Ni (镍)', category: 0, x: 80, y: 460, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：不锈钢精炼、镍镉电池、电镀废气、工业粉尘', shapValue: 0.32 },
  { id: 'Co', name: 'Co (钴)', category: 0, x: 80, y: 540, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：硬质合金加工、锂电池正极、磁性材料冶炼', shapValue: 0.24 },
  { id: 'Li', name: 'Li (锂)', category: 0, x: 80, y: 620, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：锂电池组装、特种陶瓷玻璃、工业制冷剂', shapValue: 0.08 },
  { id: 'Al', name: 'Al (铝)', category: 0, x: 80, y: 700, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：铝电解冶炼、焊接粉尘、净水处理剂残留', shapValue: 0.12 },
  { id: 'Mn', name: 'Mn (锰)', category: 0, x: 80, y: 780, symbolSize: 52, itemStyle: { color: '#3B82F6' }, tooltip: '主要来源：锰铁合金冶炼、高强度电焊、化肥农药制造', shapValue: 0.18 },

  { id: 'ROS', name: '氧化应激', category: 1, x: 220, y: 100, symbolSize: 52, itemStyle: { color: '#0EA5E9' }, tooltip: '重金属诱导ROS过量生成，破坏抗氧化系统，引发脂质过氧化与DNA损伤', shapValue: 0.75 },
  { id: 'DNA', name: 'DNA损伤', category: 1, x: 220, y: 220, symbolSize: 52, itemStyle: { color: '#0EA5E9' }, tooltip: '重金属直接与DNA结合或通过ROS间接攻击，导致链断裂、突变和表观遗传改变', shapValue: 0.82 },
  { id: 'Mito', name: '线粒体紊乱', category: 1, x: 220, y: 340, symbolSize: 52, itemStyle: { color: '#0EA5E9' }, tooltip: '重金属抑制线粒体呼吸链，导致ATP生成障碍和ROS爆发', shapValue: 0.65 },
  { id: 'Endo', name: '内皮损伤', category: 1, x: 220, y: 460, symbolSize: 52, itemStyle: { color: '#0EA5E9' }, tooltip: '重金属破坏血管内皮屏障，导致通透性增加和炎症反应', shapValue: 0.58 },
  { id: 'Infla', name: '神经炎症', category: 1, x: 220, y: 580, symbolSize: 52, itemStyle: { color: '#0EA5E9' }, tooltip: '重金属激活小胶质细胞和星形胶质细胞，释放促炎因子，引发神经毒性', shapValue: 0.70 },

  { id: 'Kidney', name: '肾损伤', category: 2, x: 360, y: 160, symbolSize: 52, itemStyle: { color: '#14B8A6' }, tooltip: '重金属在肾小管蓄积，直接损伤近端小管上皮细胞，导致肾功能下降', shapValue: 0.88 },
  { id: 'Liver', name: '肝损伤', category: 2, x: 360, y: 280, symbolSize: 52, itemStyle: { color: '#14B8A6' }, tooltip: '重金属在肝脏蓄积，引发肝细胞坏死、纤维化和肝功能障碍', shapValue: 0.72 },
  { id: 'BBB', name: '血脑屏障', category: 2, x: 360, y: 400, symbolSize: 52, itemStyle: { color: '#14B8A6' }, tooltip: '重金属破坏血脑屏障完整性，导致神经毒性物质进入中枢神经系统', shapValue: 0.85 },
  { id: 'Bone', name: '骨骼蓄积', category: 2, x: 360, y: 520, symbolSize: 52, itemStyle: { color: '#14B8A6' }, tooltip: '重金属替代骨骼中的钙，长期蓄积导致骨质疏松和骨代谢紊乱', shapValue: 0.62 },
  { id: 'Blood', name: '造血障碍', category: 2, x: 360, y: 640, symbolSize: 52, itemStyle: { color: '#14B8A6' }, tooltip: '重金属抑制骨髓造血功能，导致贫血和免疫功能下降', shapValue: 0.55 },

  { id: 'Neuro', name: '神经疾病', category: 3, x: 500, y: 160, symbolSize: 52, itemStyle: { color: '#EF4444' }, tooltip: '重金属诱导的神经炎症和氧化应激，导致认知障碍、帕金森样症状和神经退行性疾病', shapValue: 0.90 },
  { id: 'CKD', name: '慢性肾病', category: 3, x: 500, y: 280, symbolSize: 52, itemStyle: { color: '#EF4444' }, tooltip: '长期重金属暴露导致肾小管不可逆损伤，进展为慢性肾病和肾功能衰竭', shapValue: 0.95 },
  { id: 'LiverDis', name: '肝纤维化', category: 3, x: 500, y: 400, symbolSize: 52, itemStyle: { color: '#EF4444' }, tooltip: '重金属诱导的慢性肝损伤，进展为肝纤维化、肝硬化，甚至肝癌', shapValue: 0.78 },
  { id: 'Osteo', name: '骨质疏松', category: 3, x: 500, y: 520, symbolSize: 52, itemStyle: { color: '#EF4444' }, tooltip: '重金属在骨骼蓄积，破坏骨代谢平衡，导致骨质疏松和骨折风险增加', shapValue: 0.68 },
  { id: 'Cancer', name: '多器官癌变', category: 3, x: 500, y: 640, symbolSize: 52, itemStyle: { color: '#EF4444' }, tooltip: '重金属的DNA损伤和突变作用，导致多种器官癌变风险显著升高', shapValue: 0.88 },

  { id: 'EDTA', name: '螯合治疗', category: 4, x: 640, y: 220, symbolSize: 52, itemStyle: { color: '#10B981' }, tooltip: 'EDTA等螯合剂可与重金属形成稳定复合物，促进其从体内排出', shapValue: 0.0 },
  { id: 'Antiox', name: '抗氧化治疗', category: 4, x: 640, y: 380, symbolSize: 52, itemStyle: { color: '#10B981' }, tooltip: '补充维生素C/E、N-乙酰半胱氨酸等，清除自由基，减轻氧化应激损伤', shapValue: 0.0 },
  { id: 'Protect', name: '靶器官保护', category: 4, x: 640, y: 540, symbolSize: 52, itemStyle: { color: '#10B981' }, tooltip: '针对肝肾等靶器官进行保护治疗，减轻重金属造成的损伤', shapValue: 0.0 }
]

const rawLinks = [
  { source: 'Pb', target: 'ROS', lineStyle: { color: '#3B82F6' }, curveness: 0.1, tooltip: 'Pb²⁺可替代Ca²⁺干扰细胞信号通路，诱导氧化应激和表观遗传变化；与硫醇(-SH)结合损伤蛋白质。', strength: 0.9, confidence: 0.95 },
  { source: 'Pb', target: 'Kidney', lineStyle: { color: '#3B82F6' }, curveness: 0.1, tooltip: 'Pb在肾小管蓄积，直接损伤近端小管上皮细胞，导致肾功能下降。', strength: 0.85, confidence: 0.92 },
  { source: 'Pb', target: 'BBB', lineStyle: { color: '#3B82F6' }, curveness: 0.1, tooltip: 'Pb破坏血脑屏障完整性，进入中枢神经系统，引发神经毒性。', strength: 0.88, confidence: 0.90 },
  { source: 'Cd', target: 'Kidney', lineStyle: { color: '#8B5CF6' }, tooltip: 'Cd²⁺主要在肾脏蓄积，通过氧化应激和细胞凋亡导致肾小管损伤，是Cd中毒最主要的靶器官。', strength: 0.95, confidence: 0.98 },
  { source: 'Cd', target: 'Bone', lineStyle: { color: '#8B5CF6' }, tooltip: 'Cd替代骨骼中的钙，长期蓄积导致骨代谢紊乱和骨质疏松。', strength: 0.75, confidence: 0.85 },
  { source: 'As', target: 'DNA', lineStyle: { color: '#F59E0B' }, curveness: -0.1, tooltip: 'As诱导DNA链断裂和基因突变，是明确的致癌物，可导致多种器官癌变。', strength: 0.92, confidence: 0.99 },
  { source: 'As', target: 'Liver', lineStyle: { color: '#F59E0B' }, curveness: -0.1, tooltip: 'As在肝脏蓄积，引发肝细胞损伤和肝纤维化，是肝损伤的重要诱因。', strength: 0.80, confidence: 0.88 },
  { source: 'Hg', target: 'Infla', lineStyle: { color: '#EC4899' }, curveness: -0.2, tooltip: 'Hg激活小胶质细胞和星形胶质细胞，释放促炎因子，引发神经炎症反应。', strength: 0.88, confidence: 0.92 },
  { source: 'Hg', target: 'BBB', lineStyle: { color: '#EC4899' }, curveness: -0.2, tooltip: 'Hg极易通过血脑屏障，在中枢神经系统蓄积，导致不可逆的神经损伤。', strength: 0.95, confidence: 0.97 },
  { source: 'Cr', target: 'DNA', lineStyle: { color: '#A855F7' }, curveness: 0.15, tooltip: '六价铬是强致癌物，可直接攻击DNA，导致链断裂和突变，引发肺癌等多种癌症。', strength: 0.90, confidence: 0.98 },
  { source: 'Ni', target: 'DNA', lineStyle: { color: '#6366F1' }, curveness: -0.1, tooltip: 'Ni诱导DNA损伤和染色体畸变，是明确的致癌物，可导致肺癌和鼻咽癌。', strength: 0.85, confidence: 0.95 },
  { source: 'Ni', target: 'Infla', lineStyle: { color: '#6366F1' }, curveness: -0.1, tooltip: 'Ni可引发慢性炎症反应，促进肿瘤发生和进展。', strength: 0.70, confidence: 0.82 },
  { source: 'Co', target: 'Mito', lineStyle: { color: '#06B6D4' }, tooltip: 'Co抑制线粒体呼吸链功能，导致ATP生成障碍和ROS爆发，引发细胞损伤。', strength: 0.75, confidence: 0.85 },
  { source: 'Li', target: 'Endo', lineStyle: { color: '#84CC16' }, tooltip: 'Li破坏血管内皮屏障，导致通透性增加和炎症反应，影响肾功能。', strength: 0.60, confidence: 0.78 },
  { source: 'Al', target: 'BBB', lineStyle: { color: '#F97316' }, curveness: 0.2, tooltip: 'Al可通过受损的血脑屏障进入中枢神经系统，与神经退行性疾病相关。', strength: 0.65, confidence: 0.75 },
  { source: 'Mn', target: 'Infla', lineStyle: { color: '#EAB308' }, curveness: -0.3, tooltip: 'Mn诱导小胶质细胞激活和促炎因子释放，引发神经炎症和多巴胺能神经元损伤。', strength: 0.80, confidence: 0.88 },
  { source: 'Mn', target: 'BBB', lineStyle: { color: '#EAB308' }, curveness: -0.3, tooltip: 'Mn极易通过血脑屏障，在纹状体蓄积，导致帕金森样症状。', strength: 0.85, confidence: 0.90 },

  { source: 'ROS', target: 'Kidney', lineStyle: { color: '#0EA5E9' }, tooltip: 'ROS过量生成导致肾小管上皮细胞氧化损伤和凋亡，加重肾损伤。', strength: 0.85, confidence: 0.92 },
  { source: 'ROS', target: 'Liver', lineStyle: { color: '#0EA5E9' }, tooltip: 'ROS引发肝细胞脂质过氧化和氧化损伤，导致肝功能障碍。', strength: 0.78, confidence: 0.88 },
  { source: 'ROS', target: 'BBB', lineStyle: { color: '#0EA5E9' }, tooltip: 'ROS破坏血脑屏障的完整性，导致神经毒性物质进入中枢神经系统。', strength: 0.82, confidence: 0.90 },
  { source: 'DNA', target: 'Cancer', lineStyle: { color: '#0EA5E9' }, tooltip: 'DNA损伤和突变是重金属致癌的核心机制，可导致多种器官癌变。', strength: 0.95, confidence: 0.99 },
  { source: 'Mito', target: 'Liver', lineStyle: { color: '#0EA5E9' }, tooltip: '线粒体功能障碍导致肝细胞能量代谢紊乱和ROS生成，加重肝损伤。', strength: 0.72, confidence: 0.85 },
  { source: 'Endo', target: 'Kidney', lineStyle: { color: '#0EA5E9' }, tooltip: '内皮损伤导致肾血流量下降和肾功能障碍，加重肾损伤。', strength: 0.70, confidence: 0.82 },
  { source: 'Infla', target: 'BBB', lineStyle: { color: '#0EA5E9' }, tooltip: '神经炎症反应破坏血脑屏障，进一步加重中枢神经系统损伤。', strength: 0.78, confidence: 0.88 },

  { source: 'Kidney', target: 'CKD', lineStyle: { color: '#14B8A6' }, tooltip: '长期肾损伤进展为慢性肾病，最终导致肾功能衰竭。', strength: 0.98, confidence: 0.99 },
  { source: 'Liver', target: 'LiverDis', lineStyle: { color: '#14B8A6' }, tooltip: '慢性肝损伤进展为肝纤维化、肝硬化，甚至肝癌。', strength: 0.85, confidence: 0.92 },
  { source: 'BBB', target: 'Neuro', lineStyle: { color: '#14B8A6' }, tooltip: '血脑屏障破坏导致神经毒性物质进入中枢神经系统，引发神经退行性疾病。', strength: 0.92, confidence: 0.95 },
  { source: 'Bone', target: 'Osteo', lineStyle: { color: '#14B8A6' }, tooltip: '骨骼中重金属蓄积导致骨代谢紊乱，引发骨质疏松和骨折风险增加。', strength: 0.80, confidence: 0.88 },
  { source: 'Blood', target: 'Cancer', lineStyle: { color: '#14B8A6' }, tooltip: '造血系统损伤和免疫功能下降，增加肿瘤发生风险。', strength: 0.65, confidence: 0.75 },

  { source: 'EDTA', target: 'Pb', lineStyle: { color: '#34D399' }, curveness: 0.6, tooltip: 'EDTA与Pb形成稳定复合物，促进其从体内排出，降低体内蓄积水平。', strength: 0.90, confidence: 0.95 },
  { source: 'EDTA', target: 'Cd', lineStyle: { color: '#34D399' }, curveness: 0.6, tooltip: 'EDTA可与Cd结合，减少其在体内的蓄积，减轻肾毒性。', strength: 0.85, confidence: 0.92 },
  { source: 'Antiox', target: 'ROS', lineStyle: { color: '#A3E635' }, curveness: -0.4, tooltip: '抗氧化剂可清除自由基，减轻重金属诱导的氧化应激损伤。', strength: 0.80, confidence: 0.88 },
  { source: 'Protect', target: 'Kidney', lineStyle: { color: '#34D399' }, curveness: -0.4, tooltip: '肾保护治疗可减轻重金属对肾小管的损伤，延缓肾功能下降。', strength: 0.75, confidence: 0.85 }
]

const getUpstreamNodes = (nodeId) => rawLinks.filter(l => l.target === nodeId).map(l => baseNodes.find(n => n.id === l.source)).filter(Boolean)
const getDownstreamNodes = (nodeId) => rawLinks.filter(l => l.source === nodeId).map(l => baseNodes.find(n => n.id === l.target)).filter(Boolean)

const getNodeCategoryName = (category) => ['重金属暴露', '分子机制', '组织损伤', '临床疾病', '干预措施'][category]
const getNodeCategoryTag = (category) => ['primary', 'info', 'success', 'danger', 'success'][category]

// 联动过滤核心逻辑
const applyFilter = () => {
  let matchedKpi = kpiBaseData[0]
  if (selectedMetals.value.length > 0 || selectedDiseases.value.length > 0) {
    if (selectedMetals.value.includes('Pb') && selectedMetals.value.includes('As') && selectedDiseases.value.includes('CKD')) {
      matchedKpi = kpiBaseData[1]
    } else if (selectedMetals.value.includes('Cd') && selectedDiseases.value.includes('Osteo')) {
      matchedKpi = kpiBaseData[2]
    } else if (selectedMetals.value.includes('Hg') && selectedDiseases.value.includes('Neuro')) {
      matchedKpi = kpiBaseData[3]
    } else if (selectedMetals.value.length === 1 && selectedMetals.value[0] === 'Cr') {
      matchedKpi = kpiBaseData[4]
    } else {
      const riskAdjustment = (selectedMetals.value.length * 5) + (selectedDiseases.value.length * 3) + (exposureYears.value - 10) * 1.5
      matchedKpi = {
        ...kpiBaseData[0],
        riskScore: Math.min(98, 75 + riskAdjustment),
        riskDesc: `${selectedMetals.value.join(' + ')} 联合暴露`,
        mainFactor: selectedMetals.value.slice(0, 2).map(m => m + ' (元素)').join(' ⊕ ') || '多金属协同',
        factorDesc: '基于当前选择的核心暴露链条归因',
        confidence: Math.max(85, 96.8 - (selectedMetals.value.length * 1.5))
      }
    }
  }
  
  if (populationGroup.value === 'child') {
    matchedKpi.riskScore = Math.min(99, matchedKpi.riskScore * 1.08)
    matchedKpi.riskLevel = 'Level 3 高危'
    matchedKpi.riskTagType = 'danger'
  } else if (populationGroup.value === 'elder') {
    matchedKpi.riskScore = Math.min(99, matchedKpi.riskScore * 1.05)
  }
  
  kpiData.value = matchedKpi
  animateNumber(matchedKpi.riskScore)
  updateCausalGraph()
}

const resetFilter = () => {
  selectedMetals.value = []
  selectedDiseases.value = []
  exposureYears.value = 10
  populationGroup.value = 'adult'
  kpiData.value = { ...kpiBaseData[0] }
  animateNumber(kpiBaseData[0].riskScore)
  resetView()
  updateCausalGraph()
}

// 深度定制 ECharts 图谱渲染配额
const getKnowledgeGraphOption = () => {
  let nodes = JSON.parse(JSON.stringify(baseNodes))
  let links = JSON.parse(JSON.stringify(rawLinks))

  if (selectedMetals.value.length > 0 || selectedDiseases.value.length > 0) {
    let relevantNodeIds = new Set()
    selectedMetals.value.forEach(id => relevantNodeIds.add(id))
    selectedDiseases.value.forEach(id => relevantNodeIds.add(id))
    
    const addRelatedNodes = (nodeId) => {
      getUpstreamNodes(nodeId).forEach(n => {
        if (!relevantNodeIds.has(n.id)) { relevantNodeIds.add(n.id); addRelatedNodes(n.id) }
      })
      getDownstreamNodes(nodeId).forEach(n => {
        if (!relevantNodeIds.has(n.id)) { relevantNodeIds.add(n.id); addRelatedNodes(n.id) }
      })
    }
    relevantNodeIds.forEach(id => addRelatedNodes(id))
    
    nodes = nodes.filter(n => relevantNodeIds.has(n.id))
    links = links.filter(l => relevantNodeIds.has(l.source) && relevantNodeIds.has(l.target))
  }

  const yearMultiplier = 1 + (exposureYears.value - 10) * 0.02
  const populationMultiplier = populationGroup.value === 'child' ? 1.25 : populationGroup.value === 'elder' ? 1.15 : 1.0
  
  nodes.forEach(n => {
    if (n.category !== 4) {
      n.symbolSize = Math.round(n.symbolSize * yearMultiplier * populationMultiplier)
    }
  })

  // 反事实推演动态透明度阻断
  const checkOpacity = (src, val) => val > 0 ? Math.max(0.15, 1 - val / 100) : null
  const opacities = { Pb: simPb.value, As: simAs.value, Cd: simCd.value }
  
  links.forEach(l => {
    if (opacities[l.source] !== undefined) {
      const op = checkOpacity(l.source, opacities[l.source])
      if (op !== null) l.lineStyle.opacity = op
    }
    if (simMed.value && l.target === 'ROS') l.lineStyle.opacity = 0.25
    if (simEDTA.value && (l.source === 'Pb' || l.source === 'Cd')) l.lineStyle.opacity = 0.15
  })

  const nodeMap = new Map()
  nodes.forEach(n => { n.value = [n.x, n.y]; nodeMap.set(n.id, [n.x, n.y]) })

  const echartsLinks = links.map(edge => ({
    source: edge.source, target: edge.target,
    lineStyle: { 
      width: 2.5 + edge.strength * 3.5, 
      opacity: edge.lineStyle.opacity || 0.65, 
      curveness: edge.curveness || 0.16, 
      color: edge.lineStyle.color 
    },
    tooltip: { formatter: edge.tooltip }
  }))

  const linesData = links.filter(l => (l.lineStyle.opacity || 0.65) > 0.3).map(edge => ({
    coords: [nodeMap.get(edge.source), nodeMap.get(edge.target)],
    lineStyle: { curveness: edge.curveness || 0.16 },
    effect: { color: edge.lineStyle.color } 
  }))

  return {
    backgroundColor: 'transparent',
    tooltip: { 
      trigger: 'item', backgroundColor: 'rgba(15, 23, 42, 0.95)', borderColor: '#334155',
      textStyle: { color: '#F8FAFC', fontSize: 13 }, padding: [12, 16], borderRadius: 10,
      formatter: function(params) {
        if (params.data && params.data.tooltip) {
          return `<div style="font-weight:900;color:#3B82F6;margin-bottom:6px;font-size:14px;">${params.data.name}</div>
                  <div style="max-width:260px;line-height:1.6;color:#CBD5E1;">${params.data.tooltip}</div>`
        }
        if (params.data && params.data.source && params.data.target) {
          const linkInfo = rawLinks.find(l => l.source === params.data.source && l.target === params.data.target)
          if (linkInfo) {
            return `<div style="font-weight:900;color:#10B981;margin-bottom:6px;font-size:14px;">因果通路：${params.data.source} → ${params.data.target}</div>
                    <div style="max-width:260px;line-height:1.6;color:#CBD5E1;margin-bottom:8px;">${linkInfo.tooltip}</div>
                    <div style="border-t:1px solid #475569;padding-top:6px;font-size:11px;color:#94A3B8;display:flex;gap:12px;">
                      <span>因果强度: <strong style="color:#F59E0B">${(linkInfo.strength * 100).toFixed(0)}%</strong></span>
                      <span>置信度: <strong style="color:#34D399">${(linkInfo.confidence * 100).toFixed(0)}%</strong></span>
                    </div>`
          }
        }
        return params.name
      }
    },
    xAxis: { type: 'value', show: false, min: 0, max: 750 },
    // 修复2：扩大直角坐标系的 y 轴极值边界，并在 grid padding 预留安全量，彻底消除最上层线条裁切
    yAxis: { type: 'value', show: false, min: -35, max: 885, inverse: true },
    grid: { top: 45, bottom: 45, left: 25, right: 25 },
    series: [
      {
        type: 'effectScatter', coordinateSystem: 'cartesian2d', zlevel: 1,
        data: nodes.map(n => ({ 
          value: n.value, symbolSize: n.symbolSize * 0.96, 
          itemStyle: { color: n.itemStyle.color, shadowBlur: 30, shadowColor: n.itemStyle.color, opacity: 0.85 }
        })),
        rippleEffect: { brushType: 'stroke', scale: 2.0, period: 4 },
        label: { show: false }
      },
      {
        type: 'graph', coordinateSystem: 'cartesian2d', layout: 'none', zlevel: 2,
        data: nodes, links: echartsLinks, roam: false,
        label: { 
          show: true, position: 'inside', fontSize: 11, fontWeight: 'bold', color: '#fff',
          textShadow: '0 2px 4px rgba(0,0,0,0.4)'
        },
        itemStyle: {
          borderWidth: 2.5, borderColor: '#fff', shadowBlur: 20, shadowOffsetY: 5, shadowColor: 'rgba(15,23,42,0.15)', borderRadius: 14
        },
        edgeSymbol: ['none', 'arrow'], edgeSymbolSize: [0, 9]
      },
      {
        type: 'lines', coordinateSystem: 'cartesian2d', zlevel: 3,
        effect: { show: true, period: 3.5, trailLength: 0.4, symbol: 'circle', symbolSize: 6 },
        lineStyle: { width: 0, opacity: 0 },
        data: linesData.map(d => ({ coords: d.coords, lineStyle: { curveness: d.lineStyle.curveness }, effect: { color: d.effect.color } }))
      }
    ]
  }
}

const updateCausalGraph = () => {
  if (causalChartInstance) causalChartInstance.setOption(getKnowledgeGraphOption(), true)
}

const initAllCharts = () => {
  clearCharts()
  if(causalGraphRef.value) { 
    causalChartInstance = echarts.init(causalGraphRef.value, null, { devicePixelRatio: 3 })
    causalChartInstance.setOption(getKnowledgeGraphOption()) 
    chartsInstances.push(causalChartInstance)
    
    causalChartInstance.on('click', (params) => {
      if (params.componentType === 'series' && params.seriesType === 'graph') {
        selectedNode.value = baseNodes.find(n => n.id === params.data.id)
        drawerVisible.value = true
      }
    })
  }
}

const animateNumber = (target, duration = 1500) => {
  const start = animatedRiskScore.value
  const startTime = Date.now()
  const timer = setInterval(() => {
    const elapsed = Date.now() - startTime
    const progress = Math.min(elapsed / duration, 1)
    animatedRiskScore.value = Math.round((start + (target - start) * progress) * 10) / 10
    if (progress >= 1) clearInterval(timer)
  }, 16)
}

const handleZoom = (e) => {
  const delta = e.deltaY > 0 ? -0.08 : 0.08
  zoom.value = Math.max(0.5, Math.min(zoom.value + delta, 3.0))
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
const resetView = () => { zoom.value = 1; panX.value = 0; panY.value = 0 }
const zoomIn = () => { zoom.value = Math.min(zoom.value + 0.2, 3.0) }
const zoomOut = () => { zoom.value = Math.max(zoom.value - 0.2, 0.5) }

const particleStyle = (i) => ({
  left: `${5 + Math.random() * 90}%`,
  top: `${5 + Math.random() * 90}%`,
  animationDelay: `${Math.random() * 4}s`,
  animationDuration: `${7 + Math.random() * 5}s`
})

watch([simPb, simAs, simCd, simHg, simCr, simNi, simCo, simLi, simAl, simMn, simMed, simEDTA], () => {
  updateCausalGraph()
}, { deep: true })

onMounted(() => { 
  nextTick(() => { 
    initAllCharts()
    animateNumber(92.4)
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => { 
        if (entry.isIntersecting) entry.target.classList.add('is-visible')
      })
    }, { threshold: 0.05 })
    
    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el))
  })
  window.addEventListener('resize', () => chartsInstances.forEach(c => c.resize())) 
})

onBeforeUnmount(() => { 
  clearCharts()
})

const goToWorkspace = async () => { await router.push('/datainput') }
const goToPlan = async () => { await router.push('/plan') }
</script>

<style scoped>
/* 🛡️ 针对 Tailwind/Element Plus 的 SVG 安全控制补丁 */
:deep(.el-icon svg) {
  max-width: 1em;
  max-height: 1em;
  width: 1em;
  height: 1em;
}

.ep-header { 
  height: 64px; 
  background: #fff; 
  border-bottom: 1px solid #E2E8F0; 
  position: sticky; 
  top: 0; 
  z-index: 50; 
  display: flex; 
  justify-content: center; 
  flex-shrink: 0; 
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
  flex-direction: row; 
  align-items: center; 
  gap: 12px; 
  cursor: pointer; 
  color: #0F172A; 
  transition: color 0.2s; 
}

.back-link:hover { color: #1D4ED8; }
.back-link .back-icon { font-size: 1.2rem; font-weight: bold; }
.back-link .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px; }
.back-link .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; }
.back-link .page-title-top { font-size: 1.1rem; font-weight: 800; color: #0F172A; }

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
  color: #0F172A; 
  font-size: 0.95rem; 
  white-space: nowrap; 
}

.user-profile .avatar { 
  width: 32px; 
  height: 32px; 
  border-radius: 50%; 
  background: #EFF6FF; 
  color: #1D4ED8; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
  font-weight: 700; 
  font-size: 0.9rem; 
}

/* 修复1：还原系统原本的主视窗 CSS 上下文，彻底掐灭任何可能引起脱机的排挤源 */
.system-layout { 
  display: flex; 
  height: 100vh; 
  overflow: hidden; 
}
.main-content { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  height: 100vh; 
  overflow-y: auto;
}

/* 1. 全局控制过滤器高级样式 */
.global-control-bar {
  background: #ffffff;
  border: 1px solid #E2E8F0;
  border-radius: 20px;
  padding: 24px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  flex-wrap: nowrap;
  overflow-x: auto;
  box-shadow: 0 10px 30px -10px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.02);
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex-shrink: 0;
}

.control-label {
  font-weight: 800;
  color: #1E293B;
  font-size: 0.85rem;
  letter-spacing: 0.02em;
}

.slider-row {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 40px;
}

.control-slider {
  width: 150px;
}

.slider-value {
  font-weight: 900;
  color: #3B82F6;
  min-width: 42px;
  text-align: right;
  font-size: 1.1rem;
}

.control-actions {
  display: flex;
  gap: 12px;
  margin-left: auto;
  align-items: flex-end;
  padding-top: 24px;
}

.global-control-bar :deep(.el-select) {
  width: 230px;
}
.global-control-bar :deep(.el-select .el-input__wrapper) {
  border-radius: 12px;
  padding: 6px 12px;
  box-shadow: 0 0 0 1px #CBD5E1 inset !important;
}
.global-control-bar :deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #3B82F6 inset !important;
}

/* ✅ 修改4：人群分组样式完全还原为causal原始版本 */
.global-control-bar :deep(.el-radio-button__inner) {
  padding: 10px 24px;
  font-weight: 600;
  color: #475569;
}
.global-control-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: #3B82F6 !important;
  border-color: #3B82F6 !important;
  color: #ffffff !important;
  box-shadow: -1px 0 0 0 #3B82F6 !important;
}

/* 2. 研究核心 KPI 卡片系统 */
.research-kpi-grid { 
  display: grid;
  grid-template-columns: repeat(4, 1fr); 
  gap: 20px; 
}

.r-kpi-card { 
  background: #ffffff; 
  border: 1px solid #E2E8F0; 
  border-radius: 20px;
  padding: 24px; 
  display: flex; 
  align-items: center;
  gap: 20px;
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02), 0 2px 4px -1px rgba(0,0,0,0.01);
}

.r-kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.08), 0 10px 10px -5px rgba(15, 23, 42, 0.04);
}

.r-kpi-card.danger-level { 
  border-color: rgba(239, 68, 68, 0.15);
  background: linear-gradient(145deg, rgba(254, 242, 242, 0.4), #ffffff); 
}

.kpi-icon {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
}
.kpi-icon.danger { background: #FEE2E2; color: #EF4444; }
.kpi-icon.primary { background: #E0F2FE; color: #0284C7; }
.kpi-icon.success { background: #D1FAE5; color: #10B981; }
.kpi-icon.warning { background: #FEF3C7; color: #D97706; }

.kpi-info { display: flex; flex-direction: column; flex: 1; }
.kpi-tag { font-size: 0.72rem; font-weight: 800; color: #64748B; letter-spacing: 0.06em; text-transform: uppercase; }
.kpi-val { font-size: 2.1rem; font-weight: 900; color: #0F172A; line-height: 1.1; }

/* 3. 全景 DAG 视窗面板 */
.core-dag-section { 
  background: #ffffff; 
  border: 1px solid #E2E8F0; 
  border-radius: 24px;
  padding: 32px; 
  position: relative;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02);
}

.title-badge {
  display: inline-block;
  background: linear-gradient(135deg, #0F172A, #2563EB);
  color: #ffffff;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.section-title { font-size: 1.45rem; font-weight: 900; color: #0F172A; margin: 0 0 6px 0; letter-spacing: -0.02em; }
.section-desc { font-size: 0.88rem; color: #475569; line-height: 1.6; margin: 0; }

.info-card {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #F8FAFC;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #E2E8F0;
  width: fit-content;
}
.info-icon { width: 28px; height: 28px; border-radius: 8px; background: rgba(59, 130, 246, 0.08); color: #3B82F6; display: flex; align-items: center; justify-content: center; font-size: 0.95rem; }

.dag-viewport {
  width: 100%;
  height: 800px;
  background: linear-gradient(135deg, #F8FAFC 0%, #F1F5F9 100%);
  border-radius: 18px;
  overflow: hidden;
  position: relative;
  cursor: grab;
  border: 1px solid #E2E8F0;
  margin-top: 20px;
}
.dag-viewport.is-panning { cursor: grabbing; }

.grid-bg {
  position: absolute; width: 100%; height: 100%; top: 0; left: 0;
  background-image: linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 32px 32px; pointer-events: none; z-index: 0;
}

.floating-particles { position: absolute; width: 100%; height: 100%; top: 0; left: 0; overflow: hidden; pointer-events: none; z-index: 1; }
.particle { position: absolute; width: 5px; height: 5px; border-radius: 50%; background: rgba(59, 130, 246, 0.25); animation: floatBounce 8s infinite ease-in-out; }

@keyframes floatBounce {
  0%, 100% { transform: translate(0, 0); opacity: 0; }
  25% { transform: translate(20px, -30px); opacity: 0.8; }
  50% { transform: translate(-15px, 20px); opacity: 0.8; }
  75% { transform: translate(25px, 10px); opacity: 0.8; }
}

.dag-canvas { width: 100%; height: 100%; transform-origin: center center; transition: transform 0.04s linear; z-index: 5; position: relative; }

.floating-legend {
  position: absolute; top: 20px; right: 20px;
  background: rgba(255, 255, 255, 0.88); backdrop-filter: blur(16px);
  border-radius: 16px; padding: 16px; box-shadow: 0 10px 25px -5px rgba(15,23,42,0.08);
  z-index: 10; pointer-events: none; font-size: 0.8rem; font-weight: 700; color: #475569; min-width: 170px;
}
.legend-title { font-size: 0.85rem; font-weight: 900; color: #0F172A; margin-bottom: 10px; padding-bottom: 6px; border-bottom: 1px solid #E2E8F0; }
.floating-legend .l-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }
.floating-legend .l-row:last-child { margin-bottom: 0; }
.floating-legend .node-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; box-shadow: 0 0 0 2px #fff; }
.floating-legend .exp { background: #3B82F6; }
.floating-legend .mol { background: #0EA5E9; }
.floating-legend .bio { background: #14B8A6; }
.floating-legend .dis { background: #EF4444; }
.floating-legend .int { background: #10B981; }

/* ✅ 修改3：缩放控件移至右下角 */
.zoom-controls {
  position: absolute; bottom: 20px; right: 20px;
  background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(16px);
  border-radius: 14px; padding: 8px; z-index: 10; display: flex; flex-direction: column; align-items: center; gap: 8px;
}
.zoom-controls :deep(.el-button) { width: 30px; height: 30px; padding: 0 !important; margin: 0 !important; }
.zoom-level { font-size: 0.72rem; font-weight: 800; color: #334155; text-align: center; width: 100%; }

/* 4. 反事实推演沙盘样式 */
.full-width-card { padding: 32px; background: #ffffff; border-radius: 20px; }
.chart-title { font-size: 1.35rem; font-weight: 900; color: #0F172A; margin: 0; letter-spacing: -0.02em; }
.chart-tag { background: linear-gradient(135deg, #2563EB, #4F46E5); color: #fff; padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 800; }
.chart-desc { font-size: 0.9rem; max-width: 70%; line-height: 1.5; }

.what-if-panel .control-grid.two-column {
  display: grid; grid-template-columns: 1fr 1fr; gap: 16px 36px;
}
.what-if-panel .ctrl-row { display: flex; align-items: center; justify-content: space-between; gap: 14px; height: 38px; }
.what-if-panel .c-label { width: 150px; font-size: 0.88rem; font-weight: 700; color: #334155; flex-shrink: 0; }
.what-if-panel .c-action { flex: 1; }
.what-if-panel .c-val { width: 45px; text-align: right; font-weight: 800; color: #2563EB; font-size: 0.95rem; }

:deep(.el-slider__runway) { background-color: #E2E8F0 !important; height: 5px !important; border-radius: 3px !important; }
:deep(.el-slider__bar) { background: #2563EB !important; height: 5px !important; border-radius: 3px !important; }
:deep(.el-slider__button) { border: 3px solid #2563EB !important; background-color: #ffffff !important; width: 15px !important; height: 15px !important; box-shadow: 0 2px 5px rgba(37,99,235,0.2) !important; }

/* ✅ 修改2：箭头位置向右调整 */
.simulation-result.enhanced {
  background: #ffffff !important;
  border-radius: 16px;
  padding: 28px 40px;
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 10px 25px -15px rgba(15,23,42,0.06) !important;
  position: relative;
  overflow: hidden;
}
.simulation-result.enhanced::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 4px;
  background: linear-gradient(90deg, #64748B, #2563EB, #10B981);
}

.sr-box {
  flex: 1;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 14px;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  position: relative;
}
.sr-header-tag {
  position: absolute;
  top: 12px;
  right: 16px;
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.68rem;
  font-weight: 800;
  text-transform: uppercase;
  color: #94A3B8;
  letter-spacing: 0.05em;
}
.sr-box .sr-label {
  font-size: 0.82rem;
  color: #64748B !important;
  font-weight: 800;
  margin-bottom: 4px;
}
.sr-box .sr-val {
  font-size: 3rem;
  font-weight: 900;
  font-family: 'IBM Plex Mono', monospace;
  line-height: 1;
  color: #1E293B !important;
  text-shadow: none !important;
}
.sr-box .sr-val small {
  font-size: 1.4rem;
  color: #94A3B8 !important;
  margin-left: 2px;
}

/* 期望预测高亮盒子（若低于50%自动转翠绿） */
.sr-box.target-prediction {
  background: linear-gradient(180deg, #F8FAFC 0%, rgba(219,234,254,0.15) 100%);
  border-color: #BFDBFE;
}
.sr-box.target-prediction .sr-val {
  color: #2563EB !important;
}
.sr-box.target-prediction.is-safe-mode {
  background: linear-gradient(180deg, #F8FAFC 0%, rgba(209,250,229,0.2) 100%);
  border-color: #A7F3D0;
}
.sr-box.target-prediction.is-safe-mode .sr-val {
  color: #10B981 !important;
}

/* 转换连接线（箭头右移调整） */
.sr-arrow-wrapper {
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.sr-arrow-line {
  width: 40px;
  height: 2px;
  background: repeating-linear-gradient(90deg, #CBD5E1, #CBD5E1 4px, transparent 4px, transparent 8px);
  position: absolute;
  left: 0;
}

.gain-indicator.enhanced {
  text-align: right;
  font-size: 1.05rem;
  font-weight: 700;
  color: #475569;
  margin-top: 12px;
  padding-right: 4px;
}
.gain-indicator.enhanced .gain-value {
  font-size: 1.6rem;
  color: #10B981;
  font-weight: 900;
  text-shadow: none !important;
}

/* 5. 右侧精密学术抽屉定制 */
.scientific-drawer :deep(.el-drawer__header) { margin-bottom: 0; padding: 20px 24px; font-weight: 900; color: #0F172A; border-bottom: 1px solid #F1F5F9; }
.scientific-drawer :deep(.el-drawer__body) { padding: 24px; }
.section-title { font-size: 0.92rem; font-weight: 800; color: #0F172A; display: flex; align-items: center; }

.shap-bar { height: 20px; background: #F1F5F9; border-radius: 10px; overflow: hidden; position: relative; }
.shap-bar-fill { height: 100%; background: linear-gradient(90deg, #3B82F6, #6366F1); border-radius: 10px; transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1); }
.shap-value { position: absolute; right: 10px; top: 50%; transform: translateY(-50%); font-weight: 800; color: #1E293B; }

/* 6. 底部全局操作响应条 */
.bottom-action-bar { display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 20px 32px; border-radius: 16px; margin-top: 20px; }
.bottom-action-bar .final-run-btn { background: linear-gradient(135deg, #0F172A, #2563EB); border: none; padding: 14px 28px; border-radius: 12px; transition: all 0.3s ease; }
.bottom-action-bar .final-run-btn:hover { transform: translateY(-2px); box-shadow: 0 12px 20px -5px rgba(37,99,235,0.25); }

/* 7. 页面渐进进场触发器 */
.animate-on-scroll { opacity: 0; transform: translateY(20px); transition: 0.7s cubic-bezier(0.16, 1, 0.3, 1); }
.animate-on-scroll.is-visible { opacity: 1; transform: translateY(0); }
.delay-1 { transition-delay: 0.08s; } .delay-2 { transition-delay: 0.16s; } .delay-3 { transition-delay: 0.24s; } .delay-4 { transition-delay: 0.32s; }
</style>
