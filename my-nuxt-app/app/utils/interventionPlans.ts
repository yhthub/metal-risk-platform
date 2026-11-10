/** Shared preset occupational-health plans used by the workspace and its printable report. */
export type PreventionLevel = 'level1' | 'level2'

export interface InterventionStep {
  title: string
  tag: string
  type: 'primary' | 'warning' | 'safe' | 'danger'
  owner: string
  period: string
  desc: string
  detail: string
  indicator: string
}

export interface ObservationItem {
  label: string
  record: string
  source: string
}

export interface InterventionPlan {
  id: string
  dept: string
  years: number
  factors: string
  level: PreventionLevel
  recommendationSummary: string
  basis: { label: string; detail: string }[]
  confounders: { factor: string }[]
  workflow: InterventionStep[]
  outcomes: ObservationItem[]
}

function work(title: string, tag: string, owner: string, period: string, desc: string, detail: string, indicator: string): InterventionStep {
  const type = ['暴露阻断', '紧急防护'].includes(tag) ? 'danger'
    : ['专业评估', '专项筛查', '健康筛查', '综合评估'].includes(tag) ? 'primary'
    : ['定期监测', '长期监测'].includes(tag) ? 'warning' : 'safe'
  return { title, tag, type, owner, period, desc, detail, indicator }
}

function baseline(title: string, materials: string, period = '首次评估'): InterventionStep {
  return work(title, '健康筛查', '职业健康管理人员与职业医师', period,
    '整理已有检测资料，建立该对象的可比基线。',
    `核对${materials}的报告日期、样本类型、单位及对应接触时段；缺少的项目单列，交职业医师判断是否需要补充。`,
    '记录已取得的报告、尚缺资料和复核意见。')
}

function protection(item: string, workplace: string): InterventionStep {
  return work(item, '个人防护', '班组与职业卫生管理人员', '上岗前及更换时',
    `核对${workplace}实际使用的防护装备及佩戴方式。`,
    '根据岗位危害清单核对装备选型、领用与更换记录；现场查看佩戴和维护，记录需纠正的问题。',
    '保留装备型号、现场核查日期和整改复核结果。')
}

function hygiene(workplace: string): InterventionStep {
  return work('核查个人卫生与离岗流程', '行为干预', '班组与干预对象', '每班作业结束时',
    `沿${workplace}离岗动线检查更衣、清洗与工作服交接。`,
    '与对象核对用餐前洗手、工作服分区存放和离岗清洗的实际条件，现场记录设施或流程缺口。',
    '标记已具备的设施、待整改事项和班组反馈。')
}

function nutrition(focus: string): InterventionStep {
  return work('核对膳食与补充剂使用情况', '健康教育', '干预对象与职业医师', '健康访谈时',
    `结合${focus}，了解日常饮食及自行服用补充剂的情况。`,
    '记录品类、使用原因和对象关切；将涉及补充剂或用药的问题交专业人员评估，登记反馈。',
    '在访谈记录中列出待答复事项、复核人和反馈日期。')
}

function followup(title: string, focus: string, period = '按确认的复查安排'): InterventionStep {
  return work(title, '定期监测', '职业健康管理人员', period,
    `归集${focus}的历次记录，供专业人员纵向复核。`,
    '按日期整理原始记录，遇到单位、样本或检测方法变化时单独标记，向职业医师提交前次和本次资料。',
    '记录实际复查日期、专业意见及下次联系安排。')
}

function annual(materials: string): InterventionStep {
  return work('年度职业健康资料复核', '综合评估', '职业健康管理人员与职业医师', '年度复核',
    `汇总${materials}，梳理仍需跟进的事项。`,
    '把岗位变动、暴露记录、体检资料及已实施措施关联到同一对象编号，交专业人员确认后续安排。',
    '保存年度复核意见、待办事项和下一次联系日期。')
}

function clinical(title: string, materials: string, question: string): InterventionStep {
  return work(title, '专业评估', '职业医师', '取得资料后',
    question, `将${materials}连同岗位接触记录移交职业医师。由医师决定进一步检查、诊疗或转诊安排。`,
    '记录实际接诊日期、专业意见、后续责任人与联系安排。')
}

function laboratory(label: string): ObservationItem {
  return { label, record: '记录采样日期、样本类型、原始结果和报告单位。', source: '原始检验报告' }
}

function review(label: string, source: string, record: string): ObservationItem {
  return { label, source, record }
}

const kidney = review('肾功能复核', '体检或专科报告', '记录已检查的项目、检查日期和医师意见。')
const neuro = review('神经功能评估', '职业医师评估记录', '记录主诉、已完成的评估及下一次复核安排。')
const skin = review('皮肤状况随访', '职业健康访谈或专科记录', '记录自述变化、评估结论和后续安排。')
const annualRecord = review('年度健康复核', '职业健康档案', '记录年度复核意见及待随访事项。')

export const interventionPlans: InterventionPlan[] = [
  {
    id: 'SZ-284', dept: '第一熔炼车间', years: 18, factors: 'Pb, As', level: 'level2',
    recommendationSummary: '先核对熔炼岗位的铅、砷接触路径，再将既往检测、吸烟史与功能评估资料一并交职业医师复核。',
    basis: [
      { label: '接触背景', detail: '档案登记第一熔炼车间接触工龄 18 年，需结合历年工位变化核对两类暴露记录。' },
      { label: '资料重点', detail: '既往档案记录吸烟史，访谈时应和工作接触史分别记录，并与血铅及尿砷资料按时间对照。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '年龄：52 岁' }, { factor: '吸烟史：20 年，日约 15 支' }],
    workflow: [
      work('核查岗位接触并复核作业安排', '暴露阻断', '班组与职业卫生管理人员', '优先办理',
        '核查熔炼岗位中铅、砷接触环节，交由管理人员评估作业安排。', '梳理当前工位和近期排班，核对现场控制措施与监测记录；如需调整工作安排，留存批准及交接记录。', '记录实际涉岗工序、核查人员与处理结果。'),
      baseline('汇集铅、砷接触与体检资料', '血铅、尿砷及既往体检'),
      clinical('提交铅暴露专项临床评估', '血铅报告、采样时间与既往处理资料', '请职业医师核对接触资料与临床表现，确定评估路径。'),
      clinical('复核肝肾功能相关资料', '既往肝肾功能报告及用药记录', '将已有资料和待澄清的问题整理成专业复核清单。'),
      followup('跟进血铅与尿砷复查', '血铅、尿砷及同期岗位变化'),
      followup('建立长期神经功能随访记录', '神经行为或听力评估、对象主诉与随访意见', '长期跟踪'),
    ],
    outcomes: [laboratory('血铅'), laboratory('尿砷'), neuro, kidney],
  },
  {
    id: 'SZ-105', dept: '第一熔炼车间', years: 15, factors: 'Pb, Cd', level: 'level2',
    recommendationSummary: '将铅、镉粉尘的岗位防护、局部排风和肾功能资料列为首要核查事项，再安排长期复核。',
    basis: [
      { label: '作业环节', detail: '该对象登记在第一熔炼车间，接触工龄 15 年。先核对具体粉尘工位及局部排风运行记录。' },
      { label: '复核重点', detail: '方案涉及血铅、尿镉及肾功能资料。应区分不同样本和采样日期，并记录档案中的饮酒情况。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '年龄：48 岁' }, { factor: '饮酒：档案记载经常饮酒' }],
    workflow: [
      work('核查呼吸防护与局部排风', '紧急防护', '班组与设备管理人员', '优先办理',
        '核查熔炼工位的防护装备和粉尘捕集设施。', '现场确认罩口位置、运行状态、维护日期及装备佩戴情况，记录需工程人员复查的问题。', '登记设施复核结果、装备核查情况及整改工单。'),
      baseline('汇集肾功能及镉接触资料', '尿镉、既往肾功能及已有肾小管相关检查'),
      clinical('转交铅镉联合接触资料', '血铅、尿镉及肾功能报告', '请职业医师评估当前就诊资料与尚缺信息。'),
      followup('建立镉接触长期监测档案', '尿镉、肾功能与落实的岗位措施', '长期跟踪'),
      nutrition('已有肾功能资料和饮酒记录'),
    ],
    outcomes: [laboratory('血铅'), laboratory('尿镉'), kidney, neuro],
  },
  {
    id: 'SZ-032', dept: '第一熔炼车间', years: 14, factors: 'As, Ni', level: 'level2',
    recommendationSummary: '先核实所属车间和实际作业工序，再按砷、镍接触记录整理排班、个人检测及皮肤和呼吸系统评估资料。',
    basis: [
      { label: '岗位待核', detail: '对象所属部门登记为第一熔炼车间，背景资料另列尾气处理组。执行排班调整前须核实实际工序和接触时段。' },
      { label: '资料重点', detail: '接触工龄登记 14 年，涉及砷、镍。检测报告应结合原工序、样本类型和吸烟史分别核对。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '吸烟史：10 年，日约 10 支' }, { factor: '实际工序：待核实' }],
    workflow: [
      work('核实工序与轮岗安排', '暴露阻断', '班组与职业卫生管理人员', '安排作业前',
        '对照车间档案和排班表核实实际工作地点。', '访谈对象并核对作业日志，分别记录常规工位、临时轮岗与接触时间，由现场管理人员确认安排。', '保存核实后的工位、班次和批准记录。'),
      baseline('核对砷、镍专项检测', '尿砷、尿镍以及如已检测的砷形态分析'),
      clinical('提交肝功能资料供专业复核', '肝功能资料、既往就诊和用药记录', '由职业医师确认需追踪的检查项目及联系时间。'),
      clinical('整理皮肤与呼吸系统评估资料', '已有皮肤科、呼吸系统评估或体检资料', '核对本人曾反映的变化与已有专业记录。'),
      followup('安排阶段复查与年度回顾', '砷镍检测、岗位变动和专科复核', '按确认的随访计划'),
    ],
    outcomes: [laboratory('尿砷'), laboratory('尿镍'), review('肝功能复核', '体检或专科报告', '记录已有检查和签署的复核意见。'), skin],
  },
  {
    id: 'SZ-142', dept: '原矿粉碎区', years: 12, factors: 'Pb, Hg', level: 'level2',
    recommendationSummary: '从原矿粉碎区的铅、汞接触路径出发，核对现用防护及血铅、尿汞资料，衔接神经功能评估与后续随访。',
    basis: [
      { label: '防护现状', detail: '档案记录现用 KN95 口罩、接触工龄 12 年。需结合现场接触形态和岗位危害资料复核防护选型。' },
      { label: '联合复核', detail: '铅与汞对应的检测样本不同，整理血铅和尿汞时应分别注明单位及采样条件。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '岗位：原矿粉碎区' }, { factor: '防护档案：KN95 口罩' }],
    workflow: [
      protection('复核粉碎工位防护装备', '原矿粉碎区'),
      baseline('核对铅、汞接触基线', '血铅、尿汞与同期接触'),
      clinical('转交铅汞联合暴露评估', '铅、汞检测报告和既往专业处理记录', '将两类暴露资料按时间并列，交职业医师复核。'),
      clinical('核对神经功能评估安排', '既往神经行为评估、主诉和体检资料', '补齐既往评估信息，记录专业人员提出的复核安排。'),
      followup('衔接长期健康随访', '铅汞复查、神经功能评估与岗位防护记录', '长期跟踪'),
    ],
    outcomes: [laboratory('血铅'), laboratory('尿汞'), neuro, kidney],
  },
  {
    id: 'SZ-089', dept: '原矿粉碎区', years: 11, factors: 'Cd, Cr', level: 'level1',
    recommendationSummary: '以原矿粉碎工位的轮岗、防护和班组培训为起点，持续记录镉、铬接触及体检复核情况。',
    basis: [
      { label: '工位暴露', detail: '已有 11 年接触记录，涉及镉、铬两种金属。需核实轮岗是否改变实际接触时段。' },
      { label: '日常管理', detail: '将个人防护、离岗卫生和复训落实到同一岗位记录，便于与后续体检资料衔接。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '岗位：原矿粉碎区' }, { factor: '吸烟史：不吸烟' }],
    workflow: [
      work('核对轮岗与接触时段', '暴露阻断', '班组', '排班时',
        '核实粉碎岗位实际轮班和接触时段。', '逐班对照工作任务与在岗记录，登记转岗时间、交接人及仍存在的接触环节。', '留存轮岗台账和班组确认。'),
      baseline('整理镉、铬接触基线', '尿镉、尿铬及既往肾功能'),
      protection('核对防护装备领用与佩戴', '粉碎工位'),
      nutrition('日常饮食与在岗卫生安排'),
      followup('衔接阶段体检', '镉铬接触及肾功能资料', '按已确认的季度安排'),
      work('开展岗位防护与卫生培训', '健康教育', '班组与职业卫生培训人员', '岗前及定期复训',
        '核对粉碎工位的培训覆盖情况，安排缺项补训。', '课纲包括金属危害识别、防护装备佩戴、工后清洗更衣与用餐分区；登记受训内容和现场操作核查情况。', '记录培训日期、参与编号、操作核查及补训事项。'),
    ],
    outcomes: [laboratory('尿镉'), laboratory('尿铬'), kidney, annualRecord],
  },
  {
    id: 'SZ-311', dept: '第一熔炼车间', years: 9, factors: 'Pb, As', level: 'level1',
    recommendationSummary: '先确认熔炼工位排风和个人卫生流程，再建立血铅、尿砷与历次岗位安排的对应记录。',
    basis: [
      { label: '环境控制', detail: '第一熔炼车间接触工龄 9 年。通风设备是否随工位布置更新，是现场核查的第一项。' },
      { label: '持续记录', detail: '档案登记不吸烟。以工作时段、设备维护记录与铅砷基线资料组织后续观察。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '吸烟史：不吸烟' }, { factor: '岗位：第一熔炼车间' }],
    workflow: [
      work('核查熔炼工位排风', '环境控制', '设备管理人员与班组', '现场核查时',
        '确认局部排风与实际操作位置是否匹配。', '对照工位布置检查罩口位置、使用状态与维护记录；将需调整事项移交设备管理人员。', '登记工位、设备编号、问题及复核日期。'),
      baseline('核对血铅与尿砷基线', '血铅、尿砷及岗位环境监测'),
      nutrition('熔炼工位的工作餐与个人卫生'),
      hygiene('熔炼工位'),
      followup('跟踪血铅复查', '血铅与同期熔炼作业安排', '按已确认的季度安排'),
      annual('铅砷检测、排风维护与卫生核查'),
    ],
    outcomes: [laboratory('血铅'), laboratory('尿砷'), review('肝功能复核', '体检资料', '记录已完成检查和专业意见。'), annualRecord],
  },
  {
    id: 'SZ-402', dept: '尾气处理组', years: 8, factors: 'As, Ni', level: 'level1',
    recommendationSummary: '围绕尾气治理工位核对砷、镍接触和个人防护，分别跟踪皮肤状况、吸烟史和专业反馈。',
    basis: [
      { label: '岗位资料', detail: '尾气处理岗位登记接触工龄 8 年。日常操作与检修任务的接触环节需分别记录。' },
      { label: '访谈重点', detail: '档案有吸烟史。皮肤、呼吸主诉和吸烟情况应分别记录，供专业人员结合岗位资料复核。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '吸烟史：5 年，日约 8 支' }, { factor: '岗位：尾气处理组' }],
    workflow: [
      protection('核查尾气处理岗位防护', '尾气处理作业与检修工位'),
      baseline('整理砷、镍基线资料', '尿砷、尿镍与相关体检'),
      nutrition('岗位用餐和个人膳食习惯'),
      followup('跟踪皮肤健康资料', '皮肤变化、专业评估及对应工作任务'),
      followup('衔接常规体检与岗位记录', '砷镍复查和防护设施变化', '按已确认的季度安排'),
      work('记录烟酒情况与健康咨询', '行为干预', '干预对象与健康管理人员', '随访访谈时',
        '了解对象对生活方式支持的需求。', '记录吸烟及饮酒情况的变化，与工作场所接触记录分开；根据本人意愿衔接健康咨询。', '记录访谈日期、咨询意愿及下一次联系方式。'),
    ],
    outcomes: [laboratory('尿砷'), laboratory('尿镍'), skin, annualRecord],
  },
  {
    id: 'SZ-175', dept: '第一熔炼车间', years: 7, factors: 'Pb', level: 'level1',
    recommendationSummary: '核对铅接触岗位的防护、个人卫生及血铅基线，将历次复查与年度健康记录串联起来。',
    basis: [
      { label: '单一因素', detail: '预设档案列示铅暴露，接触工龄 7 年。围绕本岗位的防护记录与血铅资料开展核查。' },
      { label: '档案背景', detail: '对象登记年龄 35 岁，不吸烟、不饮酒。年度复核时更新这部分访谈资料。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '年龄：35 岁' }, { factor: '烟酒史：不吸烟、不饮酒' }],
    workflow: [
      protection('复核熔炼岗位个人防护', '铅接触工位'),
      baseline('核对血铅检测基线', '血铅和同期在岗记录'),
      nutrition('铅接触岗位的工作餐及既往补充剂使用'),
      hygiene('熔炼车间'),
      followup('整理历次血铅结果', '血铅与岗位防护记录', '按已确认的季度安排'),
      annual('铅接触、血液系统及神经功能相关记录'),
    ],
    outcomes: [laboratory('血铅'), review('血液系统复核', '体检报告', '记录已有检查、日期与专业意见。'), neuro, annualRecord],
  },
  {
    id: 'SZ-219', dept: '原矿粉碎区', years: 6, factors: 'Cd, Hg', level: 'level1',
    recommendationSummary: '核对粉碎工位的镉、汞接触和防护，整理尿检与肾功能资料并对齐复核时间。',
    basis: [
      { label: '接触记录', detail: '对象有 6 年原矿粉碎区接触记录，资料包含镉与汞。岗位防护和现场卫生需与检测记录对应。' },
      { label: '监测重点', detail: '核对尿镉、尿汞及肾功能资料是否取得，并区分采样日期和体检日期。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '吸烟史：不吸烟' }, { factor: '岗位：原矿粉碎区' }],
    workflow: [
      protection('核对粉碎岗位装备与维护', '原矿粉碎区'),
      baseline('整理镉、汞接触基线', '尿镉、尿汞及既往肾功能'),
      nutrition('工作餐、清洁条件及既往膳食补充情况'),
      followup('归集肾功能复核记录', '肾功能及同期镉汞资料', '按已确认的季度安排'),
      hygiene('原矿粉碎区'),
      annual('镉汞接触史及肾功能复核资料'),
    ],
    outcomes: [laboratory('尿镉'), laboratory('尿汞'), kidney, annualRecord],
  },
  {
    id: 'SZ-056', dept: '尾气处理组', years: 5, factors: 'Cr', level: 'level1',
    recommendationSummary: '先核对尾气处理工位通风和呼吸防护，再将铬接触资料与肺功能、皮肤状况的既往记录归档。',
    basis: [
      { label: '工位控制', detail: '尾气处理岗位登记接触工龄 5 年。将排风状态、检修记录与实际在岗时段对应。' },
      { label: '健康资料', detail: '当前档案列示铬暴露。核对尿铬资料及体检中已有的肺功能、皮肤状况记录。' },
    ],
    confounders: [{ factor: '性别：男性' }, { factor: '吸烟史：不吸烟' }, { factor: '岗位：尾气处理组' }],
    workflow: [
      work('核查尾气处理工位排风', '环境控制', '设备管理人员与班组', '现场核查时',
        '确认通风和粉尘控制设施的现场状态。', '对照设施清单记录罩口、气流及维护情况，并核对检修任务中的临时控制措施。', '保存检查记录、维修工单与复核日期。'),
      baseline('核对铬接触与体检基线', '尿铬和已有肺功能'),
      nutrition('铬接触档案及自行服用营养补充剂的情况'),
      protection('核查呼吸防护佩戴与维护', '尾气处理工位'),
      followup('整理尿铬与体检复查记录', '尿铬、肺功能和皮肤相关资料', '按已确认的季度安排'),
      annual('铬接触及肺功能、皮肤相关资料'),
    ],
    outcomes: [laboratory('尿铬'), review('肺功能复核', '体检或专科报告', '记录检查日期、报告结论和复核安排。'), skin, annualRecord],
  },
]

export const plansByLevel = {
  level1: interventionPlans.filter(plan => plan.level === 'level1'),
  level2: interventionPlans.filter(plan => plan.level === 'level2'),
}

export function getInterventionPlan(id: unknown): InterventionPlan | null {
  return interventionPlans.find(plan => plan.id === id) ?? null
}
