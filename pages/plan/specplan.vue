<template>
  <div class="system-layout">
   <Sidebar default-active="5" />

    <main class="main-content">
      <header class="ep-header">
        <div class="nav-wrapper">
          <div class="back-link" @click="goBack">
            <el-icon class="back-icon"><ArrowLeft /></el-icon>
            <span class="back-text">返回干预方案</span>
            <span class="divider">|</span>
            <span class="page-title-top">个人化干预方案报告</span>
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
                <h1>{{ person.id }} · {{ person.name }} 个人化干预方案</h1>
                <p>预防级别：{{ person.level === 'level2' ? '二级预防（早期筛查与临床干预）' : '一级预防（健康教育与环境阻断）' }} | 生成时间：2026-05-12 15:40</p>
              </div>
            </div>
            <div class="rh-right">
              <div class="risk-seal" :class="person.level === 'level2' ? 'seal-danger' : 'seal-warn'">
                <span>{{ person.level === 'level2' ? '高危' : '中危' }}</span>
                <strong>{{ person.score }}%</strong>
              </div>
            </div>
          </div>

          <el-divider />

          <!-- 一、干预对象信息 -->
          <div class="report-section">
            <h3 class="rs-title">一、干预对象基本信息</h3>
            <el-descriptions :column="2" border class="custom-descriptions">
              <el-descriptions-item label="工号">{{ person.id }}</el-descriptions-item>
              <el-descriptions-item label="姓名">{{ person.name }}</el-descriptions-item>
              <el-descriptions-item label="所属部门">{{ person.dept }}</el-descriptions-item>
              <el-descriptions-item label="暴露工龄">{{ person.years }} 年</el-descriptions-item>
              <el-descriptions-item label="风险驱动因子">
                <el-tag size="small" :type="person.level === 'level2' ? 'danger' : 'warning'" effect="dark" round>{{ person.factors }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="因果风险增幅">
                <el-tag size="small" :type="person.level === 'level2' ? 'danger' : 'warning'" effect="dark" round>{{ person.score }}%</el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </div>

          <!-- 二、干预目标 -->
          <div class="report-section">
            <h3 class="rs-title">二、干预目标</h3>
            <div class="goals-grid">
              <div class="goal-item" v-for="o in person.outcomes" :key="o.label">
                <el-icon><CircleCheckFilled /></el-icon>
                将 {{ o.label }} 从当前 {{ o.before }}% 降低至 {{ o.after }}% 以下
              </div>
            </div>
          </div>

          <!-- 三、干预流程 -->
          <div class="report-section">
            <h3 class="rs-title">三、干预实施流程（共 {{ person.workflow.length }} 步）</h3>
            <div class="workflow-report">
              <div class="wr-step" v-for="(step, idx) in person.workflow" :key="idx">
                <div class="wr-header">
                  <div class="wr-num" :class="step.type">步骤 {{ idx + 1 }}</div>
                  <div class="wr-title">
                    <h4>{{ step.title }}</h4>
                    <el-tag size="small" :type="getTagType(step.type)" effect="light">{{ step.tag }}</el-tag>
                  </div>
                </div>
                <div class="wr-body">
                  <p class="wr-desc">{{ step.desc }}</p>
                  <div class="wr-detail" v-if="step.detail">
                    <strong>具体操作：</strong>{{ step.detail }}
                  </div>
                  <div class="wr-indicator" v-if="step.indicator">
                    <strong>关键指标：</strong>{{ step.indicator }}
                  </div>
                  <div class="wr-meta">
                    <el-tag size="small" type="info" effect="light">⏱ {{ step.period }}</el-tag>
                    <el-tag size="small" effect="light" v-if="step.cost">费用: {{ step.cost }}</el-tag>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 四、预期成效 -->
          <div class="report-section highlight">
            <h3 class="rs-title">四、预期干预成效评估</h3>
            <div class="outcome-report">
              <div class="or-item" v-for="o in person.outcomes" :key="o.label">
                <span class="or-label">{{ o.label }}</span>
                <div class="or-bar-wrap">
                  <div class="or-bar before" :style="{ width: o.before + '%' }"><span>{{ o.before }}%</span></div>
                  <span class="or-arrow">→</span>
                  <div class="or-bar after" :style="{ width: o.after + '%' }"><span>{{ o.after }}%</span></div>
                </div>
                <span class="or-delta">-{{ (o.before - o.after).toFixed(0) }}%</span>
              </div>
            </div>
          </div>

          <!-- 五、AI 推荐依据 -->
          <div class="report-section">
            <h3 class="rs-title">五、AI 智能推荐算法依据</h3>
            <div class="recom-content">
              <div class="rc-text">
                本方案基于 <strong>G-computation 边缘因果效应</strong> 与 <strong>SHAP 特征归因</strong> 算法生成。
                系统识别 {{ person.id }} 当前的主要风险因子为 <strong>{{ person.factors }}</strong>，
                因果风险增幅达 <strong>{{ person.score }}%</strong>，
                属于{{ person.level === 'level2' ? '高危易感人群，需立即启动二级预防措施（进一步检查 + 临床干预）' : '中危预警人群，以一级预防措施为主（健康教育 + 环境阻断）' }}。
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
              <el-button type="info" size="large" plain @click="goBack">返回方案列表</el-button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, CircleCheckFilled, Printer } from '@element-plus/icons-vue'
import * as echarts from 'echarts'

const router = useRouter()
const route = useRoute()

const goBack = () => { router.back() }
const handlePrint = () => { setTimeout(() => { window.print() }, 500) }

const getTagType = (type) => {
  if (type === 'danger') return 'danger'
  if (type === 'warning') return 'warning'
  if (type === 'primary') return 'primary'
  return 'success'
}

// 完整的人员数据（与 plan/index.vue 同步）
const allPersons = {
  'SZ-284': { id: 'SZ-284', name: '张建国', dept: '第一熔炼车间', years: 18, factors: 'Pb, As', score: 68.5, level: 'level2',
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
  'SZ-105': { id: 'SZ-105', name: '刘伟', dept: '第一熔炼车间', years: 15, factors: 'Pb, Cd', score: 62.1, level: 'level2',
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
  'SZ-032': { id: 'SZ-032', name: '王强', dept: '第一熔炼车间', years: 14, factors: 'As, Ni', score: 55.4, level: 'level2',
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
  'SZ-142': { id: 'SZ-142', name: '李明', dept: '原矿粉碎区', years: 12, factors: 'Pb, Hg', score: 48.2, level: 'level2',
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
  },
  'SZ-089': { id: 'SZ-089', name: '赵铁柱', dept: '原矿粉碎区', years: 11, factors: 'Cd, Cr', score: 41.5, level: 'level1',
    workflow: [
      { title: '岗位轮换与暴露时间管控', tag: '暴露阻断', type: 'warning', desc: '实施轮岗制度，将高暴露岗位连续作业时间缩短至 4 小时以内。', detail: '与低暴露岗位（质检、仓库）轮换，每 2 周轮换一次。工间在通风良好区域休息 30 分钟以上。', indicator: '1 个月后复查尿 Cd，预期下降 10-15%', period: '长期执行', cost: '低' },
      { title: 'Cd/Cr 暴露基线评估', tag: '健康筛查', type: 'primary', desc: '检测尿镉、尿铬及肾功能早期标志物，建立个人暴露基线。', detail: '尿 Cd、尿 Cr、尿 β2-微球蛋白、尿 NAG 酶、血常规、肝肾功能、尿常规。', indicator: '尿 Cd > 3 μg/g Cr 或 β2-微球蛋白 > 200 μg/L 需升级管理', period: '3-5 个工作日', cost: '低' },
      { title: '标准防护装备配发', tag: '个人防护', type: 'warning', desc: '配发 KN95 口罩、防护手套、护目镜，培训正确佩戴方法。', detail: '由安全员现场指导佩戴，确保面部密合。每周检查口罩使用状况，每月更换滤芯。', indicator: '防护依从率 > 90%', period: '即刻执行', cost: '低' },
      { title: '钙锌营养拮抗方案', tag: '营养干预', type: 'safe', desc: '每日服用钙锌补充剂，食堂增设高钙高锌菜品。', detail: '钙片 600mg + 锌 15mg/日。食堂每日供应牛奶、豆腐、虾皮。果胶膳食纤维辅助排毒。', indicator: '3 个月后复查尿 Cd，结合轮岗效果综合评估', period: '长期维持', cost: '极低' },
      { title: '季度常规体检', tag: '定期监测', type: 'primary', desc: '每 3 个月复查尿 Cd、尿 Cr 及肾功能指标。', detail: '检查项目：尿 Cd、尿 Cr、尿 β2-微球蛋白、肝肾功能。连续 2 次异常者升级为高危管理。', indicator: '连续 4 个季度指标稳定或下降为达标', period: '每 3 个月', cost: '低' },
      { title: '职业卫生知识培训', tag: '健康教育', type: 'safe', desc: '参加职业危害防护培训，掌握个人卫生规范与防护要点。', detail: '每半年复训一次，新入职人员必须岗前培训合格方可上岗。', indicator: '培训考核通过率 100%', period: '每半年一次', cost: '极低' }
    ],
    outcomes: [
      { label: '尿 Cd 浓度', before: 42, after: 28 },
      { label: '尿 Cr 浓度', before: 35, after: 22 },
      { label: '肾损伤风险', before: 30, after: 18 },
      { label: '综合健康风险', before: 41.5, after: 25 }
    ]
  },
  'SZ-311': { id: 'SZ-311', name: '陈刚', dept: '第一熔炼车间', years: 9, factors: 'Pb, As', score: 36.8, level: 'level1',
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
  'SZ-402': { id: 'SZ-402', name: '孙磊', dept: '尾气处理组', years: 8, factors: 'As, Ni', score: 32.1, level: 'level1',
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
  'SZ-175': { id: 'SZ-175', name: '周波', dept: '第一熔炼车间', years: 7, factors: 'Pb', score: 28.5, level: 'level1',
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
  'SZ-219': { id: 'SZ-219', name: '吴涛', dept: '原矿粉碎区', years: 6, factors: 'Cd, Hg', score: 24.2, level: 'level1',
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
  'SZ-056': { id: 'SZ-056', name: '郑凯', dept: '尾气处理组', years: 5, factors: 'Cr', score: 18.6, level: 'level1',
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
}

const personId = route.query.person || 'SZ-284'
const person = computed(() => allPersons[personId] || allPersons['SZ-284'])

const recomChartRef = ref(null)
let recomChartInstance = null

const initRecommendationChart = () => {
  if (!recomChartRef.value) return
  recomChartInstance = echarts.init(recomChartRef.value)
  recomChartInstance.setOption({
    radar: {
      indicator: [
        { name: '阻断效能', max: 100 }, { name: '临床可行性', max: 100 }, { name: '成本可控', max: 100 },
        { name: '实施便捷度', max: 100 }, { name: '长期依从性', max: 100 }
      ],
      shape: 'circle',
      axisName: { color: '#475569', fontWeight: 'bold' }
    },
    series: [{
      type: 'radar',
      data: [{
        value: person.value.level === 'level2'
          ? [88, 92, 65, 70, 80]
          : [72, 95, 90, 88, 85],
        areaStyle: { color: person.value.level === 'level2' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(217, 119, 6, 0.2)' },
        lineStyle: { color: person.value.level === 'level2' ? '#EF4444' : '#D97706' },
        itemStyle: { color: person.value.level === 'level2' ? '#EF4444' : '#D97706' }
      }]
    }]
  })
}

const resizeChart = () => { if (recomChartInstance) recomChartInstance.resize() }
onMounted(() => { nextTick(() => { initRecommendationChart() }); window.addEventListener('resize', resizeChart) })
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); if (recomChartInstance) recomChartInstance.dispose() })
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

.main-content { flex: 1; display: flex; flex-direction: column; height: 100vh; overflow-y: auto; scroll-behavior: smooth; }
.ep-header { height: 60px; background: #fff; border-bottom: 1px solid $border-color; position: sticky; top: 0; z-index: 50; display: flex; justify-content: center; flex-shrink: 0; }
.nav-wrapper { width: 100%; padding: 0 40px; display: flex; justify-content: space-between; align-items: center; }
.back-link { display: flex; align-items: center; gap: 12px; cursor: pointer; color: $text-main; &:hover { color: $color-primary; } .back-text { font-size: 1.05rem; font-weight: 600; } .divider { color: #D1D5DB; margin: 0 4px; } .page-title-top { font-size: 1.1rem; font-weight: 800; } }
.user-profile { display: flex; align-items: center; gap: 12px; font-weight: 500; font-size: 0.95rem; .avatar { width: 32px; height: 32px; border-radius: 50%; background: #EFF6FF; color: $color-primary; display: flex; justify-content: center; align-items: center; font-weight: 700; } }

.report-view-wrapper { flex: 1 0 auto; background: #E2E8F0; padding: 40px 0; display: flex; justify-content: center; align-items: flex-start; }
.report-paper { background: #fff; width: 1000px; height: max-content; padding: 80px; position: relative; box-shadow: 0 20px 50px rgba(0,0,0,0.1); border-radius: 2px; }
.report-watermark { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-35deg); font-size: 80px; color: rgba(0,0,0,0.03); font-weight: 900; pointer-events: none; white-space: nowrap; }

.report-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;
  .rh-left { display: flex; align-items: center; gap: 12px; }
  .report-logo-custom { width: 32px; height: 32px; color: $color-primary; margin-bottom: 4px; }
  h1 { font-size: 24px; color: $text-main; margin: 0 0 10px 0; font-weight: 800; letter-spacing: -1px; } p { font-size: 13px; color: $text-muted; margin: 0; }
  .risk-seal { border: 3px solid; width: 100px; height: 100px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; transform: rotate(15deg);
    &.seal-danger { border-color: $color-danger; span { font-size: 12px; color: $color-danger; } strong { font-size: 22px; color: $color-danger; } }
    &.seal-warn { border-color: $color-warn; span { font-size: 12px; color: $color-warn; } strong { font-size: 22px; color: $color-warn; } }
  }
}

.report-section { margin-top: 40px; .rs-title { font-size: 18px; font-weight: 800; color: $text-main; border-bottom: 2px solid $text-main; padding-bottom: 8px; margin-bottom: 20px; } &.highlight { background: #F1F5F9; padding: 30px; border-radius: 8px; } }

.goals-grid { display: grid; grid-template-columns: 1fr; gap: 12px; .goal-item { display: flex; align-items: center; gap: 10px; font-size: 15px; color: #334155; font-weight: 500; .el-icon { color: #10B981; font-size: 18px; } } }

/* 干预流程样式 */
.workflow-report { display: flex; flex-direction: column; gap: 16px; }
.wr-step { border: 1px solid $border-color; border-radius: 8px; padding: 20px; &:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); } }
.wr-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
.wr-num { width: 72px; height: 32px; border-radius: 6px; display: flex; justify-content: center; align-items: center; font-weight: 800; font-size: 0.8rem; flex-shrink: 0;
  &.danger { background: #FEF2F2; color: #EF4444; border: 1px solid #FECACA; }
  &.primary { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
  &.warning { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
  &.safe { background: #ECFDF5; color: #059669; border: 1px solid #A7F3D0; }
}
.wr-title { flex: 1; display: flex; align-items: center; gap: 10px; h4 { margin: 0; font-size: 1rem; font-weight: 700; color: $text-main; } }
.wr-body { padding-left: 86px;
  .wr-desc { margin: 0 0 10px 0; font-size: 0.9rem; color: #475569; line-height: 1.6; }
  .wr-detail, .wr-indicator { font-size: 0.85rem; color: #64748B; margin-bottom: 8px; line-height: 1.5; strong { color: $text-main; } }
  .wr-detail { padding: 10px 12px; background: #F8FAFC; border-radius: 6px; border: 1px solid #F1F5F9; }
  .wr-indicator { padding: 10px 12px; background: #FFFBEB; border-radius: 6px; border: 1px solid #FDE68A; strong { color: #92400E; } }
  .wr-meta { display: flex; gap: 8px; margin-top: 10px; }
}

/* 预期成效样式 */
.outcome-report { display: flex; flex-direction: column; gap: 14px; }
.or-item { display: flex; align-items: center; gap: 12px; .or-label { width: 120px; font-size: 0.85rem; font-weight: 700; color: $text-main; flex-shrink: 0; text-align: right; } .or-delta { font-size: 0.9rem; font-weight: 800; color: #10B981; width: 50px; } }
.or-bar-wrap { flex: 1; display: flex; align-items: center; gap: 8px; }
.or-bar { height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding: 0 8px; font-size: 0.75rem; font-weight: 700; color: #fff; min-width: 40px;
  &.before { background: #EF4444; }
  &.after { background: #10B981; }
}
.or-arrow { color: #9CA3AF; font-weight: 700; font-size: 0.9rem; }

.recom-content { display: flex; gap: 30px; align-items: center; .rc-text { flex: 1; font-size: 15px; color: #334155; line-height: 1.8; } .rc-chart { width: 300px; height: 300px; } }

.report-footer { margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end; .sign { font-family: 'Brush Script MT', cursive; font-size: 24px; margin-left: 10px; text-decoration: underline; color: #1e293b; } .sign-system { font-weight: 700; color: #94a3b8; } }

@media print { .sidebar, .ep-header, .report-btns { display: none !important; } .main-content { height: auto; overflow: visible; } .report-paper { box-shadow: none; padding: 40px; } }
</style>
