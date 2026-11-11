import type { KnowledgeRelation } from './knowledgeTypes'

export const extendedMetalRelations: KnowledgeRelation[] = [
  {
    id: 'hg-vapour-tremor', metals: ['Hg'], kind: 'health', topic: 'other',
    from: '金属汞蒸气', to: '手部震颤', title: '曾接触汞蒸气的工人更常出现手部震颤',
    finding: '研究人员检查了 77 名曾接触汞蒸气的氯碱厂工人和 53 名对照者。维持姿势时出现震颤的人，前一组占 18.2%，后一组占 7.5%。',
    limit: '这是既往职业暴露人群的一次检查。某位劳动者出现手抖时，仍需结合接触史和其他可能原因评估。',
    studyType: '职业人群比较', source: {
      title: 'A neurological and neurophysiological study of chloralkali workers previously exposed to mercury vapour',
      issuer: 'Acta Neurologica Scandinavica', year: 1993, locator: '摘要，神经系统检查中的姿势性震颤',
      url: 'https://pubmed.ncbi.nlm.nih.gov/8116345/',
    },
  },
  {
    id: 'hg-vapour-brain', metals: ['Hg'], kind: 'mechanism', topic: 'other',
    from: '金属汞蒸气', to: '汞在脑内滞留', title: '吸入的金属汞怎样进入脑部',
    finding: '吸入的金属汞可经血液进入脑部。部分汞随后转为二价汞，这种形态较难再穿过血脑屏障，因而可能滞留。',
    limit: '这项官方毒理评估描述金属汞在体内的转运。它无法根据一次检测判断某个人脑内的汞含量。',
    studyType: '官方毒理评估', source: {
      title: 'Elemental mercury and inorganic mercury: toxicological overview',
      issuer: '英国卫生安全局（UKHSA）', year: 2025, locator: 'Kinetics and metabolism，Distribution 与 Metabolism',
      url: 'https://www.gov.uk/government/publications/mercury-properties-incident-management-and-toxicology/elemental-mercury-and-inorganic-mercury-toxicological-overview',
    },
  },
  {
    id: 'hg-lamp-ventilation', metals: ['Hg'], kind: 'control',
    from: '含汞灯管回收', to: '安装局部排风', title: '在含汞灯管回收工位设置局部排风',
    finding: '美国职业安全卫生研究所调查一家废旧灯管回收厂后，建议在产生污染物的作业点增设局部排风，并修复已有排风系统。',
    limit: '这是对特定回收现场的工程建议。设备布置和实际效果需要结合工位与空气监测核查。',
    studyType: '工作场所调查', source: {
      title: 'Evaluation of Mercury and Noise Exposure at a Lightbulb Recycler',
      issuer: '美国国家职业安全卫生研究所（NIOSH）', year: 2024, locator: '调查报告 2023-0015-3402，Recommendations',
      url: 'https://stacks.cdc.gov/view/cdc/172296',
    },
  },
  {
    id: 'as-smelter-lung', metals: ['As'], kind: 'health', topic: 'other',
    from: '冶炼中的无机砷', to: '肺癌风险', title: '铜冶炼作业中的砷暴露与肺癌风险',
    finding: '研究人员根据瑞典铜冶炼厂的工种、年代与监测资料估算累积砷暴露，比较了 107 名肺癌病例和 214 名对照。考虑吸烟后，累积砷暴露较高者的肺癌风险仍较高。',
    limit: '结果来自历史冶炼环境。饮食中的不同砷形态和当前低暴露岗位需要各自的证据。',
    studyType: '职业病例对照研究', source: {
      title: 'Arsenic exposure, smoking, and lung cancer in smelter workers—a case-control study',
      issuer: 'American Journal of Epidemiology', year: 1991, locator: '摘要，累积暴露分组及调整吸烟后的分析',
      url: 'https://doi.org/10.1093/oxfordjournals.aje.a116128',
    },
  },
  {
    id: 'as-cell-enzyme', metals: ['As'], kind: 'mechanism', topic: 'other',
    from: '三价无机砷', to: '抗氧化酶活性下降', title: '三价砷可干扰细胞的一种抗氧化酶',
    finding: '在培养的大鼠肝细胞中加入三价无机砷后，帮助细胞应对氧化压力的硫氧还蛋白还原酶活性下降。实验还发现，一种甲基化的三价砷代谢物也会抑制这种酶。',
    limit: '这是体外酶活性变化。它能说明一种可能机制，不能用来判断劳动者的器官损伤程度。',
    studyType: '细胞实验', source: {
      title: 'Arsenicals inhibit thioredoxin reductase in cultured rat hepatocytes',
      issuer: 'Chemical Research in Toxicology', year: 2001, locator: '摘要，大鼠肝细胞中酶活性随暴露浓度和时间的变化',
      url: 'https://pubmed.ncbi.nlm.nih.gov/11258980/',
    },
  },
  {
    id: 'as-dust-cleaning', metals: ['As'], kind: 'control',
    from: '无机砷粉尘', to: '防止清扫扬尘', title: '清理含砷积尘时避免再次扬尘',
    finding: '美国职业安全与健康管理局的无机砷标准规定，受污染的地面和表面不得用压缩空气吹扫。采用吸尘设备时，使用和倒空集尘容器都要尽量减少粉尘回到工作区。',
    limit: '原条款适用于美国相关作业场所。现场可据此核查清洁工序，并按所在地要求选用设备。',
    studyType: '职业卫生标准', source: {
      title: '29 CFR 1910.1018 — Inorganic arsenic', issuer: '美国职业安全与健康管理局（OSHA）',
      locator: '第 (k)(2)–(3) 款，Cleaning floors 与 Vacuuming',
      url: 'https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1018#1910.1018(k)(2)',
    },
  },
  {
    id: 'crvi-chromate-lung', metals: ['Cr'], kind: 'health', topic: 'other',
    from: '六价铬', to: '肺癌死亡风险', title: '铬酸盐生产工人的六价铬暴露与肺癌死亡风险',
    finding: '一项铬酸盐生产工人队列研究用岗位监测和工龄估算累积六价铬暴露。随访显示，累积暴露越高，肺癌死亡风险越高；分析中考虑了入职时的吸烟情况。',
    limit: '研究针对特定工厂和六价铬。解释其他工艺的数据时，需要先分清铬的价态与接触途径。',
    studyType: '职业人群随访', source: {
      title: 'Lung cancer among workers in chromium chemical production', issuer: 'American Journal of Industrial Medicine',
      year: 2000, locator: '摘要，累积六价铬暴露与肺癌的比例风险模型',
      url: 'https://pubmed.ncbi.nlm.nih.gov/10893504/',
    },
  },
  {
    id: 'crvi-cell-chromosomes', metals: ['Cr'], kind: 'mechanism', topic: 'other',
    from: '六价铬', to: '染色体断裂', title: '六价铬可在实验条件下损伤染色体',
    finding: '在培养的人支气管上皮细胞和肺成纤维细胞中，恢复细胞内抗坏血酸水平后，研究人员观察到六价铬处理引起的染色体断裂增加。',
    limit: '细胞培养条件会影响实验结果。这项研究不能换算岗位安全界值，也不能用于指导维生素摄入。',
    studyType: '细胞实验', source: {
      title: 'Ascorbate acts as a highly potent inducer of chromate mutagenesis and clastogenesis: linkage to DNA breaks in G2 phase by mismatch repair',
      issuer: 'Nucleic Acids Research', year: 2007, locator: '摘要，支气管上皮细胞与肺成纤维细胞实验',
      url: 'https://doi.org/10.1093/nar/gkl1069',
    },
  },
  {
    id: 'crvi-plating-mist', metals: ['Cr'], kind: 'control',
    from: '六价铬电镀槽', to: '槽边捕集酸雾', title: '在电镀槽边捕集含六价铬的雾滴',
    finding: '镀槽表面的气泡破裂时，含六价铬的细小雾滴会进入空气。美国职业安全与健康管理局建议设计并维护局部排风，定期检查气流，减少雾滴进入作业者呼吸区。',
    limit: '这条措施对应产生含铬雾滴的电镀工序。焊接、喷涂等作业需要分别评估污染源与捕集方式。',
    studyType: '岗位防护指南', source: {
      title: 'Controlling Hexavalent Chromium Exposures during Electroplating', issuer: '美国职业安全与健康管理局（OSHA）',
      year: 2013, locator: '事实说明 FS-3648，第 2 页，Engineering controls 中的局部排风',
      url: 'https://www.osha.gov/sites/default/files/publications/OSHA_FS-3648_ELECTROPLATING.pdf#page=2',
    },
  },
  {
    id: 'ni-plating-eczema', metals: ['Ni'], kind: 'health', topic: 'other',
    from: '接触镍盐', to: '手部湿疹', title: '镀镍作业者的镍过敏与手部湿疹',
    finding: '芬兰研究人员调查了 38 家电镀厂的镀镍作业者。硫酸镍斑贴试验呈过敏反应的人中，七成报告当时或过去出现过手部湿疹。',
    limit: '斑贴试验反映对镍过敏。要确定手部湿疹是否与工作有关，还需核对接触时间、其他刺激物和皮肤情况。',
    studyType: '工作场所调查', source: {
      title: 'Hand dermatitis and allergic patch test reactions caused by nickel in electroplaters',
      issuer: 'Contact Dermatitis', year: 1997, locator: '摘要，硫酸镍斑贴试验和手部湿疹问卷',
      url: 'https://pubmed.ncbi.nlm.nih.gov/9145262/',
    },
  },
  {
    id: 'ni-refinery-lung', metals: ['Ni'], kind: 'health', topic: 'other',
    from: '精炼中的镍化合物', to: '肺癌发病', title: '镍精炼工人队列中的肺癌发病',
    finding: '挪威镍精炼工人队列在 1953 至 1993 年间观察到 203 例新发肺癌，按参照人群发病率预计约 68 例。研究还分别分析了镍的形态和吸烟情况。',
    limit: '人数比较反映整个历史队列。具体作业中往往同时接触多种镍化合物，吸烟也会影响肺癌风险。',
    studyType: '职业人群随访', source: {
      title: 'Exposure to nickel compounds and smoking in relation to incidence of lung and nasal cancer among nickel refinery workers',
      issuer: 'Occupational and Environmental Medicine', year: 1996, locator: '摘要，随访期间的观察与预期发病人数',
      url: 'https://pubmed.ncbi.nlm.nih.gov/8943837/',
    },
  },
  {
    id: 'ni-immune-receptor', metals: ['Ni'], kind: 'mechanism', topic: 'other',
    from: '镍离子', to: '免疫受体被激活', title: '镍离子可触发与接触过敏有关的免疫信号',
    finding: '实验发现，镍离子可直接激活人的免疫受体 TLR4，引起炎症信号。研究人员还在表达该人类受体的小鼠中观察到对镍的接触性过敏反应。',
    limit: '证据来自受体实验和转基因小鼠。判断个人是否对镍过敏，还需结合实际接触情况和临床检查。',
    studyType: '细胞与动物实验', source: {
      title: 'Crucial role for human Toll-like receptor 4 in the development of contact allergy to nickel',
      issuer: 'Nature Immunology', year: 2010, locator: '图 3 与图 6，人受体实验及转基因小鼠的接触反应',
      url: 'https://www.nature.com/articles/ni.1919',
    },
  },
  {
    id: 'ni-plating-mixing', metals: ['Ni'], kind: 'control',
    from: '含镍电镀槽', to: '改用液流搅拌', title: '调整镀镍槽的搅拌方式，减少含镍雾滴',
    finding: '英国职业健康与安全管理局资助的镀镍槽试验比较了不同控制方式。以泵推动槽液循环，替代向槽内鼓入空气，可降低镍向空气中的释放，试验中也减少了表面污染。',
    limit: '效果来自受控镀槽试验。改造前需要确认镀槽工艺相容，改造后再通过现场采样验证。',
    studyType: '工程控制试验', source: {
      title: 'Evaluating the efficacy of exposure controls used on electrolytic nickel plating lines',
      issuer: '英国职业健康与安全管理局（HSE）研究报告', year: 2022, locator: 'RR1184，执行摘要及 Eductors 搅拌试验结果',
      url: 'https://www.hse.gov.uk/research/assets/docs/rr1184.pdf',
    },
  },
]
