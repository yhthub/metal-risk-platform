# 面向职业金属复合暴露的智能干预推荐与决策支持系统

## 项目概述

本系统面向职业卫生与流行病学研究场景，融合环境监测、流行病学调查及多组学数据，构建基于因果推理的重金属健康风险评估与干预推荐模型。系统覆盖"暴露数据接入 → 多维可视化分析 → 风险量化预警 → 因果知识推理 → 智能干预策略生成 → 知识库问答"全链路决策支持。

## 技术栈

| 类别 | 技术 |
|------|------|
| 框架 | Nuxt 4 + Vue 3 (Composition API) |
| 构建 | Vite 7 |
| CSS | Tailwind CSS 4 + SCSS |
| UI 组件 | Element Plus (自动导入) |
| 可视化 | ECharts 6 |
| 包管理 | pnpm |
| 语言 | TypeScript |

## 系统架构

```
my-nuxt-app/
├── pages/                           # 页面路由 (Nuxt 文件路由)
│   ├── index.vue                    # 系统首页 Landing Page
│   ├── datainput/index.vue          # 职业暴露数据接入与特征工程
│   ├── risk/
│   │   ├── index.vue                # 风险量化与预警控制台
│   │   └── report.vue               # 全员风险评估深度报告
│   ├── causal/index.vue             # 因果知识推理 全景 DAG
│   ├── plan/
│   │   ├── index.vue                # 智能干预与阻断策略推荐
│   │   └── specplan.vue             # 个人化干预方案报告
│   └── agent/index.vue              # RAG 知识库智能问答助手
├── components/
│   └── Sidebar.vue                  # 全局侧边导航组件
├── assets/css/app.css               # 全局样式
├── app.vue                          # 根组件（含 KeepAlive 页面缓存）
├── nuxt.config.ts                   # Nuxt 配置
└── .claude/                         # Claude Code 配置与技能
```

## 功能模块

### 1. 系统首页 (`/`)

项目门户页面，展示系统核心能力与学术定位。

- 顶部固定导航栏（评估模型 / 数据视图 / 因果图谱 / 系统文档）
- 全屏 Hero 区域：项目标题、副标题、核心使命标识
- 重金属元素浮动粒子背景动画（Pb、Hg、Cr、Cd、As、Ni、Zn、Cu、Mn、V 共 10 种）
- 数据波形粒子 SVG 动画
- 三组核心能力展示卡片（含 CSS 3D 透视交互、SVG 动画、因果推断网络可视化）
- 系统闭环声明：风险识别 → 因果解析 → 干预推荐 → 效果反馈
- 页脚含四大链接分区

### 2. 数据接入与特征工程 (`/datainput`)

职业暴露数据的结构化录入、批量导入与多维度可视化分析。本页面为系统数据流起点。

- **管道步骤指示器**（3 步）：数据接入配置 → 多维可视化分析 → 风险推理模型
- **工种选择**：冶炼工 / 采矿工 / 电焊工 / 其他
- **单人录入模式**：
  - 基础个体档案（ID、性别、年龄、暴露工龄）+ 个体影响因素（学历、婚姻状况、吸烟情况、饮酒情况、BMI、防护装备使用、既往职业病史）
  - 8 种核心重金属暴露指标（Pb、Cd、Hg、Th、Li、Cr、Ni、Co），单位自适应（μg/L、μg/g）
  - 伴生非金属与标志物（As、Rn）+ LIS 体检报告上传
  - 临床监测基线参考面板（10 项安全阈值）
- **群体导入模式**：CSV/XLSX 拖拽上传，解析 1,245 条样本特征数据
- **人口学特征统计行**（3 张 ECharts 图表）：
  - 婚姻状况分布（嵌套环形饼图）：已婚/未婚/离异/丧偶
  - 文化程度构成（横向柱状图）：小学及以下 → 硕士及以上 6 级
  - 家庭年收入分布（堆叠柱状图）：<3万 ~ >20万 6 段，男/女分色
- **群体可视化仪表盘**（8 张 ECharts 图表）：
  - KPI 概览卡片（总人数 1,245、男性 856 人/68.7%、女性 389 人/31.3%）
  - 特征共线性矩阵（Correlation Heatmap）
  - 核心暴露分布四分位数（Quartiles）
  - 特征分布与异常离群点（Boxplot）
  - 主成分降维特征聚类（PCA Projection）
  - 数据检出率与缺失评估（LOD Analysis）
  - 核密度平滑分布（Density Smooth）
  - 群体暴露浓度频数分布直方图（Concentration Histogram）
  - 工龄-年龄-暴露水平画像（Bubble Chart）
- **个体可视化仪表盘**（6 张 ECharts 图表）：
  - 个体多维暴露全景画像（Relative Exposure Index 柱状图）
  - 靶向因子偏移雷达图（Radar）
  - 核心指标纵向时间序列（Longitudinal）
  - 暴露特征群体排位（Percentiles）
  - 靶器官风险归因拆解（嵌套环形图）
  - 特征标准化偏离度（Z-Score）+ 多维异常综合指数（Anomaly Index 仪表盘）

### 3. 风险量化与预警 (`/risk`)

基于 20 种预训练模型的风险评估与综合预警控制台。

- **管道步骤**：全流程打勾完成态
- **数据源挂载**：单文件 `第一熔炼车间_全体环境与生物监测表.csv`（closable 标签），"查看特征明细"跳转 datainput 页面
- **模型选择器**：20 种预训练模型（filterable 下拉选择），涵盖六大类：
  - 机器学习：XGBoost、LightGBM、Random Forest、CatBoost、Elastic Net、GAM
  - 深度学习：DNN、SHAP-Integrated MLP、DeepSurv、AFT-NN
  - 因果推断：G-computation、QG-Comp、TMLE、Causal Forest
  - 贝叶斯：BKMR、Bayesian Network、BKMR-CS
  - 生存分析：Cox-PH、Weibull-AFT
  - 集成框架：SuperLearner
- **深度推理过程可视化**：5 步推理链，可展开/折叠
- **综合预警定级**：重大规模健康风险预警横幅
- **ECharts 可视化矩阵**：
  - 特异性高危易感人群预警榜（Top 10，横向柱状图）
  - 高危预警对象人群占比（Gauge 仪表盘，显示 10 人）
  - 致病元凶权重榜（BKMR 特征重要性玫瑰图）
  - 毒物剂量-致病突变曲线（Dose-Response Sigmoid 曲线）
  - 高发职业病靶向预测（Progress Bar）
  - 双毒物协同放大效应（Joint Exposure 热力图）
  - SHAP 特征归因贡献条形图（正负双向）
- **模型字典页脚**：20 个预训练模型的详细介绍
- **底部操作**：下载风险评估报告 / 针对高危名单生成智能阻断策略

### 4. 风险评估深度报告 (`/risk/report`)

面向打印输出的正式风险评估长卷报告。数据与 risk 页面同步（SZ-284 为首要高危人员，10 人花名册）。

- A4 纸样式布局 + 防伪水印背景
- **高危人员排查清单**：10 人花名册表格（工号与 risk 预警榜一致），按等级着色
- **首要高危人员 (SZ-284) 综合靶器官预测**：仪表盘 68.5% + 4 项疾病概率条形
- **重金属暴露结构与 SHAP 归因**：雷达图 + 10 项因子贡献条形图
- **毒物剂量-致病突变曲线**：与 risk 页面一致的 Sigmoid 曲线
- **双毒物协同放大效应**：与 risk 页面一致的热力图
- 系统算法签名行 + 打印/存档按钮

### 5. 因果知识推理 (`/causal`)

全景多模态复合暴露有向无环图（DAG）可视化与反事实推演。

- **全局控制栏**：
  - 暴露因子选择（10 种金属多选）
  - 目标疾病靶点（5 种多选）
  - 群体暴露年限滑块（1-30 年）
  - 人群分组单选（成人 / 儿童 / 老人）
- **KPI 指标卡片**（4 张）：综合因果风险评分、主导致病因子、推断置信度、最优干预优先级
- **核心 DAG 视口**：ECharts 渲染 30+ 节点 5 层结构，35+ 因果连线，粒子流动动画，缩放/平移/详情抽屉
- **反事实因果推演沙盘**：10 种金属滑块 + 抗氧化/EDTA 开关，实时计算干预收益
- **筛选联动**：控制栏 → KPI → DAG 全局联动

### 6. 智能干预策略推荐 (`/plan`)

基于风险预警结果的个人化干预方案系统，按预防级别分类推荐。

- **全链路状态核验**：4 步管道 + 数据文件挂载 + 提交人/时间
- **预警人群分级选择器**：
  - 二级预防（高危 4 人）：SZ-284、SZ-105、SZ-032、SZ-142（因果风险增幅 > 45%）
  - 一级预防（中危 6 人）：SZ-089、SZ-311、SZ-402、SZ-175、SZ-219、SZ-056
- **高危人群个人化干预流程**（二级预防）：
  - 每人独立的步骤式工作流（5-6 步），包含：紧急阻断 → 精准诊断 → 临床干预 → 靶器官保护 → 疗效追踪 → 远期防控
  - 每步含：具体操作、关键指标、时间周期、费用
  - 底部预期成效对比条形图（before → after）
  - 配色：红色/危险色系
- **中危人群个人化干预流程**（一级预防）：
  - 每人独立的步骤式工作流（6 步），包含：环境控制 → 健康筛查 → 营养干预 → 行为干预 → 定期监测 → 综合评估
  - 配色：琥珀/暖黄色系
- **核心致病机制靶向阻断验证网络**：SVG DAG 干预阻断可视化
- **底部操作**：导出当前选中人员干预报告 / 预案推送至 EHS / 一键下发至 HIS
- **页面状态保持**：通过 `<NuxtPage :keepalive="{}" />` 实现返回时不重新生成方案

### 7. 个人化干预方案报告 (`/plan/specplan`)

个人化干预方案的详细报告页面，根据路由参数 `?person=SZ-284` 加载对应人员数据。

- A4 纸样式布局 + 防伪水印背景
- **干预对象基本信息**：工号、姓名、部门、工龄、风险因子、因果风险增幅（Descriptions 组件）
- **干预目标**：根据每个人的 outcomes 自动生成
- **干预实施流程**：完整展示该人员的所有 workflow 步骤（具体操作 + 关键指标 + 周期 + 费用）
- **预期干预成效**：before→after 条形图 + 降幅百分比
- **AI 推荐算法依据**：根据 level 动态显示推荐逻辑 + ECharts 雷达图
- 内置全部 10 人（4 高危 + 6 中危）的完整干预方案数据
- 审核签名 + 打印/导出按钮

### 8. RAG 知识库问答助手 (`/agent`)

基于检索增强生成的智能知识问答与决策溯源助手。

- **模型切换**（el-select 下拉，20 种模型与 risk 页面同步）：XGBoost、DNN、LightGBM、G-computation、BKMR、Random Forest 等
- **知识库多选挂载**：9 个毒理学数据库可多选（el-checkbox），默认选中前 2 个
  - 职业重金属复合暴露因果库、IARC 致癌物风险评级报告、WHO IPCS、ToxNet、NHANES、CTD、EPA/ATSDR、职业病临床诊疗指南、PubMed
  - 至少保留 1 个知识库，支持自定义上传（.pdf/.md）
- **欢迎页界面**：
  - Hero 区域 + 已挂载知识库数量标签
  - 输入框 + 知识库多选器
  - 深度思考开关 + 联网检索按钮 + 附件上传
  - 3 个快捷提问入口
- **对话界面**：
  - 消息列表：用户气泡（蓝色）+ AI 气泡（白色）
  - 已结合检索源显示所有已选知识库
  - 深度思考过程可展开/折叠
  - 结构化知识卡片（暴露源、分子机制、生物标志物、靶器官、证据等级）
  - **智能推荐知识库**：根据用户提问内容，自动推荐未选中的相关知识库（蓝色可点击标签 + 推荐理由）
  - 消息操作栏（复制/重新生成/赞/踩）
- **模拟知识库**：内置 Pb、As、Cd、Hg 四种重金属的毒理数据
- Toast 通知系统

## 数据流

```
数据接入 (datainput)
  │  单人录入 (含影响因素: 学历/婚姻/吸烟/饮酒/BMI/防护/病史)
  │  群体 CSV/XLSX 导入 (1,245 条样本)
  │  人口学特征统计 (婚姻/学历/收入)
  │  8 种核心重金属 + 2 种伴生标志物
  ▼
风险量化预警 (risk)
  │  20 种预训练模型可选
  │  5 步推理链 (特征张量 → G-computation → BKMR → 风险筛查 → DAG)
  │  高危易感 Top 10 识别 (SZ-284 等)
  │  → 深度报告 (risk/report) 打印输出
  ▼
因果知识推理 (causal)
  │  10 种金属全景 DAG (5 层结构)
  │  反事实推演沙盘 (10 金属滑块 + 抗氧化/EDTA 开关)
  ▼
智能干预策略 (plan)
  │  二级预防 (高危 4 人): 个人化临床干预流程
  │  一级预防 (中危 6 人): 个人化健康教育流程
  │  → 方案详情 (plan/specplan) 打印输出
  ▼
知识库问答 (agent)
  20 种模型 + 9 大毒理数据库多选 + 智能推荐知识库 + 深度推理
```

## 部署指南

### 环境要求

| 依赖 | 最低版本 | 推荐版本 |
|------|----------|----------|
| Node.js | 18.0+ | 20.x LTS |
| pnpm | 8.0+ | 9.x |
| 操作系统 | Windows 10+ / macOS 12+ / Ubuntu 20.04+ | - |

### 全新设备部署步骤

#### 1. 安装 Node.js

```bash
# Windows (使用 nvm-windows)
# 下载安装 nvm-windows: https://github.com/coreybutler/nvm-windows/releases
nvm install 20
nvm use 20

# macOS (使用 nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
nvm install 20
nvm use 20

# Ubuntu
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

验证安装：

```bash
node -v    # 应输出 v20.x.x
npm -v     # 应输出 10.x.x
```

#### 2. 安装 pnpm

```bash
# 通用方式
corepack enable
corepack prepare pnpm@latest --activate

# 或使用 npm 全局安装
npm install -g pnpm

# 验证
pnpm -v    # 应输出 9.x.x
```

#### 3. 克隆项目

```bash
git clone <仓库地址>
cd vite+vue3/my-nuxt-app
```

#### 4. 安装依赖

```bash
pnpm install
```

> **pnpm 说明**：本项目使用 pnpm 管理依赖，其幽灵依赖（phantom dependencies）机制与 npm/yarn 不同。如果遇到模块找不到的问题，可在项目根目录创建 `.npmrc` 文件：
> ```
> shamefully-hoist=true
> ```

#### 5. 启动开发服务器

```bash
pnpm dev
```

浏览器访问 http://localhost:3000 即可看到系统首页。

#### 6. 构建生产版本（可选）

```bash
# 构建
pnpm build

# 预览生产版本
pnpm preview
```

#### 7. 部署到服务器（可选）

```bash
# 构建后部署
pnpm build

# 使用 Node.js 直接运行
node .output/server/index.mjs

# 或使用 PM2 进程管理
npm install -g pm2
pm2 start .output/server/index.mjs --name "occupational-health-system"
pm2 save
pm2 startup
```

#### 8. Docker 容器化部署（可选）

前置要求：安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)（Windows 需启用 WSL2 后端）。

```bash
# 方式一：使用 docker-compose（推荐）
pnpm docker:up          # 构建并启动容器
pnpm docker:down        # 停止并移除容器
pnpm docker:logs        # 查看实时日志

# 方式二：手动构建与运行
pnpm docker:build       # 构建 Docker 镜像
pnpm docker:run          # 运行容器（映射到 3000 端口）

# 方式三：直接使用 docker 命令
docker build -t nuxt-occupational-health .
docker run -d -p 3000:3000 --name nuxt-app nuxt-occupational-health
```

构建完成后访问 http://localhost:3000。

Docker 配置文件说明：
- `Dockerfile`：多阶段构建，builder 阶段编译 + runner 阶段仅包含运行时产物，镜像体积最小化
- `docker-compose.yml`：容器编排配置，含健康检查与自动重启策略
- `.dockerignore`：排除 node_modules、.nuxt、.git 等非必要文件，加速构建

### 常见问题

**Q: `element-plus/dist/index.css` 报错 outside of Vite serving allow list**

A: pnpm 将依赖提升到了工作区根目录。本项目已在 `nuxt.config.ts` 中配置了 `server.fs.allow`，如仍有问题，在项目根目录创建 `.npmrc`：
```
shamefully-hoist=true
```

**Q: 端口被占用**

A: 使用其他端口启动：
```bash
pnpm dev --port 3001
```

**Q: 安装依赖时报错**

A: 清除缓存后重试：
```bash
pnpm store prune
rm -rf node_modules
rm -rf .nuxt
pnpm install
```

**Q: ECharts 图表不显示**

A: 确保浏览器窗口足够宽（≥1200px），ECharts 图表需要足够的容器尺寸才能正确渲染。

## 项目特性

- **Nuxt 4 目录规范**：`app/` 目录兼容、Composition API + `<script setup>`
- **TypeScript 支持**：全项目 TypeScript 类型安全
- **Tailwind CSS 4 + SCSS 混合**：causal 页面大量使用 Tailwind 工具类，其余页面以 SCSS scoped 为主
- **Element Plus 自动导入**：无需手动注册组件，图标按需引入
- **ECharts 6 深度集成**：每个分析页面均含多实例图表，支持响应式缩放
- **全局公共组件**：Sidebar 侧边导航复用，统一顶栏布局模式
- **管道步骤指示器**：跨页面进度可视化，支持激活/完成/成功三种状态
- **推理过程可视化**：大模型思考链可展开/折叠，含旋转加载动画
- **打印友好**：报告页面均含 `@media print` 样式 + 防伪水印
- **页面状态保持**：`<NuxtPage :keepalive="{}" />` 实现跨页面导航不丢失状态
- **个人化干预方案**：按预防级别（一级/二级）为每位预警对象生成独立的步骤式干预流程
- **知识库多选**：RAG 助手支持同时挂载多个知识库，智能推荐相关知识库
- **模型同步**：risk 页面与 agent 页面共享 20 种预训练模型列表
- **CSS 3D 交互**：首页卡片鼠标跟踪透视效果
- **SVG 动画**：因果路径流动、数据波形粒子、脉冲辉光节点
- **IntersectionObserver 滚动动画**：causal 页面各区域入场时触发淡入效果
- **数字滚动动画**：causal 页面 KPI 风险评分数值动态递增
- **路由联动**：页面间通过 vue-router 实现数据流导航

//cd my-nuxt-app && pnpm dev