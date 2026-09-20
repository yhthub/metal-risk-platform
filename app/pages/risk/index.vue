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
            <span class="ds-label">当前评估对象 (群体样本) 挂载特征文件：</span>
            <div class="file-chips">
              <el-tag size="large" effect="plain" round class="custom-tag" closable @close="handleFileRemove">
                <el-icon><Document /></el-icon> 第一熔炼车间_全体环境与生物监测表.csv
              </el-tag>
            </div>
          </div>
          <div class="ds-right">
            <el-button link type="primary" class="mr-4" @click="goToDatainput">查看特征明细</el-button>
            <el-dropdown trigger="hover" placement="bottom-end">
              <el-button type="primary" plain><el-icon><Plus /></el-icon> 追加数据源</el-button>
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
              <el-select v-model="selectedModel" size="large" placeholder="选择模型" class="custom-el-select" style="width: 280px;" filterable>
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
              <svg class="sparkle-icon" :class="{ 'spinning': isReasoning }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L15 9L22 12L15 15L12 22L9 15L2 12L9 9L12 2Z" fill="currentColor" />
              </svg>
              <span class="t-text">{{ isReasoning ? '模型深度思考与因果计算中...' : '查看完整推演过程 (Show thinking)' }}</span>
            </div>
            <el-icon class="chevron-icon" :class="{ 'rotated': isThinkingExpanded }"><ArrowDown /></el-icon>
          </div>
          <div class="thinking-body" v-show="isThinkingExpanded">
            <ul class="think-steps">
              <li class="t-step active">加载特征张量：提取 1245 名工人的暴露特征与临床基线...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 1 }">运算 G-computation：模拟全体暴露浓度提升一个四分位数，推演边缘因果效应...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 2 }">提取 BKMR 参数：捕获特征后验包含概率 (PIP) 与多毒物剂量-反应曲线...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 3 }">风险定级筛查：锁定因果风险飙升幅度 top 5% 的极端敏感个体...</li>
              <li class="t-step" :class="{ 'active': thinkProgress >= 4 }">构建有向无环图 (DAG)，生成最短致病因果拦截路径...</li>
            </ul>
          </div>
        </div>

        <div class="results-dashboard" v-if="reasoningComplete && !isReasoning">

          <div class="alert-conclusion-banner">
            <div class="a-icon"><el-icon><WarningFilled /></el-icon></div>
            <div class="a-content">
              <h4>系统综合预警定级：<span class="level-danger">【重大规模健康风险预警】</span></h4>
              <p>结合 G方法 (G-computation) 与贝叶斯核机器回归 (BKMR) 测算，系统已完成全员因果效应模拟。
                当前车间若污染等级上升一档，将引发严重的多靶器官致病暴发。已为您精准锁定特异性高危易感10人，亟需立即采取干预与隔离措施！</p>
            </div>
          </div>

          <div class="results-grid">
            
            <div class="result-card col-span-4 border-danger">
              <div class="r-head">
                <div class="title-group">
                  <h4>特异性高危易感人群预警榜 <el-tag size="small" type="danger" effect="dark" round>首要干预对象</el-tag></h4>
                  <span class="sub-desc"><strong>(G-computation 模拟)</strong> 假设污染加重一档，患病概率飙升最猛的易感个体，已按因果效应(Δ)进行危险分级。</span>
                </div>
              </div>
              <div class="chart-box" ref="warningRankRef" style="height: 320px;"></div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <div class="title-group">
                  <h4>高危预警对象人群占比</h4>
                  <span class="sub-desc">全厂触发极高危易感阈值的人数规模</span>
                </div>
              </div>
              <div class="chart-box" ref="dashGaugeRef" style="height: 320px;"></div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <div class="title-group">
                  <h4>致病元凶权重榜</h4>
                  <span class="sub-desc"><strong>(BKMR 特征重要性)</strong> AI 揪出的幕后黑手，面积越大说明对生病的贡献越大。</span>
                </div>
              </div>
              <div class="chart-box" ref="toxinWeightRef"></div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <div class="title-group">
                  <h4>毒物剂量-致病突变曲线</h4>
                  <span class="sub-desc"><strong>(Dose-Response)</strong> 以铅为例，毒素累积到虚线位置后，生病概率会突然大爆发。</span>
                </div>
              </div>
              <div class="chart-box" ref="doseResponseRef"></div>
            </div>

            <div class="result-card col-span-2">
              <div class="r-head">
                <div class="title-group">
                  <h4>高发职业病靶向预测</h4>
                  <span class="sub-desc">基于大模型，预测当前群体未来最容易集中爆发的疾病类型。</span>
                </div>
              </div>
              <div class="disease-list">
                <div class="d-item" v-for="disease in diseaseRisks" :key="disease.name">
                  <div class="d-info">
                    <span class="d-name">{{ disease.name }}</span>
                    <span class="d-val" :class="disease.status">{{ disease.prob }}%</span>
                  </div>
                  <el-progress :percentage="disease.prob" :color="getDiseaseColor(disease.status)" :stroke-width="10" :show-text="false" class="custom-progress" />
                </div>
              </div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <div class="title-group">
                  <h4>双毒物“狼狈为奸”协同放大效应</h4>
                  <span class="sub-desc"><strong>(Joint Exposure Risk)</strong> 当铅(Pb)和砷(As)同时存在时，生病概率会成倍放大（越红越危险）。</span>
                </div>
              </div>
              <div class="chart-box" ref="jointEffectRef"></div>
            </div>

            <div class="result-card col-span-3">
              <div class="r-head">
                <div class="title-group">
                  <h4>风险推手与保护因素拆解</h4>
                  <span class="sub-desc"><strong>(SHAP Attribution)</strong> 量化每种金属把风险推高了多少（红色），或起到了什么保护作用（绿色）。</span>
                </div>
              </div>
              <div class="shap-chart">
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
            </div>

          </div>

          <div class="bottom-action-bar">
            <el-button type="success" size="large" plain :icon="Download" @click="goToReportPage" style="margin-right: 12px;">
              下载风险评估报告 (完整版)
            </el-button>
            <el-button type="primary" size="large" class="final-run-btn" @click="goToPlan">
              针对高危名单生成智能阻断策略 ➔
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
import { Coin, DataLine, TrendCharts, Share, DocumentChecked, ArrowLeft, ArrowDown, Document, Plus, Upload, FolderOpened, Link, WarningFilled, Download, Check } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()

const goToDatainput = async () => {
  await router.push('/datainput')
}

const handleFileRemove = () => {
  ElMessage.info('已移除挂载文件，请从数据接入页面重新上传')
}
const goToPlan = async () => { await router.push('/plan') }

const goToReportPage = async () => {
  setTimeout(async () => {
    await router.push('/risk/report')
  }, 600)
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

const dashGaugeRef = ref(null);
const warningRankRef = ref(null);
const toxinWeightRef = ref(null);
const doseResponseRef = ref(null);
const jointEffectRef = ref(null);

let chartsInstances = []
const clearCharts = () => { chartsInstances.forEach(c => c.dispose()); chartsInstances = [] }

const getGaugeOption = () => ({
  series: [{
    type: 'gauge', startAngle: 180, endAngle: 0, center: ['50%', '75%'], radius: '100%',
    min: 0, max: 30, splitNumber: 3,
    axisLine: {
      lineStyle: {
        width: 15,
        color: [[0.33, '#10B981'], [0.66, '#F59E0B'], [1, '#EF4444']]
      }
    },
    pointer: { show: true, length: '60%', width: 5 },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { show: true, distance: -25, color: '#64748B', fontSize: 10, formatter: '{value}%' },
    detail: {
      fontSize: 36, fontWeight: 'bold', offsetCenter: [0, '-10%'],
      formatter: '{value}%',
      color: 'inherit'
    },
    data: [{ value: 8.5, name: '高危占比 (10人/1,245人)', title: { offsetCenter: [0, '25%'], fontSize: 12, color: '#64748B' } }]
  }]
})

// ✅ 核心修复：基于数值的局部渐变颜色映射逻辑
const getWarningRankOption = () => {
  const data = [
    { name: 'SZ-284', value: 68.5 },
    { name: 'SZ-105', value: 62.1 },
    { name: 'SZ-032', value: 55.4 },
    { name: 'SZ-142', value: 48.2 },
    { name: 'SZ-089', value: 41.5 },
    { name: 'SZ-311', value: 36.8 },
    { name: 'SZ-402', value: 32.1 },
    { name: 'SZ-175', value: 28.5 },
    { name: 'SZ-219', value: 24.2 },
    { name: 'SZ-056', value: 18.6 }
  ];

  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '工号 {b}<br/>因果风险增幅: {c}%' },
    grid: { left: '10%', right: '8%', top: '5%', bottom: '15%' },
    xAxis: { type: 'value', name: 'Δ 因果效应风险突增 (%)', nameLocation: 'middle', nameGap: 25, splitLine: { lineStyle: { type: 'dashed' } } },
    yAxis: { 
      type: 'category', 
      data: data.map(item => item.name),
      inverse: true, // 数值大的排在最上面
      axisLabel: { fontWeight: 'bold' }, 
      axisTick: { show: false } 
    },
    series: [{
      name: '边际风险增量', 
      type: 'bar', 
      barWidth: '50%',
      // 动态映射每个柱状图和文字的颜色
      data: data.map(item => {
        let colorStops = [];
        let labelColor = '';
        if (item.value > 50) {
          colorStops = [{ offset: 0, color: '#EF4444' }, { offset: 1, color: '#FCA5A5' }]; // 极危：深红到浅红
          labelColor = '#EF4444';
        } else if (item.value > 30) {
          colorStops = [{ offset: 0, color: '#F97316' }, { offset: 1, color: '#FDBA74' }]; // 高危：深橙到浅橙
          labelColor = '#F97316';
        } else {
          colorStops = [{ offset: 0, color: '#FBBF24' }, { offset: 1, color: '#FDE047' }]; // 临界：深黄到浅黄
          labelColor = '#FBBF24';
        }
        return {
          value: item.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, colorStops),
            borderRadius: [0, 4, 4, 0]
          },
          label: { color: labelColor }
        };
      }),
      label: { show: true, position: 'right', formatter: '+{c}%', fontWeight: 'bold' },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#EF4444', width: 2 },
        label: { formatter: '极度危险界限', position: 'insideStartTop' },
        data: [{ xAxis: 50 }]
      }
    }]
  }
}

const getToxinWeightOption = () => ({
  tooltip: { trigger: 'item', formatter: '{b}: {d}%' },
  series: [{
    name: '特征重要性(PIP)', type: 'pie', radius: ['20%', '80%'], center: ['50%', '50%'], roseType: 'radius',
    itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
    label: { show: true, formatter: '{b}\n{d}%', fontSize: 11, fontWeight: 'bold' },
    data: [
      { value: 45, name: 'Pb 铅', itemStyle: { color: '#EF4444' } },
      { value: 25, name: 'As 砷', itemStyle: { color: '#F97316' } },
      { value: 15, name: 'Cd 镉', itemStyle: { color: '#F59E0B' } },
      { value: 10, name: 'Cr 铬', itemStyle: { color: '#3B82F6' } },
      { value: 5, name: '其他', itemStyle: { color: '#9CA3AF' } }
    ]
  }]
})

const getDoseResponseOption = () => {
  const data = Array.from({length: 50}, (_, i) => {
    const x = i * 2;
    const y = 100 / (1 + Math.exp(-0.15 * (x - 60))); // Sigmoid
    return [x, y];
  });
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '15%', right: '5%', top: '10%', bottom: '20%' },
    xAxis: { type: 'value', name: '体内蓄积剂量 (μg/L)', nameLocation: 'middle', nameGap: 25, splitLine: { show: false } },
    yAxis: { type: 'value', name: '患病概率 (%)', max: 100 },
    series: [{
      name: '致病风险', type: 'line', data: data, smooth: true, symbol: 'none',
      lineStyle: { color: '#EF4444', width: 3 },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(239, 68, 68, 0.4)' }, { offset: 1, color: 'rgba(239, 68, 68, 0)' }]) },
      markLine: {
        silent: true, symbol: 'none',
        lineStyle: { color: '#F59E0B', type: 'dashed', width: 2 },
        label: { formatter: '爆发拐点', position: 'insideStartTop' },
        data: [{ xAxis: 50 }]
      }
    }]
  }
}

const getJointEffectOption = () => {
  const heatmapData = [];
  const yLabels = ['低', '较低', '中等', '高', '极高(As)'];
  const xLabels = ['低', '较低', '中等', '高', '极高(Pb)'];
  for (let i = 0; i < 5; i++) {
    for (let j = 0; j < 5; j++) {
      let risk = (i + 1) * (j + 1) * 3.5 + Math.random() * 5;
      heatmapData.push([j, i, risk.toFixed(1)]);
    }
  }
  return {
    tooltip: { position: 'top', formatter: (p) => `联合致病概率: ${p.data[2]}%` },
    grid: { left: '15%', right: '5%', top: '5%', bottom: '15%' },
    xAxis: { type: 'category', data: xLabels, name: '铅浓度', nameLocation: 'middle', nameGap: 25, axisTick: {show: false} },
    yAxis: { type: 'category', data: yLabels, name: '砷浓度', axisTick: {show: false} },
    visualMap: {
      min: 0, max: 100, calculable: true, orient: 'horizontal', left: 'center', bottom: '0%', show: false,
      inRange: { color: ['#F0FDF4', '#FDE047', '#EF4444'] }
    },
    series: [{
      name: '风险概率', type: 'heatmap', data: heatmapData,
      label: { show: true, color: '#111827', fontWeight: 'bold' },
      itemStyle: { borderWidth: 2, borderColor: '#fff', borderRadius: 4 }
    }]
  }
}

const initDashboardCharts = () => {
  clearCharts()
  if (warningRankRef.value) { const c = echarts.init(warningRankRef.value); c.setOption(getWarningRankOption()); chartsInstances.push(c) }
  if (dashGaugeRef.value) { const c = echarts.init(dashGaugeRef.value); c.setOption(getGaugeOption()); chartsInstances.push(c) }
  if (toxinWeightRef.value) { const c = echarts.init(toxinWeightRef.value); c.setOption(getToxinWeightOption()); chartsInstances.push(c) }
  if (doseResponseRef.value) { const c = echarts.init(doseResponseRef.value); c.setOption(getDoseResponseOption()); chartsInstances.push(c) }
  if (jointEffectRef.value) { const c = echarts.init(jointEffectRef.value); c.setOption(getJointEffectOption()); chartsInstances.push(c) }
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
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 24px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.02);
  &.border-danger { border-color: #FCA5A5; border-top: 4px solid #EF4444; }
}

.r-head {
  margin-bottom: 16px; border-bottom: 1px solid #F8FAFC; padding-bottom: 12px; display: flex; justify-content: space-between; align-items: center;
  .title-group { display: flex; flex-direction: column; gap: 6px; }
  h4 { margin: 0; font-size: 1.05rem; font-weight: 800; color: $text-main; display: flex; align-items: center; gap: 8px;}
  .sub-desc { font-size: 0.85rem; color: $text-muted; }
}

.chart-box { width: 100%; height: 260px; }

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
</style>
