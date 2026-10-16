# RAG 体验版调整与索引核对

日期：2026-10-11。按用户要求面向 5–10 人简单体验，本轮不做系统性检索质量评估、医学准确率评估或性能压测。

## 已落实的体验行为

- 合适检索切块仍提供给模型；有证据路径保留编号和来源检查。
- 无匹配切块、中文术语展开不完整、检索不可用/超时时，真实模型仍可给一般知识回答，前置明确“检索信息不足、未获本次检索证据支持”。一般回答不提供假引用或把检索候选算成已引用出处。
- 一般回答为 `general_answer/general_knowledge/evidence_support=none`；页面区分问答可用 `can_chat` 与检索就绪 `rag_ready`。模型本身不可用仍为错误，不返回模板假答案。
- `start-dev.bat` 默认复用现有 Ollama `llama3.1:8b`，Hybrid 缺 dense 时允许**显式** BM25 降级，不显示双路已跑通。已指定的进程环境变量保留，不安装/拉取/启动模型。
- 前端、后端、两层 Nginx 统一 `Authorization: Bearer <token>`。只保留体验用共享口令和基础限流，不新增企业账户模块。
- 原严格无证据探针显式设 `RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK=false`。历史 RAW 保留，没有因为新体验策略而重跑或修改旧首次结果。

当前已经运行的旧后端需要关闭后重新通过 `start-dev.bat` 启动来应用新的进程环境。代码热更新并不改变旧进程中的 `RAG_LLM_PROVIDER`。Ollama 应处于运行状态且已安装对应 tag；批处理不会下载模型或启动另一个 Ollama 服务。

## 为什么旧实验能运行，却未找到网站可加载的 FAISS

只读核对的旧代码和 2026-10-04 双机回执表明：两机当时具有完整三库实验检索资产；最新 24,139,516 行检索采用 **MedCPT 分片 exact 扫描 + SQLite FTS5 BM25**，不是 FAISS ANN。

直接依据：

- `D:/研究生资料材料/Med-RR_EBM_Evidence_Sufficiency/EBM_Suff-gpt-5.6-实验总指挥/outputs/WWW_五数据集统一库切换_2026-10-04/unified_retrieval_001/TRI_CORPUS_RUNTIME_CONTRACT.json`：`exact_streamed_all_shards`、768D FP32、1,224 分片。
- `D:/Research/MedRR-EBM-Sufficiency/04_experiments/EXP-WWW-FIVEBENCH-UNIFIED-001/preparation_001/unified_retrieval_001/retrieve_unified.py`：逐分片 mmap 和内积，接口文头明确 No ANN。
- 同目录旧计划 `五数据集统一库与双服务器执行方案.md`：旧索引排队停止，当前全库采用分片精确检索；未来近似索引属于另一个服务格式。
- `UNIFIED_FORMAT_PROBE.json` 保存的 PubMed 包元数据当时为 `index_ready=false`；旧 `index/medtext/medcpt` 是 240,815 行教材和 StatPearls 向量目录，不是含 PubMed 的全库 FAISS 成品。

因此要复用的是已有向量、原文、行轴、编码器和 BM25；不能把“网站尚无完成的全库 FAISS generation”概括成“服务器缺少所有 dense 检索资产”。本轮现有 SSH 无密钥登录尝试失败，未登录 YHT 或 ZZP，更没有全机搜索；不能排除别处存在历史 FAISS。没有向实验主控发消息、启动新实验、读取活动 SQLite/WAL、扫描向量或重编码。

## 阿里 ECS 最新截图的边界

新增数据盘为 460 GiB，现有 SQLite 约 64.23 GB、原向量约 74.16 GB、原 Llama 权重约 16.06 GB；容量足以容纳目前材料并留出余量，前提是盘实际可用且空闲空间满足要求。ANN serving 可不带全部原 npy，但 E 盘原导出保持不动。

终端截图显示总内存 3.4 GiB、available 1.5 GiB、swap 0。新增 `nvme1n1 460G` 的 FSTYPE 空白，截图没有挂载列；不能把它当作已经可写入的网站目录。`nvidia-smi` 是 command not found，不能单凭这一条证明没有 GPU，更不应直接安装提示中的 NVIDIA 软件。

仅确认这些信息即可，不格式化、不分区：

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
df -hT
lspci | grep -Ei 'VGA|3D|NVIDIA'
```

当前磁盘容量解决了存储限制，未解决 8B 推理内存/算力限制。现有 ECS 可承载网站入口；完整模型服务需要已有适当算力节点或另行确认的资源方案。未采购、扩容、初始化云盘或部署。

## 本轮验证

- 后端与启动/网关静态契约：75 项 PASS，1 条现有 Starlette/httpx 弃用 warning。
- 前端：36 项离线 PASS，包含 Vue/TypeScript/CSS 编译和模拟 API 下组件行为；不是真实模型质量验收。
- `start-dev.bat --check` PASS，确认 Ollama + 显式降级 + 一般知识 fallback 环境；没有启动服务。
- Nginx 仅静态模板契约核对，未在服务器启动或做公网测试。
- 本轮真实 LLM 调用、全库 ANN 构建、系统性质量/性能实验均为 0。
