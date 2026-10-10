# 职业金属复合暴露智能干预推荐与决策支持系统

## 项目概述

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
