# 职业金属复合暴露智能干预推荐与决策支持系统 - 后端API

## 项目概述

本后端服务为"职业金属复合暴露智能干预推荐与决策支持系统"提供API接口支持，基于Python FastAPI框架开发。

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.115.6 |
| ASGI服务器 | uvicorn | 0.34.0 |
| 数据处理 | pandas | 2.2.3 |
| 数据验证 | Pydantic | 2.10.4 |
| 文件处理 | openpyxl | 3.1.5 |
| 语言 | Python | 3.10+ |

## 目录结构

```
backend/
├── app/                        # 应用主目录
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py               # 配置模块（含CORS配置）
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── datainput.py        # 数据接入模块
│   │   ├── risk.py             # 风险量化模块
│   │   ├── causal.py           # 因果推理模块
│   │   ├── plan.py             # 干预策略模块
│   │   └── agent.py            # RAG问答模块
│   ├── models/                 # 数据模型
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic模型定义
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── data_service.py     # 数据接入服务
│   │   ├── risk_service.py     # 风险量化服务
│   │   ├── causal_service.py   # 因果推理服务
│   │   ├── plan_service.py     # 干预策略服务
│   │   └── agent_service.py    # RAG问答服务
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── helpers.py          # 辅助工具函数
├── data/                       # 数据目录
│   └── uploads/                # 文件上传目录
├── requirements.txt            # Python依赖
├── .env.example                # 环境变量配置示例
├── .gitignore                  # Git忽略配置
├── CORS_CONFIG.md              # CORS配置详细文档
├── start.sh                    # Linux/Mac启动脚本
├── start.bat                   # Windows启动脚本
└── README.md                   # 项目文档
```

## 快速开始

### 1. 环境要求

- Python 3.10+
- pip 或 conda

### 2. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 开发模式（自动重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 或使用Python直接运行
python -m uvicorn app.main:app --reload
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- API信息: http://localhost:8000/api/info

## CORS跨域配置

本项目已内置CORS跨域支持，允许前端应用跨域访问API。

### 默认配置

默认允许以下源访问：
- `http://localhost:3000` (Nuxt开发服务器)
- `http://localhost:3001`
- `http://127.0.0.1:3000`
- `http://127.0.0.1:3001`

### 自定义配置

**方式1：环境变量（推荐）**

```bash
# .env文件
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=GET,POST,PUT,DELETE,OPTIONS
CORS_ALLOW_HEADERS=Content-Type,Authorization
```

**方式2：配置文件**

编辑 `app/config.py` 文件中的 `CORS_ORIGINS_DEFAULT` 列表。

### 详细文档

更多CORS配置说明请参考：[CORS_CONFIG.md](CORS_CONFIG.md)

## API模块

### 1. 数据接入模块 (`/api/datainput`)

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/datainput/single` | 单人数据录入 |
| POST | `/api/datainput/batch` | 群体CSV/XLSX导入 |
| GET | `/api/datainput/statistics/{file_id}` | 数据统计信息 |
| GET | `/api/datainput/visualization/{file_id}` | 可视化数据 |
| GET | `/api/datainput/records` | 获取所有记录 |
| GET | `/api/datainput/records/{record_id}` | 获取单条记录 |

### 2. 风险量化模块 (`/api/risk`)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/risk/models` | 获取可用模型列表 |
| POST | `/api/risk/assess` | 执行风险评估 |
| GET | `/api/risk/high-risk/{assessment_id}` | 获取高危人员名单 |
| GET | `/api/risk/detail/{assessment_id}` | 获取评估详情 |
| GET | `/api/risk/report/{assessment_id}` | 生成风险报告 |

### 3. 因果推理模块 (`/api/causal`)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/causal/dag` | 获取DAG数据 |
| POST | `/api/causal/counterfactual` | 反事实推演 |
| GET | `/api/causal/kpi` | KPI指标 |
| GET | `/api/causal/nodes` | 节点列表 |
| GET | `/api/causal/edges` | 边列表 |
| GET | `/api/causal/pathway/{metal}` | 金属致病路径 |

### 4. 干预策略模块 (`/api/plan`)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/plan/strategies/{person_id}` | 个人干预方案 |
| GET | `/api/plan/all` | 所有干预方案 |
| GET | `/api/plan/high-risk` | 高危人群方案 |
| GET | `/api/plan/medium-risk` | 中危人群方案 |
| GET | `/api/plan/report/{person_id}` | 个人报告 |
| GET | `/api/plan/comparison` | 成效对比 |

### 5. RAG问答模块 (`/api/agent`)

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/api/agent/knowledge-bases` | 知识库列表 |
| POST | `/api/agent/chat` | 问答消息 |
| POST | `/api/agent/upload-kb` | 上传知识库 |
| GET | `/api/agent/models` | 模型列表 |
| GET | `/api/agent/quick-prompts` | 快捷提问 |

## 数据模型

### 个体数据 (IndividualData)

```python
{
    "id": "SZ-102",
    "gender": "male",
    "age": 45,
    "work_years": 12.5,
    "job": "smelting",
    "education": "high",
    "marital": "married",
    "smoking": "current_lt10",
    "drinking": "occasional",
    "bmi": 24.5,
    "ppe": "basic",
    "pb": 124.0,
    "cd": 89.0,
    "hg": 24.0,
    "th": 12.0,
    "li": 18.0,
    "cr": 34.0,
    "ni": 65.0,
    "co": 40.0,
    "as_val": 105.0,
    "rn": 30.0
}
```

### 风险评估结果 (RiskAssessmentResult)

```python
{
    "assessment_id": "ASSESS-abc12345",
    "model_name": "xgboost",
    "total_population": 1245,
    "high_risk_count": 10,
    "high_risk_ratio": 0.8,
    "high_risk_persons": [...],
    "warning_level": "重大规模健康风险预警",
    "warning_message": "..."
}
```

### 干预方案 (InterventionPlan)

```python
{
    "person_id": "SZ-284",
    "name": "张伟",
    "dept": "第一熔炼车间",
    "years": 15,
    "factors": "Pb, As, Cd",
    "score": 68.5,
    "level": "level2",
    "workflow": [...],
    "outcomes": [...]
}
```

## 前端集成

### Nuxt配置

在 `nuxt.config.ts` 中添加API配置：

```typescript
export default defineNuxtConfig({
  runtimeConfig: {
    public: {
      apiBase: process.env.API_BASE_URL || 'http://localhost:8000'
    }
  }
})
```

### 创建Composable

```typescript
// composables/useApi.ts
export const useApi = () => {
  const config = useRuntimeConfig()
  const baseURL = config.public.apiBase

  const fetchModels = async () => {
    return await $fetch(`${baseURL}/api/risk/models`)
  }

  const runAssessment = async (modelId: string) => {
    return await $fetch(`${baseURL}/api/risk/assess`, {
      method: 'POST',
      params: { model_id: modelId }
    })
  }

  const sendChat = async (message: string, model: string, kbs: string[]) => {
    return await $fetch(`${baseURL}/api/agent/chat`, {
      method: 'POST',
      body: {
        message,
        model,
        knowledge_bases: kbs,
        enable_deep_think: true
      }
    })
  }

  return { fetchModels, runAssessment, sendChat }
}
```

## 开发说明

### 添加新的API端点

1. 在 `models/schemas.py` 中定义数据模型
2. 在 `services/` 中实现业务逻辑
3. 在 `api/` 中定义路由
4. 在 `main.py` 中注册路由

### 数据存储

当前版本使用内存数据存储，重启后数据会丢失。生产环境建议：
- 添加数据库支持（PostgreSQL/MongoDB）
- 实现数据持久化
- 添加缓存层（Redis）

### 认证授权

当前版本暂未实现认证。生产环境建议：
- 添加JWT认证
- 实现用户权限管理
- 添加API限流

## 常见问题

**Q: 如何修改端口？**

A: 启动时指定端口：
```bash
uvicorn app.main:app --reload --port 8001
```

**Q: 如何处理跨域问题？**

A: 已配置CORS允许localhost:3000和3001。如需添加其他域名，在 `main.py` 中修改 `allow_origins`。

**Q: 如何添加新的知识库？**

A: 在 `services/agent_service.py` 中的 `KNOWLEDGE_BASES` 列表添加新知识库信息。

## 许可证

MIT License
