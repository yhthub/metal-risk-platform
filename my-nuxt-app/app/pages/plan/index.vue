<template>
  <div class="system-layout">
    <Sidebar default-active="5" />
    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="nav-left">
            <NuxtLink to="/" class="back-link"><el-icon><ArrowLeft /></el-icon> 系统首页</NuxtLink>
            <span class="divider" aria-hidden="true"></span>
            <span class="page-title-top">方案推荐</span>
          </div>
        </div>
      </header>

      <div class="page-container">
        <PipelineSteps :current="4" />
        <section class="plan-heading" aria-labelledby="plan-title">
          <div>
            <h1 id="plan-title">干预方案案例</h1>
            <p>选择预防场景与案例，浏览管理措施、实施安排和方案报告。</p>
          </div>
          <div class="heading-meta"><span><strong>2</strong> 个预防场景</span><span><strong>{{ highRiskPersons.length + mediumRiskPersons.length }}</strong> 个预设案例</span></div>
        </section>
        <p class="demo-notice"><el-icon><InfoFilled /></el-icon><span>以下为预设案例，供了解干预流程。个体诊疗与用药需由专业人员评估。</span></p>

        <section class="scenario-section" aria-labelledby="scenario-title">
          <div class="section-heading"><h2 id="scenario-title">选择预防场景</h2></div>
          <div class="scenario-options" role="group" aria-label="预防场景">
            <button type="button" class="scenario-option" :class="{ selected: selectedLevel === 'level2' }" :aria-pressed="selectedLevel === 'level2'" @click="selectedLevel = 'level2'">
              <span class="scenario-icon"><el-icon><FirstAidKit /></el-icon></span>
              <span class="scenario-copy"><strong>二级预防</strong><span>早期筛查 · 专业评估 · 随访管理</span></span>
              <span class="scenario-count">{{ highRiskPersons.length }} 个案例</span><el-icon v-if="selectedLevel === 'level2'" class="selected-mark"><CircleCheck /></el-icon>
            </button>
            <button type="button" class="scenario-option" :class="{ selected: selectedLevel === 'level1' }" :aria-pressed="selectedLevel === 'level1'" @click="selectedLevel = 'level1'">
              <span class="scenario-icon"><el-icon><Sunny /></el-icon></span>
              <span class="scenario-copy"><strong>一级预防</strong><span>健康教育 · 暴露管理 · 持续监测</span></span>
              <span class="scenario-count">{{ mediumRiskPersons.length }} 个案例</span><el-icon v-if="selectedLevel === 'level1'" class="selected-mark"><CircleCheck /></el-icon>
            </button>
          </div>
        </section>

        <div class="plan-workspace">
          <aside class="case-panel" aria-labelledby="case-title">
            <div class="case-heading"><h2 id="case-title">案例对象</h2><span>{{ currentPersons.length }} 个</span></div>
            <div class="case-list" role="group" aria-label="选择案例对象">
              <button v-for="person in currentPersons" :key="person.id" type="button" class="case-option" :class="{ selected: selectedPerson.id === person.id }" :aria-pressed="selectedPerson.id === person.id" @click="selectPerson(person.id)">
                <span class="case-avatar" aria-hidden="true">{{ person.name.slice(0, 1) }}</span>
                <span class="case-copy"><strong>{{ person.name }}</strong><span>{{ person.id }}</span></span>
                <el-icon class="case-arrow"><ArrowRight /></el-icon>
              </button>
            </div>
            <p class="case-hint">点击姓名切换。每个案例包含独立的步骤与报告。</p>
          </aside>

          <section :key="selectedPerson.id" class="plan-detail" aria-label="当前案例方案">
            <div class="person-summary">
              <div class="person-summary-top">
                <div><span class="detail-kicker">{{ selectedLevel === 'level2' ? '二级预防' : '一级预防' }} · 方案示例</span><h2>{{ selectedPerson.name }} <span>{{ selectedPerson.id }}</span></h2></div>
                <el-button type="primary" :icon="Document" @click="goToReport">查看方案报告</el-button>
              </div>
              <div class="person-meta"><span>{{ selectedPerson.dept }}</span><span>暴露工龄 {{ selectedPerson.years }} 年</span><span>涉及因素 {{ selectedPerson.factors }}</span><span class="example-score">示例风险增幅 {{ selectedPerson.score }}%</span></div>
            </div>

            <div class="section-heading workflow-heading"><h2>实施步骤</h2><span>共 {{ selectedPerson.workflow.length }} 步 · 展开查看操作与指标</span></div>
            <div class="workflow-grid">
              <article v-for="(step, index) in selectedPerson.workflow" :key="index" class="workflow-card">
                <div class="workflow-card-header"><span class="step-index">{{ String(index + 1).padStart(2, '0') }}</span><span class="step-tag">{{ step.tag }}</span></div>
                <h3>{{ step.title }}</h3>
                <p class="step-description">{{ step.desc }}</p>
                <div class="step-meta"><span><el-icon><Clock /></el-icon>{{ step.period }}</span><span v-if="step.cost">费用等级：{{ step.cost }}</span></div>
                <details v-if="step.detail || step.indicator" class="step-more">
                  <summary>查看操作与指标 <span aria-hidden="true">＋</span></summary>
                  <div v-if="step.detail" class="step-extra"><strong>操作示例</strong><p>{{ step.detail }}</p></div>
                  <div v-if="step.indicator" class="step-extra"><strong>观察指标示例</strong><p>{{ step.indicator }}</p></div>
                </details>
              </article>
            </div>

            <details class="outcomes-panel">
              <summary><span><el-icon><TrendCharts /></el-icon>成效展示示例</span><span class="outcomes-toggle">展开查看</span></summary>
              <div class="outcomes-body">
                <p>以下百分比为预设展示值，不是本次分析的预测结果或疗效承诺。</p>
                <div class="outcome-grid"><div v-for="outcome in selectedPerson.outcomes" :key="outcome.label" class="outcome-item"><h3>{{ outcome.label }}</h3><div class="outcome-row"><span>干预前</span><div class="outcome-track"><i :style="{ width: outcome.before + '%' }"></i></div><strong>{{ outcome.before }}%</strong></div><div class="outcome-row after"><span>干预后</span><div class="outcome-track"><i :style="{ width: outcome.after + '%' }"></i></div><strong>{{ outcome.after }}%</strong></div></div></div>
              </div>
            </details>
            <div class="detail-footer"><span>完整案例、步骤与成效示例均可在报告中查看。</span><button type="button" @click="goToReport">查看方案报告 <el-icon><ArrowRight /></el-icon></button></div>
          </section>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { ArrowLeft, ArrowRight, CircleCheck, Clock, Document, FirstAidKit, InfoFilled, Sunny, TrendCharts } from '@element-plus/icons-vue'
import { PRODUCT_SHORT_NAME } from '~/utils/product'

useHead({ title: `方案推荐 · ${PRODUCT_SHORT_NAME}` })
const router = useRouter()
const route = useRoute()
const selectedLevel = ref('level2')
const activePerson = ref('SZ-284')
const activeMediumPerson = ref('SZ-089')

const highRiskPersons = ref([
  {
    id: 'SZ-284', name: '张建国', dept: '第一熔炼车间', years: 18, factors: 'Pb, As', score: 68.5, levelClass: 'danger',
    workflow: [
      { title: '立即调离高危岗位', tag: '紧急阻断', type: 'danger', desc: '从熔炼一线调至无尘辅助区，彻底脱离 Pb/As 暴露源，防止剂量继续累积。', detail: '当日办理调岗手续，安排至仓库管理或质检辅助岗位。调岗后 1 周内禁止进入熔炼车间区域。', indicator: '调岗后 2 周复查血铅，目标下降 > 15%', period: '立即执行', cost: '中' },
      { title: '职业健康深度体检', tag: '精准诊断', type: 'primary', desc: '全面排查体内重金属蓄积水平与靶器官损伤程度，为后续治疗提供依据。', detail: '全血 Pb、尿 As 定量检测；肝功（ALT/AST）、肾功（肌酐/尿素氮）；尿 β2-微球蛋白、NAG 酶（早期肾小管损伤标志物）；神经传导速度测试；血常规+网织红细胞计数。', indicator: '血 Pb > 400 μg/L 或尿 As > 100 μg/L 时启动驱铅治疗', period: '3-5 个工作日', cost: '低' },
      { title: 'EDTA-CaNa2 驱铅试验治疗', tag: '临床干预', type: 'warning', desc: '对血铅超标者实施依地酸钙钠试验性驱铅，同步评估体内可动员铅储备量。', detail: 'EDTA-CaNa2 1g + 5% GS 250ml 静脉滴注，每日 1 次，连续 3 天为一疗程。停药 4 天后复查血铅与 24h 尿铅排泄量。根据排铅量决定是否追加 1-2 个疗程。', indicator: '24h 尿铅 > 500 μg 为阳性，提示体内铅储备显著', period: '每疗程 7 天，共 1-3 疗程', cost: '中' },
      { title: 'GSH 抗氧化保护治疗', tag: '靶器官保护', type: 'warning', desc: '给予还原型谷胱甘肽保护肝肾靶器官，中和重金属诱发的氧化损伤。', detail: 'GSH 1.8g + NS 250ml 静脉滴注，每日 1 次，连续 7-14 天。同时口服维生素 E 400IU/日协同抗氧化。', indicator: '治疗后 ALT/AST 恢复正常，尿 β2-微球蛋白下降', period: '7-14 天', cost: '中' },
      { title: '双周生化溯源复查', tag: '疗效追踪', type: 'primary', desc: '每 2 周复查全血 Pb、尿 As，跟踪驱铅效果并防范骨骼蓄积铅反流入血。', detail: '停药后第 2 周首次复查，此后每 2 周一次直至连续 3 次正常。重点关注血铅是否出现"反弹升高"现象。', indicator: '连续 3 次血 Pb < 200 μg/L 视为治疗达标', period: '治疗后 2-8 周', cost: '低' },
      { title: '长效神经行为深度随访', tag: '远期防控', type: 'safe', desc: '建立 12 个月专项档案，每季度评估神经功能与认知状态。', detail: '每季度进行：神经传导速度测试、MMSE 认知量表测评、纯音听力检测。建立个人纵向趋势图，发现异常立即升级处理。', indicator: '神经传导速度下降 > 10% 或 MMSE 评分下降 > 3 分需神经内科会诊', period: '12 个月', cost: '中' }
    ],
    outcomes: [
      { label: '血 Pb 浓度', before: 98, after: 35 },
      { label: '尿 As 浓度', before: 82, after: 40 },
      { label: '神经病变风险', before: 65, after: 25 },
      { label: '肾损伤风险', before: 52, after: 20 }
    ]
  },
  {
    id: 'SZ-105', name: '刘伟', dept: '第一熔炼车间', years: 15, factors: 'Pb, Cd', score: 62.1, levelClass: 'danger',
    workflow: [
      { title: 'P100 全面罩 + 局部负压排风', tag: '紧急防护', type: 'danger', desc: '不调岗但强制升级防护等级，大幅降低 Pb/Cd 吸入量。', detail: '配发 P100 全面罩，工位加装便携式负压排风罩。每日上岗前进行呼吸器密合性自检，每周由安全部门复核一次。', indicator: '2 周后复查血 Pb，预期下降 10-15%', period: '即刻执行', cost: '低' },
      { title: '肾功能深度筛查', tag: '精准诊断', type: 'primary', desc: 'Cd 对肾小管的损伤不可逆且早期隐匿，必须通过专项指标捕获极早期病变。', detail: '尿 Cd 定量、尿 β2-微球蛋白、尿 NAG 酶、尿视黄醇结合蛋白、肾小球滤过率(eGFR)、肾脏超声。', indicator: '尿 Cd > 5 μg/g Cr 或 β2-微球蛋白 > 300 μg/L 提示肾小管损伤', period: '3-5 个工作日', cost: '低' },
      { title: '驱铅治疗 + 保肾联合方案', tag: '临床干预', type: 'warning', desc: '在密切监测肾功能前提下实施 EDTA 驱铅，同时给予保肾治疗。', detail: 'EDTA-CaNa2 1g 静滴 × 3 天，同步给予金水宝胶囊（虫草制剂）保肾。治疗期间每日监测尿量与尿常规。', indicator: '肌酐清除率 < 60ml/min 时禁用 EDTA，改用 DMSA 口服', period: '1-2 个疗程', cost: '中' },
      { title: 'Cd 蓄积专项监测', tag: '长期管控', type: 'primary', desc: 'Cd 在肾脏的生物半衰期长达 10-30 年，需建立长期监测计划。', detail: '每 3 个月检测尿 Cd 与 β2-微球蛋白。建立个人 Cd 蓄积趋势图。若尿 Cd 持续 > 3 μg/g Cr，需考虑永久调离。', indicator: '尿 Cd 年均下降 > 10% 为有效干预', period: '持续 3-5 年', cost: '低' },
      { title: '营养拮抗与膳食干预', tag: '辅助措施', type: 'safe', desc: '通过高钙高锌膳食竞争性减少 Cd/Pb 吸收，补充维 C 促进排泄。', detail: '每日钙片 600mg + 锌 15mg，维生素 C 1000mg。食堂优先供应牛奶、豆制品、海产品。禁止饮酒（加重肾脏负担）。', indicator: '3 个月后复查血 Pb，结合驱铅效果综合评估', period: '长期维持', cost: '极低' }
    ],
    outcomes: [
      { label: '血 Pb 浓度', before: 95, after: 40 },
      { label: '尿 Cd 蓄积', before: 78, after: 55 },
      { label: '肾小管损伤', before: 60, after: 30 },
      { label: '神经病变风险', before: 55, after: 35 }
    ]
  },
  {
    id: 'SZ-032', name: '王强', dept: '第一熔炼车间', years: 14, factors: 'As, Ni', score: 55.4, levelClass: 'danger',
    workflow: [
      { title: '岗位轮换 + 工时管控', tag: '暴露阻断', type: 'danger', desc: '将高暴露岗位连续作业时间缩短至 4 小时以内，配合轮岗降低累积剂量。', detail: '与 SZ-284（已调离）互换岗位，安排间歇性进入熔炼区。每日高暴露时段不超过 4 小时，工间在通风良好区域休息 30 分钟。', indicator: '1 个月后尿 As 代谢物预期下降 20%', period: '长期执行', cost: '低' },
      { title: 'As 代谢物 + Ni 专项检测', tag: '精准诊断', type: 'primary', desc: '检测尿中砷代谢物形态分布与尿镍浓度，评估实际内暴露剂量。', detail: '尿总砷、无机砷/有机砷比值（判断 As 来源）、尿 Ni、发砷、肝功全套、皮肤科会诊（砷角化筛查）。', indicator: '无机砷占比 > 20% 提示职业暴露为主，尿 Ni > 40 μg/L 需重点关注', period: '3-5 个工作日', cost: '低' },
      { title: '抗氧化与肝脏保护治疗', tag: '靶器官保护', type: 'warning', desc: 'As 和 Ni 均具有显著肝毒性，需给予保肝与抗氧化联合治疗。', detail: '多烯磷脂酰胆碱 456mg tid 口服保肝，GSH 1.2g 静滴 × 7 天抗氧化。禁止饮酒，避免使用肝毒性药物。', indicator: 'ALT/AST 恢复正常，γ-GT 下降', period: '14-28 天', cost: '中' },
      { title: '皮肤与呼吸系统专项筛查', tag: '并发症排查', type: 'primary', desc: '慢性砷暴露可致皮肤角化、色素沉着及肺癌风险升高，需专项排查。', detail: '皮肤科全面体检（掌跖角化、色素异常、 Bowen 病筛查）；胸部低剂量 CT；肺功能检测。', indicator: '发现皮肤角化灶需活检排除癌前病变', period: '1-2 周', cost: '低' },
      { title: '季度复查与年度评估', tag: '长期监测', type: 'safe', desc: '建立 As/Ni 长期监测档案，每季度复查暴露指标，年度全面评估。', detail: '每 3 个月：尿 As 形态分析、尿 Ni、肝功。每年：胸部 CT、皮肤科复查、神经传导速度。', indicator: '连续 4 个季度尿 As < 50 μg/L 视为稳定', period: '持续 2 年以上', cost: '低' }
    ],
    outcomes: [
      { label: '尿 As 浓度', before: 82, after: 35 },
      { label: '尿 Ni 浓度', before: 56, after: 30 },
      { label: '肝损伤风险', before: 50, after: 22 },
      { label: '皮肤病变风险', before: 40, after: 15 }
    ]
  },
  {
    id: 'SZ-142', name: '李明', dept: '原矿粉碎区', years: 12, factors: 'Pb, Hg', score: 48.2, levelClass: 'warn',
    workflow: [
      { title: '标准防护装备全面升级', tag: '暴露阻断', type: 'danger', desc: '配发半面罩+P100滤盒、防化手套、护目镜，强化个人防护。', detail: '由安全员现场指导佩戴，确保面部密合。每周检查滤毒盒使用状况，每月更换一次。工服由企业统一清洗，禁止带回家。', indicator: '2 周后复查血 Pb，评估防护效果', period: '即刻执行', cost: '低' },
      { title: 'Pb/Hg 联合暴露精准检测', tag: '精准诊断', type: 'primary', desc: '同时评估铅和汞的体内蓄积水平及联合毒性效应。', detail: '全血 Pb、尿 Hg、血汞、24h 尿汞排泄量、肾功（肌酐/尿素氮/胱抑素 C）、神经行为功能测试（WHO-NCTB）。', indicator: '血 Pb > 300 μg/L 且尿 Hg > 20 μg/L 时需药物干预', period: '3-5 个工作日', cost: '低' },
      { title: '驱铅 + 排汞联合治疗', tag: '临床干预', type: 'warning', desc: '根据检测结果选择 EDTA 驱铅或 DMSA 排汞，或两者序贯治疗。', detail: '若以 Pb 为主：EDTA 1g × 3 天驱铅；若以 Hg 为主：DMSA 10mg/kg × 5 天排汞。两者并存时先驱铅再排汞，间隔 1 周。', indicator: '治疗后 24h 尿铅/尿汞排泄量评估清除效果', period: '2-4 周', cost: '中' },
      { title: '神经行为功能评估', tag: '靶器官评估', type: 'primary', desc: 'Pb/Hg 均具有显著神经毒性，需系统评估中枢与周围神经功能。', detail: 'WHO 神经行为核心测试组合（NCTB）：情绪状态 Profile、简单反应时、数字广度、手提转速度、Benton 视觉保留、目标追踪。', indicator: '任一测试维度 Z 分 < -2 需神经内科进一步评估', period: '1-2 天', cost: '低' },
      { title: '长期随访与健康管理', tag: '持续管控', type: 'safe', desc: '建立 Pb/Hg 联合暴露长期随访档案，动态调整干预强度。', detail: '每月复查血 Pb/尿 Hg × 3 个月，此后每季度一次。年度神经行为复测。个人健康档案电子化管理，自动趋势预警。', indicator: '连续 6 个月血 Pb < 200 μg/L 且尿 Hg < 10 μg/L 视为达标', period: '12-24 个月', cost: '低' }
    ],
    outcomes: [
      { label: '血 Pb 浓度', before: 72, after: 32 },
      { label: '尿 Hg 浓度', before: 60, after: 25 },
      { label: '神经毒性风险', before: 48, after: 18 },
      { label: '肾损伤风险', before: 38, after: 15 }
    ]
  }
])

const mediumRiskPersons = ref([
  {
    id: 'SZ-089', name: '赵铁柱', dept: '原矿粉碎区', years: 11, factors: 'Cd, Cr', score: 41.5,
    workflow: [
      { title: '岗位轮换与暴露时间管控', tag: '暴露阻断', type: 'warning', desc: '实施轮岗制度，将高暴露岗位连续作业时间缩短至 4 小时以内。', detail: '与低暴露岗位（质检、仓库）轮换，每 2 周轮换一次。工间在通风良好区域休息 30 分钟以上。', indicator: '1 个月后复查尿 Cd，预期下降 10-15%', period: '长期执行', cost: '低' },
      { title: 'Cd/Cr 暴露基线评估', tag: '健康筛查', type: 'primary', desc: '检测尿镉、尿铬及肾功能早期标志物，建立个人暴露基线。', detail: '尿 Cd、尿 Cr、尿 β2-微球蛋白、尿 NAG 酶、血常规、肝肾功能、尿常规。', indicator: '尿 Cd > 3 μg/g Cr 或 β2-微球蛋白 > 200 μg/L 需升级管理', period: '3-5 个工作日', cost: '低' },
      { title: '标准防护装备配发', tag: '个人防护', type: 'warning', desc: '配发 KN95 口罩、防护手套、护目镜，培训正确佩戴方法。', detail: '由安全员现场指导佩戴，确保面部密合。每周检查口罩使用状况，每月更换滤芯。', indicator: '防护依从率 > 90%', period: '即刻执行', cost: '低' },
      { title: '钙锌营养拮抗方案', tag: '营养干预', type: 'safe', desc: '每日服用钙锌补充剂，食堂增设高钙高锌菜品。', detail: '钙片 600mg + 锌 15mg/日。食堂每日供应牛奶、豆腐、虾皮。果胶膳食纤维辅助排毒。', indicator: '3 个月后复查尿 Cd，结合轮岗效果综合评估', period: '长期维持', cost: '极低' },
      { title: '季度常规体检', tag: '定期监测', type: 'primary', desc: '每 3 个月复查尿 Cd、尿 Cr 及肾功能指标。', detail: '检查项目：尿 Cd、尿 Cr、尿 β2-微球蛋白、肝肾功能。连续 2 次异常者升级为高危管理。', indicator: '连续 4 个季度指标稳定或下降为达标', period: '每 3 个月', cost: '低' },
      { title: '职业卫生知识培训', tag: '健康教育', type: 'safe', desc: '参加职业危害防护培训，掌握个人卫生规范与防护要点。', content: '培训内容：重金属危害认知、正确佩戴口罩、工后淋浴更衣、禁止车间进食。', indicator: '培训考核通过率 100%', detail: '每半年复训一次，新入职人员必须岗前培训合格方可上岗。', period: '每半年一次', cost: '极低' }
    ],
    outcomes: [
      { label: '尿 Cd 浓度', before: 42, after: 28 },
      { label: '尿 Cr 浓度', before: 35, after: 22 },
      { label: '肾损伤风险', before: 30, after: 18 },
      { label: '综合健康风险', before: 41.5, after: 25 }
    ]
  },
  {
    id: 'SZ-311', name: '陈刚', dept: '第一熔炼车间', years: 9, factors: 'Pb, As', score: 36.8,
    workflow: [
      { title: '工位通风改善', tag: '环境控制', type: 'warning', desc: '在工位加装局部排风罩，降低 Pb/As 粉尘吸入浓度。', detail: '安装便携式负压排风罩，连接粉尘收集池。每日开工前检查排风系统运行状态。', indicator: '工位粉尘浓度下降 > 50%', period: '1-2 周安装', cost: '中' },
      { title: 'Pb/As 基线检测', tag: '健康筛查', type: 'primary', desc: '检测全血铅和尿砷代谢物，评估当前内暴露水平。', detail: '全血 Pb、尿 As（含无机砷/有机砷比值）、肝功能、血常规。', indicator: '血 Pb > 200 μg/L 或尿 As > 50 μg/L 需加强干预', period: '3-5 个工作日', cost: '低' },
      { title: '维生素 C 与抗氧化补充', tag: '营养干预', type: 'safe', desc: '每日补充维生素 C 1000mg，促进铅排泄并抗氧化。', detail: '维生素 C 可将六价铬还原为三价铬，同时加速铅的排泄。配合优质蛋白饮食。', indicator: '3 个月后血 Pb 预期下降 10-15%', period: '长期维持', cost: '极低' },
      { title: '个人卫生规范强化', tag: '行为干预', type: 'warning', desc: '严格执行工后淋浴、工服单独清洗、禁止车间进食。', detail: '设置更衣淋浴区，工服由企业统一清洗。洗手后方可进食饮水。', indicator: '卫生规范依从率 > 95%', period: '长期执行', cost: '极低' },
      { title: '季度血铅监测', tag: '定期监测', type: 'primary', desc: '每 3 个月复查全血 Pb 和尿 As，追踪暴露趋势。', detail: '建立个人纵向趋势图。连续 2 次上升趋势需升级为高危管理并安排深度体检。', indicator: '连续 4 个季度血 Pb < 200 μg/L 为达标', period: '每 3 个月', cost: '低' },
      { title: '年度职业健康体检', tag: '综合评估', type: 'safe', desc: '每年一次全面体检，含神经传导速度和肺功能检测。', detail: '依据《职业健康监护技术规范》(GBZ 188) 执行，含纯音听力、神经传导、肺功能等。', indicator: '体检结果归入个人健康档案', period: '每年一次', cost: '低' }
    ],
    outcomes: [
      { label: '血 Pb 浓度', before: 55, after: 30 },
      { label: '尿 As 浓度', before: 42, after: 25 },
      { label: '肝损伤风险', before: 28, after: 15 },
      { label: '综合健康风险', before: 36.8, after: 20 }
    ]
  },
  {
    id: 'SZ-402', name: '孙磊', dept: '尾气处理组', years: 8, factors: 'As, Ni', score: 32.1,
    workflow: [
      { title: '防护装备升级', tag: '个人防护', type: 'warning', desc: '配发半面罩+P100滤盒和防化手套，强化呼吸与皮肤防护。', detail: '尾气处理岗位 As/Ni 粉尘浓度较高，需升级至 P100 级别防护。每周检查面罩密合性。', indicator: '2 周后尿 As 预期下降 10%', period: '即刻执行', cost: '低' },
      { title: 'As/Ni 基线检测', tag: '健康筛查', type: 'primary', desc: '检测尿砷代谢物和尿镍浓度，评估实际内暴露水平。', detail: '尿总砷、无机砷比值、尿 Ni、肝功、皮肤科筛查（砷角化）。', indicator: '无机砷占比 > 15% 或尿 Ni > 30 μg/L 需重点关注', period: '3-5 个工作日', cost: '低' },
      { title: '高钙锌膳食方案', tag: '营养干预', type: 'safe', desc: '食堂增设高钙高锌菜品，发放钙锌补充剂。', detail: '钙片 600mg + 锌 15mg/日。增加牛奶、豆制品、海产品摄入。', indicator: '3 个月后复查暴露指标', period: '长期维持', cost: '极低' },
      { title: '皮肤健康监测', tag: '专项筛查', type: 'primary', desc: '每 6 个月进行皮肤科检查，排查砷相关皮肤病变。', detail: '重点检查掌跖角化、皮肤色素异常、 Bowen 病等癌前病变。发现异常立即活检。', indicator: '无新发角化灶或色素异常', period: '每 6 个月', cost: '低' },
      { title: '季度常规体检', tag: '定期监测', type: 'primary', desc: '每 3 个月复查尿 As、尿 Ni 和肝功能。', detail: '建立个人暴露趋势档案。连续 2 次异常者升级管理。', indicator: '连续 4 个季度指标稳定为达标', period: '每 3 个月', cost: '低' },
      { title: '戒烟限酒指导', tag: '行为干预', type: 'safe', desc: '提供戒烟限酒咨询，吸烟会加重呼吸道对 As 粉尘的吸收。', detail: '研究显示吸烟工人重金属暴露风险升高 15-20%。提供尼古丁替代疗法支持。', indicator: '吸烟者戒烟或减量 > 50%', period: '持续跟踪', cost: '低' }
    ],
    outcomes: [
      { label: '尿 As 浓度', before: 40, after: 22 },
      { label: '尿 Ni 浓度', before: 32, after: 18 },
      { label: '皮肤病变风险', before: 25, after: 12 },
      { label: '综合健康风险', before: 32.1, after: 18 }
    ]
  },
  {
    id: 'SZ-175', name: '周波', dept: '第一熔炼车间', years: 7, factors: 'Pb', score: 28.5,
    workflow: [
      { title: '标准防护配发', tag: '个人防护', type: 'warning', desc: '配发 KN95 口罩和防护手套，培训正确使用方法。', detail: '每日上岗前自检口罩密合性。工服由企业统一清洗，禁止带回家中。', indicator: '防护依从率 > 90%', period: '即刻执行', cost: '低' },
      { title: '血铅基线检测', tag: '健康筛查', type: 'primary', desc: '检测全血铅浓度和血常规，评估当前铅暴露水平。', detail: '全血 Pb、血常规（关注网织红细胞、点彩红细胞）、锌原卟啉(ZPP)。', indicator: '血 Pb > 150 μg/L 需加强干预', period: '1-3 个工作日', cost: '低' },
      { title: '钙锌竞争性营养补充', tag: '营养干预', type: 'safe', desc: '每日服用钙锌补充剂，通过竞争性吸收减少铅摄入。', detail: '钙片 600mg + 锌 15mg/日。增加牛奶、豆制品摄入。', indicator: '3 个月后血 Pb 预期下降 10%', period: '长期维持', cost: '极低' },
      { title: '个人卫生规范', tag: '行为干预', type: 'warning', desc: '工后淋浴更衣，禁止在车间进食饮水。', detail: '洗手后方可进食。工服与日常衣物分开清洗。', indicator: '卫生规范执行率 100%', period: '长期执行', cost: '极低' },
      { title: '季度血铅监测', tag: '定期监测', type: 'primary', desc: '每 3 个月复查全血 Pb，追踪暴露趋势。', detail: '建立个人血铅趋势图。若连续 2 次上升，升级为中高危管理。', indicator: '连续 4 个季度血 Pb < 150 μg/L 为达标', period: '每 3 个月', cost: '低' },
      { title: '年度职业健康体检', tag: '综合评估', type: 'safe', desc: '每年全面体检，含神经系统和肾功能评估。', detail: '依据 GBZ 188 执行，含血常规、肝肾功能、神经传导速度、纯音听力。', indicator: '体检结果归入健康档案', period: '每年一次', cost: '低' }
    ],
    outcomes: [
      { label: '血 Pb 浓度', before: 35, after: 18 },
      { label: '血液系统风险', before: 22, after: 10 },
      { label: '神经毒性风险', before: 20, after: 10 },
      { label: '综合健康风险', before: 28.5, after: 15 }
    ]
  },
  {
    id: 'SZ-219', name: '吴涛', dept: '原矿粉碎区', years: 6, factors: 'Cd, Hg', score: 24.2,
    workflow: [
      { title: '防护装备配发', tag: '个人防护', type: 'warning', desc: '配发 KN95 口罩、防化手套，强化呼吸与皮肤防护。', detail: '粉碎区粉尘浓度较高，需确保口罩密合性。每周检查更换滤芯。', indicator: '防护依从率 > 90%', period: '即刻执行', cost: '低' },
      { title: 'Cd/Hg 基线检测', tag: '健康筛查', type: 'primary', desc: '检测尿镉和尿汞，评估两种金属的蓄积水平。', detail: '尿 Cd、尿 Hg、尿 β2-微球蛋白、肾功能全套。', indicator: '尿 Cd > 2 μg/g Cr 或尿 Hg > 10 μg/L 需重点关注', period: '3-5 个工作日', cost: '低' },
      { title: '高钙膳食方案', tag: '营养干预', type: 'safe', desc: '增加高钙食品摄入，竞争性减少 Cd/Hg 肠道吸收。', detail: '每日牛奶 500ml、豆腐或虾皮。补充维生素 C 500mg/日。', indicator: '3 个月后复查尿 Cd/Hg', period: '长期维持', cost: '极低' },
      { title: '肾功能定期监测', tag: '定期监测', type: 'primary', desc: '每 3 个月检测尿 Cd、尿 Hg 和肾功能早期标志物。', detail: '尿 Cd、尿 Hg、尿 β2-微球蛋白、尿常规。建立个人趋势图。', indicator: '连续 4 个季度指标稳定为达标', period: '每 3 个月', cost: '低' },
      { title: '个人卫生强化', tag: '行为干预', type: 'warning', desc: '工后淋浴更衣，工服单独清洗，禁止车间进食。', detail: '粉碎区粉尘易附着衣物，必须更换清洁衣物后方可离开。', indicator: '卫生规范执行率 100%', period: '长期执行', cost: '极低' },
      { title: '年度综合体检', tag: '综合评估', type: 'safe', desc: '每年全面体检，重点关注肾功能和神经系统。', detail: '含肾功能、神经传导速度、纯音听力、血常规等。', indicator: '体检结果归入健康档案', period: '每年一次', cost: '低' }
    ],
    outcomes: [
      { label: '尿 Cd 浓度', before: 28, after: 15 },
      { label: '尿 Hg 浓度', before: 22, after: 12 },
      { label: '肾损伤风险', before: 18, after: 8 },
      { label: '综合健康风险', before: 24.2, after: 12 }
    ]
  },
  {
    id: 'SZ-056', name: '郑凯', dept: '尾气处理组', years: 5, factors: 'Cr', score: 18.6,
    workflow: [
      { title: '工位通风改善', tag: '环境控制', type: 'warning', desc: '在尾气处理工位加装局部排风，降低铬粉尘浓度。', detail: '安装移动式排风除尘设备，配合湿式操作减少粉尘扬起。', indicator: '工位 Cr 浓度下降 > 40%', period: '1-2 周', cost: '中' },
      { title: 'Cr 暴露基线检测', tag: '健康筛查', type: 'primary', desc: '检测尿铬浓度和肺功能，评估当前暴露水平。', detail: '尿 Cr、血常规、肝肾功能、肺功能检测、胸部 X 线。', indicator: '尿 Cr > 30 μg/L 或肺功能异常需加强干预', period: '1-3 个工作日', cost: '低' },
      { title: '维生素 C 抗氧化补充', tag: '营养干预', type: 'safe', desc: '每日补充维生素 C 1000mg，将六价铬还原为低毒三价铬。', detail: '维生素 C 是铬中毒的关键拮抗剂。配合优质蛋白饮食。', indicator: '3 个月后复查尿 Cr', period: '长期维持', cost: '极低' },
      { title: '呼吸防护强化', tag: '个人防护', type: 'warning', desc: '配发 KN95 口罩，培训正确佩戴方法。', detail: '铬粉尘主要经呼吸道吸入，确保口罩密合性是关键。', indicator: '防护依从率 > 95%', period: '即刻执行', cost: '低' },
      { title: '季度常规体检', tag: '定期监测', type: 'primary', desc: '每 3 个月复查尿 Cr 和肺功能。', detail: '建立个人暴露趋势档案。连续 2 次异常升级管理。', indicator: '连续 4 个季度尿 Cr < 20 μg/L 为达标', period: '每 3 个月', cost: '低' },
      { title: '年度综合体检', tag: '综合评估', type: 'safe', desc: '每年全面体检，含肺功能和皮肤科检查。', detail: '铬可致鼻中隔穿孔和皮肤溃疡，年度体检需专项排查。', indicator: '体检结果归入健康档案', period: '每年一次', cost: '低' }
    ],
    outcomes: [
      { label: '尿 Cr 浓度', before: 20, after: 10 },
      { label: '肺功能风险', before: 15, after: 6 },
      { label: '皮肤病变风险', before: 12, after: 5 },
      { label: '综合健康风险', before: 18.6, after: 8 }
    ]
  }
])

const currentPersons = computed(() => selectedLevel.value === 'level2' ? highRiskPersons.value : mediumRiskPersons.value)
const selectedPerson = computed(() => {
  const id = selectedLevel.value === 'level2' ? activePerson.value : activeMediumPerson.value
  return currentPersons.value.find(person => person.id === id) || currentPersons.value[0]
})
const selectPerson = (id) => {
  if (selectedLevel.value === 'level2') activePerson.value = id
  else activeMediumPerson.value = id
}
watch(() => route.query.person, (value) => {
  const id = typeof value === 'string' ? value : ''
  if (highRiskPersons.value.some(person => person.id === id)) {
    selectedLevel.value = 'level2'
    activePerson.value = id
  } else if (mediumRiskPersons.value.some(person => person.id === id)) {
    selectedLevel.value = 'level1'
    activeMediumPerson.value = id
  }
}, { immediate: true })
const goToReport = () => router.push({ path: '/plan/specplan', query: { person: selectedPerson.value.id } })
</script>

<style scoped>
* { box-sizing: border-box; }
.system-layout { display: flex; height: 100vh; overflow: hidden; background: #f6f9fc; color: #22364b; }
.main-content { flex: 1; min-width: 0; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; }
.ep-header { position: sticky; top: 0; z-index: 30; flex-shrink: 0; background: #fff; border-bottom: 1px solid #e5edf4; }
.nav-wrapper { min-height: 64px; padding: 16px 32px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.nav-left { display: flex; align-items: center; gap: 18px; min-width: 0; }
.back-link { display: inline-flex; align-items: center; gap: 8px; color: #647c92; font-size: 13px; text-decoration: none; }
.back-link:hover { color: #287cb9; }
.divider { width: 1px; height: 16px; background: #dfe8f0; }
.page-title-top { font-size: 15px; font-weight: 700; }
.header-caption { color: #8a9caf; font-size: 12px; }
.page-container { flex: 1 0 auto; width: 100%; max-width: 1400px; margin: 0 auto; padding: 30px 36px 48px; min-width: 0; box-sizing: border-box; }
.plan-heading { margin-top: 0; display: flex; justify-content: space-between; gap: 24px; align-items: center; }
.eyebrow { font-size: 10px; letter-spacing: 1.4px; color: #5791ba; font-weight: 700; }
.plan-heading h1 { margin: 10px 0 9px; font-size: clamp(21px, 1.9vw, 28px); font-weight: 700; letter-spacing: -.4px; line-height: 1.4; }
.plan-heading p { color: #74899c; font-size: 13px; margin: 0; line-height: 1.8; }
.heading-meta { display: flex; gap: 20px; flex-shrink: 0; color: #8799aa; font-size: 11px; }
.heading-meta span { display: flex; flex-direction: column; gap: 5px; }
.heading-meta strong { font-size: 24px; color: #4a779a; font-weight: 600; }
.demo-notice { display: flex; align-items: flex-start; gap: 8px; color: #6d8598; background: #edf5fb; border-radius: 8px; padding: 11px 14px; margin: 22px 0 26px; font-size: 12px; line-height: 1.7; }
.demo-notice .el-icon { flex-shrink: 0; margin-top: 4px; color: #5e9ac5; }
.section-heading { display: flex; justify-content: space-between; gap: 16px; align-items: baseline; margin-bottom: 12px; }
.section-heading h2, .case-heading h2 { font-size: 15px; margin: 0; font-weight: 700; }
.section-heading > span { font-size: 11px; color: #8b9aac; }
.scenario-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.scenario-option { display: flex; align-items: center; gap: 13px; text-align: left; width: 100%; padding: 19px; background: #fff; border: 1px solid #e2eaf2; border-radius: 12px; cursor: pointer; color: inherit; font-family: inherit; transition: border-color .15s, background .15s; min-width: 0; }
.scenario-option:hover { border-color: #a7c9e2; }
.scenario-option.selected { border-color: #73b0da; background: #f3f9fd; box-shadow: 0 0 0 1px #c5e0f2; }
.scenario-icon { display: grid; place-items: center; flex-shrink: 0; width: 42px; height: 42px; border-radius: 11px; background: #edf4fa; color: #5c98c2; font-size: 21px; }
.scenario-option.selected .scenario-icon { background: #dfedf8; color: #287fba; }
.scenario-copy { display: flex; flex: 1; min-width: 0; flex-direction: column; gap: 6px; }
.scenario-copy strong { font-size: 15px; }
.scenario-copy > span { color: #7f92a4; font-size: 11px; line-height: 1.6; }
.scenario-count { color: #6e8ba3; font-size: 11px; white-space: nowrap; }
.selected-mark { color: #2884bf; flex-shrink: 0; }
.plan-workspace { display: grid; grid-template-columns: 210px minmax(0, 1fr); align-items: start; gap: 22px; margin-top: 26px; }
.case-panel { background: #fff; border: 1px solid #e3ebf2; border-radius: 12px; padding: 16px 10px; position: sticky; top: 20px; }
.case-heading { display: flex; justify-content: space-between; align-items: center; padding: 0 7px 15px; }
.case-heading > span { font-size: 11px; color: #97a8b7; }
.case-list { display: flex; flex-direction: column; gap: 7px; }
.case-option { display: flex; align-items: center; gap: 10px; padding: 12px 10px; min-height: 64px; border: 1px solid transparent; background: transparent; border-radius: 8px; text-align: left; cursor: pointer; font-family: inherit; color: #465e73; }
.case-option:hover { background: #f4f8fb; }
.case-option.selected { background: #edf6fc; border-color: #d1e6f5; color: #287eb8; }
.case-avatar { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 50%; font-size: 13px; font-weight: 600; color: #839ab0; background: #f0f4f8; flex-shrink: 0; }
.case-option.selected .case-avatar { color: #2b7db7; background: #dceefb; }
.case-copy { display: flex; flex: 1; flex-direction: column; gap: 5px; min-width: 0; }
.case-copy strong { font-size: 13px; }
.case-copy > span { font-size: 10px; color: #92a2b2; letter-spacing: .5px; }
.case-arrow { font-size: 12px; color: #a5bacb; }
.case-hint { font-size: 10px; color: #94a5b4; line-height: 1.8; margin: 16px 7px 0; padding-top: 12px; border-top: 1px solid #eef2f6; }
.plan-detail { min-width: 0; }
.person-summary { padding: 22px 24px; background: linear-gradient(110deg, #fff, #f5fafd); border: 1px solid #e0ebf3; border-radius: 12px; }
.person-summary-top { display: flex; align-items: center; justify-content: space-between; gap: 18px; }
.detail-kicker { color: #7099b9; font-size: 11px; }
.person-summary h2 { font-size: 23px; font-weight: 700; margin: 8px 0 0; line-height: 1.4; }
.person-summary h2 > span { color: #8ba0b2; font-size: 12px; font-weight: 500; margin-left: 9px; }
.person-summary :deep(.el-button) { border-radius: 8px; min-height: 38px; flex-shrink: 0; }
.person-meta { display: flex; flex-wrap: wrap; gap: 8px 14px; font-size: 11px; color: #7a90a3; margin-top: 18px; padding-top: 14px; border-top: 1px solid #e7eff5; line-height: 1.6; }
.person-meta .example-score { color: #8796a5; }
.workflow-heading { margin-top: 26px; }
.workflow-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; align-items: start; }
.workflow-card { border: 1px solid #e1eaf2; border-radius: 12px; padding: 20px; background: #fff; min-width: 0; }
.workflow-card-header { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.step-index { width: 30px; height: 30px; display: grid; place-items: center; border-radius: 8px; background: #eef5fb; color: #4b91c0; font-size: 12px; font-weight: 700; }
.step-tag { color: #7f9aaf; font-size: 10px; background: #f3f7fa; border-radius: 4px; padding: 4px 7px; }
.workflow-card h3 { margin: 15px 0 9px; font-size: 14px; color: #2e485e; line-height: 1.6; font-weight: 700; }
.step-description { font-size: 12px; color: #74899b; line-height: 1.9; margin: 0; }
.step-meta { display: flex; flex-wrap: wrap; gap: 8px 12px; font-size: 10px; color: #8a9dac; margin-top: 14px; line-height: 1.6; }
.step-meta > span { display: inline-flex; align-items: center; gap: 5px; }
.step-more { border-top: 1px solid #edf2f6; margin-top: 15px; padding-top: 12px; }
.step-more summary { display: flex; align-items: center; justify-content: space-between; cursor: pointer; font-size: 11px; color: #5d94ba; list-style: none; min-height: 24px; }
summary::-webkit-details-marker { display: none; }
.step-more[open] summary > span { transform: rotate(45deg); }
.step-extra { padding: 11px 12px; margin-top: 10px; border-radius: 7px; background: #f7fafc; }
.step-extra strong { font-size: 10px; color: #7890a4; font-weight: 600; }
.step-extra p { font-size: 11px; line-height: 1.9; color: #687f93; margin: 5px 0 0; overflow-wrap: anywhere; }
.outcomes-panel { border: 1px solid #e1eaf2; border-radius: 12px; background: #fff; margin-top: 20px; }
.outcomes-panel > summary { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 18px 20px; cursor: pointer; list-style: none; }
.outcomes-panel summary > span:first-child { display: inline-flex; align-items: center; gap: 9px; color: #496a83; font-size: 13px; font-weight: 600; }
.outcomes-toggle { font-size: 11px; color: #8da4b6; }
.outcomes-panel[open] .outcomes-toggle { display: none; }
.outcomes-body { padding: 0 20px 20px; }
.outcomes-body > p { margin: 0 0 18px; font-size: 11px; color: #8da0b0; line-height: 1.8; }
.outcome-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 20px 24px; }
.outcome-item h3 { margin: 0 0 10px; font-size: 12px; color: #607c92; font-weight: 600; }
.outcome-row { display: flex; align-items: center; gap: 9px; font-size: 10px; color: #92a1b0; margin-top: 7px; }
.outcome-row > span { flex-shrink: 0; }
.outcome-row > strong { width: 30px; text-align: right; font-weight: 500; }
.outcome-track { flex: 1; height: 7px; background: #edf3f7; border-radius: 4px; overflow: hidden; }
.outcome-track i { display: block; height: 100%; background: #b4cedf; border-radius: inherit; }
.after .outcome-track i { background: #6aa9d1; }
.detail-footer { display: flex; justify-content: space-between; align-items: center; gap: 15px; padding: 20px 2px 0; font-size: 11px; color: #90a1b0; line-height: 1.7; }
.detail-footer button { display: flex; align-items: center; gap: 7px; padding: 8px 0; border: 0; background: none; color: #4e95c3; cursor: pointer; font-family: inherit; font-size: 12px; white-space: nowrap; }
button:focus-visible, a:focus-visible, summary:focus-visible { outline: 2px solid #438fc4; outline-offset: 4px; }
@media (max-width: 1280px) { .page-container { padding: 26px 24px 40px; } .heading-meta { display: none; } .plan-workspace { grid-template-columns: 180px minmax(0, 1fr); gap: 16px; } .scenario-option { padding: 15px; gap: 10px; } .scenario-count { display: none; } .workflow-card { padding: 17px; } }
@media (max-width: 900px) { .plan-workspace { grid-template-columns: 1fr; } .case-panel { position: static; padding: 14px; } .case-list { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); } .case-option { min-height: 58px; padding: 9px; } .case-hint { display: none; } }
@media (max-width: 600px) { .nav-wrapper { padding: 14px 16px; min-height: 58px; } .nav-left { gap: 12px; } .header-caption { display: none; } .page-container { padding: 20px 14px 32px; }  .plan-heading h1 { font-size: 21px; } .plan-heading p { font-size: 12px; } .demo-notice { margin: 18px 0 22px; font-size: 11px; padding: 10px 12px; } .section-heading { gap: 10px; } .section-heading > span { font-size: 10px; } .scenario-options { grid-template-columns: 1fr; gap: 10px; } .scenario-option { min-height: 80px; padding: 15px; } .scenario-count { display: inline; } .scenario-copy > span { font-size: 10px; } .case-list { grid-template-columns: repeat(2, minmax(0, 1fr)); } .person-summary { padding: 18px; } .person-summary-top { align-items: flex-start; flex-wrap: wrap; gap: 14px; } .person-summary-top :deep(.el-button) { min-height: 42px; } .person-summary h2 { font-size: 22px; } .person-meta { gap: 7px 12px; } .workflow-grid { grid-template-columns: 1fr; } .workflow-card { padding: 18px; } .workflow-card h3 { font-size: 15px; } .step-description { font-size: 12px; } .step-more summary { min-height: 36px; } .outcome-grid { grid-template-columns: 1fr; } .detail-footer { flex-direction: column; align-items: flex-start; gap: 5px; } .detail-footer button { min-height: 40px; } }
@media (prefers-reduced-motion: reduce) { .scenario-option { transition: none; } }
</style>
