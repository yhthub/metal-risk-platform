# 职业金属复合暴露智能干预推荐与决策支持系统

## 当前版本：4.1-风险模型

分支：`4.1-风险模型`。这是风险模型接入的研究测试版本，不是经过临床验证的诊断产品；本次 GitHub 更新不代表同步更新阿里云线上服务。

- 数据接入：单人动态录入、样本与单位核对、公开数据演示；群体文件导入、格式说明及可下载的数据清洗流程。
- 风险模型：接入 NHANES 已训练 CPU XGBoost / CatBoost 模型组；单人指标、原生 SHAP 与输入响应图，整份文件群体计算、基本资料、分布及报告导出。
- 综合相对预警：规范对象编号、共同有效结局的排名百分位等权合成、整行合并的榜单与占比、可调阈值和红/绿/数据不足三种状态。当前基础输入版 12 项中 7 项提供估计，5 项默认暂不出值。
- 两种群体演示复用同一批公开 NHANES 20 人和真实模型：普通预设 80 分，预警案例预设 75 分，界面明确说明阈值用途，不伪造预测。
- 循证问答：保留 BM25、可选 MedCPT 双路与 Ollama / 兼容模型服务适配；能力取决于实际配置和索引。无检索支持的回答明确标注，不把降级路径当成双路成功。
- 因果推理、疾病概率和智能干预等其余原型仍保留；没有模型或验证支持的图不会生成虚构结果。

### 运行本版本

风险功能使用 **Python 3.12+** 独立环境和 `backend/requirements-prediction.txt`。先安装前端依赖，并另行准备已发布模型资产，再运行 `start-dev.bat`；也可设置 `OCC_HEALTH_PYTHON` 指向兼容环境。

模型权重、完整检索库、真实上传文件、私有配置、操作日志和 `outputs/` 备份不随源码发布。没有模型资产时会明确显示“模型未就绪”，不会返回假结果。原 Docker 模板不是已适配风险模型的现成镜像。

当前安装、接口、资产配置和验收说明见：

- [4.1 版本说明](docs/RELEASE_4.1_RISK_MODEL.md)
- [NHANES 模型接入与运行](docs/NHANES_LOCAL_MODEL.md)
- [RAG 本机 Ollama 配置](docs/rag_ollama_local.md)
- [检索双路与资产复用](docs/rag_hybrid_reuse.md)
- [单人样本、单位与参考条件](docs/individual_input_reference_contract.md)

## 以下为 3.0 历史说明

以下早期设计、原型和启动说明为历史背景；与本节或 4.1 版本说明不一致时，以当前版本文档为准。历史脚本名称和临床/因果愿景不代表 4.1 已实现或验证的功能。

## 历史原型概述

本系统面向职业卫生与流行病学研究场景，融合环境监测、流行病学调查及多组学数据，构建基于因果推理的重金属健康风险评估与干预推荐模型。

## 项目结构

```
vite+vue3/
├── my-nuxt-app/          # 前端项目 (Nuxt 4 + Vue 3)
├── backend/              # 后端项目 (Python FastAPI)
├── package.json          # 根目录package.json（用于同时启动前后端）
├── start-dev.bat         # Windows启动脚本（双窗口）
├── start-dev.sh          # Linux/Mac启动脚本
├── start-dev-concurrently.bat  # Windows启动脚本（单窗口）
└── README.md             # 本文件
```

## 快速开始

### 方式一：双窗口启动（推荐新手）

**Windows:**
```bash
# 双击运行 start-dev.bat
# 或在命令行执行
start-dev.bat
```

**Linux/Mac:**
```bash
# 添加执行权限
chmod +x start-dev.sh

# 运行脚本
./start-dev.sh
```

这会打开两个窗口：
- 窗口1：前端服务 (http://localhost:3000)
- 窗口2：后端服务 (http://localhost:8000)

### 方式二：单窗口启动（使用concurrently）

**Windows:**
```bash
# 双击运行 start-dev-concurrently.bat
# 或在命令行执行
start-dev-concurrently.bat
```

**手动执行:**
```bash
# 安装concurrently
npm install

# 同时启动前后端
npm run dev
```

这会在一个窗口中同时显示前后端日志，用不同颜色区分。

### 方式三：手动分别启动

**终端1 - 启动后端:**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**终端2 - 启动前端:**
```bash
cd my-nuxt-app
pnpm install
pnpm dev
```

## 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | http://localhost:3000 | Nuxt应用 |
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | Swagger UI |
| API文档 | http://localhost:8000/redoc | ReDoc |

## 首次部署

### 1. 安装依赖

```bash
# 安装所有依赖（前端+后端）
npm run install:all

# 或分别安装
npm run install:frontend
npm run install:backend
```

### 2. 启动服务

```bash
# 使用npm脚本
npm run dev

# 或使用启动脚本
start-dev.bat  # Windows
./start-dev.sh # Linux/Mac
```

## 常见问题

### Q1: 端口被占用怎么办？

**前端端口(3000)被占用:**
```bash
cd my-nuxt-app
pnpm dev --port 3001
```

**后端端口(8000)被占用:**
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8001
```

记得同步修改前端的API配置。

### Q2: Python命令找不到？

**Windows:**
```bash
# 使用python3或py
python3 -m uvicorn app.main:app --reload --port 8000
# 或
py -m uvicorn app.main:app --reload --port 8000
```

**Linux/Mac:**
```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

### Q3: 后端依赖安装失败？

```bash
# 创建虚拟环境（推荐）
cd backend
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Q4: 前端无法访问后端API？

1. 确认后端服务已启动 (http://localhost:8000/docs 能访问)
2. 检查CORS配置是否正确
3. 查看浏览器控制台错误信息

## 开发指南

### 项目结构说明

```
backend/
├── app/
│   ├── main.py          # FastAPI入口
│   ├── config.py        # 配置文件
│   ├── api/             # API路由
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   └── utils/           # 工具函数
├── data/uploads/        # 文件上传目录
└── requirements.txt     # Python依赖

my-nuxt-app/
├── pages/               # 页面路由
├── components/          # 组件
├── assets/              # 静态资源
├── nuxt.config.ts       # Nuxt配置
└── package.json         # 前端依赖
```

### 添加新功能

1. **后端API:**
   - 在 `app/models/schemas.py` 定义数据模型
   - 在 `app/services/` 实现业务逻辑
   - 在 `app/api/` 定义路由

2. **前端页面:**
   - 在 `pages/` 创建页面
   - 在 `components/` 创建组件
   - 使用 `useApi()` 调用后端API

## 技术栈

### 前端
- **框架**: Nuxt 4 + Vue 3
- **UI**: Element Plus
- **样式**: Tailwind CSS 4 + SCSS
- **图表**: ECharts 6
- **动画**: GSAP

### 后端
- **框架**: FastAPI
- **数据处理**: pandas
- **数据验证**: Pydantic
- **服务器**: uvicorn

## 相关文档

- [前端README](my-nuxt-app/README.md)
- [后端README](backend/README.md)
- [CORS配置](backend/CORS_CONFIG.md)
- [API文档](http://localhost:8000/docs) (启动后访问)

## 许可证

MIT License
