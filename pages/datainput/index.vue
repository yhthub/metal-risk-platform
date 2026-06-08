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
                    <div class="clinical-input-grid cols-4" style="margin-top: 16px;">
                      <div class="clinical-input-item">
                        <span class="label">学历</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.education">
                            <option value="">请选择</option>
                            <option value="primary">小学及以下</option>
                            <option value="middle">初中</option>
                            <option value="high">高中/中专</option>
                            <option value="college">大专</option>
                            <option value="bachelor">本科</option>
                            <option value="master">硕士及以上</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">婚姻状况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.marital">
                            <option value="">请选择</option>
                            <option value="unmarried">未婚</option>
                            <option value="married">已婚</option>
                            <option value="divorced">离异</option>
                            <option value="widowed">丧偶</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">吸烟情况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.smoking">
                            <option value="">请选择</option>
                            <option value="never">从不吸烟</option>
                            <option value="former">已戒烟</option>
                            <option value="current_lt10">现吸 (&lt;10支/日)</option>
                            <option value="current_ge10">现吸 (≥10支/日)</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">饮酒情况</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.drinking">
                            <option value="">请选择</option>
                            <option value="never">从不饮酒</option>
                            <option value="occasional">偶尔饮酒</option>
                            <option value="frequent">经常饮酒</option>
                            <option value="daily">每日饮酒</option>
                          </select>
                        </div>
                      </div>
                    </div>
                    <div class="clinical-input-grid cols-4" style="margin-top: 16px;">
                      <div class="clinical-input-item">
                        <span class="label">BMI (体质指数)</span>
                        <div class="input-wrap"><input type="number" v-model="formData.singleData.bmi" placeholder="0.0" step="0.1" /><span class="unit">kg/m²</span></div>
                      </div>
                      <div class="clinical-input-item">
                        <span class="label">防护装备使用</span>
                        <div class="input-wrap select-wrap">
                          <select v-model="formData.singleData.ppe">
                            <option value="">请选择</option>
                            <option value="none">无防护</option>
                            <option value="basic">基本防护 (口罩/手套)</option>
                            <option value="standard">标准防护 (半面罩+护目镜)</option>
                            <option value="full">全面防护 (P100+防护服)</option>
                          </select>
                        </div>
                      </div>
                      <div class="clinical-input-item" style="grid-column: span 2;">
                        <span class="label">既往职业病史</span>
                        <div class="input-wrap"><input type="text" v-model="formData.singleData.history" placeholder="如：2023年诊断轻度铅中毒，已治愈" /></div>
                      </div>
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
          
          <!-- 群体模式大屏 -->
          <div v-if="formData.mode === 'batch'" class="batch-dashboard-container animate-on-scroll is-visible">
            
            <div class="kpi-row">
              <div class="kpi-card total"><el-icon class="kpi-icon"><Avatar /></el-icon><div class="kpi-info"><span>总提取解析人数</span><strong>1,245<small> 人</small></strong></div></div>
              <div class="kpi-card male"><el-icon class="kpi-icon"><Male /></el-icon><div class="kpi-info"><span>男性占比</span><strong>856<small> 人 (68.7%)</small></strong></div></div>
              <div class="kpi-card female"><el-icon class="kpi-icon"><Female /></el-icon><div class="kpi-info"><span>女性占比</span><strong>389<small> 人 (31.3%)</small></strong></div></div>
              <div class="kpi-card ready"><el-icon class="kpi-icon"><CircleCheckFilled /></el-icon><div class="kpi-info"><span>多维度暴露评估基线</span><strong>预处理就绪</strong></div></div>
            </div>

            <!-- 人口学特征统计行 -->
            <div class="batch-charts-grid demographic-row">

              <!-- 婚姻状况 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>婚姻状况分布 (Marital Status)</h4>
                  <span class="sub-title">统计群体婚姻结构，评估家庭因素对职业暴露易感性的潜在修饰效应。</span>
                </div>
                <div id="batchChartMarital" class="b-c-canvas"></div>
              </div>

              <!-- 文化程度 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>文化程度构成 (Education Level)</h4>
                  <span class="sub-title">呈现群体受教育水平分布，分析文化程度与防护认知、健康素养的关联。</span>
                </div>
                <div id="batchChartEducation" class="b-c-canvas"></div>
              </div>

              <!-- 家庭年收入 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>家庭年收入分布 (Annual Household Income)</h4>
                  <span class="sub-title">揭示群体经济水平分层，辅助评估医疗可及性与营养干预的可行性。</span>
                </div>
                <div id="batchChartIncome" class="b-c-canvas"></div>
              </div>

            </div>

            <!-- 图表矩阵: 3 列 x 3 行 -->
            <div class="batch-charts-grid">

              <!-- 图表 1 (占 2 列) -->
              <div class="b-chart-card col-span-2">
                <div class="b-c-header">
                  <h4>特征共线性矩阵 (Correlation Heatmap)</h4>
                  <span class="sub-title">呈现暴露因子间的相关程度，辅助识别具有高度协同作用的复合暴露组合。</span>
                </div>
                <div id="batchChartCorr" class="b-c-canvas"></div>
              </div>

              <!-- 图表 2 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>核心暴露分布四分位数 (Quartiles)</h4>
                  <span class="sub-title">按暴露浓度将人群划分为四个区间，直观展示处于极高暴露水平（Q4区间）的样本规模。</span>
                </div>
                <div id="batchChartQuartile" class="b-c-canvas"></div>
              </div>

              <!-- 图表 3 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>特征分布与异常离群点 (Boxplot)</h4>
                  <span class="sub-title">评估各项指标的分布离散度，定位偏离整体分布的极端高值个体以供重点复查。</span>
                </div>
                <div id="batchChartBoxplot" class="b-c-canvas"></div>
              </div>

              <!-- 图表 4 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>主成分降维特征聚类 (PCA Projection)</h4>
                  <span class="sub-title">将高维特征投影至二维空间，验证健康组与高危组样本在多特征下的分布差异。</span>
                </div>
                <div id="batchChartPCA" class="b-c-canvas"></div>
              </div>

              <!-- 图表 5 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>数据检出率与缺失评估 (LOD Analysis)</h4>
                  <span class="sub-title">统计各暴露因子在检出限（LOD）以上的有效样本比例，评估数据源质量。</span>
                </div>
                <div id="batchChartMissing" class="b-c-canvas"></div>
              </div>

              <!-- 图表 6 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>核密度平滑分布 (Density Smooth)</h4>
                  <span class="sub-title">对原始暴露浓度进行概率密度拟合，消除极端值干扰，揭示人群真实分布形态。</span>
                </div>
                <div id="batchChartDensity" class="b-c-canvas"></div>
              </div>

              <!-- 图表 7 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>群体暴露浓度频数分布 (Concentration Histogram)</h4>
                  <span class="sub-title">按浓度区间统计群体样本频数，直观呈现各重金属的分布偏态与集中趋势。</span>
                </div>
                <div id="batchChartParallel" class="b-c-canvas"></div>
              </div>

              <!-- 图表 8 -->
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>工龄-年龄-暴露水平画像 (Bubble)</h4>
                  <span class="sub-title">综合呈现年龄、工龄与综合暴露指数的关系，气泡面积反映个体毒物蓄积程度。</span>
                </div>
                <div id="batchChartBubble" class="b-c-canvas"></div>
              </div>
              
            </div>
          </div>

          <!-- 单人模式科研图表 -->
          <div v-else class="single-dashboard-container animate-on-scroll is-visible">
            
            <div class="b-chart-card mb-6" style="padding-bottom: 0;">
              <div class="b-c-header">
                <h4>个体多维暴露全景画像 (Relative Exposure Index)</h4>
                <span class="sub-title">将多项绝对指标转化为相对安全限值的比率，直观呈现各指标是否突破安全或预警阈值。</span>
              </div>
              <div id="singleChartMaster" style="width: 100%; height: 350px;"></div>
            </div>

            <div class="batch-charts-grid" style="margin-top: 24px;">
              
              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>靶向因子偏移雷达图 (Radar)</h4>
                  <span class="sub-title">对比个体指标与国家职业卫生基线的覆盖面积，精准定位偏离安全基准的主要特征向。</span>
                </div>
                <div id="singleChartRadar" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>核心指标纵向时间序列 (Longitudinal)</h4>
                  <span class="sub-title">追踪个体连续多年的暴露水平演变，底部绿色阴影区代表临床参考的安全基线范围。</span>
                </div>
                <div id="singleChartTimeline" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>暴露特征群体排位 (Percentiles)</h4>
                  <span class="sub-title">评估个体各项重金属指标在整体流行病学队列中的相对水平与百分位排名。</span>
                </div>
                <div id="singleChartPercentile" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>靶器官风险归因拆解 (Organ Breakdown)</h4>
                  <span class="sub-title">内环指示存在潜在受损风险的靶器官，外环解析导致该风险的主导金属及协同因子。</span>
                </div>
                <div id="singleChartRiskPie" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>特征标准化偏离度 (Z-Score)</h4>
                  <span class="sub-title">量化个体各项指标偏离群体均值的标准差倍数，识别个体特异性的高吸收或高暴露项。</span>
                </div>
                <div id="singleChartZScore" class="b-c-canvas"></div>
              </div>

              <div class="b-chart-card col-span-1">
                <div class="b-c-header">
                  <h4>多维异常综合指数 (Anomaly Index)</h4>
                  <span class="sub-title">基于马氏距离等算法生成的综合健康偏移指标，表征个体整体状态偏离正常群体的程度。</span>
                </div>
                <div id="singleChartAnomaly" class="b-c-canvas"></div>
              </div>

            </div>
          </div>
          
          <div class="bottom-action-bar">
            <div class="tips">
              <el-icon><CircleCheckFilled /></el-icon>
              数据特征清洗完毕，相关性与缺失率预处理（EDA）校验完成。您可以安全地将特征矩阵推入 <strong>复合风险量化与推理模型</strong>。
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
  CircleCheckFilled, InfoFilled, ArrowLeft, Male, Female, Avatar
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const currentStep = ref(1)

const formData = ref({
  job: 'smelting', mode: 'batch',
  singleData: {
    name: '', gender: 'male', age: null, workYears: null,
    pb: 1.24, cd: 0.89, hg: 0.12, th: 0.05, li: 0.18, cr: 0.34, ni: 0.45, co: 0.11, as: 1.05, rn: 15.0,
    education: '', marital: '', smoking: '', drinking: '', bmi: null, ppe: '', history: ''
  }
})

const hasFile = ref(true)
const isAnalyzing = ref(false)
const showDashboard = ref(false)

const activeFilter = ref('all')
const toggleFilter = (status) => { activeFilter.value = activeFilter.value === status ? 'all' : status }

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
      nextTick(() => {
        initSingleECharts()
        window.scrollTo({ top: 800, behavior: 'smooth' })
      })
    }
  }, 1200)
}

const goToRiskWarning = async () => { 
  currentStep.value = 3 
  await navigateTo('/risk') 
}

const goToHome = async () => {
  await navigateTo('/')
}

let batchCharts = []

const initBatchECharts = () => {
  batchCharts.forEach(c => c.dispose())
  batchCharts = []

  // 1. 共线性矩阵 (Heatmap)
  const domCorr = document.getElementById('batchChartCorr')
  if (domCorr) {
    const chartCorr = echarts.init(domCorr)
    const corrData = [
      [0,0, 1.00], [0,1, 0.45], [0,2, 0.62], [0,3, 0.15], [0,4, 0.22],
      [1,0, 0.45], [1,1, 1.00], [1,2, 0.38], [1,3, 0.11], [1,4, 0.28],
      [2,0, 0.62], [2,1, 0.38], [2,2, 1.00], [2,3, 0.33], [2,4, 0.19],
      [3,0, 0.15], [3,1, 0.11], [3,2, 0.33], [3,3, 1.00], [3,4, 0.41],
      [4,0, 0.22], [4,1, 0.28], [4,2, 0.19], [4,3, 0.41], [4,4, 1.00]
    ]
    chartCorr.setOption({
      tooltip: { position: 'top', formatter: (p) => `Pearson(r): ${p.data[2]}` },
      grid: { left: '10%', right: '5%', top: '5%', bottom: '15%' },
      xAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisLine: {show: false}, axisTick: {show: false} },
      yAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisLine: {show: false}, axisTick: {show: false} },
      visualMap: { 
        min: 0, max: 1, calculable: true, orient: 'horizontal', 
        left: 'center', bottom: '0%', itemWidth: 12, itemHeight: 120, 
        inRange: { color: ['#F8FAFC', '#93C5FD', '#1E3A8A'] }, show: false 
      },
      series: [{ 
        type: 'heatmap', data: corrData, 
        label: { show: true, color: '#fff', fontWeight: 'bold' }, 
        itemStyle: { borderWidth: 2, borderColor: '#fff', borderRadius: 4 } 
      }]
    })
    batchCharts.push(chartCorr)
  }

  // 2. 四分位数分布 (Bar)
  const domQuartile = document.getElementById('batchChartQuartile')
  if (domQuartile) {
    const chartQuartile = echarts.init(domQuartile)
    chartQuartile.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: ['Q1 (<25%)', 'Q2 (中位)', 'Q3 (75%)', 'Q4 (极端)'], axisLabel: { fontSize: 11, fontWeight: 'bold' }, axisTick: {show: false} },
      yAxis: { type: 'value', name: '样本分布数量', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        name: '样本数', type: 'bar', barWidth: '45%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#3B82F6' }, { offset: 1, color: '#93C5FD' }
          ]),
          borderRadius: [4, 4, 0, 0]
        },
        label: { show: true, position: 'top', fontWeight: 'bold', color: '#1E3A8A' },
        data: [312, 450, 280, 203]
      }]
    })
    batchCharts.push(chartQuartile)
  }

  // 3. 异常值检测 (Boxplot)
  const domBoxplot = document.getElementById('batchChartBoxplot')
  if (domBoxplot) {
    const chartBoxplot = echarts.init(domBoxplot)
    chartBoxplot.setOption({
      tooltip: { trigger: 'item', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: ['Pb', 'Cd', 'As', 'Hg', 'Cr'], axisTick: {show: false}, axisLabel: {fontWeight: 'bold'} },
      yAxis: { type: 'value', name: 'Z-Score 浓度', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: '分布范围', type: 'boxplot',
          itemStyle: { color: '#EFF6FF', borderColor: '#3B82F6', borderWidth: 2 },
          data: [
            [-1.2, -0.5, 0.2, 0.8, 2.5],
            [-0.8, -0.2, 0.4, 1.1, 3.2],
            [-1.5, -0.6, 0.1, 0.9, 2.1],
            [-0.9, -0.3, 0.3, 0.7, 1.8],
            [-1.0, -0.4, 0.0, 0.5, 1.5]
          ]
        },
        {
          name: '极端离群点', type: 'scatter',
          itemStyle: { color: '#EF4444' },
          data: [ [0, 3.1], [0, 3.5], [1, 4.2], [1, 4.5], [2, 2.8], [3, 2.5] ]
        }
      ]
    })
    batchCharts.push(chartBoxplot)
  }

  // 4. PCA 主成分降维投影 (Scatter)
  const domPCA = document.getElementById('batchChartPCA')
  if (domPCA) {
    const chartPCA = echarts.init(domPCA)
    const dataCluster1 = Array.from({length: 40}, () => [Math.random()*10 - 5, Math.random()*10 - 5]);
    const dataCluster2 = Array.from({length: 30}, () => [Math.random()*8 + 2, Math.random()*8 + 3]);
    chartPCA.setOption({
      tooltip: { trigger: 'item', formatter: 'PC1: {c[0]}<br/>PC2: {c[1]}' },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', name: 'PC1 (45%)', scale: true, splitLine: { show: false } },
      yAxis: { type: 'value', name: 'PC2 (22%)', scale: true, splitLine: { show: false } },
      series: [
        { type: 'scatter', name: '健康本底组', data: dataCluster1, itemStyle: { color: '#10B981', opacity: 0.6 } },
        { type: 'scatter', name: '高暴露风险组', data: dataCluster2, itemStyle: { color: '#EF4444', opacity: 0.6 } }
      ]
    })
    batchCharts.push(chartPCA)
  }

  // 5. 缺失值与检出率占比 (Stacked Bar)
  const domMissing = document.getElementById('batchChartMissing')
  if (domMissing) {
    const chartMissing = echarts.init(domMissing)
    chartMissing.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: ['Cr', 'Hg', 'As', 'Cd', 'Pb'], axisTick: {show: false}, axisLabel: {fontWeight: 'bold'} },
      series: [
        { name: '有效检出', type: 'bar', stack: 'total', barWidth: '40%', itemStyle: { color: '#34D399', borderRadius: [0,0,0,0] }, label: { show: true, position: 'insideRight', formatter: '{c}%', color: '#fff' }, data: [88, 76, 92, 85, 98] },
        { name: '低于LOD/缺失', type: 'bar', stack: 'total', barWidth: '40%', itemStyle: { color: '#FCA5A5', borderRadius: [0,4,4,0] }, data: [12, 24, 8, 15, 2] }
      ]
    })
    batchCharts.push(chartMissing)
  }

  // 6. 暴露浓度“偏科”纠正 (Density Area Line)
  const domDensity = document.getElementById('batchChartDensity')
  if (domDensity) {
    const chartDensity = echarts.init(domDensity)
    const xData = Array.from({length: 50}, (_, i) => i);
    const yBefore = xData.map(x => Math.exp(-Math.pow(x - 10, 2) / 20) * 100 + Math.random()*5);
    const yAfter = xData.map(x => Math.exp(-Math.pow(x - 25, 2) / 100) * 60);
    chartDensity.setOption({
      tooltip: { trigger: 'axis' },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '15%' },
      xAxis: { type: 'category', data: xData, show: false },
      yAxis: { type: 'value', name: '数据密度', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        { name: '处理前', type: 'line', smooth: true, symbol: 'none', data: yBefore, itemStyle: { color: '#EF4444' }, areaStyle: { opacity: 0.2 } },
        { name: '处理后', type: 'line', smooth: true, symbol: 'none', data: yAfter, itemStyle: { color: '#3B82F6' }, areaStyle: { opacity: 0.4 } }
      ]
    })
    batchCharts.push(chartDensity)
  }

  // 7. 群体暴露浓度频数分布 (Histogram)
  const domParallel = document.getElementById('batchChartParallel')
  if (domParallel) {
    const chartParallel = echarts.init(domParallel)
    const bins = ['0-20', '20-40', '40-60', '60-80', '80-100', '100-150', '150-200', '200-300', '300+']
    const pbFreq  = [68, 195, 312, 278, 186, 112, 58, 28, 8]
    const asFreq  = [124, 248, 305, 241, 158, 98, 48, 18, 5]
    chartParallel.setOption({
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' },
        formatter: function (params) {
          let res = params[0].axisValue + ' μg/L<br/>'
          params.forEach(p => { res += `${p.marker} ${p.seriesName}: ${p.value} 人<br/>` })
          return res
        }
      },
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '18%' },
      xAxis: {
        type: 'category',
        data: bins,
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 10, rotate: 30 }
      },
      yAxis: { type: 'value', name: '样本数 (人)', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: 'Pb (铅)', type: 'bar', barWidth: '35%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#60A5FA' }, { offset: 1, color: '#3B82F6' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          data: pbFreq
        },
        {
          name: 'As (砷)', type: 'bar', barWidth: '35%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#A7F3D0' }, { offset: 1, color: '#10B981' }
            ]),
            borderRadius: [4, 4, 0, 0]
          },
          data: asFreq
        }
      ]
    })
    batchCharts.push(chartParallel)
  }

  // 8. 工龄-年龄-毒素累积画像 (Bubble Scatter)
  const domBubble = document.getElementById('batchChartBubble')
  if (domBubble) {
    const chartBubble = echarts.init(domBubble)
    const bubbleData = [
      [25, 2, 15], [30, 5, 25], [35, 8, 40], [42, 15, 65], [48, 20, 85], [55, 25, 110],
      [28, 4, 20], [38, 12, 55], [45, 18, 75], [52, 22, 95], [58, 28, 130]
    ]
    chartBubble.setOption({
      tooltip: { formatter: (p) => `年龄: ${p.data[0]}岁<br/>工龄: ${p.data[1]}年<br/>特征指数: ${p.data[2]}` },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', name: '年龄 (岁)', splitLine: { show: false } },
      yAxis: { type: 'value', name: '工龄 (年)', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [{
        type: 'scatter',
        data: bubbleData,
        symbolSize: function (data) { return Math.max(data[2] / 3, 10); }, 
        itemStyle: {
          color: function(params) { return params.data[2] > 70 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(59, 130, 246, 0.7)'; },
          borderColor: '#fff', borderWidth: 1
        }
      }]
    })
    batchCharts.push(chartBubble)
  }

  // ========== 人口学特征统计图表 ==========

  // D1. 婚姻状况分布 (Pie)
  const domMarital = document.getElementById('batchChartMarital')
  if (domMarital) {
    const chartMarital = echarts.init(domMarital)
    chartMarital.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} 人 ({d}%)' },
      legend: { orient: 'horizontal', bottom: '2%', itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 12, fontWeight: 600 } },
      series: [{
        type: 'pie',
        radius: ['35%', '60%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
        label: { show: true, formatter: '{b}\n{d}%', fontWeight: 'bold', fontSize: 12 },
        labelLine: { show: true, length: 8, length2: 12 },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.2)' }
        },
        data: [
          { value: 682, name: '已婚', itemStyle: { color: '#3B82F6' } },
          { value: 327, name: '未婚', itemStyle: { color: '#10B981' } },
          { value: 158, name: '离异', itemStyle: { color: '#F59E0B' } },
          { value: 78,  name: '丧偶', itemStyle: { color: '#8B5CF6' } }
        ]
      }]
    })
    batchCharts.push(chartMarital)
  }

  // D2. 文化程度构成 (Horizontal Bar)
  const domEducation = document.getElementById('batchChartEducation')
  if (domEducation) {
    const chartEducation = echarts.init(domEducation)
    chartEducation.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '22%', right: '10%', bottom: '10%', top: '10%' },
      xAxis: { type: 'value', name: '人数', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: {
        type: 'category',
        data: ['小学及以下', '初中', '高中/中专', '大专', '本科', '硕士及以上'],
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 12 }
      },
      series: [{
        type: 'bar',
        barWidth: '50%',
        data: [
          { value: 86,  itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FCA5A5' }, { offset: 1, color: '#EF4444' }]) } },
          { value: 312, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#FCD34D' }, { offset: 1, color: '#F59E0B' }]) } },
          { value: 428, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#A7F3D0' }, { offset: 1, color: '#10B981' }]) } },
          { value: 245, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#93C5FD' }, { offset: 1, color: '#3B82F6' }]) } },
          { value: 142, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#C4B5FD' }, { offset: 1, color: '#6366F1' }]) } },
          { value: 32,  itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#DDD6FE' }, { offset: 1, color: '#8B5CF6' }]) } }
        ],
        label: { show: true, position: 'right', fontWeight: 'bold', fontSize: 12, color: '#374151', formatter: '{c} 人' },
        itemStyle: { borderRadius: [0, 4, 4, 0] }
      }]
    })
    batchCharts.push(chartEducation)
  }

  // D3. 家庭年收入分布 (Stacked Bar by range)
  const domIncome = document.getElementById('batchChartIncome')
  if (domIncome) {
    const chartIncome = echarts.init(domIncome)
    chartIncome.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: function(params) {
        let res = params[0].axisValue + '<br/>'
        params.forEach(p => { res += `${p.marker} ${p.seriesName}: ${p.value} 人<br/>` })
        return res
      }},
      legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, textStyle: { fontSize: 10 } },
      grid: { left: '15%', right: '5%', bottom: '15%', top: '18%' },
      xAxis: {
        type: 'category',
        data: ['<3万', '3~5万', '5~8万', '8~12万', '12~20万', '>20万'],
        axisTick: { show: false },
        axisLabel: { fontWeight: 'bold', fontSize: 11 }
      },
      yAxis: { type: 'value', name: '人数', splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        {
          name: '男性', type: 'bar', stack: 'total', barWidth: '45%',
          itemStyle: { color: '#3B82F6', borderRadius: [0, 0, 0, 0] },
          label: { show: true, color: '#fff', fontWeight: 'bold', fontSize: 11 },
          data: [52, 148, 245, 218, 138, 55]
        },
        {
          name: '女性', type: 'bar', stack: 'total', barWidth: '45%',
          itemStyle: { color: '#EC4899', borderRadius: [4, 4, 0, 0] },
          label: { show: true, color: '#fff', fontWeight: 'bold', fontSize: 11 },
          data: [38, 102, 118, 72, 42, 17]
        }
      ]
    })
    batchCharts.push(chartIncome)
  }
}

/* ==============================================
   初始化单人模式科研 ECharts (纯 EDA 阶段)
   ============================================== */
let singleCharts = []

const initSingleECharts = () => {
  singleCharts.forEach(c => c.dispose())
  singleCharts = []

  // 1. 主图：相对暴露指数画像
  const domMaster = document.getElementById('singleChartMaster')
  if (domMaster) {
    const chartMaster = echarts.init(domMaster)
    const elements = ['Pb(铅)', 'Cd(镉)', 'Hg(汞)', 'Th(钍)', 'Li(锂)', 'Cr(铬)', 'Ni(镍)', 'Co(钴)', 'As(砷)', 'Rn(氡)']
    const values = [124, 89, 24, 12, 18, 34, 65, 40, 105, 30]
    chartMaster.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, formatter: '{b}: {c}% 相对限值' },
      grid: { left: '5%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
      xAxis: { type: 'category', data: elements, axisLabel: { fontWeight: 'bold' }, axisTick: { show: false } },
      yAxis: { type: 'value', max: 150, splitLine: { lineStyle: { type: 'dashed' } } },
      visualMap: { show: false, pieces: [{ gt: 0, lte: 50, color: '#34D399' }, { gt: 50, lte: 100, color: '#FBBF24' }, { gt: 100, color: '#EF4444' }] },
      series: [{
        name: '相对暴露指数', type: 'bar', barWidth: '40%', data: values, itemStyle: { borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: 'top', formatter: '{c}%', fontWeight: 'bold' },
        markLine: {
          silent: true, symbol: 'none', lineStyle: { width: 2, type: 'dashed' },
          data: [
            { yAxis: 50, lineStyle: { color: '#FBBF24' }, label: { formatter: '早期预警界限 (50%)', position: 'insideEndTop' } },
            { yAxis: 100, lineStyle: { color: '#EF4444' }, label: { formatter: '危险超标界限 (100%)', position: 'insideEndTop' } }
          ]
        }
      }]
    })
    singleCharts.push(chartMaster)
  }

  // 子图 1：雷达图
  const domRadar = document.getElementById('singleChartRadar')
  if (domRadar) {
    const chartRadar = echarts.init(domRadar)
    chartRadar.setOption({
      tooltip: {}, legend: { bottom: 0, itemWidth: 12, itemHeight: 12 },
      radar: { indicator: [{ name: 'Pb 铅', max: 150 }, { name: 'As 砷', max: 150 }, { name: 'Cd 镉', max: 100 }, { name: 'Hg 汞', max: 50 }, { name: 'Cr 铬', max: 50 }, { name: 'Ni 镍', max: 100 }], radius: '60%', center: ['50%', '45%'] },
      series: [{
        name: '暴露分布对比', type: 'radar',
        data: [
          { value: [124, 105, 89, 24, 34, 65], name: '受试者指标', areaStyle: { color: 'rgba(239, 68, 68, 0.3)' }, lineStyle: { color: '#EF4444' }, itemStyle: { color: '#EF4444' } },
          { value: [100, 100, 100, 100, 100, 100], name: '临床安全阈值上限', areaStyle: { color: 'rgba(16, 185, 129, 0.1)' }, lineStyle: { color: '#10B981', type: 'dashed' }, itemStyle: { color: '#10B981' } }
        ]
      }]
    })
    singleCharts.push(chartRadar)
  }

  // 子图 2：折线图
  const domTimeline = document.getElementById('singleChartTimeline')
  if (domTimeline) {
    const chartTimeline = echarts.init(domTimeline)
    chartTimeline.setOption({
      tooltip: { trigger: 'axis' }, legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10 },
      grid: { left: '12%', right: '5%', bottom: '15%', top: '20%' },
      xAxis: { type: 'category', boundaryGap: false, data: ['2022', '2023', '2024', '2025', '2026(今)'] },
      yAxis: { type: 'value', max: 150, splitLine: { lineStyle: { type: 'dashed' } } },
      series: [
        { name: 'Pb 走势', type: 'line', data: [80, 95, 110, 118, 124], smooth: true, itemStyle: { color: '#EF4444' }, lineStyle: { width: 3 }, markArea: { itemStyle: { color: 'rgba(16, 185, 129, 0.1)' }, data: [ [{ yAxis: '0' }, { yAxis: '100' }] ] } },
        { name: 'As 走势', type: 'line', data: [70, 85, 95, 102, 105], smooth: true, itemStyle: { color: '#F59E0B' }, lineStyle: { width: 3 } },
        { name: 'Cd 走势', type: 'line', data: [45, 55, 68, 79, 89], smooth: true, itemStyle: { color: '#3B82F6' }, lineStyle: { width: 3 } }
      ]
    })
    singleCharts.push(chartTimeline)
  }

  // 子图 3：条形图
  const domPercentile = document.getElementById('singleChartPercentile')
  if (domPercentile) {
    const chartPercentile = echarts.init(domPercentile)
    chartPercentile.setOption({
      tooltip: { formatter: '{b} 处于全厂前 {c}% 水平' },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '10%' },
      xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%' }, splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: ['Cr', 'Ni', 'Cd', 'As', 'Pb'], axisTick: { show: false }, axisLabel: { fontWeight: 'bold' } },
      series: [{
        name: '百分位', type: 'bar', barWidth: '40%', data: [42, 68, 85, 92, 98],
        itemStyle: { color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [{ offset: 0, color: '#FCA5A5' }, { offset: 1, color: '#EF4444' }]), borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: 'right', formatter: '前 {c}%', fontWeight: 'bold' },
        markLine: { silent: true, symbol: 'none', label: { formatter: '中位数\n(P50)', position: 'start' }, lineStyle: { color: '#64748B', type: 'dashed' }, data: [{ xAxis: 50 }] }
      }]
    })
    singleCharts.push(chartPercentile)
  }

  // 子图 4：嵌套环形图
  const domRiskPie = document.getElementById('singleChartRiskPie')
  if (domRiskPie) {
    const chartRiskPie = echarts.init(domRiskPie)
    chartRiskPie.setOption({
      tooltip: { trigger: 'item', formatter: '{a} <br/>{b}: {c} ({d}%)' },
      series: [
        {
          name: '受累靶器官', type: 'pie', selectedMode: 'single', radius: [0, '40%'], label: { position: 'inner', fontSize: 11, color: '#fff', fontWeight: 'bold' }, labelLine: { show: false }, itemStyle: { borderColor: '#fff', borderWidth: 1 },
          data: [ { value: 45, name: '神经系', itemStyle: { color: '#EF4444' } }, { value: 35, name: '泌尿系', itemStyle: { color: '#F59E0B' } }, { value: 20, name: '肝/心', itemStyle: { color: '#3B82F6' } } ]
        },
        {
          name: '主导金属特征', type: 'pie', radius: ['50%', '75%'], itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 }, label: { formatter: '{b|{b}}\n{c}%', rich: { b: { fontSize: 12, fontWeight: 'bold' } } },
          data: [ { value: 30, name: 'Pb 诱导', itemStyle: { color: '#FCA5A5' } }, { value: 15, name: 'Hg 协同', itemStyle: { color: '#F87171' } }, { value: 25, name: 'As 诱导', itemStyle: { color: '#FCD34D' } }, { value: 10, name: 'Cd 协同', itemStyle: { color: '#FBBF24' } }, { value: 12, name: 'Cd 蓄积', itemStyle: { color: '#93C5FD' } }, { value: 8, name: 'Cr/Ni', itemStyle: { color: '#60A5FA' } } ]
        }
      ]
    })
    singleCharts.push(chartRiskPie)
  }

  // 子图 5：特征标准化 Z-Score 偏离图 
  const domZScore = document.getElementById('singleChartZScore')
  if (domZScore) {
    const chartZScore = echarts.init(domZScore)
    chartZScore.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '15%', right: '10%', bottom: '15%', top: '15%' },
      xAxis: { type: 'value', name: '偏离程度', splitLine: { lineStyle: { type: 'dashed' } } },
      yAxis: { type: 'category', data: ['Cr', 'Ni', 'Cd', 'As', 'Pb'], axisTick: { show: false }, axisLabel: { fontWeight: 'bold' } },
      series: [
        {
          name: '特异性偏离', type: 'bar', barWidth: '50%',
          label: { show: true, position: 'right', formatter: '{c}' },
          data: [
            { value: -0.8, itemStyle: { color: '#34D399' }, label: { position: 'left' } },
            { value: 0.3, itemStyle: { color: '#FBBF24' } },
            { value: 1.5, itemStyle: { color: '#F87171' } },
            { value: 2.1, itemStyle: { color: '#EF4444' } },
            { value: 3.2, itemStyle: { color: '#B91C1C' } }
          ]
        }
      ]
    })
    singleCharts.push(chartZScore)
  }

  // 子图 6：多维异常检测指数 (Gauge)
  const domAnomaly = document.getElementById('singleChartAnomaly')
  if (domAnomaly) {
    const chartAnomaly = echarts.init(domAnomaly)
    chartAnomaly.setOption({
      tooltip: { formatter: '{a} <br/>{b} : {c}' },
      series: [
        {
          name: '偏移指数', type: 'gauge',
          center: ['50%', '60%'], radius: '80%',
          min: 0, max: 20,
          splitNumber: 4,
          axisLine: {
            lineStyle: {
              width: 12,
              color: [ [0.5, '#34D399'], [0.8, '#FBBF24'], [1, '#EF4444'] ]
            }
          },
          pointer: { itemStyle: { color: 'auto' } },
          axisTick: { distance: -12, length: 8, lineStyle: { color: '#fff', width: 2 } },
          splitLine: { distance: -12, length: 20, lineStyle: { color: '#fff', width: 3 } },
          axisLabel: { color: 'inherit', distance: 20, fontSize: 10 },
          detail: { valueAnimation: true, formatter: '{value}', color: 'inherit', fontSize: 24, fontWeight: 'bold' },
          data: [{ value: 16.4, name: '报警红区' }],
          title: { offsetCenter: [0, '30%'], fontSize: 12, color: '#64748B', fontWeight: 'bold' }
        }
      ]
    })
    singleCharts.push(chartAnomaly)
  }
}

onMounted(() => {
  window.addEventListener('resize', () => { 
    batchCharts.forEach(c => c.resize()) 
    singleCharts.forEach(c => c.resize())
  })
})
</script>

<style lang="scss" scoped>
@use "sass:color";
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

.main-content { flex: 1; display: flex; flex-direction: column; overflow-y: auto; scroll-behavior: smooth; background: #F8FAFC;}

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

.page-container { padding: 40px; max-width: 1400px; margin: 0 auto; width: 100%; padding-bottom: 100px; }

.pipeline-steps { display: flex; align-items: center; margin-bottom: 30px; background: transparent; padding: 0; border: none; .step { display: flex; align-items: center; gap: 8px; font-size: 0.95rem; font-weight: 600; color: $text-muted; .step-num { width: 24px; height: 24px; border-radius: 50%; background: #E5E7EB; display: flex; justify-content: center; align-items: center; font-size: 0.85rem; } &.active { color: $color-primary; .step-num { background: $color-primary; color: #FFF; } } } .step-line { flex: 1; height: 2px; background: #E5E7EB; margin: 0 16px; position: relative; transition: 0.3s; &.active-line { background: $color-primary; } } }

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
  &.ready .kpi-icon { background: #ECFDF5; color: #10B981; }
  .kpi-info { display: flex; flex-direction: column; span { font-size: 0.85rem; color: $text-muted; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;} strong { font-size: 1.8rem; font-weight: 900; color: $text-main; small { font-size: 0.9rem; color: #94A3B8; font-weight: 600;}} .text-danger { color: #EF4444; } }
}

.batch-charts-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; margin-bottom: 40px; }
.demographic-row { margin-bottom: 16px; padding-bottom: 8px; border-bottom: 2px dashed #E2E8F0; }
.b-chart-card { 
  background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02); display: flex; flex-direction: column;
  .b-c-header { margin-bottom: 16px; padding-bottom: 16px; border-bottom: 1px dashed #F1F5F9; h4 { margin: 0; font-size: 1.05rem; font-weight: 800; color: $text-main; } .sub-title { font-size: 0.85rem; color: $text-muted; margin-top: 6px; display: block;} }
  .b-c-canvas { flex: 1; min-height: 280px; width: 100%; }
}
.col-span-2 { grid-column: span 2; }
.col-span-1 { grid-column: span 1; }
.mb-6 { margin-bottom: 24px; }

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

@media (max-width: 1200px) { .batch-charts-grid { grid-template-columns: 1fr 1fr; } .kpi-row { grid-template-columns: 1fr 1fr; } .card-layout-grid { flex-direction: column; } .form-entry-area { border-right: none; border-bottom: 1px solid $border-color; } .clinical-input-grid { grid-template-columns: repeat(2, 1fr); } .bottom-action-bar { flex-direction: column; gap: 20px; align-items: stretch; .btn-next-step{ width: 100%; } } }
</style>