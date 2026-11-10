# 阿里云 MedCPT 安装及验证

2026-11-09，按用户确认的范围完成：先安装并验证 MedCPT，保留线上六来源 BM25，待取得完整向量资产后再接全库检索。本次没有更换网站检索后端、启动常驻模型服务或构建真实全库向量索引。

## 官方兼容关系

[MedCPT 官方示例](https://github.com/ncbi/MedCPT#searching-pubmed-with-medcpt)直接使用 FAISS `IndexFlatIP(768)` 搜索 Article Encoder 产生的文档向量，查询向量来自 Query Encoder。两者为同一向量空间，使用 float32、CLS、原始内积，不额外做 L2 归一化；查询上限64 token，文档上限512 token。FAISS 是索引和搜索组件，不是 MedCPT 的模型权重。

本次验证遵循这一精确内积示例。将来选择 IVFPQ 等压缩近似索引时，需要另做召回率、延迟和内存评估，不能将其效果等同于官方 Flat 示例。

## 已安装资产

- 模型目录：`/data/zhiwei/models/MedCPT_20261109`。
- Query Encoder：`MedCPT-Query-Encoder/d83a36cc6b8e3a5c5e9d9d6ba156808c1643dcbc`。
- Article Encoder：`MedCPT-Article-Encoder/d05a736da4bb84ee4057b7f7999485be6ed85465`。
- 双模型共16个文件、877,783,460字节，复用 D 盘现存资产。权重SHA-256与官方固定revision的LFS哈希一致，配置/tokenizer等小文件与官方Git blob一致；上传后再次核对完整SHA-256。
- 独立 Python 环境：`/data/zhiwei/runtime/medcpt_cpu_20261109`。主要版本为 PyTorch 2.6.0+cpu、Transformers 4.51.3、Accelerate 1.6.0、FAISS CPU 1.11.0、NumPy 1.26.4。完整版本见该目录 `DEPENDENCIES.txt`。
- 使用兼容Linux/Python3.10的官方分发wheel离线安装，31个安装包上传哈希一致，`pip check`通过。现有网站Python环境未修改。

## 验证结果与范围

独立脚本 `verify_medcpt.py` 依次启动 Query、Article、FAISS 三个子进程，两个编码器不同时驻留；线程数1、batch size 1，使用原始float32模型，没有量化。

- 两编码器均成功产生4×768有限数值向量。
- 四条合成英文文档与四个问题的机械验证通过；四个问题的预期top1均命中，但这不是实际库检索质量评测。
- FAISS分数与NumPy直接内积的最大绝对差约 `7.63e-6`。
- 索引保存/读取后的ID和分数、文档ID映射一致。
- Query阶段峰值RSS约637 MiB，Article约647 MiB，FAISS阶段约46 MiB；全测试约12.7秒。这是小样本验证，不能当作全库并发或生产延迟指标。
- 验证进程退出后释放模型内存，网站与Nginx进程未重启。线上仍为 `combined_bm25`，原医学库及新增三库检索正常，风险模型状态正常。

运行时请求了独立systemd资源上限（850 MiB、75%单核CPU时间、无swap、PrivateNetwork）并只开放验证输出目录写入。瞬时unit执行结束后被卸载，事后查询出现的默认属性不用于证明运行期资源配置；上面的RSS来自子进程实际记录。

## 记录及复查

- 云端安装回执：`/data/zhiwei/runtime/medcpt_cpu_20261109/DEPLOYMENT_RECEIPT.json`。
- 云端验证报告：`/data/zhiwei/verification/medcpt_20261109/smoke_001/smoke_report.json`。
- 模型清单：`/data/zhiwei/models/MedCPT_20261109/MODEL_MANIFEST.json`。
- 本地记录：`C:/Users/30643/.codex/visualizations/2026/11/09/01a1be1f-fe10-78c0-8719-37ad2d897305/medcpt_deploy/`。

再次验证应选择全新输出目录，继续使用独立环境及资源限制，不在网站API进程内临时加载模型。

## 全库接入尚需的资产

本次确认云端原库manifest声明的1224个向量分片均不在服务器，亦无完成的全库FAISS索引；本机定点查找只找到完整编码器，没有确认可直接使用的全库向量。原24,139,516条轴对应约69.06 GiB的768维float32向量。官方PubMed向量不能直接替换现有行轴，必须核对文档映射。

新增三库也没有已确认的MedCPT文档向量；发现的旧BGE预览为512维、897条归一化向量，与MedCPT契约不兼容。今后应取得或生成与真实文档ID一致的向量，在足够资源的独立环境构建并验证索引，再另行接入线上。当前四条合成验证索引不参与网站检索。
