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
                <el-tag size="large" effect="plain" round class="custom-tag"><el-icon><Document /></el-icon> 第一熔炼车间_全体环境与生物监测表.csv</el-tag>
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
              <el-tag type="warning" effect="dark" round size="small"><el-icon><Warning /></el-icon> 已识别 10 名高危易感个体</el-tag>
            </div>
            <el-button link type="primary" class="detail-btn" @click="goToWorkspace">查看特征明细</el-button>
          </div>
        </div>

        <!-- 预警人群分级选择 -->
        <div class="warning-level-section">
          <div class="wls-header">
            <h3><el-icon><UserFilled /></el-icon> 预警人群分级与干预策略匹配</h3>
            <p class="wls-desc">系统已根据因果风险评估将预警对象分为两级，不同级别对应不同预防策略：</p>
          </div>
          <div class="wls-cards">
            <div class="wls-card" :class="{ active: selectedLevel === 'level2' }" @click="selectedLevel = 'level2'">
              <div class="wls-badge danger">二级预防</div>
              <div class="wls-info">
                <h4>高危易感人群 <span class="wls-count">4 人</span></h4>
                <p>因果风险增幅 > 45%，需早期筛查、进一步诊断与临床干预</p>
                <div class="wls-workers">SZ-284 · SZ-105 · SZ-032 · SZ-142</div>
              </div>
            </div>
            <div class="wls-card" :class="{ active: selectedLevel === 'level1' }" @click="selectedLevel = 'level1'">
              <div class="wls-badge warn">一级预防</div>
              <div class="wls-info">
                <h4>中危预警人群 <span class="wls-count">6 人</span></h4>
                <p>因果风险增幅 18%~45%，以健康教育、环境改善、营养干预为主</p>
                <div class="wls-workers">SZ-089 · SZ-311 · SZ-402 · SZ-175 · SZ-219 · SZ-056</div>
              </div>
            </div>
          </div>
        </div>

        <div class="action-card" v-if="!isGenerated">
          <div class="action-content">
            <div class="a-text">
              <h3>智能干预策略矩阵生成</h3>
              <p>系统将基于风险评估结果，为{{ selectedLevel === 'level2' ? '高危易感人群（二级预防：早期筛查 + 临床干预）' : '中危预警人群（一级预防：健康教育 + 环境改善）' }}生成针对性干预预案。</p>
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
              <li class="t-step active">锁定靶点：识别靶器官【中枢神经系统、肾脏】与致病因子【Pb, As, Cd】...</li>
              <li class="t-step" :class="{'active': genProgress >= 1}">匹配预防级别：{{ selectedLevel === 'level2' ? '高危人群 → 二级预防策略（早期筛查 + 临床干预）' : '中危人群 → 一级预防策略（健康教育 + 环境阻断）' }}...</li>
              <li class="t-step" :class="{'active': genProgress >= 2}">查询文献库：匹配《国家职业病防治指南》及《职业健康监护技术规范》...</li>
              <li class="t-step" :class="{'active': genProgress >= 3}">制定干预矩阵：生成针对性阻断方案，并分配实施权重...</li>
              <li class="t-step" :class="{'active': genProgress >= 4}">渲染就绪：多维阻断策略及预测对比图表已生成。</li>
            </ul>
          </div>
        </div>

        <div class="results-dashboard" v-if="isGenerated && !isGenerating">
          
          <div class="alert-conclusion-banner">
            <div class="a-icon"><el-icon><Check /></el-icon></div>
            <div class="a-content">
              <h4>干预策略池生成完毕：<span class="level-safe">【{{ selectedLevel === 'level2' ? '二级预防：高危人群早期筛查与临床干预' : '一级预防：中危人群健康教育与环境阻断' }}】</span></h4>
              <p>{{ selectedLevel === 'level2'
                ? '以下方案面向因果风险增幅 > 45% 的 4 名高危个体，重点在于进一步检查确认、早期临床干预和高频随访，防止疾病进展。'
                : '以下方案面向全体 10 名预警对象，重点在于健康教育、暴露源阻断和营养支持，防止疾病发生。' }}</p>
            </div>
          </div>

          <!-- 二级预防：高危人群个人化干预流程 -->
          <div v-if="selectedLevel === 'level2'">
            <div class="person-tabs">
              <div
                v-for="person in highRiskPersons"
                :key="person.id"
                class="person-tab"
                :class="{ active: activePerson === person.id }"
                @click="activePerson = person.id"
              >
                <span class="pt-id">{{ person.id }}</span>
                <span class="pt-score" :class="person.levelClass">{{ person.score }}%</span>
              </div>
            </div>

            <div v-for="person in highRiskPersons" :key="person.id" v-show="activePerson === person.id" class="person-workflow">
              <div class="pw-profile">
                <div class="pw-info">
                  <h3>{{ person.id }} · {{ person.name }}</h3>
                  <div class="pw-meta">
                    <el-tag size="small" effect="plain" round>{{ person.dept }}</el-tag>
                    <el-tag size="small" effect="plain" round>工龄 {{ person.years }} 年</el-tag>
                    <el-tag size="small" :type="person.levelClass === 'danger' ? 'danger' : 'warning'" effect="dark" round>风险因子: {{ person.factors }}</el-tag>
                    <el-tag size="small" type="danger" effect="dark" round>因果风险增幅 {{ person.score }}%</el-tag>
                  </div>
                </div>
              </div>

              <div class="workflow-steps">
                <div class="wf-step" v-for="(step, idx) in person.workflow" :key="idx">
                  <div class="wf-step-header">
                    <div class="wf-step-num" :class="step.type">{{ idx + 1 }}</div>
                    <div class="wf-step-title">
                      <h4>{{ step.title }}</h4>
                      <span class="wf-step-tag">{{ step.tag }}</span>
                    </div>
                  </div>
                  <div class="wf-step-body">
                    <p class="wf-desc">{{ step.desc }}</p>
                    <div class="wf-detail" v-if="step.detail">
                      <strong>具体操作：</strong>{{ step.detail }}
                    </div>
                    <div class="wf-indicator" v-if="step.indicator">
                      <strong>关键指标：</strong>{{ step.indicator }}
                    </div>
                    <div class="wf-timeline">
                      <el-tag size="small" type="info" effect="light">⏱ {{ step.period }}</el-tag>
                      <el-tag size="small" effect="light" v-if="step.cost">费用: {{ step.cost }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <div class="pw-outcome">
                <h4><el-icon><Check /></el-icon> 预期干预成效</h4>
                <div class="outcome-grid">
                  <div class="outcome-item" v-for="o in person.outcomes" :key="o.label">
                    <span class="o-label">{{ o.label }}</span>
                    <div class="o-bar-wrap">
                      <div class="o-bar-before" :style="{ width: o.before + '%' }"><span>{{ o.before }}%</span></div>
                      <div class="o-arrow">→</div>
                      <div class="o-bar-after" :style="{ width: o.after + '%' }"><span>{{ o.after }}%</span></div>
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>

          <!-- 一级预防：中危人群个人化干预流程 -->
          <div v-if="selectedLevel === 'level1'">
            <div class="person-tabs level1-tabs">
              <div
                v-for="person in mediumRiskPersons"
                :key="person.id"
                class="person-tab level1-tab"
                :class="{ active: activeMediumPerson === person.id }"
                @click="activeMediumPerson = person.id"
              >
                <span class="pt-id">{{ person.id }}</span>
                <span class="pt-score level1-score">{{ person.score }}%</span>
              </div>
            </div>

            <div v-for="person in mediumRiskPersons" :key="person.id" v-show="activeMediumPerson === person.id" class="person-workflow">
              <div class="pw-profile level1-profile">
                <div class="pw-info">
                  <h3>{{ person.id }} · {{ person.name }}</h3>
                  <div class="pw-meta">
                    <el-tag size="small" effect="plain" round>{{ person.dept }}</el-tag>
                    <el-tag size="small" effect="plain" round>工龄 {{ person.years }} 年</el-tag>
                    <el-tag size="small" type="warning" effect="dark" round>风险因子: {{ person.factors }}</el-tag>
                    <el-tag size="small" type="warning" effect="dark" round>因果风险增幅 {{ person.score }}%</el-tag>
                  </div>
                </div>
              </div>

              <div class="workflow-steps">
                <div class="wf-step" v-for="(step, idx) in person.workflow" :key="idx">
                  <div class="wf-step-header">
                    <div class="wf-step-num" :class="step.type">{{ idx + 1 }}</div>
                    <div class="wf-step-title">
                      <h4>{{ step.title }}</h4>
                      <span class="wf-step-tag">{{ step.tag }}</span>
                    </div>
                  </div>
                  <div class="wf-step-body">
                    <p class="wf-desc">{{ step.desc }}</p>
                    <div class="wf-detail" v-if="step.detail">
                      <strong>具体操作：</strong>{{ step.detail }}
                    </div>
                    <div class="wf-indicator" v-if="step.indicator">
                      <strong>关键指标：</strong>{{ step.indicator }}
                    </div>
                    <div class="wf-timeline">
                      <el-tag size="small" type="info" effect="light">⏱ {{ step.period }}</el-tag>
                      <el-tag size="small" effect="light" v-if="step.cost">费用: {{ step.cost }}</el-tag>
                    </div>
                  </div>
                </div>
              </div>

              <div class="pw-outcome level1-outcome">
                <h4><el-icon><Check /></el-icon> 预期干预成效</h4>
                <div class="outcome-grid">
                  <div class="outcome-item" v-for="o in person.outcomes" :key="o.label">
                    <span class="o-label">{{ o.label }}</span>
                    <div class="o-bar-wrap">
                      <div class="o-bar-before level1-before" :style="{ width: o.before + '%' }"><span>{{ o.before }}%</span></div>
                      <div class="o-arrow">→</div>
                      <div class="o-bar-after level1-after" :style="{ width: o.after + '%' }"><span>{{ o.after }}%</span></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
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
            <el-button type="success" size="large" plain class="mr-3" @click="goToPdfReport">
              导出当前选中人员干预报告
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowLeft, ArrowDown, ArrowRight, User, Clock, CircleCheck, Warning, Document, UserFilled, Check, Connection, Position, FirstAidKit } from '@element-plus/icons-vue'

const router = useRouter()
const isGenerating = ref(false)
const isGenerated = ref(false)
const isThinkingExpanded = ref(false)
const genProgress = ref(0)

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

const goToWorkspace = async () => {
  router.push('/datainput')
}

const goToPdfReport = async () => {
  const personId = selectedLevel.value === 'level2' ? activePerson.value : activeMediumPerson.value
  router.push({
    path: '/plan/specplan',
    query: { person: personId }
  })
}

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
    if (selectedLevel.value === 'level1') {
      activeMediumPerson.value = mediumRiskPersons.value[0].id
    } else {
      activePerson.value = highRiskPersons.value[0].id
    }
  }, 3500)
}

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

.warning-level-section { background: #fff; border-radius: 12px; border: 1px solid $border-color; padding: 24px 28px; margin-bottom: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.02);
  .wls-header { margin-bottom: 20px; h3 { margin: 0 0 8px 0; font-size: 1.15rem; font-weight: 800; color: $text-main; display: flex; align-items: center; gap: 8px; .el-icon { color: $color-primary; } } .wls-desc { margin: 0; font-size: 0.9rem; color: $text-muted; line-height: 1.5; } }
  .wls-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .wls-card { display: flex; gap: 16px; padding: 18px 20px; border: 2px solid $border-color; border-radius: 10px; cursor: pointer; transition: all 0.25s; &:hover { border-color: #93C5FD; background: #F8FAFC; } &.active { border-color: $color-primary; background: #EFF6FF; box-shadow: 0 0 0 3px rgba(29,78,216,0.1); } }
  .wls-badge { flex-shrink: 0; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 800; height: fit-content; margin-top: 2px; &.danger { background: #FEF2F2; color: #EF4444; border: 1px solid #FECACA; } &.warn { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; } }
  .wls-info { h4 { margin: 0 0 6px 0; font-size: 1rem; font-weight: 700; color: $text-main; .wls-count { font-size: 0.85rem; color: $text-muted; font-weight: 600; margin-left: 8px; } } p { margin: 0 0 8px 0; font-size: 0.85rem; color: $text-muted; line-height: 1.5; } .wls-workers { font-size: 0.8rem; color: $color-primary; font-weight: 600; font-family: monospace; } }
}

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

/* 一级预防（中危）专用配色 */
.level1-tabs { gap: 10px; flex-wrap: wrap; }
.level1-tab { border-color: #FDE68A;
  &:hover { border-color: #FBBF24; background: #FFFBEB; }
  &.active { border-color: #D97706; background: #FFFBEB; box-shadow: 0 0 0 3px rgba(217,119,6,0.1); }
  .level1-score { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
}
.level1-profile { border-left: 4px solid #D97706; background: #FFFBEB;
  .pw-info h3 { color: #92400E; }
}
.level1-outcome { border-left: 4px solid #D97706;
  h4 { color: #92400E; .el-icon { color: #D97706; } }
}
.level1-before { background: #F59E0B !important; }
.level1-after { background: #D97706 !important; }

/* 个人化干预流程样式 */
.person-tabs { display: flex; gap: 12px; margin-bottom: 24px; }
.person-tab { display: flex; align-items: center; gap: 8px; padding: 10px 18px; border: 2px solid $border-color; border-radius: 10px; cursor: pointer; transition: all 0.25s; background: #fff;
  &:hover { border-color: #93C5FD; }
  &.active { border-color: $color-primary; background: #EFF6FF; box-shadow: 0 0 0 3px rgba(29,78,216,0.1); }
  .pt-id { font-weight: 800; font-size: 0.95rem; color: $text-main; font-family: monospace; }
  .pt-score { font-weight: 700; font-size: 0.85rem; padding: 2px 8px; border-radius: 4px; &.danger { background: #FEF2F2; color: #EF4444; } &.warn { background: #FFFBEB; color: #D97706; } }
}

.person-workflow { animation: fadeIn 0.4s ease-out forwards; }
.pw-profile { background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
  .pw-info h3 { margin: 0 0 10px 0; font-size: 1.2rem; font-weight: 800; color: $text-main; }
  .pw-meta { display: flex; gap: 8px; flex-wrap: wrap; }
}

.workflow-steps { display: flex; flex-direction: column; gap: 0; margin-bottom: 24px; }
.wf-step { background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 20px 24px; margin-bottom: 12px; position: relative; transition: all 0.2s;
  &:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
}
.wf-step-header { display: flex; align-items: center; gap: 14px; margin-bottom: 12px; }
.wf-step-num { width: 32px; height: 32px; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 800; font-size: 0.9rem; flex-shrink: 0;
  &.danger { background: #FEF2F2; color: #EF4444; border: 2px solid #FECACA; }
  &.primary { background: #EFF6FF; color: #1D4ED8; border: 2px solid #BFDBFE; }
  &.warning { background: #FFFBEB; color: #D97706; border: 2px solid #FDE68A; }
  &.safe { background: #ECFDF5; color: #059669; border: 2px solid #A7F3D0; }
}
.wf-step-title { flex: 1; display: flex; align-items: center; gap: 10px;
  h4 { margin: 0; font-size: 1.05rem; font-weight: 700; color: $text-main; }
  .wf-step-tag { font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; background: #F1F5F9; color: #475569; }
}
.wf-step-body { padding-left: 46px;
  .wf-desc { margin: 0 0 10px 0; font-size: 0.9rem; color: #475569; line-height: 1.6; }
  .wf-detail, .wf-indicator { font-size: 0.85rem; color: #64748B; margin-bottom: 8px; line-height: 1.5; strong { color: $text-main; } }
  .wf-detail { padding: 10px 12px; background: #F8FAFC; border-radius: 6px; border: 1px solid #F1F5F9; }
  .wf-indicator { padding: 10px 12px; background: #FFFBEB; border-radius: 6px; border: 1px solid #FDE68A; strong { color: #92400E; } }
  .wf-timeline { display: flex; gap: 8px; margin-top: 10px; }
}

.pw-outcome { background: #fff; border: 1px solid $border-color; border-radius: 12px; padding: 20px 24px;
  h4 { margin: 0 0 16px 0; font-size: 1.05rem; font-weight: 700; color: #065F46; display: flex; align-items: center; gap: 8px; .el-icon { color: #10B981; } }
}
.outcome-grid { display: flex; flex-direction: column; gap: 12px; }
.outcome-item { display: flex; align-items: center; gap: 12px;
  .o-label { width: 120px; font-size: 0.85rem; font-weight: 700; color: $text-main; flex-shrink: 0; text-align: right; }
}
.o-bar-wrap { flex: 1; display: flex; align-items: center; gap: 8px; }
.o-bar-before, .o-bar-after { height: 24px; border-radius: 4px; display: flex; align-items: center; justify-content: flex-end; padding: 0 8px; font-size: 0.75rem; font-weight: 700; color: #fff; min-width: 40px; transition: width 0.6s ease; }
.o-bar-before { background: #EF4444; }
.o-bar-after { background: #10B981; }
.o-arrow { color: #9CA3AF; font-weight: 700; font-size: 0.9rem; }

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