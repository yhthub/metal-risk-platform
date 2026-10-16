# RAG 与单人动态可视化交付记录

日期：2026-10-11。项目：`D:/gradstu/gard1/vite+vue3`。

## 已实现

- 两个 RAG 评测客户端使用与当前 `ApiGuard` 一致的 `Authorization: Bearer`。禁用自动重定向、环境代理和密钥回显；没有绕过鉴权或把错误响应当成功。
- 原生 Ollama 适配复用已安装的 `llama3.1:8b`（Q4_K_M），每次请求绑定 4096 上下文、512 输出及单并发预算。原始迁移权重未改，没有下载新模型、手工转换原始权重或启动全库索引构建。
- BM25 全库检索零 AND 命中时，先有界检查字面词存在性，避免未知词被丢弃后凭高频词补召。公开缺词诊断，不声称某个科学主题不存在证据。
- 单人页保留统一的卡片与图表风格，输入实时重绘；增加每项样本、单位及必要情境选择和口径改换确认。缺失不补零，不构造假采样时间。
- 原趋势图换成参考可比性矩阵；其余图用可计算的参考占比、排序、偏移、录入状态及覆盖率代替虚构的群体百分位、器官归因、Z-score 和健康综合分。群体模块原逻辑未改。

参考规则与来源见 [单人输入契约](individual_input_reference_contract.md)。不同参考不合成为安全线；条件不符、无权威匹配来源或未确认口径时不画比较值。该模块目前为客户端计算，不等于单人档案持久化、预测模型或临床验证。

## 真实 RAG 运行与未完成项

检索使用 E 盘闭合导出，目录报告 24,139,516 个切块，其中 PubMed 23,898,701 个；这些不是独立论文计数。预检读取已完成目录信息和文件身份，不扫描全表、向量或 YHT 运行中的数据库。

首次固定两题、每题一次的真实功能 smoke：

| 用例 | 首次结果 | 验收边界 |
| --- | --- | --- |
| cadmium kidney | HTTP 200；Ollama 真实生成；引用编号检查通过；37.687 秒 | BM25→证据→本机模型→机械引用检查，不是医学准确率 |
| quazylophenezn42 kidney | HTTP 504；8.016 秒检索超时 | 失败保留；从失败 HTTP 不能推断模型调用为零 |

原始整轮仍为 FAIL：`outputs/rag_hybrid_20261011/ollama_bm25_functional_20261011_001/` 中 `manifest.json`、`first_raw.jsonl` 和 `mechanical_summary.json` 未被覆盖。首例与前端构建有重叠，不能当独立性能基准，也不能据此确定超时原因。

缺词路径修正后的独立回归：HTTP 200、`insufficient_evidence`、0.047 秒、没有模型调用、语料身份未变。原机械检查误读字段层级，原 `absent_term_regression_001.json` 的 FAIL 仍保留。独立 `absent_term_regression_offline_review_001.json` 为 `OFFLINE_REVIEW_PASS`：只纠正诊断路径断言，模型与文件身份的运行时断言沿用原记录，没有再请求语料或模型。

实际本机 API socket 状态和浏览器 `/agent` 页面已核对：显示现有模型就绪、完整库预检、BM25 单路，以及 MedCPT 不可用。该观察是状态展示验收，不代替一次真实生成；真实生成依据上述 RAW。

**完整 MedCPT+BM25 未验收**：Query Encoder 文件和原向量可复用，但缺少已完成的全库独立 FAISS 索引。默认 Hybrid 缺依赖时明确拒绝；当前功能测试显式用 BM25，不是静默降级。还需完整索引、真实 Query Encoder 运行和有可信相关性标注的独立召回评估。未部署到阿里云，没有购买或变更云资源，也没有联系实验主控或启动 YHT 实验。

## 机械与视觉检查

- 最后一次隔离运行：Python `180 passed, 2 skipped, 1 warning`。两项实际 FAISS 微型 fixture 测试因未安装可选 FAISS 跳过；PASS 不代表完整模型/双路能力。
- 最后一次代码状态的前端：单人页 32 项、RAG 页 30 项离线检查通过；包含真实 Vue watcher 和 ECharts option 检查，不调用语料或模型。
- 生产构建 exit 0；仍有原有 Browserslist、sourcemap、PURE 注释、Tailwind CSS 语法和大 chunk 等警告。没有把构建成功说成无警告。
- 曾在 build、Python 和前端测试并行时遇到一次鉴权 loopback 测试的 `WinError 10053` 传输中断：179 passed、1 failed、2 skipped。根因未确定，未修改或放宽断言；build 完成后单独执行全套得到上述 180 passed。该测试波动不能解释为鉴权断言成功，也不能归因于 CPU 或安全软件。
- 已在浏览器实际检查空输入、3 项合成实测值、铅数值更新和样本口径改变的保护。矩阵文字溢出、参考线标签裁切及下部图表标签布局按实际渲染修正。截图数据仅为合成 QA 输入，不是用户健康资料。
- 文件差异空白检查通过；已有 `.gitignore` 改动保留。

可重现测试（PowerShell，项目根）：

```powershell
$env:PYTHONPATH='D:/gradstu/gard1/vite+vue3/backend'
python -m pytest backend/tests tests -q
```

前端目录：

```powershell
node --test tests/individual-profile.test.cjs tests/rag-frontend.test.cjs
pnpm build
```

本机运行配置见 [Ollama 使用说明](rag_ollama_local.md) 与 `deploy/.env.ollama.example`。仅绑定 loopback 的本地测试不代表公网安全或部署验收。

截图：[占比、雷达与矩阵](../outputs/individual_input_20261011/dynamic_single_profile.jpg)，[最终排序、录入状态、偏移与覆盖率](../outputs/individual_input_20261011/dynamic_single_profile_lower_final.jpg)。覆盖率保留仪表外形，用蓝色进度环和灰色背景，取消会遮挡数值的指针；没有绿色“安全区”。

收尾已停止本次临时前端预览、API 和本次启动的 Ollama serve 进程；安装程序、现有模型及 E 盘语料保持不动。RAW 中 `service_retained=true` 描述首次 smoke 完成当时的状态，不代表收尾后仍运行。
