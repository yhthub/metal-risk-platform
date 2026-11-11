export type CausalMetal = 'Pb' | 'Cd' | 'Hg'
export type CausalOutcome = 'renal' | 'sbp' | 'unsupported'

export const metalNames: Record<CausalMetal, string> = {
  Pb: '铅',
  Cd: '镉',
  Hg: '汞',
}

export const outcomeNames: Record<CausalOutcome, string> = {
  renal: '肾功能与尿液指标',
  sbp: '收缩压',
  unsupported: '其他指标',
}

export interface CausalSource {
  title: string
  issuer: string
  year: number
  locator: string
  url: string
}

export interface CausalPathway {
  id: string
  metals: CausalMetal[]
  outcome: CausalOutcome
  title: string
  from: string
  to: string
  relation: string
  kind: 'single' | 'joint' | 'mechanism'
  summary: string
  observed: string
  limits: string
  sourceType: string
  source: CausalSource
}

export interface CausalControl {
  id: string
  metals: CausalMetal[]
  label: string
  text: string
  source: CausalSource
}

const nhanesRenalStudy: CausalSource = {
  title: 'Blood Cadmium and Lead and Chronic Kidney Disease in US Adults: A Joint Analysis',
  issuer: 'American Journal of Epidemiology',
  year: 2009,
  locator: '表 2，模型 3',
  url: 'https://doi.org/10.1093/aje/kwp248',
}

const jointRenalSource: CausalSource = {
  ...nhanesRenalStudy,
  locator: '第 1159 页，联合暴露与分组分析结果',
}

export const pathways: CausalPathway[] = [
  {
    id: 'pb-cd-albuminuria',
    metals: ['Pb', 'Cd'],
    outcome: 'renal',
    title: '铅镉共同暴露与白蛋白尿',
    from: '血铅与血镉',
    to: '白蛋白尿',
    relation: '联合暴露关联',
    kind: 'joint',
    summary: '在美国 14,778 名成年人的横断面调查中，血铅和血镉均处于最高四分位的一组，更常检出白蛋白尿。研究以尿白蛋白与肌酐比评估这一结局。',
    observed: '与两者均在最低四分位的人群相比，白蛋白尿的比值比（OR）为 2.34（95% CI 1.72–3.18）。对数血铅与对数血镉的乘积项检验 P = 0.003。',
    limits: '交互结果仅适用于这项研究的模型与白蛋白尿指标。一次调查无法确定暴露先后，生物学上的协同作用仍需独立验证。',
    sourceType: '人群横断面研究',
    source: jointRenalSource,
  },
  {
    id: 'pb-cd-egfr',
    metals: ['Pb', 'Cd'],
    outcome: 'renal',
    title: '铅镉共同暴露与较低肾小球滤过率',
    from: '血铅与血镉',
    to: '较低 eGFR',
    relation: '联合暴露关联',
    kind: 'joint',
    summary: '同一项美国成人调查还分析了估算肾小球滤过率（eGFR）低于 60 mL/min/1.73 m² 的情况。两种金属水平均较高的一组更常达到这一标准。',
    observed: '与两种金属均在最低四分位的人群相比，两者均在最高四分位组的 OR 为 1.98（95% CI 1.27–3.10）。此结局的乘积项检验 P = 0.17。',
    limits: '该分析未检出明确的乘法交互。横断面测量缺少肾功能的长期变化信息，不能用来判断个人是否患有慢性肾病。',
    sourceType: '人群横断面研究',
    source: jointRenalSource,
  },
  {
    id: 'pb-egfr',
    metals: ['Pb'],
    outcome: 'renal',
    title: '血铅与较低肾小球滤过率',
    from: '血铅',
    to: '较低 eGFR',
    relation: '观察性关联',
    kind: 'single',
    summary: '美国成人调查在同时考虑血镉及其他协变量后，较高血铅仍与较低的估算肾小球滤过率相关。',
    observed: '血铅最高与最低四分位组相比，eGFR 低于 60 mL/min/1.73 m² 的 OR 为 1.56（95% CI 1.17–2.08）。',
    limits: '血铅和肾功能在同次调查中测量。结果适用于受调查的一般成年人，向特定岗位外推需另有数据支持。',
    sourceType: '人群横断面研究',
    source: nhanesRenalStudy,
  },
  {
    id: 'cd-proximal-tubule',
    metals: ['Cd'],
    outcome: 'renal',
    title: '职业镉暴露与近端肾小管功能',
    from: '随访中的血镉',
    to: '尿 β₂-微球蛋白持续升高',
    relation: '随访关联',
    kind: 'single',
    summary: '日本一家镍镉电池厂的职业健康随访发现，较高的血镉与后续出现近端肾小管功能异常指标相关。',
    observed: '研究纳入 238 名作业人员。结局要求尿 β₂-微球蛋白至少连续两次达到研究设定的标准，借此识别持续性变化。',
    limits: '研究观察的是该工厂人群的肾小管指标。判断某位劳动者的肾功能还需要结合其他检查和临床评估。',
    sourceType: '职业人群随访',
    source: {
      title: 'Increased risk of proximal tubular dysfunction due to occupational cadmium exposure: a survival analysis study',
      issuer: 'Journal of Occupational Health',
      year: 2025,
      locator: '方法中的结局定义与结果中的生存分析',
      url: 'https://pubmed.ncbi.nlm.nih.gov/40042158/',
    },
  },
  {
    id: 'cd-egfr',
    metals: ['Cd'],
    outcome: 'renal',
    title: '血镉与较低肾小球滤过率',
    from: '血镉',
    to: '较低 eGFR',
    relation: '观察性关联',
    kind: 'single',
    summary: '美国成人调查在考虑血铅及其他协变量后，血镉较高组更常出现较低的估算肾小球滤过率。',
    observed: '血镉最高与最低四分位组相比，eGFR 低于 60 mL/min/1.73 m² 的 OR 为 1.32（95% CI 1.04–1.68）。',
    limits: '这是同一批美国成年人的横断面数据，研究无法判断暴露和肾功能变化的时间顺序。',
    sourceType: '人群横断面研究',
    source: nhanesRenalStudy,
  },
  {
    id: 'cd-tubular-uptake',
    metals: ['Cd'],
    outcome: 'renal',
    title: '镉对近端肾小管细胞摄取白蛋白的影响',
    from: '培养细胞接触氯化镉',
    to: '白蛋白摄取减少',
    relation: '细胞实验机制',
    kind: 'mechanism',
    summary: '在猪近端肾小管 LLC-PK1 细胞中，接触氯化镉后，参与蛋白重吸收的 megalin 和 ClC5 表达下降。荧光标记显示细胞摄取白蛋白的能力也减弱。',
    observed: '图 5 比较了对照组与 10 μmol/L 氯化镉处理 9 小时的细胞，后者摄入的荧光标记白蛋白较少。',
    limits: '观察来自培养细胞。该实验不能确定人体暴露阈值、个体发病概率或人群中白蛋白尿的具体病因。',
    sourceType: '体外细胞实验',
    source: {
      title: 'Cadmium impairs albumin reabsorption by down-regulating megalin and ClC5 channels in renal proximal tubule cells',
      issuer: 'Environmental Health Perspectives',
      year: 2010,
      locator: '方法、结果与图 5，荧光白蛋白摄取实验',
      url: 'https://pubmed.ncbi.nlm.nih.gov/20576581/',
    },
  },
  {
    id: 'pb-sbp',
    metals: ['Pb'],
    outcome: 'sbp',
    title: '职业铅暴露与收缩压变化',
    from: '血铅的年度变化',
    to: '收缩压的年度变化',
    relation: '随访关联',
    kind: 'single',
    summary: '韩国职业队列对 575 名在岗或曾经从事铅作业的人员进行随访，发现血铅变化与同期收缩压变化相关。',
    observed: '血铅的年增幅每多 10 μg/dL，收缩压的年变化平均高 0.9 mmHg（95% CI 0.1–1.6）。',
    limits: '该人群基线平均血铅为 31.4 μg/dL，研究结果外推到低暴露人群需谨慎。研究所测的结局是收缩压变化。',
    sourceType: '职业人群随访',
    source: {
      title: 'Changes in systolic blood pressure associated with lead in blood and bone',
      issuer: 'Epidemiology',
      year: 2006,
      locator: '摘要，研究方法与纵向结果',
      url: 'https://pubmed.ncbi.nlm.nih.gov/16906055/',
    },
  },
]

export function selectPathways(metals: readonly CausalMetal[], outcome: CausalOutcome): CausalPathway[] {
  return pathways.filter(path => path.outcome === outcome && path.metals.every(metal => metals.includes(metal)))
}

export const controlSources: CausalControl[] = [
  {
    id: 'pb-source-capture',
    metals: ['Pb'],
    label: '含铅粉尘的源头控制',
    text: '排查产生含铅粉尘或烟雾的工序，评估密闭、隔离和局部排风的可行性，并检查控制设施的运行与维护情况。',
    source: {
      title: 'Information for Employers',
      issuer: '美国国家职业安全卫生研究所（NIOSH）',
      year: 2026,
      locator: '2026 年更新，Engineering controls',
      url: 'https://www.cdc.gov/niosh/lead/prevention/information-for-employers.html',
    },
  },
  {
    id: 'cd-ventilation',
    metals: ['Cd'],
    label: '含镉工序的排风核查',
    text: '对依靠通风控制镉暴露的工序，可结合现场条件测量捕集风速、管道风速或静压，核查控制设施的有效性。',
    source: {
      title: 'Cadmium, 29 CFR 1910.1027',
      issuer: '美国职业安全与健康管理局（OSHA）',
      year: 1992,
      locator: '1992 年生效，第 (f)(3)(i) 款，通风有效性核查',
      url: 'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1027#1910.1027(f)(3)(i)',
    },
  },
]
