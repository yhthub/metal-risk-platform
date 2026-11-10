# D 盘本地轻量检索

2026-11-09，Windows 本地检索切回原有证据库：

`D:/研究生资料材料/研1/智能风险预测干预系统/evidence-pipeline/data/db`

- `evidence.db`：本地规范资料。
- `scientific_evidence.db`：本地科学文献。
- `guidelines_evidence.db`：本地指南资料；历史来源分类不是质量认证。

三库共约 1.18 GiB，使用既有 FTS5 trigram 索引。连接为 SQLite `mode=ro`，保留 WAL 读取语义，不创建数据库、不重建索引、不加载嵌入模型。每次请求顺序查询至多三个库、单并发、默认共 3 秒预算，单库候选最多 32 条，SQLite页缓存每连接约2 MiB，禁用mmap。查询不会将整库读入Python内存。

本次检索适配只对原库按需读取，保留来源URL、页码、条款、原切块ID和真实标准号/DOI；跨库ID加来源前缀。每库使用真实BM25排序，跨库按概念覆盖率和库内名次合并，不直接比较不同库的原始BM25分数。中文短词通过显式词表展开，未知概念保留；无法被trigram匹配的短词会返回说明，不能据此宣称没有相关证据。

超过24个检索概念的问题会返回拆分问题的提示并停止本次检索，不会截断末尾条件。

## 启动与配置

继续使用项目根目录的 `start-dev.bat`。默认检索后端为 `local_evidence`，检索方式为 `bm25`，不使用 E 盘大库或 MedCPT。若后端已在运行，需要重启本地后端使新代码生效。

自定义本地启动时，可以在当前 PowerShell 窗口设置：

```powershell
$env:RAG_RETRIEVAL_BACKEND = 'local_evidence'
$env:RAG_EVIDENCE_DB_DIR = 'D:/研究生资料材料/研1/智能风险预测干预系统/evidence-pipeline/data/db'
$env:RAG_RETRIEVAL_MODE = 'bm25'
$env:RAG_LOCAL_DB_TIMEOUT_SECONDS = '3'
```

`RAG_EVIDENCE_DB_DIR` 指向包含三个SQLite文件的目录。local_evidence 模式不会读取旧的 `RAG_CORPUS_ROOT`，也不会因缺文件自动切回大库。直接启动 Python API 时，Windows 未指定后端且没有显式 MedRR corpus 配置，也默认使用本地三库；若使用已有自定义进程配置，应明确设定上述后端。

生成模型配置与检索库配置分开。切换检索库不会下载、加载或验证 Ollama 模型；低资源条件下可只调用 `/api/agent/evidence-search` 验证检索，不调用 `/chat`。`/status` 中的检索就绪与生成就绪应分别检查。

Linux 未显式配置时仍为原 MedRR 检索路径，显式 `RAG_RETRIEVAL_BACKEND=medrr` 可保留原有部署配置。首次本地切换没有改动云端；后续经用户另行授权，阿里云已使用 `combined_bm25` 并列接入三库，详见 [阿里云联合检索记录](ALIYUN_COMBINED_RETRIEVAL.md)。本地默认保持不变。

## 来源与质量

三库可读、能够命中只证明检索功能可用，不能证明历史文档标签准确、标准现行或指南质量已核验。接口保留原始元数据但不把它转换成已验证的证据等级；缺少DOI/PMID时保持空值。

历史大库导出、冻结评测脚本和旧回执保留以便追溯，不是当前本地检索入口。
