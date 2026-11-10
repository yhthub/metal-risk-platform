# v5.0 · 阿里云线上版本快照

2026-11-10 在新一轮全站用语和 UI 优化之前保存。分支 `release/v5`，标签 `v5.0`；此版本代表当时实际部署的前后端，不是本地主工作区尚未发布的 v4.2 业务改动合集。

## 来源

- 前端：`site_cleaning_demo_20261110_001/public`。从该发布构建对应的源码目录提取，覆盖文件与部署清单逐一核对；线上 64 个静态文件哈希验证通过。仅将本机临时构建目录 `.nuxt-final` 还原为通用 `.nuxt`。
- 后端：`site_rag_synthesis_20261109_004/backend`。直接从当前运行服务工作目录读取 52 个应用及依赖清单文件，逐文件校验 SHA256。
- 原有及相关新增测试、说明文档作为开发辅助一起保留，不属于运行服务提取内容。详细来源与哈希见 `releases/v5.0-source-manifest.json`。

## 已有功能与边界

单人/群体数据接入、公开 NHANES 案例、清洗及 XLSX→CSV 转换；真实风险指标模型、局部解释、群体分析与报告；BM25 top-k 检索及大模型医学知识问答；全站移动适配和可收起侧栏。方案推荐与部分因果页面仍为预设演示，尚未按本次风险分析自动生成。

模型权重、检索库、用户上传文件、私有环境配置、API 密钥、依赖目录和静态构建产物不随源码公开。部署需另行提供已有运行资产；缺少资产时不能将源码克隆视为完整服务上线。

## 构建与运行

前端使用 Node.js 与 pnpm。进入 `my-nuxt-app`，执行 `pnpm install --frozen-lockfile`，再执行 `pnpm generate`。本地运行参见该目录 package.json 的 dev 命令。

当前阿里云静态构建使用以下环境变量：

```text
NUXT_APP_BASE_URL=/zhiwei/
NUXT_PUBLIC_API_BASE=/zhiwei
NUXT_PUBLIC_PUBLIC_DEMO=true
```

后端使用 Python 3.12+，风险依赖见 `backend/requirements-prediction.txt`，线上依赖清单为 `backend/requirements-cloud41.txt`。应用入口为 `app.main:app`。模型、语料、服务认证与生成接口配置由私有环境变量提供，模板仅作字段参考，不包含可用凭据。生产服务由现有 systemd 和 Nginx 管理，不应直接运行仓库中历史固定路径部署脚本覆盖当前服务。

前端可以独立回退到 `site_cleaning_demo_20261110_001/public`；本次 GitHub 快照本身没有修改云端应用或配置。
