import { controlSources, pathways } from './causalEvidence'
import { coreMetalRelations } from './coreMetalEvidence'
import { extendedMetalRelations } from './extendedMetalEvidence'
import { additionalFieldEvidence } from './additionalFieldEvidence'
import { existingFieldChecks, existingStudyChecks } from './evidenceDossier'
import type { KnowledgeRelation } from './knowledgeTypes'

const plainLabels: Record<string, string> = {
  '白蛋白尿': '尿中白蛋白偏高',
  '较低 eGFR': '肾脏过滤能力偏低',
  '尿 β₂-微球蛋白持续升高': '尿中肾小管指标持续升高',
  '白蛋白摄取减少': '细胞回收白蛋白减少',
  '收缩压的年度变化': '收缩压（高压）变化',
}
const plainFindings: Record<string, string> = {
  'pb-egfr': '一项美国成人调查发现，血铅较高的一组更常出现肾脏过滤能力偏低。研究用估算肾小球滤过率（eGFR）衡量过滤能力。',
  'cd-egfr': '一项美国成人调查发现，血镉较高的一组更常出现肾脏过滤能力偏低。研究在比较时也考虑了血铅水平。',
  'pb-cd-albuminuria': '在同一次调查中，血铅和血镉都较高的成年人，更常被检出尿中白蛋白偏高。',
  'pb-cd-egfr': '血铅和血镉都较高的一组，更常出现肾脏过滤能力偏低。这个指标上的统计检验没有发现明确的联合作用。',
  'cd-proximal-tubule': '一项电池厂随访发现，血镉较高的工人，后来更常连续两次检出尿中一种小分子蛋白偏高。它反映肾小管回收蛋白的功能。',
  'cd-tubular-uptake': '猪肾小管细胞接触氯化镉后，负责回收蛋白的部分分子减少，细胞摄取的白蛋白也减少了。',
  'pb-sbp': '对韩国铅作业人员的随访发现，血铅增加较多的人，同期收缩压（通常所说的“高压”）平均也升高得更多。',
}
const earlierStudies: KnowledgeRelation[] = pathways.map(path => ({
  id: path.id, metals: path.metals, topic: path.outcome === 'sbp' ? 'sbp' : 'renal',
  kind: path.kind === 'mechanism' ? 'mechanism' : 'health',
  from: path.from, to: plainLabels[path.to] ?? path.to, title: path.title,
  finding: plainFindings[path.id] ?? path.summary, detail: path.summary + ' ' + path.observed,
  limit: path.limits, studyType: path.sourceType, source: path.source,
}))
const earlierControls: KnowledgeRelation[] = controlSources.map(control => ({
  id: control.id, metals: control.metals, kind: 'control',
  from: control.metals.includes('Pb') ? '含铅粉尘或烟雾' : '含镉工序',
  to: control.metals.includes('Pb') ? '在产尘处控制粉尘' : '检查排风是否有效',
  title: control.label, finding: control.text, limit: '具体做法需结合作业工艺和现场监测结果。',
  source: control.source, studyType: '职业防护资料',
}))

const seleniumProfile = {
  title: 'Toxicological Profile for Selenium', issuer: '美国毒物与疾病登记署（ATSDR）', year: 2003,
  url: 'https://www.atsdr.cdc.gov/ToxProfiles/tp92.pdf', locator: '第 3 章，第 32 页，吸入暴露与呼吸系统',
}
const selenium: KnowledgeRelation[] = [
  { id: 'se-airway', metals: ['Se'], kind: 'health', topic: 'other', from: '工作场所含硒粉尘', to: '鼻咽刺激和咳嗽',
    title: '吸入含硒粉尘与鼻咽不适', finding: '职业暴露报告记录了吸入含硒粉尘后出现鼻咽刺激和咳嗽的情况。部分工序的粉尘可能同时含有二氧化硒。',
    limit: '早期报告没有给出与症状对应的空气浓度，不能用一次血硒检测推算吸入量。', studyType: '职业暴露资料评估', source: seleniumProfile },
  { id: 'se-local-irritation', metals: ['Se'], kind: 'mechanism', from: '二氧化硒', to: '遇水形成刺激性酸',
    title: '二氧化硒为什么会刺激接触部位', finding: '二氧化硒遇水可生成亚硒酸。接触汗液等水分时，这一化学变化有助于解释它对接触部位的刺激。',
    limit: '这一过程针对二氧化硒，不能推广到膳食中的各种硒。', studyType: '毒理学资料评估', source: seleniumProfile },
  { id: 'se-local-exhaust', metals: ['Se'], kind: 'control', from: '二氧化硒粉尘', to: '防止扬尘并就地排风',
    title: '在二氧化硒粉尘产生处设置排风', finding: '国际化学品安全卡建议防止粉尘扩散，并在吸入暴露的防护措施中列出局部排风。可先核查开包、转移粉料等容易扬尘的工序。',
    limit: '这张安全卡针对二氧化硒；其他形态的硒需要查阅相应资料。', studyType: '国际化学品安全卡',
    source: { title: 'ICSC 0946 – Selenium dioxide', issuer: '国际劳工组织与世界卫生组织', year: 2000,
      locator: '粉尘控制提示及 Inhalation / Prevention 栏', url: 'https://www.inchem.org/documents/icsc/icsc/eics0946.htm' } },
]

const jointExposure: KnowledgeRelation[] = [
  { id: 'pb-cd-kidney-mitochondria', metals: ['Pb', 'Cd'], kind: 'mechanism', topic: 'renal',
    from: '铅和镉（大鼠实验）', to: '肾细胞的供能结构改变', title: '共同接触铅和镉时，大鼠肾细胞的线粒体出现结构变化',
    finding: '研究者让大鼠通过饮水接触铅盐、镉盐或两者的混合物。八周后，混合暴露组肾皮质细胞内的线粒体结构变化更明显。线粒体是细胞产生能量的部位。',
    limit: '这是特定剂量下的大鼠饮水实验，不能直接用来估算工人的肾损伤风险。', studyType: '动物实验',
    source: { title: 'Effects of lead and/or cadmium on the oxidative damage of rat kidney cortex mitochondria',
      issuer: 'Biological Trace Element Research', year: 2010, locator: '摘要，8 周暴露分组及肾皮质线粒体超微结构观察',
      url: 'https://pubmed.ncbi.nlm.nih.gov/19902158/' } },
  { id: 'pb-cd-workwear', metals: ['Pb', 'Cd'], kind: 'control',
    from: '电子废物回收中的铅、镉', to: '工作服集中清洗', title: '减少将含铅、镉的粉尘带回家',
    finding: '美国职业安全卫生研究所调查一家电子废物回收厂后，建议为接触铅或镉的人员提供现场清洗或签约洗衣服务。这样可避免把可能沾有金属粉尘的工作服带回家清洗。',
    limit: '这是回收工序中控制粉尘带出的措施。报告没有测量这一措施对个人发病风险的影响。', studyType: '工作场所调查',
    source: { title: 'Evaluation of Exposure to Metals, Flame Retardants, and Nanomaterials at an Electronics Recycling Company',
      issuer: '美国国家职业安全卫生研究所（NIOSH）', year: 2018, locator: 'HHE 2015-0050-3308，What the Employer Can Do 中衣物清洗建议',
      url: 'https://www.cdc.gov/niosh/hhe/reports/pdfs/2015-0050-3308.pdf' } },
]

const existingRelations = [...earlierStudies, ...earlierControls, ...coreMetalRelations, ...extendedMetalRelations, ...selenium, ...jointExposure]

export const knowledgeRelations: KnowledgeRelation[] = [
  ...existingRelations.map(path => path.kind === 'control'
    ? { ...path, field: existingFieldChecks[path.id] }
    : { ...path, study: existingStudyChecks[path.id] }),
  ...additionalFieldEvidence,
]
