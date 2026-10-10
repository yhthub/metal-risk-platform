from typing import List, Dict, Any, Optional
from ..models.schemas import (
    InterventionPlan, InterventionLevel,
    WorkflowStep, OutcomeMetric
)


# 高危人群干预方案（二级预防）
HIGH_RISK_PLANS = [
    InterventionPlan(
        person_id="SZ-284",
        name="张伟",
        dept="第一熔炼车间",
        years=15,
        factors="Pb, As, Cd",
        score=68.5,
        level=InterventionLevel.LEVEL2,
        workflow=[
            WorkflowStep(
                title="紧急阻断与隔离",
                tag="暴露阻断",
                type="danger",
                desc="立即调离高暴露岗位，停止接触致病因子。",
                detail="从第一熔炼车间调至行政后勤岗位，彻底切断 Pb/As/Cd 暴露源。工服全部更换，进行全身去污淋浴。",
                indicator="脱离暴露环境后 1 周内复查血 Pb，预期开始下降",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="深度精准诊断",
                tag="精准诊断",
                type="primary",
                desc="进行全面的靶器官损伤评估和毒物蓄积量检测。",
                detail="全血 Pb、尿 Cd、尿 As 代谢物、肾功能全套、神经传导速度、肺功能、骨密度、头颅 MRI。",
                indicator="明确各金属蓄积水平及靶器官损伤程度",
                period="1-2 周",
                cost="中"
            ),
            WorkflowStep(
                title="EDTA 螯合驱铅治疗",
                tag="临床干预",
                type="danger",
                desc="对血 Pb > 400 μg/L 的患者实施 EDTA 钙钠螯合治疗。",
                detail="EDTA 钙钠 1g/m² 体表面积，加入 5% 葡萄糖 250ml 静脉滴注，连用 3 天停 4 天为一疗程。监测尿 Pb 排泄量。",
                indicator="疗程结束后血 Pb 下降 > 30%",
                period="3-4 个疗程",
                cost="中"
            ),
            WorkflowStep(
                title="靶器官保护治疗",
                tag="器官保护",
                type="warning",
                desc="针对已受损的肾脏和神经系统进行保护性治疗。",
                detail="肾脏保护：ACEI/ARB 类药物降低肾小球内压。神经保护：B 族维生素、神经生长因子。抗氧化：N-乙酰半胱氨酸。",
                indicator="3 个月后肾功能指标改善，神经传导速度恢复",
                period="6 个月",
                cost="中"
            ),
            WorkflowStep(
                title="高频疗效追踪",
                tag="疗效监测",
                type="primary",
                desc="治疗期间每周监测关键指标，评估治疗效果。",
                detail="每周复查血 Pb、肾功能。每月评估神经传导速度。记录症状改善情况。",
                indicator="连续 4 周血 Pb < 200 μg/L 为初步达标",
                period="每周/每月",
                cost="低"
            ),
            WorkflowStep(
                title="远期防控与康复",
                tag="远期防控",
                type="safe",
                desc="治愈后持续监测，防止复发和远期并发症。",
                detail="每 3 个月复查一次，持续 2 年。建立个人健康档案。提供营养指导和生活方式建议。",
                indicator="2 年内无复发，各器官功能稳定",
                period="2 年",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="血 Pb 浓度", before=85, after=35),
            OutcomeMetric(label="肾损伤风险", before=68.5, after=25),
            OutcomeMetric(label="神经毒性风险", before=62, after=20),
            OutcomeMetric(label="综合健康风险", before=68.5, after=25)
        ]
    ),
    InterventionPlan(
        person_id="SZ-105",
        name="李强",
        dept="第一熔炼车间",
        years=12,
        factors="Pb, As",
        score=62.1,
        level=InterventionLevel.LEVEL2,
        workflow=[
            WorkflowStep(
                title="紧急岗位调离",
                tag="暴露阻断",
                type="danger",
                desc="立即调离第一熔炼车间，切断 Pb/As 暴露源。",
                detail="调至质检或仓库岗位。工服全部更换消毒。",
                indicator="1 周后血 Pb 预期下降 10%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="全面健康评估",
                tag="精准诊断",
                type="primary",
                desc="评估 Pb/As 蓄积水平及靶器官损伤程度。",
                detail="血 Pb、尿 As 代谢物、肝肾功能、神经传导、肺功能。",
                indicator="明确损伤分级",
                period="1-2 周",
                cost="中"
            ),
            WorkflowStep(
                title="驱铅+抗氧化治疗",
                tag="临床干预",
                type="danger",
                desc="EDTA 螯合驱铅联合抗氧化治疗。",
                detail="EDTA 钙钠静脉滴注 + 维生素 C 1000mg/日 + N-乙酰半胱氨酸 600mg/日。",
                indicator="治疗后血 Pb 下降 > 25%",
                period="3 个疗程",
                cost="中"
            ),
            WorkflowStep(
                title="神经系统保护",
                tag="器官保护",
                type="warning",
                desc="针对砷暴露导致的周围神经病变进行保护。",
                detail="B 族维生素、α-硫辛酸、神经生长因子注射。",
                indicator="神经传导速度改善",
                period="3-6 个月",
                cost="中"
            ),
            WorkflowStep(
                title="定期复查",
                tag="疗效监测",
                type="primary",
                desc="治疗期间密切监测各项指标。",
                detail="每 2 周复查血 Pb、尿 As。每月评估肝肾功能。",
                indicator="连续 3 个月指标稳定下降",
                period="每 2 周",
                cost="低"
            ),
            WorkflowStep(
                title="长期随访",
                tag="远期防控",
                type="safe",
                desc="治愈后持续随访 2 年。",
                detail="每季度复查一次。提供营养和生活方式指导。",
                indicator="2 年内无复发",
                period="2 年",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="血 Pb 浓度", before=72, after=30),
            OutcomeMetric(label="尿 As 浓度", before=58, after=22),
            OutcomeMetric(label="神经毒性风险", before=62.1, after=22),
            OutcomeMetric(label="综合健康风险", before=62.1, after=22)
        ]
    ),
    InterventionPlan(
        person_id="SZ-032",
        name="王刚",
        dept="原矿粉碎区",
        years=18,
        factors="Pb, Cd, Hg",
        score=55.4,
        level=InterventionLevel.LEVEL2,
        workflow=[
            WorkflowStep(
                title="岗位轮换",
                tag="暴露阻断",
                type="danger",
                desc="调离原矿粉碎区，切断多金属暴露源。",
                detail="轮换至低暴露岗位。工服全面更换。",
                indicator="脱离暴露后体内金属蓄积开始代谢",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="多金属蓄积评估",
                tag="精准诊断",
                type="primary",
                desc="全面评估 Pb/Cd/Hg 三种金属的蓄积水平。",
                detail="血 Pb、尿 Cd、尿 Hg、肾功能全套、骨密度、神经传导。",
                indicator="明确各金属蓄积量和靶器官损伤",
                period="1-2 周",
                cost="中"
            ),
            WorkflowStep(
                title="综合螯合治疗",
                tag="临床干预",
                type="danger",
                desc="针对多种金属蓄积进行综合螯合治疗。",
                detail="EDTA 驱铅 + 二巯丁二酸(DMSA)驱汞。分阶段进行。",
                indicator="各金属水平下降 > 30%",
                period="4-6 个疗程",
                cost="高"
            ),
            WorkflowStep(
                title="肾脏保护",
                tag="器官保护",
                type="warning",
                desc="Cd/Hg 对肾脏损伤风险高，需重点保护。",
                detail="ACEI/ARB 降压护肾。优质低蛋白饮食。避免肾毒性药物。",
                indicator="肾功能指标稳定或改善",
                period="6-12 个月",
                cost="中"
            ),
            WorkflowStep(
                title="密集监测",
                tag="疗效监测",
                type="primary",
                desc="治疗期间每周监测关键指标。",
                detail="每周复查血/尿金属水平。每月评估肾功能。",
                indicator="指标持续下降",
                period="每周",
                cost="低"
            ),
            WorkflowStep(
                title="长期康复",
                tag="远期防控",
                type="safe",
                desc="治愈后长期随访，重点关注肾功能和骨骼健康。",
                detail="每 3 个月复查。补充钙和维生素 D。定期骨密度检测。",
                indicator="3 年内无复发",
                period="3 年",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="血 Pb 浓度", before=65, after=25),
            OutcomeMetric(label="尿 Cd 浓度", before=55, after=20),
            OutcomeMetric(label="尿 Hg 浓度", before=42, after=15),
            OutcomeMetric(label="综合健康风险", before=55.4, after=20)
        ]
    ),
    InterventionPlan(
        person_id="SZ-142",
        name="刘明",
        dept="尾气处理组",
        years=10,
        factors="As, Cr",
        score=48.2,
        level=InterventionLevel.LEVEL2,
        workflow=[
            WorkflowStep(
                title="防护装备升级",
                tag="暴露阻断",
                type="warning",
                desc="升级至 P100 级别呼吸防护，减少 As/Cr 吸入。",
                detail="配发半面罩+P100 滤盒、防化手套。培训正确使用方法。",
                indicator="防护依从率 > 95%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="As/Cr 基线检测",
                tag="精准诊断",
                type="primary",
                desc="评估当前 As/Cr 暴露水平。",
                detail="尿 As 代谢物、尿 Cr、肝肾功能、肺功能、皮肤科筛查。",
                indicator="明确暴露水平和损伤程度",
                period="1-2 周",
                cost="低"
            ),
            WorkflowStep(
                title="抗氧化+维生素 C 治疗",
                tag="临床干预",
                type="warning",
                desc="大剂量维生素 C 将六价 Cr 还原为三价 Cr，同时抗氧化。",
                detail="维生素 C 2000mg/日 + N-乙酰半胱氨酸 600mg/日 + 优质蛋白饮食。",
                indicator="3 个月后尿 Cr 预期下降 20%",
                period="3-6 个月",
                cost="低"
            ),
            WorkflowStep(
                title="皮肤健康监测",
                tag="专项筛查",
                type="primary",
                desc="砷可致皮肤癌，需定期皮肤科检查。",
                detail="每 3 个月皮肤科检查，排查角化、色素异常。发现异常立即活检。",
                indicator="无新发病灶",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="季度复查",
                tag="疗效监测",
                type="primary",
                desc="定期监测 As/Cr 水平和靶器官功能。",
                detail="每 3 个月复查尿 As、尿 Cr、肝肾功能、肺功能。",
                indicator="连续 4 个季度指标稳定",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="长期健康监护",
                tag="远期防控",
                type="safe",
                desc="建立个人健康档案，长期随访。",
                detail="每年全面体检。重点关注肺功能和皮肤健康。",
                indicator="5 年内无职业病发生",
                period="5 年",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="尿 As 浓度", before=48, after=22),
            OutcomeMetric(label="尿 Cr 浓度", before=38, after=18),
            OutcomeMetric(label="肺功能风险", before=42, after=15),
            OutcomeMetric(label="综合健康风险", before=48.2, after=18)
        ]
    )
]


# 中危人群干预方案（一级预防）
MEDIUM_RISK_PLANS = [
    InterventionPlan(
        person_id="SZ-089",
        name="赵铁柱",
        dept="原矿粉碎区",
        years=11,
        factors="Cd, Cr",
        score=41.5,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="岗位轮换与暴露时间管控",
                tag="暴露阻断",
                type="warning",
                desc="实施轮岗制度，将高暴露岗位连续作业时间缩短至 4 小时以内。",
                detail="与低暴露岗位（质检、仓库）轮换，每 2 周轮换一次。工间在通风良好区域休息 30 分钟以上。",
                indicator="1 个月后复查尿 Cd，预期下降 10-15%",
                period="长期执行",
                cost="低"
            ),
            WorkflowStep(
                title="Cd/Cr 暴露基线评估",
                tag="健康筛查",
                type="primary",
                desc="检测尿镉、尿铬及肾功能早期标志物，建立个人暴露基线。",
                detail="尿 Cd、尿 Cr、尿 β2-微球蛋白、尿 NAG 酶、血常规、肝肾功能、尿常规。",
                indicator="尿 Cd > 3 μg/g Cr 或 β2-微球蛋白 > 200 μg/L 需升级管理",
                period="3-5 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="标准防护装备配发",
                tag="个人防护",
                type="warning",
                desc="配发 KN95 口罩、防护手套、护目镜，培训正确佩戴方法。",
                detail="由安全员现场指导佩戴，确保面部密合。每周检查口罩使用状况，每月更换滤芯。",
                indicator="防护依从率 > 90%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="钙锌营养拮抗方案",
                tag="营养干预",
                type="safe",
                desc="每日服用钙锌补充剂，食堂增设高钙高锌菜品。",
                detail="钙片 600mg + 锌 15mg/日。食堂每日供应牛奶、豆腐、虾皮。果胶膳食纤维辅助排毒。",
                indicator="3 个月后复查尿 Cd，结合轮岗效果综合评估",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="季度常规体检",
                tag="定期监测",
                type="primary",
                desc="每 3 个月复查尿 Cd、尿 Cr 及肾功能指标。",
                detail="检查项目：尿 Cd、尿 Cr、尿 β2-微球蛋白、肝肾功能。连续 2 次异常者升级为高危管理。",
                indicator="连续 4 个季度指标稳定或下降为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="职业卫生知识培训",
                tag="健康教育",
                type="safe",
                desc="参加职业危害防护培训，掌握个人卫生规范与防护要点。",
                detail="培训内容：重金属危害认知、正确佩戴口罩、工后淋浴更衣、禁止车间进食。每半年复训一次。",
                indicator="培训考核通过率 100%",
                period="每半年一次",
                cost="极低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="尿 Cd 浓度", before=42, after=28),
            OutcomeMetric(label="尿 Cr 浓度", before=35, after=22),
            OutcomeMetric(label="肾损伤风险", before=30, after=18),
            OutcomeMetric(label="综合健康风险", before=41.5, after=25)
        ]
    ),
    InterventionPlan(
        person_id="SZ-311",
        name="陈刚",
        dept="第一熔炼车间",
        years=9,
        factors="Pb, As",
        score=36.8,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="工位通风改善",
                tag="环境控制",
                type="warning",
                desc="在工位加装局部排风罩，降低 Pb/As 粉尘吸入浓度。",
                detail="安装便携式负压排风罩，连接粉尘收集池。每日开工前检查排风系统运行状态。",
                indicator="工位粉尘浓度下降 > 50%",
                period="1-2 周安装",
                cost="中"
            ),
            WorkflowStep(
                title="Pb/As 基线检测",
                tag="健康筛查",
                type="primary",
                desc="检测全血铅和尿砷代谢物，评估当前内暴露水平。",
                detail="全血 Pb、尿 As（含无机砷/有机砷比值）、肝功能、血常规。",
                indicator="血 Pb > 200 μg/L 或尿 As > 50 μg/L 需加强干预",
                period="3-5 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="维生素 C 与抗氧化补充",
                tag="营养干预",
                type="safe",
                desc="每日补充维生素 C 1000mg，促进铅排泄并抗氧化。",
                detail="维生素 C 可将六价铬还原为三价铬，同时加速铅的排泄。配合优质蛋白饮食。",
                indicator="3 个月后血 Pb 预期下降 10-15%",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="个人卫生规范强化",
                tag="行为干预",
                type="warning",
                desc="严格执行工后淋浴、工服单独清洗、禁止车间进食。",
                detail="设置更衣淋浴区，工服由企业统一清洗。洗手后方可进食饮水。",
                indicator="卫生规范依从率 > 95%",
                period="长期执行",
                cost="极低"
            ),
            WorkflowStep(
                title="季度血铅监测",
                tag="定期监测",
                type="primary",
                desc="每 3 个月复查全血 Pb 和尿 As，追踪暴露趋势。",
                detail="建立个人纵向趋势图。连续 2 次上升趋势需升级为高危管理并安排深度体检。",
                indicator="连续 4 个季度血 Pb < 200 μg/L 为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="年度职业健康体检",
                tag="综合评估",
                type="safe",
                desc="每年一次全面体检，含神经传导速度和肺功能检测。",
                detail="依据《职业健康监护技术规范》(GBZ 188) 执行，含纯音听力、神经传导、肺功能等。",
                indicator="体检结果归入个人健康档案",
                period="每年一次",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="血 Pb 浓度", before=55, after=30),
            OutcomeMetric(label="尿 As 浓度", before=42, after=25),
            OutcomeMetric(label="肝损伤风险", before=28, after=15),
            OutcomeMetric(label="综合健康风险", before=36.8, after=20)
        ]
    ),
    InterventionPlan(
        person_id="SZ-402",
        name="孙磊",
        dept="尾气处理组",
        years=8,
        factors="As, Ni",
        score=32.1,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="防护装备升级",
                tag="个人防护",
                type="warning",
                desc="配发半面罩+P100滤盒和防化手套，强化呼吸与皮肤防护。",
                detail="尾气处理岗位 As/Ni 粉尘浓度较高，需升级至 P100 级别防护。每周检查面罩密合性。",
                indicator="2 周后尿 As 预期下降 10%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="As/Ni 基线检测",
                tag="健康筛查",
                type="primary",
                desc="检测尿砷代谢物和尿镍浓度，评估实际内暴露水平。",
                detail="尿总砷、无机砷比值、尿 Ni、肝功、皮肤科筛查（砷角化）。",
                indicator="无机砷占比 > 15% 或尿 Ni > 30 μg/L 需重点关注",
                period="3-5 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="高钙锌膳食方案",
                tag="营养干预",
                type="safe",
                desc="食堂增设高钙高锌菜品，发放钙锌补充剂。",
                detail="钙片 600mg + 锌 15mg/日。增加牛奶、豆制品、海产品摄入。",
                indicator="3 个月后复查暴露指标",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="皮肤健康监测",
                tag="专项筛查",
                type="primary",
                desc="每 6 个月进行皮肤科检查，排查砷相关皮肤病变。",
                detail="重点检查掌跖角化、皮肤色素异常、 Bowen 病等癌前病变。发现异常立即活检。",
                indicator="无新发角化灶或色素异常",
                period="每 6 个月",
                cost="低"
            ),
            WorkflowStep(
                title="季度常规体检",
                tag="定期监测",
                type="primary",
                desc="每 3 个月复查尿 As、尿 Ni 和肝功能。",
                detail="建立个人暴露趋势档案。连续 2 次异常者升级管理。",
                indicator="连续 4 个季度指标稳定为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="戒烟限酒指导",
                tag="行为干预",
                type="safe",
                desc="提供戒烟限酒咨询，吸烟会加重呼吸道对 As 粉尘的吸收。",
                detail="研究显示吸烟工人重金属暴露风险升高 15-20%。提供尼古丁替代疗法支持。",
                indicator="吸烟者戒烟或减量 > 50%",
                period="持续跟踪",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="尿 As 浓度", before=40, after=22),
            OutcomeMetric(label="尿 Ni 浓度", before=32, after=18),
            OutcomeMetric(label="皮肤病变风险", before=25, after=12),
            OutcomeMetric(label="综合健康风险", before=32.1, after=18)
        ]
    ),
    InterventionPlan(
        person_id="SZ-175",
        name="周波",
        dept="第一熔炼车间",
        years=7,
        factors="Pb",
        score=28.5,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="标准防护配发",
                tag="个人防护",
                type="warning",
                desc="配发 KN95 口罩和防护手套，培训正确使用方法。",
                detail="每日上岗前自检口罩密合性。工服由企业统一清洗，禁止带回家中。",
                indicator="防护依从率 > 90%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="血铅基线检测",
                tag="健康筛查",
                type="primary",
                desc="检测全血铅浓度和血常规，评估当前铅暴露水平。",
                detail="全血 Pb、血常规（关注网织红细胞、点彩红细胞）、锌原卟啉(ZPP)。",
                indicator="血 Pb > 150 μg/L 需加强干预",
                period="1-3 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="钙锌竞争性营养补充",
                tag="营养干预",
                type="safe",
                desc="每日服用钙锌补充剂，通过竞争性吸收减少铅摄入。",
                detail="钙片 600mg + 锌 15mg/日。增加牛奶、豆制品摄入。",
                indicator="3 个月后血 Pb 预期下降 10%",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="个人卫生规范",
                tag="行为干预",
                type="warning",
                desc="工后淋浴更衣，禁止在车间进食饮水。",
                detail="洗手后方可进食。工服与日常衣物分开清洗。",
                indicator="卫生规范执行率 100%",
                period="长期执行",
                cost="极低"
            ),
            WorkflowStep(
                title="季度血铅监测",
                tag="定期监测",
                type="primary",
                desc="每 3 个月复查全血 Pb，追踪暴露趋势。",
                detail="建立个人血铅趋势图。若连续 2 次上升，升级为中高危管理。",
                indicator="连续 4 个季度血 Pb < 150 μg/L 为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="年度职业健康体检",
                tag="综合评估",
                type="safe",
                desc="每年全面体检，含神经系统和肾功能评估。",
                detail="依据 GBZ 188 执行，含血常规、肝肾功能、神经传导速度、纯音听力。",
                indicator="体检结果归入健康档案",
                period="每年一次",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="血 Pb 浓度", before=35, after=18),
            OutcomeMetric(label="血液系统风险", before=22, after=10),
            OutcomeMetric(label="神经毒性风险", before=20, after=10),
            OutcomeMetric(label="综合健康风险", before=28.5, after=15)
        ]
    ),
    InterventionPlan(
        person_id="SZ-219",
        name="吴涛",
        dept="原矿粉碎区",
        years=6,
        factors="Cd, Hg",
        score=24.2,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="防护装备配发",
                tag="个人防护",
                type="warning",
                desc="配发 KN95 口罩、防化手套，强化呼吸与皮肤防护。",
                detail="粉碎区粉尘浓度较高，需确保口罩密合性。每周检查更换滤芯。",
                indicator="防护依从率 > 90%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="Cd/Hg 基线检测",
                tag="健康筛查",
                type="primary",
                desc="检测尿镉和尿汞，评估两种金属的蓄积水平。",
                detail="尿 Cd、尿 Hg、尿 β2-微球蛋白、肾功能全套。",
                indicator="尿 Cd > 2 μg/g Cr 或尿 Hg > 10 μg/L 需重点关注",
                period="3-5 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="高钙膳食方案",
                tag="营养干预",
                type="safe",
                desc="增加高钙食品摄入，竞争性减少 Cd/Hg 肠道吸收。",
                detail="每日牛奶 500ml、豆腐或虾皮。补充维生素 C 500mg/日。",
                indicator="3 个月后复查尿 Cd/Hg",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="肾功能定期监测",
                tag="定期监测",
                type="primary",
                desc="每 3 个月检测尿 Cd、尿 Hg 和肾功能早期标志物。",
                detail="尿 Cd、尿 Hg、尿 β2-微球蛋白、尿常规。建立个人趋势图。",
                indicator="连续 4 个季度指标稳定为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="个人卫生强化",
                tag="行为干预",
                type="warning",
                desc="工后淋浴更衣，工服单独清洗，禁止车间进食。",
                detail="粉碎区粉尘易附着衣物，必须更换清洁衣物后方可离开。",
                indicator="卫生规范执行率 100%",
                period="长期执行",
                cost="极低"
            ),
            WorkflowStep(
                title="年度综合体检",
                tag="综合评估",
                type="safe",
                desc="每年全面体检，重点关注肾功能和神经系统。",
                detail="含肾功能、神经传导速度、纯音听力、血常规等。",
                indicator="体检结果归入健康档案",
                period="每年一次",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="尿 Cd 浓度", before=28, after=15),
            OutcomeMetric(label="尿 Hg 浓度", before=22, after=12),
            OutcomeMetric(label="肾损伤风险", before=18, after=8),
            OutcomeMetric(label="综合健康风险", before=24.2, after=12)
        ]
    ),
    InterventionPlan(
        person_id="SZ-056",
        name="郑凯",
        dept="尾气处理组",
        years=5,
        factors="Cr",
        score=18.6,
        level=InterventionLevel.LEVEL1,
        workflow=[
            WorkflowStep(
                title="工位通风改善",
                tag="环境控制",
                type="warning",
                desc="在尾气处理工位加装局部排风，降低铬粉尘浓度。",
                detail="安装移动式排风除尘设备，配合湿式操作减少粉尘扬起。",
                indicator="工位 Cr 浓度下降 > 40%",
                period="1-2 周",
                cost="中"
            ),
            WorkflowStep(
                title="Cr 暴露基线检测",
                tag="健康筛查",
                type="primary",
                desc="检测尿铬浓度和肺功能，评估当前暴露水平。",
                detail="尿 Cr、血常规、肝肾功能、肺功能检测、胸部 X 线。",
                indicator="尿 Cr > 30 μg/L 或肺功能异常需加强干预",
                period="1-3 个工作日",
                cost="低"
            ),
            WorkflowStep(
                title="维生素 C 抗氧化补充",
                tag="营养干预",
                type="safe",
                desc="每日补充维生素 C 1000mg，将六价铬还原为低毒三价铬。",
                detail="维生素 C 是铬中毒的关键拮抗剂。配合优质蛋白饮食。",
                indicator="3 个月后复查尿 Cr",
                period="长期维持",
                cost="极低"
            ),
            WorkflowStep(
                title="呼吸防护强化",
                tag="个人防护",
                type="warning",
                desc="配发 KN95 口罩，培训正确佩戴方法。",
                detail="铬粉尘主要经呼吸道吸入，确保口罩密合性是关键。",
                indicator="防护依从率 > 95%",
                period="即刻执行",
                cost="低"
            ),
            WorkflowStep(
                title="季度常规体检",
                tag="定期监测",
                type="primary",
                desc="每 3 个月复查尿 Cr 和肺功能。",
                detail="建立个人暴露趋势档案。连续 2 次异常升级管理。",
                indicator="连续 4 个季度尿 Cr < 20 μg/L 为达标",
                period="每 3 个月",
                cost="低"
            ),
            WorkflowStep(
                title="年度综合体检",
                tag="综合评估",
                type="safe",
                desc="每年全面体检，含肺功能和皮肤科检查。",
                detail="铬可致鼻中隔穿孔和皮肤溃疡，年度体检需专项排查。",
                indicator="体检结果归入健康档案",
                period="每年一次",
                cost="低"
            )
        ],
        outcomes=[
            OutcomeMetric(label="尿 Cr 浓度", before=20, after=10),
            OutcomeMetric(label="肺功能风险", before=15, after=6),
            OutcomeMetric(label="皮肤病变风险", before=12, after=5),
            OutcomeMetric(label="综合健康风险", before=18.6, after=8)
        ]
    )
]


async def get_intervention_plan(person_id: str) -> Optional[InterventionPlan]:
    """获取个人干预方案"""
    # 先查高危人群
    for plan in HIGH_RISK_PLANS:
        if plan.person_id == person_id:
            return plan

    # 再查中危人群
    for plan in MEDIUM_RISK_PLANS:
        if plan.person_id == person_id:
            return plan

    return None


async def get_all_plans(level: InterventionLevel = None) -> List[InterventionPlan]:
    """获取所有干预方案"""
    if level == InterventionLevel.LEVEL2:
        return HIGH_RISK_PLANS
    elif level == InterventionLevel.LEVEL1:
        return MEDIUM_RISK_PLANS
    else:
        return HIGH_RISK_PLANS + MEDIUM_RISK_PLANS


async def get_high_risk_plans() -> List[InterventionPlan]:
    """获取高危人群干预方案"""
    return HIGH_RISK_PLANS


async def get_medium_risk_plans() -> List[InterventionPlan]:
    """获取中危人群干预方案"""
    return MEDIUM_RISK_PLANS
