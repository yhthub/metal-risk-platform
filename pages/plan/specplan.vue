<template>
  <div class="system-layout">
   <Sidebar default-active="5" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goBack">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">返回方案列表</span>
            <span class="divider">|</span>
            <span class="page-title-top">方案深度解析报告</span>
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
          <div class="report-watermark">AI INTERVENTION REPORT</div>
          
          <div class="report-header">
            <div class="rh-left">
              <svg class="report-logo-custom" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
              <div class="rh-text">
                <h1>{{ activePlan.title }}</h1>
                <p>编号：INTER-20260512-{{ activePlan.id.toUpperCase() }} | 生成时间：2026-05-12 15:40</p>
              </div>
            </div>
            <div class="rh-right">
              <div class="risk-seal">
                <span>风险级别</span>
                <strong class="text-danger">HIGH</strong>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="report-section">
            <h3 class="rs-title">一、干预对象与场景评估</h3>
            <el-descriptions :column="2" border class="custom-descriptions">
              <el-descriptions-item label="评估对象">SZ-102 (冶炼工)</el-descriptions-item>
              <el-descriptions-item label="所属单位">第一熔炼车间</el-descriptions-item>
              <el-descriptions-item label="核心场景">高温铅砷蒸汽复合暴露环境，工龄12年，存在个体防护效能衰减现象。</el-descriptions-item>
            </el-descriptions>
          </div>

          <div class="report-section">
            <h3 class="rs-title">二、风险触发条件 (Trigger Conditions)</h3>
            <div class="trigger-box">
              <div class="t-item danger">
                <span class="t-label">全血 Pb 浓度：</span>
                <span class="t-value">1.24 μg/L (超标 124%)</span>
              </div>
              <div class="t-item danger">
                <span class="t-label">尿 As 浓度：</span>
                <span class="t-value">1.05 μg/g (超标 105%)</span>
              </div>
              <div class="t-item warn">
                <span class="t-label">核心预警：</span>
                <span class="t-value">SHAP 贡献度显示 Pb 对中枢神经系统损伤驱动力达 0.85。</span>
              </div>
            </div>
          </div>

          <div class="report-section">
            <h3 class="rs-title">三、干预目标 (Intervention Goals)</h3>
            <div class="goals-grid">
              <div class="goal-item"><el-icon><CircleCheckFilled /></el-icon> 2周内将血铅浓度下降至 0.6 μg/L 以下</div>
              <div class="goal-item"><el-icon><CircleCheckFilled /></el-icon> 阻断血脑屏障进一步受损，逆转早期神经功能震颤</div>
              <div class="goal-item"><el-icon><CircleCheckFilled /></el-icon> 提升肾小管 GSH 储备，防范慢性肾损伤进展</div>
            </div>
          </div>

          <div class="report-section">
            <h3 class="rs-title">四、四维阻断策略矩阵</h3>
            <el-row :gutter="20">
              <el-col :span="6" v-for="m in measureDetails" :key="m.label">
                <div class="measure-card" :class="m.type">
                  <div class="m-icon"><el-icon><component :is="m.icon" /></el-icon></div>
                  <h4>{{ m.label }}措施</h4>
                  <p>{{ m.content }}</p>
                </div>
              </el-col>
            </el-row>
          </div>

          <div class="report-section">
            <h3 class="rs-title">五、标准化实施路径流程 (Clinical Pathway)</h3>
            <el-steps :active="2" finish-status="success" simple style="margin-top: 20px">
              <el-step title="准备期：脱岗隔离与体检" />
              <el-step title="实施期：药物干预与膳食调整" />
              <el-step title="巩固期：定期随访监测" />
            </el-steps>
            <div class="process-detail">
              <p><strong>1. 第1-3天：</strong> 停止现场作业，入住职业病观察病房，建立驱铅液体通路。</p>
              <p><strong>2. 第4-10天：</strong> 每日监测心电图与肾功，根据尿量调整依地酸钙钠剂量。</p>
              <p><strong>3. 第14天以后：</strong> 出院后维持低铅饮食，每日补锌 20mg。</p>
            </div>
          </div>

          <div class="report-section">
            <h3 class="rs-title">六、预期效果评估指标</h3>
            <div class="metrics-container">
              <div class="metric-block">
                <div class="mb-title">生化指标 (Biochemical)</div>
                <p>血铅 (Pb) 降幅 > 40% | 尿 As 降幅 > 50% | 尿 NAG 酶恢复正常</p>
              </div>
              <div class="metric-block">
                <div class="mb-title">功能指标 (Functional)</div>
                <p>神经传导速度恢复 > 5% | 步态稳定性评分提升 | 认知专注度恢复</p>
              </div>
            </div>
          </div>

          <div class="report-section highlight">
            <h3 class="rs-title">七、AI 智能推荐算法依据</h3>
            <div class="recom-content">
              <div class="rc-text">
                本推荐基于 <strong>德尔菲专家共识</strong> 与 <strong>AHP 层次分析模型</strong>。系统识别 SZ-102 当前的主要矛盾在于 <strong>“高暴露水平下的敏感靶器官（神经）”</strong>。经 XGBoost 模拟测算，本方案的风险阻断期望值最高（0.89），且实施成本与调岗冲突系数最低。
              </div>
              <div class="rc-chart" ref="recomChartRef"></div>
            </div>
          </div>

          <div class="report-footer">
            <div class="sign-area">
              <p>审核医生：<span class="sign">Dr. Li Hua</span></p>
              <p>系统认证：<span class="sign-system">AI Decision Engine v3.2</span></p>
            </div>
            <div class="report-btns">
              <el-button type="success" size="large" @click="handlePrint"><el-icon><Printer /></el-icon> 打印并导出正式报告</el-button>
              <el-button type="info" size="large" plain @click="goBack">返回方案矩阵</el-button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Coin, DataLine, TrendCharts, Share, DocumentChecked, ArrowLeft, CircleCheckFilled, OfficeBuilding, Avatar, FirstAidKit, Management, Printer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
// ✨ 已删除 import { ElMessage } from 'element-plus'，Nuxt会自动导入它，从而解决dayjs报错

const router = useRouter()
const route = useRoute()

// 接收路由参数（如列表页跳转时通过 query 传递的 id 和 title）
const activePlan = ref({
  id: route.query.id || 'env1',
  title: route.query.title || '干预方案详情'
})

const measureDetails = [
  { label: '环境', type: 'env', icon: 'OfficeBuilding', content: '车间负压吸风频率提升 15Hz，每 2 小时实施湿式地面清洗，避免粉尘扬起。' },
  { label: '防护', type: 'pro', icon: 'Avatar', content: '更换为 3M-P100 级高效滤棉面罩，增加个体皮肤暴露隔离涂层应用。' },
  { label: '健康', type: 'hea', icon: 'FirstAidKit', content: '启动 1 周期（3天）EDTA-CaNa2 络合治疗，后续 2 周内补充 GSH 还原剂。' },
  { label: '管理', type: 'man', icon: 'Management', content: '工作时长由 8h 缩减为 6h，实施岗位轮转监测，每 2 周进行一次血铅快检。' }
]

const recomChartRef = ref(null)
let recomChartInstance = null

// 返回上一页
const goBack = () => {
  router.back()
}

// 打印报告
const handlePrint = () => {
  ElMessage.success('报告正在排版中，准备调用系统打印机...')
  setTimeout(() => {
    window.print()
  }, 500)
}

// 初始化 ECharts 雷达图
const initRecommendationChart = () => {
  if (!recomChartRef.value) return
  recomChartInstance = echarts.init(recomChartRef.value)
  recomChartInstance.setOption({
    radar: {
      indicator: [
        { name: '阻断效能', max: 100 }, { name: '临床可行性', max: 100 }, { name: '成本可控', max: 100 },
        { name: '调岗连续性', max: 100 }, { name: '代谢友好度', max: 100 }
      ],
      shape: 'circle',
      axisName: { color: '#475569' }
    },
    series: [{
      type: 'radar',
      data: [{ value: [89, 95, 70, 85, 90], areaStyle: { color: 'rgba(29, 78, 216, 0.2)' }, lineStyle: { color: '#1D4ED8' } }]
    }]
  })
}

const resizeChart = () => {
  if (recomChartInstance) recomChartInstance.resize()
}

onMounted(() => {
  nextTick(() => {
    initRecommendationChart()
  })
  window.addEventListener('resize', resizeChart)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeChart)
  if (recomChartInstance) recomChartInstance.dispose()
})
</script>

<style lang="scss" scoped>
$color-primary: #1D4ED8;
$color-bg: #F8FAFC; 
$text-main: #0F172A; 
$text-muted: #64748B; 
$border-color: #E2E8F0;
$color-danger: #EF4444; 
$color-warn: #F59E0B;

* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; background-color: $color-bg; font-family: 'Inter', -apple-system, sans-serif; overflow: hidden; }

/* ==========================================
   侧边栏与顶栏框架样式
   ========================================== */
.sidebar { width: 260px; background-color: #fff; border-right: 1px solid $border-color; display: flex; flex-direction: column; z-index: 10; flex-shrink: 0; box-shadow: 2px 0 10px rgba(0,0,0,0.02); }
.brand-logo { height: 60px; display: flex; align-items: center; gap: 12px; padding: 0 24px; border-bottom: 1px solid $border-color; color: $text-main; font-weight: 800; font-size: 1.15rem; svg { width: 24px; height: 24px; color: $color-primary; } }
.menu-container { padding: 24px 16px; overflow-y: auto; flex: 1; }
.menu-group { margin-bottom: 30px; }
.menu-title { font-size: 0.8rem; font-weight: 700; color: #9CA3AF; margin-bottom: 12px; padding-left: 12px; text-transform: uppercase; }
.menu-item { display: flex; align-items: center; gap: 12px; padding: 12px 16px; border-radius: 8px; color: $text-muted; font-size: 0.95rem; font-weight: 500; cursor: pointer; transition: 0.2s; margin-bottom: 4px; &:hover { background-color: #F1F5F9; color: $text-main; } &.active { background-color: #EFF6FF; color: $color-primary; font-weight: 600; } }

.main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth; }
.ep-header { height: 60px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex; justify-content: center; flex-shrink: 0; }
.nav-wrapper { width: 100%; padding: 0 40px; display: flex; justify-content: space-between; align-items: center; }
.back-link { display: flex; align-items: center; gap: 12px; cursor: pointer; color: $text-main; &:hover { color: $color-primary; } .back-text { font-size: 1.05rem; font-weight: 600; } .divider { color: #D1D5DB; margin: 0 4px; } .page-title-top { font-size: 1.1rem; font-weight: 800; } }
.user-profile { display: flex; align-items: center; gap: 12px; font-weight: 500; font-size: 0.95rem; .avatar { width: 32px; height: 32px; border-radius: 50%; background: #EFF6FF; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; } }


/* ==========================================
   报告页面核心样式 (保证灰底和白纸自适应高度)
   ========================================== */
.report-view-wrapper { 
  flex: 1 0 auto; 
  background: #E2E8F0;
  padding: 40px 0; 
  display: flex; 
  justify-content: center; 
  align-items: flex-start; 
}

.report-paper { 
  background: #fff; 
  width: 1000px; 
  height: max-content;
  padding: 80px; 
  position: relative; 
  box-shadow: 0 20px 50px rgba(0,0,0,0.1); 
  border-radius: 2px; 
}

.report-watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-35deg); font-size: 80px; color: rgba(0,0,0,0.03); font-weight: 900; pointer-events: none; white-space: nowrap; }
.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; 
  .rh-left { display: flex; align-items: center; gap: 12px; }
  /* ✨ 核心修改：自定义 SVG 图标的样式，使其保持蓝色调并调整大小 */
  .report-logo-custom { width: 32px; height: 32px; color: $color-primary; margin-bottom: 4px;} 
  h1 { font-size: 28px; color: $text-main; margin: 0 0 10px 0; font-weight: 800; letter-spacing: -1px;} p { font-size: 13px; color: $text-muted; margin: 0; } .risk-seal { border: 3px solid $color-danger; width: 100px; height: 100px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; transform: rotate(15deg); span { font-size: 12px; color: $color-danger; } strong { font-size: 22px; color: $color-danger; } } }

.report-section { margin-top: 40px; .rs-title { font-size: 18px; font-weight: 800; color: $text-main; border-bottom: 2px solid $text-main; padding-bottom: 8px; margin-bottom: 20px; } &.highlight { background: #F1F5F9; padding: 30px; border-radius: 8px; } }

.trigger-box { display: flex; gap: 20px; .t-item { flex: 1; padding: 16px; border-radius: 4px; border-left: 4px solid; &.danger { background: #FEF2F2; border-color: $color-danger; color: #991B1B;} &.warn { background: #FFFBEB; border-color: $color-warn; color: #92400E;} .t-label { font-size: 12px; display: block; margin-bottom: 4px; } .t-value { font-size: 16px; font-weight: 700; } } }

.goals-grid { display: grid; grid-template-columns: 1fr; gap: 12px; .goal-item { display: flex; align-items: center; gap: 10px; font-size: 15px; color: #334155; font-weight: 500; } }

.measure-card { padding: 24px; border: 1px solid #E2E8F0; border-radius: 8px; height: 100%; .m-icon { font-size: 24px; margin-bottom: 12px; } h4 { margin: 0 0 10px 0; font-size: 16px; font-weight: 800; } p { font-size: 13px; color: #64748B; line-height: 1.6; margin: 0;} &.env { border-top: 4px solid #3B82F6; .m-icon { color: #3B82F6;} } &.pro { border-top: 4px solid #F59E0B; .m-icon { color: #F59E0B;} } &.hea { border-top: 4px solid #EF4444; .m-icon { color: #EF4444;} } &.man { border-top: 4px solid #8B5CF6; .m-icon { color: #8B5CF6;} } }

.process-detail { background: #F8FAFC; padding: 20px; border-radius: 6px; margin-top: 20px; p { font-size: 14px; margin-bottom: 10px; color: #334155; line-height: 1.6; } }

.metrics-container { display: flex; gap: 20px; .metric-block { flex: 1; padding: 20px; border: 1px dashed $border-color; .mb-title { font-weight: 800; font-size: 14px; color: $color-primary; margin-bottom: 8px; } p { font-size: 13px; margin: 0; color: $text-muted; } } }

.recom-content { display: flex; gap: 30px; align-items: center; .rc-text { flex: 1; font-size: 15px; color: #334155; line-height: 1.8; } .rc-chart { width: 300px; height: 300px; } }

.report-footer { margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end; .sign { font-family: 'Brush Script MT', cursive; font-size: 24px; margin-left: 10px; text-decoration: underline; color: #1e293b; } .sign-system { font-weight: 700; color: #94a3b8; } }

/* 打印样式支持 */
@media print {
  .sidebar, .ep-header, .report-btns { display: none !important; }
  .main-content { height: auto; overflow: visible; }
  .report-paper { box-shadow: none; padding: 40px; }
}
</style>