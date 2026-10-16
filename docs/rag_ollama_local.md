# 用现有 Ollama 做真实 RAG 功能验证

2026-10-11 用户选择复用本机 Ollama，不继续要求手工转换从服务器迁移的原始权重。原始权重保持不动，也没有下载替代模型。

## 已核对的运行材料

现有 `llama3.1:8b` 为 Ollama 8B / Q4_K_M，约 4.92GB，已安装版本 0.5.12。模型名必须按实际服务的 tag 配置；`Llama-3.1-8B` 是另一运行配置的别名，不能拿它请求当前 Ollama。模型元数据中 131072 的训练上下文不代表本机已分配相同长度。

后端增加 `RAG_LLM_PROVIDER=ollama` 原生适配，使用 `/api/tags` 与 `/api/chat`，而非无检索的旧 `/api/agent/ollama/chat`。原来的 OpenAI-compatible 模型服务路径仍保留。Ollama 每次请求显式绑定 `options.num_ctx`、`num_predict` 与 RAG 上下文/输出预算，防止旧版本默认上下文比产品预算更短。模型响应必须完成、模型名一致且非空；失败不使用模板回答兜底。[Ollama 原生聊天接口](https://docs.ollama.com/api/chat)说明了请求选项与完成状态；[上下文说明](https://docs.ollama.com/context-length)强调实际分配影响内存。

模型调用禁止跟随重定向，也不继承桌面代理。密钥只由受保护进程环境提供，测试使用临时内存密钥，不写入 RAW 或配置文件。两个 RAG 评测脚本现在都发送 `Authorization: Bearer`，与当前 `ApiGuard` 一致；旧 `X-API-Key` 不再使用。

## 本机 profile

`deploy/.env.ollama.example` 是无密钥示例，不能作为公网配置。完整闭合语料位于 E 盘，来源与行轴沿用原导出；不连接 YHT 正在使用的实验数据库。

当前可先执行的功能链为完整库的 **BM25 → 证据选取 → Ollama → 引用编号校验**，必须显式设置 `RAG_RETRIEVAL_MODE=bm25`。这不是 Hybrid 的静默降级，更不是 MedCPT+BM25 双路验收。默认产品 Hybrid 仍在缺少独立 MedCPT 索引时明确拒绝；不能用“向量文件在 E 盘”代替可运行完整索引。

在新的 PowerShell 会话中设置局部环境，再启动本机 API（无真实密钥，仅允许 loopback）：

```powershell
$env:RAG_LLM_PROVIDER = 'ollama'
$env:RAG_LLM_BASE_URL = 'http://127.0.0.1:11434'
$env:RAG_LLM_MODEL = 'llama3.1:8b'
$env:RAG_CORPUS_ROOT = 'E:/医学检索库_完整_20261010'
$env:RAG_RETRIEVAL_MODE = 'bm25'
$env:RAG_ALLOW_DEGRADED_RETRIEVAL = 'false'
$env:RAG_LLM_CONTEXT_WINDOW = '4096'
$env:RAG_LLM_MAX_TOKENS = '512'
$env:RAG_LLM_CONTEXT_CHARS = '3500'
$env:RAG_LLM_TIMEOUT_SECONDS = '180'
$env:RAG_MAX_CONCURRENT_GENERATIONS = '1'
$env:RAG_TOP_K = '2'
$env:RAG_CANDIDATE_K = '8'
python -m uvicorn app.main:app --app-dir 'D:/gradstu/gard1/vite+vue3/backend' --host 127.0.0.1 --port 8000
```

前端开发会话的 `NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000`。状态页面显示真实模型与检索通路，不让单路看起来像双路；本地测试不能等同于 8.148.158.242 已部署或公网访问已安全。

## 验收口径

`scripts/rag_ollama_smoke.py` 默认只计划，实际请求须 `--execute`；输出必须是新的目录。固定公开问题仅作工程功能验证，每题一个首次记录，失败不自动重试；不写个人健康信息，不提供医学准确率或自编 qrels。真实结果以该次 `manifest.json`、`first_raw.jsonl` 与 `mechanical_summary.json` 为准，服务目录/状态或单测 PASS 不证明生成已成功。

第一次真实功能运行的正例实际生成成功、编号校验通过，负例在 8 秒检索预算内超时，整轮仍为 FAIL，记录保留且不覆盖。该次有前端 build 并行运行，时间不作独立性能结论。随后修正零 AND 结果下的宽泛 OR 补召：先用有界 FTS 字面词存在性检查，若有未匹配词，不丢掉该词后仅凭高频词生成回答；返回空候选并公开诊断。这是工程检索策略变化，不是证明某个科研主题不存在证据。

修正后单独执行缺词回归，实际 HTTP 200、`insufficient_evidence`、0.047 秒，禁止构造模型的探针没有触发。该回归最初检查脚本误读诊断字段层级而记录 FAIL；原文件保持不变，独立离线复核纠正检查路径后为 `OFFLINE_REVIEW_PASS`。复核不重发请求，也不重新验证当前运行时；不把第一次两题 smoke 改记通过。细节见 [本次实现与验收记录](rag_individual_delivery_20261011.md)。

完整 MedCPT+BM25 还须完整行轴索引、实际 Query Encoder 和独立召回验收。现有全库索引 builder 保留，只复用已经导出的向量，不重编码；本次 Ollama 测试不启动全库 ANN 构建、YHT 实验或云端部署。
