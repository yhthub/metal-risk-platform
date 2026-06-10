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

          <!-- 二、AI 智能推荐算法依据 -->
          <div class="report-section">
            <h3 class="rs-title">二、AI 智能推荐算法依据</h3>

            <!-- 核心结论（置顶突出） -->
            <div class="recommendation-hero">
              <div class="rh-badge">核心推荐依据</div>
              <p class="rh-text">{{ person.recommendationSummary }}</p>
              <div class="rh-meta">
                <span>算法：G-computation + SHAP 特征归因</span>
                <span>对象：{{ person.id }} ({{ person.name }})</span>
                <span>风险增幅：{{ person.score }}%</span>
              </div>
            </div>

            <!-- 支撑论据：SHAP + 混杂因素 + 雷达图 -->
            <div class="evidence-grid">
              <div class="shap-analysis">
                <h4>SHAP 特征归因分解</h4>
                <div class="shap-bars">
                  <div class="shap-row" v-for="s in person.shapBreakdown" :key="s.factor">
                    <span class="shap-label">{{ s.factor }}</span>
                    <div class="shap-track">
                      <div class="shap-bar" :style="{ width: Math.abs(s.value) * 100 + '%', background: s.value > 0 ? '#EF4444' : '#10B981' }">
                        <span class="shap-val">{{ s.value > 0 ? '+' : '' }}{{ (s.value * 100).toFixed(0) }}%</span>
                      </div>
                    </div>
                    <span class="shap-desc">{{ s.desc }}</span>
                  </div>
                </div>
              </div>

              <div class="confounders-analysis">
                <h4>混杂因素校正</h4>
                <ul>
                  <li v-for="c in person.confounders" :key="c.factor">
                    <strong>{{ c.factor }}：</strong>{{ c.impact }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- 三、干预目标 -->
          <div class="report-section">
            <h3 class="rs-title">三、干预目标</h3>
            <div class="goals-grid">
              <div class="goal-item" v-for="o in person.outcomes" :key="o.label">
                <el-icon><CircleCheckFilled /></el-icon>
                将 {{ o.label }} 从当前 {{ o.before }}% 降低至 {{ o.after }}% 以下
              </div>
            </div>
          </div>

          <!-- 四、干预流程 -->
          <div class="report-section">
            <h3 class="rs-title">四、干预实施流程（共 {{ person.workflow.length }} 步）</h3>
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

          <!-- 五、预期成效 -->
          <div class="report-section">
            <h3 class="rs-title">五、预期干预成效评估</h3>
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
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ArrowLeft, CircleCheckFilled, Printer } from '@element-plus/icons-vue'

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
    ],
    shapBreakdown: [
      { factor: 'Pb (铅) 暴露', value: 0.38, desc: '最大正向贡献因子，驱动中枢神经系统退行性病变风险' },
      { factor: 'As (砷) 暴露', value: 0.22, desc: '协同增强 Pb 的神经毒性，同时增加肝损伤风险' },
      { factor: '暴露工龄 (18年)', value: 0.08, desc: '长期累积暴露显著提升体内蓄积剂量' },
      { factor: '吸烟 (20年, 15支/日)', value: 0.05, desc: '吸烟加重呼吸道金属粉尘吸收率约 15-20%' },
      { factor: '年龄 (52岁)', value: 0.03, desc: '年龄增长导致肾脏排泄功能自然衰退' },
      { factor: '高钙膳食', value: -0.04, desc: '膳食钙竞争性抑制铅的肠道吸收' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性工人血铅基线水平普遍高于女性约 10-15%，且更易出现神经行为异常。' },
      { factor: '吸烟：20年烟龄，每日 15 支', impact: 'SHAP 分析显示吸烟贡献了 5% 的额外敏感性。吸烟者呼吸道黏膜纤毛清除功能下降，重金属粉尘沉积率升高。本方案将戒烟干预纳入核心措施之一。' },
      { factor: '年龄：52 岁', impact: '50 岁以上工人肾小球滤率自然下降约 10%，重金属排泄能力减弱，需在驱铅治疗中严格监测肾功能。' }
    ],
    recommendationSummary: '本方案针对点：铅砷联合暴露下的中枢神经系统保护与戒烟干预。SHAP 分析显示，铅(Pb)贡献了 38% 的额外敏感性，砷(As)贡献了 22%，两者合计 60%——这意味着该个体的风险几乎完全由 Pb 和 As 的协同毒性驱动。更关键的是，20 年吸烟史（每日 15 支）额外贡献了 5% 的敏感性，吸烟导致的呼吸道黏膜纤毛损伤使铅粉尘沉积率升高 15-20%，形成"暴露-吸收"的正反馈。因此，本方案的核心策略是：①立即调离高危岗位切断暴露源；②EDTA 驱铅降低体内蓄积剂量；③GSH 抗氧化保护肝肾靶器官；④将戒烟干预作为独立措施纳入，打破吸烟对铅毒性的放大效应。'
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
    ],
    shapBreakdown: [
      { factor: 'Pb (铅) 暴露', value: 0.32, desc: '主要正向贡献因子，驱动神经退行性病变风险' },
      { factor: 'Cd (镉) 暴露', value: 0.25, desc: '镉对肾近曲小管具有不可逆毒性，生物半衰期 10-30 年' },
      { factor: '暴露工龄 (15年)', value: 0.07, desc: '长期低剂量累积暴露导致骨骼镉蓄积' },
      { factor: '饮酒 (经常)', value: 0.04, desc: '酒精加重肝脏代谢负担，降低金属解毒能力' },
      { factor: '性别：男性', value: 0.02, desc: '男性肾小管损伤风险略高于女性' },
      { factor: '高锌膳食', value: -0.03, desc: '锌与镉竞争肠黏膜转运蛋白，减少吸收' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性工人镉暴露后肾损伤发生率高于女性约 12%。' },
      { factor: '饮酒：经常饮酒', impact: 'SHAP 分析显示饮酒贡献了 4% 的额外敏感性。酒精与镉在肝脏代谢中存在竞争，长期饮酒会削弱机体对镉的解毒能力。本方案建议严格戒酒。' },
      { factor: '年龄：48 岁', impact: '接近 50 岁，肾脏排泄功能开始自然衰退，镉蓄积风险进一步升高。' }
    ],
    recommendationSummary: '本方案针对点：铅镉联合暴露下的肾脏不可逆损伤预防与戒酒干预。SHAP 分析显示，铅(Pb)贡献了 32% 的额外敏感性，镉(Cd)贡献了 25%，两者合计 57%。与其他高危对象不同，该个体面临的核心威胁是镉对肾近曲小管的不可逆损伤——镉在肾脏的生物半衰期长达 10-30 年，一旦损伤不可逆转。同时，经常饮酒的习惯额外贡献了 4% 的敏感性，酒精与镉在肝脏代谢中存在竞争，削弱了机体对镉的解毒能力。因此，本方案的核心策略是：①防护升级降低吸入量；②深度肾功能筛查（β2-微球蛋白、NAG 酶）捕获极早期损伤；③驱铅治疗同步保肾；④建立 3-5 年镉蓄积长期监测计划；⑤严格戒酒消除混杂因素。'
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
    ],
    shapBreakdown: [
      { factor: 'As (砷) 暴露', value: 0.30, desc: '最大正向贡献因子，驱动肝损伤与皮肤角化风险' },
      { factor: 'Ni (镍) 暴露', value: 0.18, desc: '镍协同增强砷的肝毒性，同时增加呼吸系统风险' },
      { factor: '暴露工龄 (14年)', value: 0.06, desc: '长期暴露导致砷在皮肤和肝脏中持续蓄积' },
      { factor: '吸烟 (10年, 10支/日)', value: 0.04, desc: '吸烟加重呼吸道粉尘沉积，放大肺部致癌风险' },
      { factor: '男性', value: 0.02, desc: '男性砷代谢效率略低于女性' },
      { factor: '维C补充', value: -0.03, desc: '维生素C促进砷的甲基化解毒代谢' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性砷的甲基化代谢效率低于女性，无机砷在体内停留时间更长。' },
      { factor: '吸烟：10年烟龄，每日 10 支', impact: 'SHAP 分析显示吸烟贡献了 4% 的额外敏感性。吸烟者肺癌风险与砷暴露存在乘法交互效应，联合风险远高于单独暴露。' },
      { factor: '工种：尾气处理组', impact: '尾气处理岗位的砷/镍粉尘浓度高于熔炼岗位约 20%，属于高暴露工种。' }
    ],
    recommendationSummary: '本方案针对点：砷镍联合暴露下的肝脏保护与皮肤癌前病变筛查。SHAP 分析显示，砷(As)贡献了 30% 的额外敏感性，镍(Ni)贡献了 18%，两者合计 48%。该个体的独特风险在于砷的双重靶器官毒性——肝脏（慢性肝损伤）和皮肤（掌跖角化、色素沉着、Bowen 病）。10 年吸烟史额外贡献了 4% 的敏感性，砷与吸烟存在乘法交互效应，联合致癌风险远高于单独暴露。因此，本方案的核心策略是：①岗位轮换缩短连续暴露时间；②保肝治疗（多烯磷脂酰胆碱 + GSH）；③皮肤科专项筛查排除癌前病变；④砷代谢物形态分析判断暴露来源；⑤建议戒烟以消除砷-吸烟的乘法交互效应。'
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
    ],
    shapBreakdown: [
      { factor: 'Pb (铅) 暴露', value: 0.28, desc: '主要正向贡献因子，驱动神经毒性与血液系统损伤' },
      { factor: 'Hg (汞) 暴露', value: 0.15, desc: '汞具有强神经毒性，与铅协同放大中枢损伤风险' },
      { factor: '暴露工龄 (12年)', value: 0.05, desc: '长期暴露导致铅在骨骼中深度蓄积' },
      { factor: '年龄 (45岁)', value: 0.02, desc: '中年阶段代谢能力开始下降' },
      { factor: '防护不足', value: 0.03, desc: '原矿粉碎区粉尘浓度高，原有防护等级不足' },
      { factor: '钙锌补充', value: -0.02, desc: '钙锌竞争性减少铅汞肠道吸收' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性铅暴露后神经行为异常发生率高于女性。' },
      { factor: '工种：原矿粉碎区', impact: '原矿粉碎岗位粉尘浓度是熔炼岗位的 1.5 倍，铅/汞吸入风险显著更高。SHAP 模型已将工种作为分层变量纳入。' },
      { factor: '防护现状：KN95 口罩', impact: 'KN95 对金属粉尘的过滤效率约 95%，升级至 P100（99.97%）可进一步降低吸入量约 10 倍。' }
    ],
    recommendationSummary: '本方案针对点：铅汞联合暴露下的神经毒性协同阻断与序贯排金属治疗。SHAP 分析显示，铅(Pb)贡献了 28% 的额外敏感性，汞(Hg)贡献了 15%，两者合计 43%。该个体的独特风险在于铅和汞均具有强神经毒性，存在协同放大效应——铅破坏血脑屏障通透性，汞直接攻击神经元，两者叠加可加速中枢神经退行性病变。原矿粉碎区的高粉尘浓度（防护不足贡献 3%）是重要的环境因素。因此，本方案的核心策略是：①防护装备全面升级至 P100 级别；②序贯治疗——先 EDTA 驱铅，间隔 1 周后 DMSA 排汞；③WHO-NCTB 神经行为核心测试评估中枢/周围神经功能；④建立 12-24 个月 Pb/Hg 联合长期随访档案。'
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
    ],
    shapBreakdown: [
      { factor: 'Cd (镉) 暴露', value: 0.22, desc: '最大正向贡献因子，驱动肾近曲小管损伤' },
      { factor: 'Cr (铬) 暴露', value: 0.12, desc: '六价铬具有肝毒性和致癌性，协同增加靶器官负担' },
      { factor: '暴露工龄 (11年)', value: 0.05, desc: '长期暴露导致镉在肾脏持续蓄积' },
      { factor: '年龄 (42岁)', value: 0.02, desc: '中年阶段代谢能力开始下降' },
      { factor: '高钙膳食', value: -0.03, desc: '钙与镉竞争吸收，降低肠道镉摄入' },
      { factor: '防护升级', value: -0.02, desc: 'KN95 口罩降低粉尘吸入率约 95%' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性镉暴露后肾损伤风险略高于女性。' },
      { factor: '工种：原矿粉碎区', impact: '粉碎岗位粉尘浓度较高，是镉/铬暴露的主要来源。' },
      { factor: '非吸烟者', impact: '不吸烟，无额外的呼吸道暴露叠加效应，SHAP 模型中吸烟贡献为 0。' }
    ],
    recommendationSummary: '本方案针对点：镉铬联合暴露下的肾小管早期损伤拦截与钙锌竞争性拮抗。SHAP 分析显示，镉(Cd)贡献了 22% 的额外敏感性，铬(Cr)贡献了 12%，两者合计 34%。该个体的独特风险在于镉和铬的肾脏协同毒性——镉直接损伤近曲小管上皮细胞（不可逆），六价铬通过氧化应激加重肾小管损伤。该个体不吸烟，无额外混杂因素叠加，风险纯粹由职业暴露驱动。因此，本方案的核心策略是：①岗位轮换缩短连续暴露时间；②基线检测建立个人暴露档案；③钙锌营养拮抗——钙/锌与镉/铬共用肠黏膜转运蛋白，高水平钙锌可竞争性减少有害金属吸收；④季度 β2-微球蛋白和 NAG 酶监测捕获极早期肾损伤。'
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
    ],
    shapBreakdown: [
      { factor: 'Pb (铅) 暴露', value: 0.20, desc: '主要正向贡献因子，驱动血液系统与神经损伤' },
      { factor: 'As (砷) 暴露', value: 0.12, desc: '砷增加肝损伤与皮肤病变风险' },
      { factor: '暴露工龄 (9年)', value: 0.04, desc: '中等工龄，累积暴露量适中' },
      { factor: '年龄 (38岁)', value: 0.01, desc: '相对年轻，代谢排泄能力尚可' },
      { factor: '维C补充', value: -0.02, desc: '维生素C促进铅排泄并抗氧化' },
      { factor: '防护升级', value: -0.02, desc: '工位排风降低粉尘吸入浓度' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性铅暴露后血液系统异常发生率略高于女性。' },
      { factor: '非吸烟者', impact: '不吸烟，无额外呼吸道暴露叠加效应。' },
      { factor: '工种：第一熔炼车间', impact: '熔炼车间铅/砷粉尘浓度为全厂最高区域，是主要暴露来源。' }
    ],
    recommendationSummary: '本方案针对点：铅砷低水平联合暴露下的环境阻断与维生素C拮抗。SHAP 分析显示，铅(Pb)贡献了 20% 的额外敏感性，砷(As)贡献了 12%，两者合计 32%，风险水平中等。该个体不吸烟、不饮酒、年龄较轻（38 岁），混杂因素极少，风险几乎完全由职业暴露驱动——这意味着环境干预的效果预期最佳。因此，本方案的核心策略是：①工位加装局部排风罩从源头降低粉尘浓度；②基线检测确认当前内暴露水平；③维生素 C 1000mg/日——维C可将六价铬还原为三价铬，同时加速铅排泄并抗氧化；④个人卫生规范强化切断经口/经皮肤二次暴露途径；⑤季度血铅监测追踪趋势。'
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
    ],
    shapBreakdown: [
      { factor: 'As (砷) 暴露', value: 0.18, desc: '最大正向贡献因子，驱动肝损伤与皮肤角化风险' },
      { factor: 'Ni (镍) 暴露', value: 0.10, desc: '镍增加呼吸系统敏感性与皮肤过敏风险' },
      { factor: '暴露工龄 (8年)', value: 0.03, desc: '中等工龄，累积暴露量适中' },
      { factor: '吸烟 (5年, 8支/日)', value: 0.03, desc: '吸烟加重呼吸道粉尘沉积，放大砷的肺部致癌交互效应' },
      { factor: '防护升级', value: -0.02, desc: 'P100 滤盒降低粉尘吸入率' },
      { factor: '钙锌膳食', value: -0.02, desc: '钙锌竞争性减少砷镍肠道吸收' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性砷代谢效率低于女性，无机砷停留时间更长。' },
      { factor: '吸烟：5年烟龄，每日 8 支', impact: 'SHAP 分析显示吸烟贡献了 3% 的额外敏感性。虽然烟龄较短，但砷与吸烟的乘法交互效应已开始显现。建议尽早戒烟。' },
      { factor: '工种：尾气处理组', impact: '尾气处理岗位砷/镍浓度高于均值约 20%。' }
    ],
    recommendationSummary: '本方案针对点：砷镍联合暴露下的皮肤癌前病变早筛与戒烟窗口期干预。SHAP 分析显示，砷(As)贡献了 18% 的额外敏感性，镍(Ni)贡献了 10%，两者合计 28%。该个体的核心靶点是砷相关的皮肤角化和色素异常——慢性砷暴露可在 5-15 年后发展为 Bowen 病或皮肤鳞癌。5 年吸烟史额外贡献了 3% 的敏感性，虽然烟龄较短，但砷与吸烟的乘法交互效应正在积累，现在戒烟可以阻断这一进程。因此，本方案的核心策略是：①防护升级至 P100 级别；②砷代谢物形态分析判断暴露来源；③每 6 个月皮肤科专项检查排查癌前病变；④戒烟指导——当前处于砷-吸烟交互效应的早期窗口期，戒烟的边际收益最大。'
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
    ],
    shapBreakdown: [
      { factor: 'Pb (铅) 暴露', value: 0.18, desc: '唯一职业暴露因子，驱动血液系统与神经损伤' },
      { factor: '暴露工龄 (7年)', value: 0.04, desc: '中等工龄，累积暴露量适中' },
      { factor: '年龄 (35岁)', value: 0.01, desc: '相对年轻，代谢排泄能力良好' },
      { factor: '防护升级', value: -0.02, desc: 'KN95 口罩降低粉尘吸入率' },
      { factor: '钙锌补充', value: -0.02, desc: '钙锌竞争性减少铅肠道吸收' },
      { factor: '个人卫生', value: -0.01, desc: '工后淋浴更衣切断二次暴露途径' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性铅暴露后血液系统异常发生率略高于女性。' },
      { factor: '非吸烟、非饮酒', impact: '无烟酒混杂因素，SHAP 模型中烟酒贡献均为 0。该个体的风险几乎完全由职业暴露驱动，干预效果预期最佳。' },
      { factor: '年龄：35 岁', impact: '相对年轻，肾脏排泄功能良好，铅的生物半衰期较短，干预后恢复预期较快。' }
    ],
    recommendationSummary: '本方案针对点：单一铅暴露下的标准防护与钙锌竞争性阻断。SHAP 分析显示，铅(Pb)贡献了 18% 的额外敏感性，是唯一的正向风险因子——无镉、砷、汞等其他金属的协同毒性。该个体无吸烟、饮酒等混杂因素，年龄较轻（35 岁），肾脏排泄功能良好，铅的生物半衰期较短，干预后恢复预期最快。这是全部 10 名预警对象中风险结构最简单的案例。因此，本方案的核心策略是：①标准防护（KN95 口罩）即可满足需求；②血铅基线检测确认当前水平；③钙锌竞争性营养补充——钙/锌与铅共用肠黏膜转运蛋白，每日钙片 600mg + 锌 15mg 可有效减少铅的肠道吸收；④季度血铅监测追踪趋势。'
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
    ],
    shapBreakdown: [
      { factor: 'Cd (镉) 暴露', value: 0.15, desc: '最大正向贡献因子，驱动肾近曲小管损伤' },
      { factor: 'Hg (汞) 暴露', value: 0.08, desc: '汞增加神经系统与肾脏的双重毒性负担' },
      { factor: '暴露工龄 (6年)', value: 0.02, desc: '工龄较短，累积蓄积量有限' },
      { factor: '年龄 (32岁)', value: 0.01, desc: '年轻，代谢排泄能力良好' },
      { factor: '高钙膳食', value: -0.02, desc: '钙与镉竞争吸收' },
      { factor: '防护升级', value: -0.01, desc: 'KN95 口罩降低粉尘吸入率' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性镉暴露后肾损伤风险略高于女性。' },
      { factor: '非吸烟者', impact: '不吸烟，无额外呼吸道暴露叠加效应。' },
      { factor: '工种：原矿粉碎区', impact: '粉碎区镉/汞粉尘浓度较高，但工龄仅 6 年，累积风险有限。' }
    ],
    recommendationSummary: '本方案针对点：镉汞联合暴露下的早期肾功能保护与高钙膳食拮抗。SHAP 分析显示，镉(Cd)贡献了 15% 的额外敏感性，汞(Hg)贡献了 8%，两者合计 23%。该个体的独特优势在于工龄最短（6 年）且年龄最轻（32 岁）——这意味着体内蓄积量有限，肾脏尚未出现实质性损伤，是"窗口期"干预的最佳时机。镉和汞均以肾脏为主要靶器官，但早期干预可以阻止蓄积量达到损伤阈值。因此，本方案的核心策略是：①防护配发降低吸入量；②Cd/Hg 基线检测确认当前蓄积水平；③高钙膳食方案——每日牛奶 500ml + 钙片，钙与镉/汞竞争肠道吸收；④肾功能定期监测（β2-微球蛋白）捕获极早期变化；⑤个人卫生强化防止粉尘带入家庭环境。'
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
    ],
    shapBreakdown: [
      { factor: 'Cr (铬) 暴露', value: 0.14, desc: '唯一职业暴露因子，驱动肺功能损伤与皮肤溃疡风险' },
      { factor: '暴露工龄 (5年)', value: 0.02, desc: '工龄最短，累积蓄积量最低' },
      { factor: '年龄 (29岁)', value: 0.01, desc: '最年轻，代谢排泄能力最强' },
      { factor: '维C补充', value: -0.02, desc: '维生素C将六价铬还原为低毒三价铬' },
      { factor: '防护升级', value: -0.01, desc: 'KN95 口罩降低铬粉尘吸入率' },
      { factor: '通风改善', value: -0.01, desc: '局部排风降低工位铬浓度' }
    ],
    confounders: [
      { factor: '性别：男性', impact: '男性铬暴露后肺功能下降速率略高于女性。' },
      { factor: '非吸烟者', impact: '不吸烟，无额外呼吸道暴露叠加效应。铬粉尘主要经呼吸道吸入，不吸烟者的肺部清除能力显著优于吸烟者。' },
      { factor: '工种：尾气处理组', impact: '尾气处理岗位铬粉尘浓度较高，但工龄仅 5 年，累积风险最低。' }
    ],
    recommendationSummary: '本方案针对点：单一铬暴露下的维生素C还原解毒与呼吸道防护。SHAP 分析显示，铬(Cr)贡献了 14% 的额外敏感性，是唯一的正向风险因子。该个体是全部 10 名预警对象中风险最低的——工龄最短（5 年）、年龄最轻（29 岁）、不吸烟，体内蓄积量极其有限。铬的独特毒性在于六价铬（Cr⁶⁺）的强氧化性和致癌性，但维生素 C 可以将六价铬还原为低毒的三价铬（Cr³⁺），这是本方案营养干预的核心机制。因此，本方案的核心策略是：①工位通风改善降低铬粉尘浓度；②基线检测（尿 Cr + 肺功能）确认当前水平；③维生素 C 1000mg/日作为铬中毒的关键拮抗剂；④KN95 口罩强化呼吸防护（铬主要经呼吸道吸入）；⑤季度体检监测。成本效益最优。'
  }
}

const personId = route.query.person || 'SZ-284'
const person = computed(() => allPersons[personId] || allPersons['SZ-284'])

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

/* 推荐依据模块 */
.recommendation-hero { background: #ECFDF5; color: #064E3B; border: 1px solid #A7F3D0; border-radius: 10px; padding: 24px 28px; margin-bottom: 24px;
  .rh-badge { display: inline-block; background: #D1FAE5; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: 700; margin-bottom: 12px; letter-spacing: 1px; color: #047857; }
  .rh-text { font-size: 15px; line-height: 1.8; margin: 0 0 16px 0; color: #064E3B; }
  .rh-meta { display: flex; gap: 20px; font-size: 12px; color: #047857; border-top: 1px solid #A7F3D0; padding-top: 12px; }
}

.evidence-grid { display: flex; flex-direction: column; gap: 20px; }

.shap-analysis { margin: 16px 0; background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px 20px;
  h4 { margin: 0 0 12px 0; font-size: 14px; font-weight: 800; color: $text-main; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; }
}
.shap-bars { display: flex; flex-direction: column; gap: 8px; }
.shap-row { display: flex; align-items: center; gap: 8px;
  .shap-label { width: 140px; font-size: 12px; font-weight: 700; color: $text-main; flex-shrink: 0; text-align: right; }
  .shap-track { flex: 1; height: 18px; background: #F1F5F9; border-radius: 3px; overflow: hidden; position: relative; }
  .shap-bar { height: 100%; border-radius: 3px; display: flex; align-items: center; justify-content: flex-end; padding: 0 6px; min-width: 40px; transition: width 0.6s ease; }
  .shap-val { font-size: 11px; font-weight: 700; color: #fff; white-space: nowrap; }
  .shap-desc { flex: 2; font-size: 11px; color: #64748B; line-height: 1.3; }
}

.confounders-analysis { margin: 16px 0; background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 16px 20px;
  h4 { margin: 0 0 10px 0; font-size: 14px; font-weight: 800; color: #92400E; }
  ul { margin: 0; padding-left: 20px; li { font-size: 13px; color: #78350F; line-height: 1.6; margin-bottom: 6px; strong { color: #92400E; } } }
}

.recommendation-summary { margin: 16px 0; background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 8px; padding: 16px 20px;
  h4 { margin: 0 0 10px 0; font-size: 14px; font-weight: 800; color: #065F46; }
  p { margin: 0; font-size: 13px; color: #064E3B; line-height: 1.7; }
}

.report-footer { margin-top: 80px; display: flex; justify-content: space-between; align-items: flex-end; .sign { font-family: 'Brush Script MT', cursive; font-size: 24px; margin-left: 10px; text-decoration: underline; color: #1e293b; } .sign-system { font-weight: 700; color: #94a3b8; } }

@media print { .sidebar, .ep-header, .report-btns { display: none !important; } .main-content { height: auto; overflow: visible; } .report-paper { box-shadow: none; padding: 40px; } }
</style>
