# MedCPT + BM25 真实材料复用与检索评测

2026-10-11 只读盘点与产品代码配套。本文不批准启动服务器实验、全库扫描、建索引或 LLM 请求；既有科研授权不会自动扩展到网站产品改造。

## 已有材料，不需要重新下载或重建语料

根目录：`E:/医学检索库_完整_20261010`。**本节资产盘点**仅查看清单、来源元数据、有限目录与源码，没有打开 SQLite/WAL、加载权重、读取向量内容或登录服务器。整轮产品改造另有下文记录的封闭 SQLite 有界 BM25 验证，不应概括为整轮从未打开数据库。

| 材料 | 已核对的本地信息 | 产品用途 |
| --- | --- | --- |
| `UNIFIED_MANIFEST_PORTABLE.json` | 全局行轴 24,139,516；768 维 float32；raw inner product；无 L2 normalization | 唯一行轴/路径/来源定义，不以文件名猜路径 |
| `00_catalog/EXPORT_PROGRESS.json` | COMPLETE；1,302 个传输文件完成；1,224 个向量分片；此前导出已验证 gzip CRC 与 npy headers | 导出完成证据，不等于本次逐文件重新验证 |
| `00_catalog/SNAPSHOT_PROVENANCE.json` | 同源只读 backup API 创建并封闭；目标 delete journal；64,232,280,064 字节 | 使用封闭副本，不连接 YHT 活动生产库 |
| `replica_yht/projects/MedRR-EBM-Sufficiency/exp_www_fivebench_unified_001/unified_retrieval_001/corpus/corpus.sqlite3` | 与清单一致的 SQLite 快照；已有全局 FTS5/BM25 | 数据、标题、文本、canonical ID、稀疏检索 |
| `replica_yht/.../medcpt/shards/` 和 `replica_yht/.../precomputed/medcpt/embedding/` | 清单的 1,224 个 npy 分片覆盖全部行轴 | 全库独立 dense 召回的已有 article vectors，不是 BM25 候选重排 |
| `replica_yht/models/MedRR-EBM-Sufficiency/MedCPT/MedCPT-Query-Encoder/d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc/` | config/tokenizer/model.safetensors 均在；权重 437,951,328 字节 | 仅 query 编码器，`local_files_only=True` |
| `replica_yht/models/MedRR-EBM-Sufficiency/MedCPT/MedCPT-Article-Encoder/d05a736da4bb84ee4057b7f7999485be6ed85465/` | 同样完整的模型文件元数据 | 未来新增文档编码；本次不重编码全库 |

全库 24,139,516 是检索记录/分块，不是独立论文数。来源清单为 PubMed 23,898,701、医学教材 125,936、StatPearls 114,879。PubMed 为标题/摘要语料，不是全量 PMC 正文。元数据声明的数字没有在本轮以 SQL 全库重算。

portable manifest 的旧状态名 `CORPUS_AND_BM25_COMPLETE_DENSE_RUNTIME_PENDING` 保留历史语义；不能仅凭这个名字判定向量不存在。已有 float32 向量净数据约 74.16 GB（约 69.06 GiB）；此次有限目录/文件名盘点未找到可直接加载的 FAISS/HNSW ANN 索引，不能据此断言整个服务器上不存在 ANN。

## 可引用的既有算法，不复制旧实验整条链

薄检索实现：

- `D:/Research/MedRR-EBM-Sufficiency/04_experiments/EXP-WWW-FIVEBENCH-UNIFIED-001/preparation_001/unified_retrieval_001/retrieve_unified.py`
- 同目录 `unified_query.py`
- `D:/Research/MedRR-EBM-Sufficiency/04_experiments/EXP-WWW-FULLBENCH-PREP-001/preparation_001/controller_contracts/BM25_STOPWORDS.json`

统一库协议与历史就绪证据：

- `D:/研究生资料材料/Med-RR_EBM_Evidence_Sufficiency/EBM_Suff-gpt-5.6-实验总指挥/outputs/WWW_五数据集统一库切换_2026-10-04/unified_retrieval_001/TRI_CORPUS_RUNTIME_CONTRACT.json`
- 同目录 `三库统一检索_双机就绪说明.md`

既有 thin runner 有 `--serve` JSON-lines 协议，不是已经对网站开放的 HTTP 服务。历史环境路径与双机机械核对属于 2026-10-04 的证据，不能证明服务今天仍在运行。旧 runner 构造时会打开库并可能全库扫描，产品不直接运行它，更不调用含 Reader/Set/评估链的旧 batch runner。

复用核心契约：

- MedCPT Query Encoder + CLS，768D float32；article 向量不归一化；raw inner product 越大越前；不把数值当概率。
- BM25 来自统一三库 FTS5，title/content 权重 1/1；BM25 原分数越小越前。旧抽词为英语 token、停用词过滤、先到先得最多 28 个唯一词。产品的中文术语展开、AND→OR 补召回属于额外行为，必须记录 `prepared_query`，不宣称原实验精确复现。
- 双路独立召回后使用 RRF：各路 rank 从 1 开始，`Σ 1/(60+rank)`、等权、canonical ID 去重。同分按照 canonical ID 排序；不能直接相加 BM25 原分数与 dense 内积。RRF 的定义与常数见[原始论文](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)，论文结果不是本项目改善质量的证明。
- 旧统一检索 dense 为全分片流式精确扫描，没有把 BM25 候选当作全库 MedCPT。产品可以接入带明确 provenance/行轴/metric 元数据的外部 ANN，但必须公开 approximate、范围与参数，不能称为精确全库排序。
- `pubmed/<original_id>` 等 canonical ID 与 vector row index 必须同轴，不因换目录或换主机重写 ID。

还有 dense 同分边界的差异：旧统一检索精确 dense 按 `document_id ASC`，当前服务精确 dense 按 `row_index ASC`。最终 RRF 的 canonical ID 同分排序并不能消除前面的 dense top_k 边界差异。ANN 本身也可能改变候选顺序，不能仅凭最终 RRF tie-break 一致宣称旧检索复现；服务状态及评测记录明确公开两种 tie-break。

### query 64 与旧统一库 query 512 的明确差异

NCBI 官方使用示例为 query `max_length=64`、article `max_length=512`，并使用 CLS 表征，见[官方 MedCPT 代码](https://github.com/ncbi/MedCPT#using-medcpt)。本地 `MedCPT部署_2026-10-03/medcpt_adapter.py` 也是 query 64 / article 512。

但 2026-10-04 统一库 `unified_query.py` 的 `MAX_LENGTH=512` 确实用于 **query tokenizer**，不是 article。当前产品采用 query 64。article vectors 可继续复用；长查询的截断与召回结果可能变化，不能声称与旧服务器逐位/逐条复现。评测记录 query encoder revision/max length，冻结 query 集并单独核对长查询，不通过测试 qrels 调长度。

PubMed 预计算 article vectors 的精确模型 commit 在原包中未记载；清单明确 `not_documented_by_package`。已有小样本重编码差异核对只能作为有限兼容证据，不证明全库 bit-identical，也不能补造模型版本。

## 尚未可运行的条件

本机只有 6GB 显存、总内存约 15.77GB；全库 float32 dense 流式扫描虽不必一次载入内存，但每问读取约 74GB 数据并做 24M 个内积，不是默认交互式低延迟方案。已有向量不等于可低延迟 ANN 服务。产品入口应保持资源预检、并发 1、超时/显式不可用，不静默把 Hybrid 降成 BM25 后宣称双路成功。

允许的后续路线：确认依赖与内存预算，复用已验证的全库外部索引/服务；若没有，另行批准规划闭合的 ANN generation。不能在本轮自动构建索引、扫描全库、重新编码语料或创建服务器实验。已完成准备与真实检索/模型验收必须分开报告。

产品 FAISS serving 已区分“完整行轴/ANN generation”与“原向量分片实体”：只读服务可部署闭合 SQLite/catalog、原 portable manifest、Query Encoder 和 ANN/完成侧元数据/绑定哈希，不要求原约 74GB npy 一同挂载。完整行轴与版本绑定仍不可省略；`sharded_exact` 或索引 builder 则必须原分片全部存在/大小一致。这不表示现成 ANN 已存在，也不表示本轮删掉、迁移或压缩了 E 盘素材；原完整导出一律保留。

### 本轮已完成的有限真实检查

`D:/gradstu/gard1/vite+vue3/outputs/rag_hybrid_20261011/local_api_preflight_001.json` 记录本地鉴权：未授权 status 返回 401，带应用 key 返回 200；默认 Hybrid 缺少 dense index 时 503，没有伪装成功。显式 `mode=bm25` 的 `cadmium kidney` 使用 candidate_k=8、top_k=3，从封闭 SQLite 得到真实 PubMed hit（首条 `Cadmium and the kidney.`）。此检查的 LLM generation、dense encoder call、全向量 scan 与源修改均为 0；库计数仍来自 export catalog，不是重算。

同轮 tiny 合成 FAISS 索引测试在隔离依赖环境为 16 项 PASS；原环境为 15 项 PASS、1 项因可选 FAISS 缺失而 SKIP。它验证小索引/行轴/融合等工程行为，不是实际 MedCPT query encoder、完整 24M dense/Hybrid 召回、低延迟服务或临床质量验收。上述回执明确 corpus 快照 ready，但独立 dense 与 Llama 仍 not_ready。

### 全库 ANN builder 已准备，默认仅计划

`backend/tools/build_medcpt_index.py` 复用已有 article vectors，按有界 block 流式构造 raw-IP IVFPQ；不编码语料、不请求 LLM。默认只校验清单与文件元数据、打印 `PLAN_ONLY`，不创建输出目录、不读取向量内容。

```powershell
python "D:/gradstu/gard1/vite+vue3/backend/tools/build_medcpt_index.py" --corpus-root "E:/医学检索库_完整_20261010" --output-dir "E:/medical-rag-index/medcpt_001"
```

本轮已在真实清单运行上述计划。全库 24,139,516 行，默认 nlist=4096、m=64、8-bit PQ、nprobe=32、seed=20261011；编码+row ID 的估算为 1,738,045,152 字节，不含全部元数据，不能当作成品文件体积或峰值 RAM 保证。默认训练 200,000 行，block 8,192 行；真正执行的安全下限为 8 GiB **可用** RAM、8 GiB 空闲磁盘。本轮未加 `--execute`，未建索引。

确认资源及执行范围后才加 `--execute`。输出必须是与原语料无父子关系且不存在的新 generation；成品为 `medcpt_ivfpq.faiss` 和绑定 manifest SHA256、全局行轴、metric、encoder revision 的 `.faiss.json` 完成 sidecar。失败保留进度/partial，不覆盖原资产，不发布完成标记；服务必须验证同轴 sidecar，不能仅凭 `.faiss` 存在宣称 ready。

服务默认索引文件门控仍为 512 MiB，需要按实际成品显式设置 `RAG_DENSE_INDEX_PATH` 和 `RAG_DENSE_MAX_INDEX_BYTES`。部署示例的 2 GiB 只是文件门控，不是 RAM 预算。Windows FAISS 大索引 mmap 不可用时默认拒绝自动全量载入，只有另行确认内存后才可显式允许 in-memory；来源限定 ANN 尚需完整分源索引，不能用有限全局 top-k 后过滤冒充分源召回。

builder 另有 10 项小型/失败注入测试通过；与 dense 的 16 项在隔离 FAISS 1.12.0 环境合计 26 PASS、无 SKIP。生产 ANN 的召回质量仍须由下述外部冻结 qrels 评测，而非以这些合成测试替代。

## 独立三臂评测入口

`D:/gradstu/gard1/vite+vue3/scripts/rag_retrieval_evaluate.py` 仅使用标准库，不导入 backend/torch/faiss，不打开检索库。默认 PLAN_ONLY，不发请求、不建输出文件。

外部冻结 query JSONL 每行严格只有：

```json
{"query_id":"query_001","query":"需要检索的原始问题"}
```

禁止把答案、选项或 qrels 加进检索输入。qrels 是独立人工核验文件（3 列 `query_id<TAB>chunk_id<TAB>grade` 或 TREC 4 列 `query_id<TAB>0<TAB>chunk_id<TAB>grade`，grade 为 0..5）。不复制旧问答 gold，不随输出补造标准答案，不自动把未判断文献标成不相关。本仓库测试只含 `synthetic/...` 假 ID 和数学检查，不提供临床 gold。

冻结三臂公平口径：默认 final top_k=8，总候选预算 B=32。BM25 单路 32、MedCPT 单路 32、Hybrid 每路 16，总容量一致。B 必须为偶数且 B/2≥top_k，避免服务隐式提高预算。等候选数不等于等算力、等 I/O 或等耗时。复现旧各路 32 可选 `--budget-policy per_channel --candidate-budget 32`，Hybrid 总容量 64，报告会明确不等总预算。

离线 RAW JSONL 每条具有 `query_id/query/arm/candidate_k/top_k/response/elapsed_seconds/http_status`，每题每臂恰好一个首次记录。`response` 是 evidence-search 的真实响应，含 hits/mode/diagnostics；所有 arm 的 query 与预算必须一致。可以直接用本入口产生的 `first_raw.jsonl` 离线评分。离线重放不会伪造检索结果或计入新的检索耗时。

评测拒绝 degraded、重复 ID、非有限分数、预算/来源过滤不一致。Hybrid 还必须明确回报 `independent_dense_recall=true`、`dual_route_executed=true` 与两个 `channels.*.ready=true`；MedCPT 单路要求 independent 与 dense ready。只出现 `mode=hybrid` 不算双路已执行，这些结构性声明仍须由真实检索集成和人工评测独立核验。

只查看离线计划：

```powershell
python "D:/gradstu/gard1/vite+vue3/scripts/rag_retrieval_evaluate.py" --queries "D:/RAG评测输入/queries.jsonl" --rankings "D:/RAG评测输入/first_raw.jsonl" --qrels "D:/RAG评测输入/qrels.tsv"
```

明确执行离线评分（仅对已有 RAW；输出目录必须不存在）：

```powershell
python "D:/gradstu/gard1/vite+vue3/scripts/rag_retrieval_evaluate.py" --queries "D:/RAG评测输入/queries.jsonl" --rankings "D:/RAG评测输入/first_raw.jsonl" --qrels "D:/RAG评测输入/qrels.tsv" --execute --output "D:/RAG评测输出/retrieval_001"
```

未来经批准才能做集成。先打印计划：

```powershell
python "D:/gradstu/gard1/vite+vue3/scripts/rag_retrieval_evaluate.py" --queries "D:/RAG评测输入/queries.jsonl" --integration --base-url "http://127.0.0.1:8000"
```

只有额外加 `--execute --output <新目录>` 才 POST `/api/agent/evidence-search`，密钥从 `RAG_API_KEY` 环境读取，不写入文件。绝不请求 `/chat`、模型生成或旧实验 runner。缺少 dense/模型依赖时保存首次失败，503/429/超时不重试；该集成可能触发配置后的全库 dense 工作，所以本轮没有运行它。远程还需 `--allow-remote` + HTTPS；不默认使用保存的服务器 IP。

### 输出与结论边界

- `RUN_MANIFEST.json`：输入 SHA256、预算、query encoder 声明、来源过滤、顺序与版本；不是 corpus 全库哈希。
- `first_raw.jsonl`：首次响应正文/错误/耗时；先落盘并 fsync，再做评分；只创建、不覆盖、不重试。离线重放将输入原记录完整保存在 `source_raw`。
- `scored_rankings.json` / `SUMMARY.json`：外部 qrels 下 MRR@k、nDCG@k、Recall@k；有 positive qrels 才有指标，缺失/零分母为 NOT_EVALUATED，不补 0。未判断 hit 仅在指标计算中按 0，不成为负标签。另报 judgment coverage、失败/空结果、完成率和实际各路候选/范围信息。
- 三臂成对比较只使用均成功且均有 positive qrels 的公共题集合，并公开分母；失败保留在 completion rate 中。观测耗时受缓存、执行顺序与硬件影响，不是独立时延试验。
- 没有 qrels 时只报告工程指标，质量数值为 null/NOT_EVALUATED；不声称检索提升、医学准确率、引用支持或临床有效。RRF 分数、文档数量和代码单测均不能代替人工相关性验证。

排名评估与 graded nDCG 背景见[Stanford IR 教材](https://nlp.stanford.edu/IR-book/html/htmledition/evaluation-of-ranked-retrieval-results-1.html)。问题回答正确性、生成幻觉与引用是否支持结论属于独立的后续评测，本入口不混为一谈。

机械自测（合成数据、临时目录，不碰真实库）：

```powershell
python -m unittest discover -s "D:/gradstu/gard1/vite+vue3/tests" -p "test_rag_retrieval_evaluate.py" -v
```
