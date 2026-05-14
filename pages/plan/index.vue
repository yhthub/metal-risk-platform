<template>
  <div class="system-layout">
    <Sidebar default-active="5" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goToWorkspace">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">返回工作台</span>
            <span class="divider">|</span>
            <span class="page-title-top">智能干预与阻断策略推荐</span>
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
          <div class="step success"><span class="step-num"><el-icon><Check /></el-icon></span> 数据接入配置</div>
          <div class="step-line success-line"></div>
          <div class="step success"><span class="step-num"><el-icon><Check /></el-icon></span> 多维可视化分析</div>
          <div class="step-line success-line"></div>
          <div class="step success"><span class="step-num"><el-icon><Check /></el-icon></span> 风险预警模型</div>
          <div class="step-line success-line"></div>
          <div class="step active"><span class="step-num">4</span> 智能阻断策略</div>
        </div>

        <div class="data-verification-banner">
          <div class="dv-top">
            <div class="dv-left">
              <span class="dv-label">当前评估对象挂载特征文件：</span>
              <div class="file-chips">
                <el-tag size="large" effect="plain" round class="custom-tag"><el-icon><Document /></el-icon> SZ-102_Profile.csv</el-tag>
                <el-tag size="large" effect="plain" round class="custom-tag"><el-icon><Document /></el-icon> LIS_Biomarkers.lst</el-tag>
                <el-tag size="large" effect="plain" round class="custom-tag"><el-icon><Document /></el-icon> Smelting_Exposure.csv</el-tag>
              </div>
            </div>
            <div class="dv-right">
              <span class="meta-item"><el-icon><User /></el-icon> 提交人: Dr. 李华 (职防所)</span>
              <span class="meta-divider">|</span>
              <span class="meta-item"><el-icon><Clock /></el-icon> 2026-05-12 14:30:22</span>
            </div>
          </div>
          <div class="dv-bottom">
            <span class="dv-label">全链路状态核验：</span>
            <div class="pipeline-tags">
              <el-tag type="success" effect="dark" round size="small"><el-icon><CircleCheck /></el-icon> 数据接入配置已完成</el-tag>
              <el-icon class="p-arrow"><ArrowRight /></el-icon>
              <el-tag type="success" effect="dark" round size="small"><el-icon><CircleCheck /></el-icon> 多维可视化分析已完成</el-tag>
              <el-icon class="p-arrow"><ArrowRight /></el-icon>
              <el-tag type="danger" effect="dark" round size="small"><el-icon><Warning /></el-icon> 风险预警模型核验 (三级危险)</el-tag>
            </div>
            <el-button link type="primary" class="detail-btn">查看特征明细</el-button>
          </div>
        </div>

        <div class="action-card" v-if="!isGenerated">
          <div class="action-content">
            <div class="a-text">
              <h3>智能干预策略矩阵生成</h3>
              <p>系统将基于 XGBoost 与因果图谱的测算结果，为您生成 12 套涵盖四大维度的深度干预预案，并提供直观的干预成效对比。</p>
            </div>
            <el-button type="primary" size="large" class="btn-generate" @click="startGeneration" :loading="isGenerating">
              ✨ {{ isGenerating ? 'AI 多维策略推演中...' : '一键推演干预矩阵与成效' }}
            </el-button>
          </div>
        </div>

        <div class="gemini-thinking-container" v-if="isGenerating || isGenerated">
          <div class="thinking-header" @click="isThinkingExpanded = !isThinkingExpanded">
            <div class="t-left">
              <svg class="sparkle-icon" :class="{'spinning': isGenerating}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L15 9L22 12L15 15L12 22L9 15L2 12L9 9L12 2Z" fill="currentColor"/>
              </svg>
              <span class="t-text">{{ isGenerating ? '大模型深度推演策略中...' : '查看完整推演过程 (Show thinking)' }}</span>
            </div>
            <el-icon class="chevron-icon" :class="{'rotated': isThinkingExpanded}"><ArrowDown /></el-icon>
          </div>
          
          <div class="thinking-body" v-show="isThinkingExpanded">
            <ul class="think-steps">
              <li class="t-step active">锁定靶点：识别靶器官【中枢神经系统】与致病因子【Pb, As】...</li>
              <li class="t-step" :class="{'active': genProgress >= 1}">查询文献库：匹配《国家职业病防治指南》及络合剂使用规范...</li>
              <li class="t-step" :class="{'active': genProgress >= 2}">制定干预矩阵：生成 12 套独立阻断方案，并分配实施权重...</li>
              <li class="t-step" :class="{'active': genProgress >= 3}">构建成效测算：并行调用 24 个 ECharts 实例，量化每套方案的预期收益...</li>
              <li class="t-step" :class="{'active': genProgress >= 4}">渲染就绪：多维阻断策略及预测对比图表已生成。</li>
            </ul>
          </div>
        </div>

        <div class="results-dashboard" v-if="isGenerated && !isGenerating">
          
          <div class="alert-conclusion-banner">
            <div class="a-icon"><el-icon><Check /></el-icon></div>
            <div class="a-content">
              <h4>干预策略池生成完毕：<span class="level-safe">【共提供 12 套可选阻断方案】</span></h4>
              <p>以下方案已通过 <strong>AHP 层析分析法</strong> 评估了临床可行性与工程成本。您可以查阅每个预案的详细执行机制，<strong>鼠标悬停可查看深度解析</strong>，并通过内嵌的对比图直观评估预期成效。</p>
            </div>
          </div>

          <div class="dimension-tabs">
            <div 
              v-for="cat in interventionMatrix" 
              :key="'tab-' + cat.id"
              class="tab-item"
              :class="{ active: activeTab === cat.id }"
              @click="switchTab(cat.id)"
            >
              {{ cat.category }}
            </div>
          </div>

          <div class="dimension-section" v-for="cat in interventionMatrix" :key="cat.id" v-show="activeTab === cat.id">
            <el-row :gutter="24" class="stretch-row">
              <el-col :span="8" v-for="(plan, index) in cat.plans" :key="plan.id" class="stretch-col">
                <el-popover placement="right" :width="320" trigger="hover" popper-class="custom-popover">
                  <template #reference>
                    <el-card class="plan-card" shadow="hover">
                      <div class="plan-header">
                        <span class="plan-badge">方案 0{{ index + 1 }}</span>
                        <h4 class="plan-title">{{ plan.title }}</h4>
                      </div>
                      
                      <div class="plan-body">
                        <div class="plan-desc"><strong>执行指令：</strong>{{ plan.desc }}</div>
                        <div class="plan-mech"><strong>干预机制：</strong>{{ plan.mechanism }}</div>
                      </div>
                      
                      <div class="mini-charts-grid">
                        <div class="m-chart-item">
                          <div class="m-c-title">重金属暴露衰减评估 (μg)</div>
                          <div :id="'exp-chart-' + plan.id" class="m-c-canvas"></div>
                        </div>
                        <div class="m-chart-item">
                          <div class="m-c-title">靶器官疾病概率降幅 (%)</div>
                          <div :id="'risk-chart-' + plan.id" class="m-c-canvas"></div>
                        </div>
                      </div>
                      
                      <div class="plan-footer">
                        <el-button type="primary" plain class="w-full" @click="goToDetail(plan)">
                          查看详情
                        </el-button>
                      </div>
                    </el-card>
                  </template>
                  
                  <div class="popover-detail">
                    <h4 class="pd-title"><el-icon><ZoomIn /></el-icon> 方案深度解析</h4>
                    <p class="pd-text">{{ plan.extraDetails }}</p>
                    <div class="pd-tags">
                      <el-tag size="small" type="warning" effect="light">周期: {{ plan.period }}</el-tag>
                      <el-tag size="small" type="info" effect="light">成本预估: {{ plan.cost }}</el-tag>
                    </div>
                  </div>
                </el-popover>
              </el-col>
            </el-row>
          </div>

          <h2 class="section-title mt-10"><el-icon><Connection /></el-icon> 核心致病机制靶向阻断验证网络</h2>
          <el-card class="chart-card" shadow="never">
            <div class="causal-graph">
              <svg class="graph-svg" viewBox="0 0 1000 200">
                <defs>
                  <marker id="arrowRed" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0, 6 3, 0 6" fill="#EF4444" /></marker>
                  <marker id="arrowGreen" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0, 6 3, 0 6" fill="#10B981" /></marker>
                  <marker id="arrowGrey" markerWidth="6" markerHeight="6" refX="5" refY="3" orient="auto"><polygon points="0 0, 6 3, 0 6" fill="#9CA3AF" /></marker>
                </defs>
                <path d="M 150 150 C 350 150, 350 50, 550 50" stroke="#E5E7EB" stroke-width="2" fill="none" marker-end="url(#arrowGrey)"/>
                <path d="M 150 50 C 250 50, 300 50, 350 50" stroke="#EF4444" stroke-width="3" stroke-dasharray="8" fill="none" />
                <path class="path-safe" d="M 350 50 C 450 50, 500 50, 550 50" fill="none" marker-end="url(#arrowGreen)"/>
                <path class="path-safe delay-1" d="M 550 50 C 750 50, 750 100, 900 100" fill="none" marker-end="url(#arrowGreen)"/>
              </svg>
              
              <div class="c-node source danger" style="left: 150px; top: 50px;">Pb 暴露异常</div>
              <div class="c-node source warn" style="left: 150px; top: 150px;">Cd 暴露临界</div>
              
              <div class="c-node blocking" style="left: 350px; top: 50px;">
                <el-icon><FirstAidKit /></el-icon> AI 推荐综合干预
              </div>

              <div class="c-node mechanism safe" style="left: 550px; top: 50px;">血脑屏障恢复稳态</div>
              <div class="c-node mechanism warn" style="left: 550px; top: 150px;">肾近曲小管氧化应激</div>
              <div class="c-node target safe" style="left: 900px; top: 100px;">神经病变风险解除</div>
            </div>
          </el-card>

          <div class="bottom-action-bar">
            <el-button type="success" size="large" plain :icon="Download" class="mr-3" @click="goToPdfReport">
              导出 PDF 干预方案与评估长卷
            </el-button>
            <el-button type="warning" size="large" plain :icon="Position" class="mr-3">
              预案推送至 EHS 车间系统
            </el-button>
            <el-button type="primary" size="large" class="final-run-btn">
              一键下发至 HIS 临床诊疗系统 ➔
            </el-button>
          </div>
        </div>

      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { Coin, DataLine, TrendCharts, Share, DocumentChecked, ArrowLeft, ArrowDown, ArrowRight, User, Clock, CircleCheck, Warning, Document, Plus, Upload, FolderOpened, Link, UserFilled, OfficeBuilding, FirstAidKit, Apple, DataBoard, Check, Connection, Download, Position, ZoomIn } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const isGenerating = ref(false)
const isGenerated = ref(false)
const isThinkingExpanded = ref(false)
const genProgress = ref(0)

const activeTab = ref('')

const goToWorkspace = async () => {
  router.push('/datainput')
}

const goToDetail = async (plan) => {
  router.push({
    path: '/plan/specplan', 
    query: {
      id: plan.id,
      title: plan.title
    }
  })
}

const goToPdfReport = async () => {
  router.push({
    path: 'plan/specplan',
    query: {
      id: 'summary',
      title: '全维度智能干预综合报告'
    }
  })
}

const interventionMatrix = ref([
  {
    id: 'c1', category: '职业环境与工程阻断', icon: 'OfficeBuilding',
    plans: [
      { id: 'env1', title: '全隔离调岗预案', desc: '立即脱离重金属熔炼作业环境，调拨至无尘辅助区。', mechanism: '通过切断物理暴露源，强行终止重金属通过呼吸道与消化道的持续摄入。', preExp: [124, 105, 89], postExp: [124, 105, 89], preRisk: [92, 78], postRisk: [85, 75], extraDetails: '此方案要求企业具备完善的转岗安置制度，主要针对极度敏感或已出现实质性器官损伤的个体，隔离期需配合严格的医学观察。短期内直接阻断环境刺激源。', period: '永久或长期', cost: '中（涉及人力调配）' },
      { id: 'env2', title: 'P100级面罩与负压改造', desc: '不调岗，但强制佩戴P100全面罩，加装局部负压排风罩。', mechanism: '大幅降低悬浮粉尘气溶胶的吸入比例，兼顾生产连续性与基本防护。', preExp: [124, 105, 89], postExp: [110, 95, 80], preRisk: [92, 78], postRisk: [88, 76], extraDetails: '适用于轻中度超标人群或关键岗位不可替代人员。需定期更换滤毒盒并进行呼吸器密合性测试，排风系统需连接粉尘收集池以防二次污染。', period: '即刻执行，持续', cost: '低（仅物料消耗）' },
      { id: 'env3', title: '全自动化无人值守升级', desc: '停工实施产线自动化改造，实现熔炼环节的无人化操作。', mechanism: '从根源消除职业暴露场景，彻底切断所有工人的危险金属接触途径。', preExp: [124, 105, 89], postExp: [30, 20, 15], preRisk: [92, 78], postRisk: [40, 35], extraDetails: '彻底的终极解决方案。引入机械臂与隔离控制舱，从物理空间上把人与重金属粉尘隔绝。实施周期较长，但可一劳永逸解决该车间职业病隐患。', period: '3-6个月改造期', cost: '极高（固定资产投资）' }
    ]
  },
  {
    id: 'c2', category: '临床医疗与药物干预', icon: 'FirstAidKit',
    plans: [
      { id: 'med1', title: 'EDTA-CaNa2 靶向驱铅疗法', desc: '依地酸钙钠静脉滴注，每日1次，连续使用3天为一个疗程。', mechanism: '络合血液及软组织中游离的铅离子，形成可溶性络合物随尿液排出。', preExp: [124, 105, 89], postExp: [45, 100, 85], preRisk: [92, 78], postRisk: [45, 75], extraDetails: '首选的一线临床驱铅药物。需密切关注患者肾功能耐受情况，治疗期间需大量饮水排尿。连续三日后停药四天，视指标可开启下一疗程。', period: '1-3个短疗程', cost: '中（医疗与住院费用）' },
      { id: 'med2', title: 'GSH 抗氧化与促排联用', desc: '给予还原型谷胱甘肽保护靶器官，联合二巯丙磺钠促进排泄。', mechanism: '提供巯基结合有害金属，同时中和重金属诱发的氧自由基。', preExp: [124, 105, 89], postExp: [115, 40, 50], preRisk: [92, 78], postRisk: [80, 45], extraDetails: '主要用于缓解重金属引发的急性靶器官损害（特别是肾小管和肝脏），二巯丙磺钠对砷和汞的络合效果尤佳，为保肾促排的双管齐下方案。', period: '7-14天', cost: '中' },
      { id: 'med3', title: '重度急性血液透析干预', desc: '针对极高危对象，直接采用血液透析或血浆置换术。', mechanism: '通过体外循环物理清除血液中的重金属毒素，见效极快。', preExp: [124, 105, 89], postExp: [15, 15, 10], preRisk: [92, 78], postRisk: [30, 25], extraDetails: '属于急救干预手段，主要针对突发性急性重度暴露或已出现重金属脑病、急性肾衰竭先兆的患者。具备创伤性，需在 ICU 严密监控下进行。', period: '单次或短期数次', cost: '高（特殊医疗干预）' }
    ]
  },
  {
    id: 'c3', category: '营养与代谢拮抗支持', icon: 'Apple',
    plans: [
      { id: 'nut1', title: '高钙锌离子竞争抑制法', desc: '每日服用复合钙片与锌补充剂，并指导高钙高锌饮食。', mechanism: '高浓度的二价有益离子（钙/锌）能竞争性阻断有害离子的吸收。', preExp: [124, 105, 89], postExp: [95, 95, 70], preRisk: [92, 78], postRisk: [75, 65], extraDetails: '铅与钙、锌在肠黏膜吸收时共用转运蛋白。保持体内高水平的钙、锌离子，能有效减少微量外源性铅的吸收率，非常适合长期从事低剂量接触的人群保健。', period: '日常长期维持', cost: '极低' },
      { id: 'nut2', title: '果胶多糖大分子吸附', desc: '每日摄入高纯度柑橘果胶或大量苹果、燕麦等膳食纤维。', mechanism: '果胶分子在消化道内形成网络，强效吸附重金属并随粪便排出。', preExp: [124, 105, 89], postExp: [100, 70, 80], preRisk: [92, 78], postRisk: [85, 70], extraDetails: '临床证实，改性柑橘果胶(MCP)在消化道内不易被降解，能有效结合铅、镉、砷等离子，并阻断其肝肠循环，是一种安全无副作用的日常辅助排毒方式。', period: '日常膳食改善', cost: '低' },
      { id: 'nut3', title: '优质蛋白与维C抗氧化食疗', desc: '增加优质蛋白质摄入，每日补充 1000mg 维生素C。', mechanism: '氨基酸与游离重金属结合降低毒性；维C还原有害自由基。', preExp: [124, 105, 89], postExp: [110, 90, 75], preRisk: [92, 78], postRisk: [80, 60], extraDetails: '足量的维生素C可以将毒性极强的六价铬还原为三价铬，同时加速铅的排泄。高蛋白饮食能在消化液中沉淀重金属盐，形成难以吸收的复合物。', period: '日常饮食干预', cost: '低' }
    ]
  },
  {
    id: 'c4', category: '动态监测与随访预案', icon: 'DataBoard',
    plans: [
      { id: 'mon1', title: '高频双周生化溯源复查', desc: '实施驱铅治疗后第 2 周，复查全血 Pb、尿 As 及尿 Cd 浓度。', mechanism: '跟踪药物促排效率，防范因骨骼蓄积铅反流入血引发的“二次中毒”。', preExp: [124, 105, 89], postExp: [80, 80, 80], preRisk: [92, 78], postRisk: [85, 70], extraDetails: '在停止络合治疗后的一周内，体内骨骼组织中深层蓄积的铅会释放回血液中，导致血铅再次反弹升高。因此双周复查是决定是否开启第二疗程的金标准。', period: '治疗后 2-4 周', cost: '低（常规化验）' },
      { id: 'mon2', title: '靶器官微损伤专项监测', desc: '连续 6 个月检测尿 β2-微球蛋白、NAG 酶等指标。', mechanism: '传统重金属指标有滞后性，专项监测能捕获微观极早期实质性损伤。', preExp: [124, 105, 89], postExp: [120, 100, 85], preRisk: [92, 78], postRisk: [70, 50], extraDetails: '金属镉(Cd)造成的近曲肾小管损伤是不可逆的。常规肌酐尿素氮指标不够敏感，必须使用 β2-微球蛋白或 NAG 酶作为哨兵指标，做到毫末级预防。', period: '至少连续半年', cost: '低' },
      { id: 'mon3', title: '长效神经行为深度随访', desc: '建立为期 12 个月的专项档案，每季度进行神经肌电图评估。', mechanism: '持续随访可排除退行性中枢神经系统疾病的远期爆发风险。', preExp: [124, 105, 89], postExp: [120, 100, 85], preRisk: [92, 78], postRisk: [60, 70], extraDetails: '重金属导致的神经脱髓鞘病变通常进程缓慢且隐蔽。此方案强调通过定期的神经传导速度测试和认知量表(MMSE)测评，追踪潜在的退行性病变。', period: '1-3年长期随访', cost: '中' }
    ]
  }
])

let echartInstances = []

const switchTab = (tabId) => {
  if (activeTab.value === tabId) return;
  activeTab.value = tabId;
  nextTick(() => {
    initAllMiniCharts();
  });
}

const startGeneration = () => {
  isGenerating.value = true
  isGenerated.value = false
  isThinkingExpanded.value = true
  genProgress.value = 0
  
  const interval = setInterval(() => {
    genProgress.value++
    if (genProgress.value >= 4) clearInterval(interval)
  }, 600)

  setTimeout(() => {
    isGenerating.value = false
    isGenerated.value = true
    isThinkingExpanded.value = false 
    activeTab.value = interventionMatrix.value[0].id 
    nextTick(() => { initAllMiniCharts() })
  }, 3500)
}

const initAllMiniCharts = () => {
  interventionMatrix.value.forEach(cat => {
    if (cat.id !== activeTab.value) return; 

    cat.plans.forEach(plan => {
      const domA = document.getElementById(`exp-chart-${plan.id}`)
      if (domA) {
        const chartA = echarts.getInstanceByDom(domA) || echarts.init(domA)
        chartA.setOption({
          grid: { left: '15%', right: '5%', top: '20%', bottom: '20%' },
          tooltip: { trigger: 'axis' },
          legend: { data: ['当前', '预期'], itemWidth: 10, itemHeight: 10, top: 0, right: 0, textStyle: { fontSize: 10 } },
          xAxis: { type: 'category', data: ['Pb', 'As', 'Cd'], axisLabel: { fontSize: 10, fontWeight: 'bold' } },
          yAxis: { type: 'value', show: false }, 
          series: [
            { name: '当前', type: 'bar', data: plan.preExp, barWidth: '30%', itemStyle: { color: '#EF4444', borderRadius: [2,2,0,0] } },
            { name: '预期', type: 'bar', data: plan.postExp, barWidth: '30%', itemStyle: { color: '#10B981', borderRadius: [2,2,0,0] } }
          ]
        })
        chartA.resize();
        if (!echartInstances.includes(chartA)) echartInstances.push(chartA)
      }

      const domB = document.getElementById(`risk-chart-${plan.id}`)
      if (domB) {
        const chartB = echarts.getInstanceByDom(domB) || echarts.init(domB)
        chartB.setOption({
          grid: { left: '15%', right: '5%', top: '20%', bottom: '20%' },
          tooltip: { trigger: 'axis' },
          legend: { data: ['当前', '预期'], itemWidth: 10, itemHeight: 10, top: 0, right: 0, textStyle: { fontSize: 10 } },
          xAxis: { type: 'category', data: ['神经', '肾脏'], axisLabel: { fontSize: 10, fontWeight: 'bold' } },
          yAxis: { type: 'value', show: false },
          series: [
            { name: '当前', type: 'bar', data: plan.preRisk, barWidth: '30%', itemStyle: { color: '#F59E0B', borderRadius: [2,2,0,0] } },
            { name: '预期', type: 'bar', data: plan.postRisk, barWidth: '30%', itemStyle: { color: '#3B82F6', borderRadius: [2,2,0,0] } }
          ]
        })
        chartB.resize();
        if (!echartInstances.includes(chartB)) echartInstances.push(chartB)
      }
    })
  })
}

const resizeCharts = () => { echartInstances.forEach(c => c.resize()) }
onMounted(() => {
  if (isGenerated.value) nextTick(() => initAllMiniCharts())
  window.addEventListener('resize', resizeCharts)
})
onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeCharts)
  echartInstances.forEach(c => c.dispose())
})
</script>

<style lang="scss" scoped>
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

* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', sans-serif; overflow: hidden; }

/* 主内容区 */
.main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth; }

/* 顶栏 */
.ep-header { height: 64px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex !important; justify-content: center; flex-shrink: 0; }
.nav-wrapper { width: 100%; padding: 0 32px; display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important; justify-content: space-between !important; align-items: center !important; height: 100%; max-width: none; }
.back-link { display: flex; flex-direction: row; align-items: center; gap: 12px; cursor: pointer; color: $text-main; transition: color 0.2s; &:hover { color: $color-primary; } .back-icon { font-size: 1.2rem; font-weight: bold;} .back-text { font-size: 1.05rem; font-weight: 700; letter-spacing: 1px;} .divider { color: #D1D5DB; font-weight: 300; margin: 0 8px; } .page-title-top { font-size: 1.1rem; font-weight: 800; color: $text-main; } }
.ep-right-zone { display: flex; align-items: center; flex-direction: row; }
.user-profile { display: flex; flex-direction: row; align-items: center; gap: 12px; font-weight: 600; color: $text-main; font-size: 0.95rem; white-space: nowrap; .avatar { width: 32px; height: 32px; border-radius: 50%; background: $color-primary-light; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; font-size: 0.9rem;} }

.page-container { flex: 1 0 auto; padding: 40px; max-width: 1500px; margin: 0 auto; width: 100%; display: flex; flex-direction: column; padding-bottom: 80px;}

.pipeline-steps { display: flex; align-items: center; margin-bottom: 30px; background: transparent; padding: 0; .step { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; color: $text-muted; .step-num { width: 24px; height: 24px; border-radius: 50%; background: #E5E7EB; display: flex; justify-content: center; align-items: center; font-size: 0.85rem; } &.active { color: $color-primary; .step-num { background: $color-primary; color: #FFF; } } &.success { color: $color-safe; .step-num { background: $color-safe; color: #FFF; font-size: 1rem;} } } .step-line { flex: 1; height: 2px; background: #E5E7EB; margin: 0 16px; &.active-line { background: $color-primary; } &.success-line { background: $color-safe; } } }

.data-verification-banner { background: #fff; border-radius: 12px; border: 1px solid #93C5FD; border-left: 4px solid $color-primary; margin-bottom: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); overflow: hidden; .dv-top { display: flex; justify-content: space-between; padding: 16px 24px; border-bottom: 1px dashed #E2E8F0; } .dv-bottom { display: flex; align-items: center; padding: 12px 24px; background: #F8FAFC; .dv-label { font-weight: 700; font-size: 0.9rem; margin-right: 12px; } } .dv-left { display: flex; align-items: center; gap: 16px; } .dv-label { font-size: 0.95rem; font-weight: 700; color: $text-main; } .file-chips { display: flex; gap: 12px; flex-wrap: wrap; align-items: center;} .custom-tag { font-size: 0.9rem; font-weight: 600; color: $color-primary; background: #EFF6FF; border: none; padding: 4px 12px; height: auto; .el-icon { margin-right: 6px; font-size: 1rem; color: $color-primary;} :deep(.el-tag__close) { color: $color-primary; &:hover{background:$color-primary; color:#fff;} } } .no-file-tip { font-size: 0.9rem; color: $color-danger; font-weight: 600;} .dv-right { display: flex; align-items: center; gap: 12px; font-size: 0.9rem; color: $text-muted; font-weight: 500; .meta-item { display: flex; align-items: center; gap: 6px; } .meta-divider { color: #CBD5E1; } } .pipeline-tags { display: flex; align-items: center; gap: 8px; flex: 1; } .p-arrow { color: #9CA3AF; font-size: 0.8rem; margin: 0 4px;} }

.action-card { background: #fff; border-radius: 12px; border: 1px solid $border-color; padding: 30px; margin-bottom: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); .action-content { display: flex; justify-content: space-between; align-items: center; } .a-text h3 { margin: 0 0 8px 0; font-size: 1.2rem; color: $text-main; font-weight: 800; } .a-text p { margin: 0; color: $text-muted; font-size: 0.95rem; max-width: 600px; line-height: 1.5; } .btn-generate { font-weight: 700; font-size: 1.05rem; padding: 0 32px; height: 48px; border-radius: 8px;} }

.gemini-thinking-container { background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; margin-bottom: 30px; overflow: hidden; transition: all 0.3s ease; box-shadow: 0 4px 10px rgba(0,0,0,0.02); .thinking-header { padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none; .t-left { display: flex; align-items: center; gap: 12px; } .sparkle-icon { width: 22px; height: 22px; color: #2563EB; } .spinning { animation: spin 2s linear infinite; } .t-text { font-size: 1.05rem; font-weight: 700; color: #1E3A8A; } .chevron-icon { color: #60A5FA; transition: transform 0.3s; &.rotated { transform: rotate(180deg); } } } .thinking-body { padding: 0 24px 24px 60px; } .think-steps { list-style: none; padding: 0; margin: 0; border-left: 2px solid #DBEAFE; padding-left: 16px;} .t-step { font-size: 0.95rem; color: #64748B; margin-bottom: 12px; position: relative; &::before { content: ''; position: absolute; left: -21px; top: 6px; width: 8px; height: 8px; border-radius: 50%; background: #DBEAFE; } &.active { color: #1E40AF; font-weight: 600; &::before { background: #3B82F6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.6); } } } }
@keyframes spin { 100% { transform: rotate(360deg); } }

.results-dashboard { animation: fadeIn 0.6s ease-out forwards; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

.alert-conclusion-banner { display: flex; gap: 20px; background: #ECFDF5; border: 1px solid #6EE7B7; padding: 24px; border-radius: 12px; margin-bottom: 30px; .a-icon { font-size: 2rem; color: #10B981; } .a-content { h4 { margin: 0 0 10px 0; font-size: 1.2rem; color: #065F46; .level-safe { font-weight: 900; color: #047857;} } p { margin: 0; font-size: 0.95rem; color: #064E3B; line-height: 1.6; strong { background: #D1FAE5; padding: 2px 6px; border-radius: 4px; border: 1px solid #6EE7B7;} } } }

.dimension-tabs { display: flex; border-bottom: 2px solid #E2E8F0; margin-bottom: 30px; gap: 40px; padding: 0 10px; }
.tab-item { padding: 12px 4px; font-size: 1.15rem; font-weight: 800; color: #64748B; cursor: pointer; position: relative; transition: color 0.3s ease; display: flex; align-items: center; gap: 8px; }
.tab-item:hover { color: #0F172A; }
.tab-item.active { color: #0F172A; }
.tab-item.active::after { content: ''; position: absolute; bottom: -2px; left: 0; width: 100%; height: 3px; background-color: #1D4ED8; border-radius: 3px 3px 0 0; }

.section-title { font-size: 1.3rem; font-weight: 800; color: $text-main; margin: 0 0 20px 0; border-left: 4px solid $color-primary; padding-left: 12px; }
.mt-10 { margin-top: 50px; }

/* ✅ 核心修复：确保同一行的列自动等高拉伸，内部元素顶到底部 */
.stretch-row {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch; /* 保证一行内的 el-col 等高 */
}

.stretch-col {
  display: flex;
  flex-direction: column;
}

.dimension-section { margin-bottom: 40px; animation: fadeIn 0.4s ease-out forwards; }

.plan-card { 
  height: 100%; /* 撑满伸展后的父元素 */
  border-radius: 12px; 
  border: 1px solid $border-color; 
  display: flex; 
  flex-direction: column; 
  transition: all 0.3s;
  
  &:hover { border-color: $color-primary; box-shadow: 0 10px 20px rgba(29, 78, 216, 0.08) !important; transform: translateY(-3px); }
  
  /* 深度穿透：重置 el-card 内部产生的包裹层为 flex 容器 */
  :deep(.el-card__body) {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 24px; /* 统一内边距 */
  }

  .plan-header { margin-bottom: 16px; border-bottom: 1px dashed $border-color; padding-bottom: 12px; .plan-badge { background: #F1F5F9; color: #475569; font-size: 0.8rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; margin-bottom: 8px; display: inline-block;} .plan-title { margin: 0; font-size: 1.1rem; font-weight: 800; color: $text-main; } }
  
  .plan-body { 
    flex: 1; /* 这个元素会占据中间所有的不规则剩余空间 */
    font-size: 0.9rem; color: #334155; line-height: 1.6; 
    .plan-desc { margin-bottom: 12px; strong { color: $color-primary; } } 
    .plan-mech { padding: 12px; background: #F8FAFC; border-radius: 6px; border: 1px solid #F1F5F9; strong { color: #8B5CF6; } } 
  }
  
  .mini-charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; padding-top: 16px; border-top: 1px solid #F1F5F9; .m-chart-item { .m-c-title { font-size: 0.75rem; font-weight: 700; color: $text-muted; text-align: center; margin-bottom: 4px;} .m-c-canvas { width: 100%; height: 120px; } } }
  
  .plan-footer { 
    margin-top: auto; /* 核心：始终把 footer 推到最底部 */
    padding-top: 16px; 
    .w-full { width: 100%; font-weight: 700; border-radius: 6px; } 
  }
}

.popover-detail { padding: 4px; .pd-title { margin: 0 0 12px 0; color: $text-main; font-size: 1.05rem; font-weight: 800; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #F1F5F9; padding-bottom: 8px; .el-icon { color: $color-primary; }} .pd-text { font-size: 0.95rem; color: #475569; line-height: 1.6; margin-bottom: 16px; } .pd-tags { display: flex; gap: 8px; flex-wrap: wrap; .el-tag { font-weight: 600; font-size: 0.85rem;} } }
:deep(.custom-popover) { border-radius: 12px; box-shadow: 0 15px 30px rgba(0,0,0,0.1) !important; border: 1px solid #E2E8F0; padding: 20px;}

.chart-card { border-radius: 12px; border: 1px solid $border-color; }
.causal-graph { position: relative; height: 260px; background: #F8FAFC; border-radius: 8px; overflow: hidden;}
.graph-svg { width: 100%; height: 100%; position: absolute; top: 0; left: 0; z-index: 1; display: block !important; max-height: none !important; max-width: none !important;}
.path-safe { stroke: #10B981; stroke-width: 3; stroke-dasharray: 8; animation: dashMove 1s linear infinite; }
.delay-1 { animation-delay: 0.5s; } 
@keyframes dashMove { to { stroke-dashoffset: -20; } }
.c-node { position: absolute; transform: translate(-50%, -50%); padding: 10px 16px; border-radius: 8px; font-size: 0.9rem; font-weight: 700; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); z-index: 2; border-left: 4px solid; &.source { border-color: #3B82F6; } &.mechanism { border-color: #8B5CF6; } &.target { border-color: #10B981; } &.danger { background: #FEF2F2; border-color: #EF4444; color: #B91C1C; } &.warn { background: #FFFBEB; border-color: #F59E0B; color: #B45309; } &.safe { background: #ECFDF5; border-color: #10B981; color: #047857; } &.blocking { background: #10B981; color: #fff; border: none; box-shadow: 0 0 15px rgba(16, 185, 129, 0.4); display: flex; align-items: center; gap: 6px; font-size: 0.95rem; z-index: 10;} }

.bottom-action-bar { display: flex; justify-content: flex-end; margin-top: 40px; border-top: 1px solid #E2E8F0; padding-top: 24px; .mr-3 { margin-right: 16px;} .el-button { font-weight: 700; border-radius: 8px; } :deep(.final-run-btn) { background-color: #059669; border-color: #059669; color: #ffffff; transition: all 0.3s ease; &:hover { background-color: #047857; border-color: #047857; transform: translateY(-2px); box-shadow: 0 10px 20px rgba(5, 150, 105, 0.3); } } }
</style>