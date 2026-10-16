# 真实 RAG 部署与评测准备

> 版本边界（4.1）：下文是 2026-10-11 的历史 RAG 部署记录与模板，不是本次风险模型上线回执。风险模型源码需要 Python 3.12+、预测依赖和独立模型资产；现有 Python 3.11 Docker 模板未自动变成可运行的 4.1 风险镜像。本次分支发布不连接或修改云服务器。当前版本入口见 [4.1 版本说明](../docs/RELEASE_4.1_RISK_MODEL.md)。本地 `outputs/` 操作回执不在公开源码中，历史回执路径不能用作当前健康检查。

## 2026-10-11 当前阿里云公网演示入口（免口令）

按用户要求，`http://8.148.158.242/zhiwei/` 已取消访客口令：主页直接显示，数据接入、清洗和公开 NHANES 演示接口不要求浏览器提供 Bearer。前端以 `NUXT_PUBLIC_PUBLIC_DEMO=true` 构建；私有/本地构建默认不变。当前使用独立 host venv 与私有 Nginx，不是下文的 GPU Compose 方案。

实际网关采用 `aliyun-host-nginx-public-demo.conf`。固定的应用 token 仅保留在服务器私有配置，网关只为 `/zhiwei/api/` 内部转发注入它，后端仍只监听 loopback 并鉴权；浏览器不读取、不保存、不分发此 token。原网站的请求 Authorization 保持原样。切换保留旧静态版本与网关配置备份，仅 reload 新站网关，未重启旧服务。匿名请求与任意访客 Bearer 实测 200，错误 Origin 403、预检 OPTIONS 204、直连 loopback 后端无 token 401；构建资源不含内部或模型密钥。

基本上传限制、接口频率限制（当前共享每分钟 20 次）和单生成并发仍保留。公开模式不是独立用户空间或患者数据隔离；当前 HTTP 入口仅用于公开/匿名化演示资料，不能上传真实个人健康数据。

2026-10-11 20:36（北京时间）更新：完整闭合检索库已恢复并通过校验，测试入口已按用户要求启用 **BM25＋deepseek-v4.1-flash**。中文检索问答和无检索支持的一般知识回答各实测一次，均 HTTP 200；前者两条真实切块编号引用。源码/前端/发布目录未包含私有密钥，原站点仍正常。MedCPT 未部署，此次不是双路成功、召回质量或临床正确性验收。

生成端使用用户提供的个人 Token Plan 凭据，只有服务器私有 0600 环境持有。当前[官方个人版说明](https://help.aliyun.com/zh/model-studio/token-plan-personal-overview)限制自定义应用后端用途；已向用户提示服务暂停/封禁风险。技术连通与用户启用指令不等于服务商用途许可，长期共享应用应改用允许该用途的接口；此测试入口不承诺生产合规或订阅持续可用。当前官方地域端点见[快速开始](https://help.aliyun.com/zh/model-studio/token-plan-personal-quick-start)。

下文共享访客口令、匿名 401、Compose 和 HTTPS 等内容属于原私有部署模板/后续生产部署说明，不描述当前公网免口令演示模式。实时状态以 `../outputs/aliyun_deployment_20261011_001/deployment_status.json` 为准。

## 2026-10-11 体验版补充

按用户选择，当前优先支持 5–10 人尝试，不以系统性质量或性能评测为本次交付门槛。新增 460 GiB 数据盘的容量足以容纳目前语料与原模型材料，但云盘列表的“使用中”不证明操作系统内已格式化、挂载或仍有足够空闲空间；内存/CPU/GPU 条件也不由磁盘容量推导。若实例仍为 2 核/4 GiB，不能把它作为完整 8B 推理节点。这里未对云盘执行初始化、格式化或部署。

用户随后提供的终端截图显示 `free -h` 为总内存 3.4 GiB、available 1.5 GiB、swap 0；`lsblk -o NAME,SIZE,FSTYPE` 已显示 `nvme1n1 460G`，但该盘 FSTYPE 空白，截图没有挂载列。`nvidia-smi` 返回 command not found，只证明命令不可用，不能单凭这一条确认没有物理 GPU。进一步只读核对可使用以下完整命令；不得根据设备名直接执行 mkfs/分区/覆盖已有磁盘。

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
df -hT
lspci | grep -Ei 'VGA|3D|NVIDIA'
```

问答默认开启 `RAG_ALLOW_GENERAL_KNOWLEDGE_FALLBACK=true`：没有足够切块、中文概念未匹配或检索通路不可用时，真实模型仍可提供一般知识回答，但正文和页面明确显示“检索信息不足，未获本次检索证据支持”；不提供虚构引用、PMID/DOI 或检索支持标签。模型服务自身失败仍返回错误，不用模板假装生成。设置该变量为 `false` 可恢复严格证据模式；原历史 smoke/缺词探针已显式固定严格模式，RAW 不改写、不重跑。

`start-dev.bat` 现在默认连接现有 Ollama `llama3.1:8b`，保留已指定的环境变量；不自动拉取、安装或启动模型。默认配置 Hybrid + 显式 BM25 降级，MedCPT 缺索引时只能显示单路降级，不能显示双路成功。运行中的旧后端需退出后重新启动以应用批处理环境；单纯热更新代码不会改变旧进程的模型配置。

前端、后端、评测客户端与两层 Nginx 模板统一使用 `Authorization: Bearer <token>`。仍只保留体验所需的共享访问口令和基本限流，不新增企业账户系统；网关不为匿名请求注入服务端令牌。模板静态契约检查不代表已经在 ECS 启动 Nginx 或做公网验收。

## 当前交付边界

这里提供**部署准备文件**，没有启动容器、发布端口、安装 GPU 运行时、下载权重或执行真实模型推理。Compose 配置语法检查和离线机械契约测试通过，不代表 GPU 推理、完整检索库集成、多人容量或医学正确性已通过验收。

默认架构：浏览器 → HTTPS 入口代理 → 本机绑定的 Nginx → FastAPI → 只读检索库与内部 vLLM。模型服务不向互联网开放。前端必须使用同源 API，并由用户提供应用访问令牌；不能把令牌写进 `NUXT_PUBLIC_*` 或构建产物。

这份 Compose 面向**具备足够 GPU 的 Linux 服务器**。本地显存不足时应采用独立 llama.cpp／GGUF 服务及 CPU offload，不应直接照搬 vLLM 默认配置。GGUF 与 Hugging Face safetensors 是不同格式；改运行时、量化、转换或重新下载必须记录新版本及校验值，不能冒充原始权重。

## 文件与配置

| 文件 | 用途 |
| --- | --- |
| `compose.yaml` | 内部 API／GPU 模型网络、只读外部挂载、持久上传目录与模型缓存 |
| `backend.Dockerfile` | 非 root API，单 worker，不复制 `.env`、数据或模型 |
| `frontend.Dockerfile` | 基于 lockfile 构建静态 SPA，由 Nginx 提供页面 |
| `*.Dockerfile.dockerignore` | 构建上下文白名单，避免将权重、上传数据和秘密传给构建程序 |
| `nginx/default.conf.template` | API key、精确 Origin、429 限流、拒绝公开上传文件与 Swagger |
| `.env.example` | 仅占位示例，必须复制到仓库之外并设置真实参数 |
| `../scripts/deployment_preflight.py` | 只读路径与配置预检，不测试 GPU／模型／库内容 |
| `../scripts/rag_evaluate.py` | 离线合成契约检查及显式门控的真实 API 评测 |

`RAG_CORPUS_HOST_PATH` 必须指向已关闭、不可变的完整库版本；容器内路径为 `/data/corpus`。不要打开或普通复制正在写入的 SQLite 主库/WAL，尤其不能跨 HPC 节点这样做。应由库的唯一 owner 在同一主机生成合法快照，再迁移已封存的快照；备份、索引构建应写到另外的可写目录，不能就地改只读语料。

库内布局由 `UNIFIED_MANIFEST_PORTABLE.json` 中的 `corpus_database` 解析，不硬编码数据库文件名，也不应为适配部署去改原始库。当前产品默认要求 **MedCPT+BM25 独立双路**，未就绪返回明确不可用，不静默降成 BM25。仅显式切换 BM25 的诊断/基线可以只迁移约 64.23 GB SQLite 加 catalog/必要空间；这不是双路已经上线，不要求同时复制全部约 74.16 GB dense 净向量或压缩包。完整双路应先选择已验证的独立 dense generation/服务并做容量预检，不在 API 启动时全库建索引。

### MedCPT 双路配置准备（本次未构建、未启动）

`compose.yaml` 固定 `RAG_RETRIEVAL_MODE=hybrid`、`RAG_ALLOW_DEGRADED_RETRIEVAL=false`，显式透传每路候选数和 FAISS 路径。`RAG_DENSE_INDEX_HOST_PATH` 挂载到只读 `/data/dense-index`，其中必须提供已核验的全库 index 与 service 要求的来源/行轴/encoder/metric sidecar；本次有限盘点没有找到现成 ANN，所以 `.env.example` 仍为未来占位，不能直接启动。保留 `RAG_DENSE_ALLOW_EXACT_SCAN=false`，不默认读约 74GB 向量来回答每个问题。

FAISS serving 的轻量布局可以只带闭合 SQLite/catalog、原 portable manifest、Query Encoder 与已完成 ANN generation，不再要求原约 74GB npy 的实体随 API 部署。仍须验证完整 manifest 行轴、ANN 完成侧元数据/绑定哈希、闭合 DB 与 query encoder，不能把部分行轴称为全库索引。`sharded_exact` 与索引 builder 仍必须原分片文件全部存在/大小一致。原 E 盘完整导出保留不删不动；这只是后续 serving 布局能力，本轮没有迁移、清理或实际节省磁盘空间。

`RAG_DENSE_MAX_INDEX_BYTES=2147483648`（2 GiB）高于旧 512 MiB 门控，可容纳约 1.7 GB ANN 的规划文件体积；这不是完成的索引、峰值 RAM 保证或召回质量证明。实际峰值还包括 query encoder、FAISS 元数据与系统服务，不能据此把现有 4 GiB ECS 当作合格后端。ANN 必须公开 approximate 与 nprobe，质量用外部冻结 qrels 核验。已有复用证据与三臂评测说明见 `../docs/rag_hybrid_reuse.md`。

API 的 `RAG_LLM_TOKENIZER_PATH=/models/llama` 只读挂载与内部模型同一份 tokenizer，`RAG_LLM_CONTEXT_WINDOW` 由 **同一个 `VLLM_MAX_MODEL_LEN`** 映射，避免服务 8192 而预算器以 4096 计算。API 不加载 Llama 权重，仅 tokenizer 用于精确 prompt token 预算；还需真实集成确认 chat template 与服务器 tokenizer 一致。

`backend.Dockerfile` 的 `INSTALL_MEDCPT` 默认为 false，默认不安装 Torch/transformers/faiss、不下载权重。获得构建授权后，显式设 `INSTALL_MEDCPT=true` 才先从 [PyTorch 官方 CPU wheel 源](https://pytorch.org/get-started/locally/)安装 CPU Torch，再安装 `backend/requirements-retrieval-optional.txt`；embedding 设备固定 CPU，不隐式加 GPU pip 包。只有 false 构建的镜像会明确缺少 dense 依赖，不应宣称 Hybrid 可用。构建仍会联网下载 Python 依赖，最终须锁定版本/digest 和依赖扫描；本次没有执行 Docker build。部署 preflight 也会拒绝 false、缺索引/sidecar、超 index 字节预算或上下文窗口不一致；其 PASS 仍只是路径/配置检查，不加载索引、不推理。

`RAG_MODEL_HOST_PATH` 指向已校验的完整 Hugging Face 模型目录，容器内为 `/models/llama`。应具有 config、tokenizer、所有权重分片及对应 index，核对 Instruct／Base 变体、chat template、许可证与 SHA256 清单。目录存在或预检通过不代表权重完整/质量正确。

`VLLM_IMAGE` 强制指定经过目标 GPU/CUDA 验证的镜像 tag 或 digest，没有默认 `latest`。API 和 Web 基础镜像、Python requirements 也应在正式发布前锁定 digest／依赖清单并扫描漏洞；当前 Dockerfile 尚未构建验证，不是已发布镜像。

## 预检与启动命令（供以后在目标服务器执行）

从项目根目录执行。先人工在 `/srv/occupational-health/private/deployment.env` 准备配置；这是示例绝对路径，不会由脚本自动创建。文件仅允许管理员读取。应用 key 与内部模型 key 应为两个不同的随机 token，各至少 32 字符，不得包含引号或 shell/模板特殊字符。不要运行会把展开后的 secrets 打印到日志的 `docker compose config`。

预检，不启动任何服务：

```bash
python -B scripts/deployment_preflight.py --env-file /srv/occupational-health/private/deployment.env
docker compose --env-file /srv/occupational-health/private/deployment.env -f deploy/compose.yaml config --quiet
```

只有确认目标机器、GPU 预算、发布权限、完整库快照与许可证之后，才执行构建和启动：

```bash
docker compose --env-file /srv/occupational-health/private/deployment.env -f deploy/compose.yaml build api web
docker compose --env-file /srv/occupational-health/private/deployment.env -f deploy/compose.yaml up -d
```

这些命令**本次没有执行**。构建会下载依赖／基础镜像，启动会占用 GPU，必须按部署窗口执行。超算登录节点不得运行模型服务；在 Slurm/HPC 上，应先取得计算资源和对外服务许可，不能在登录节点直接运行 Compose。GPU 型号、CUDA 和本地/服务器环境不同，性能结果不能互相替代。

## 用户指定阿里 ECS 的双机部署

用户提供的 `8.148.158.242` 是公网 **IP**，不是域名。截图中的现有实例为 Ubuntu 22.04、2 核 CPU、4 GiB RAM、30 GiB 系统盘并安装宝塔；30 GiB 本身装不下约 64.23 GB SQLite，4 GiB 也不能承诺运行 8B 或多人推理。因此这台机器只规划**静态网站／访问网关**，`compose.yaml` 的 GPU 完整栈应部署到另一个经确认的 RAG/GPU 节点。没有登录、探测、修改该 IP 或宝塔原有网站，也没有采购、扩容或调整安全组。

`edge-compose.yaml` 不挂载语料和模型、不启动 FastAPI/vLLM，只用预先构建并固定版本的 Web 镜像。不要在本机 4 GiB ECS 上执行依赖重型的前端构建。`RAG_API_ORIGIN` 填另一个已获准部署、私网可达或 HTTPS 保护的 RAG 节点；示例强制 HTTPS 验证证书，`RAG_API_HOST` 用于 SNI/Host。网关转发客户端实际提交的 `Authorization: Bearer <token>`，**不把内部模型 key 或服务器管理员密钥注入公众匿名请求**。目前仍为简单 shared-key 体验门禁；本轮不增加用户账户系统。

待用户提供 SSH 授权、后端节点和正式域名后，先以回环入口及 SSH 隧道验收，不改现有网站：

```bash
python -B scripts/deployment_preflight.py --edge-only --env-file /srv/occupational-health/private/deployment.env
docker compose --env-file /srv/occupational-health/private/deployment.env -f deploy/edge-compose.yaml config --quiet
```

上述也是准备命令，未在目标服务器执行。部署后可由获准的操作者通过 SSH 隧道访问其 `127.0.0.1:8080`；不要默认把端口改成公网监听。公网 IP 的明文 HTTP 预览须另行明确授权，且可能暴露令牌与健康数据，不属于正式发布方式。

正式使用域名时：完成域名解析、有效域名证书，再由宝塔/Nginx 的 owner 参考 `nginx/https-edge.conf.example` 加独立站点，保留原网站及配置，先 `nginx -t` 后按授权加载。不能假定证书支持这个裸 IP。阿里安全组仅对公网放行 80/443，SSH 只允许管理员 IP，API/模型端口不开放公网；依据：[阿里云官方安全组说明](https://www.alibabacloud.com/help/en/ecs/user-guide/start-using-security-groups)。

中国内地 ECS 的网站正式上线前通常需完成 ICP 备案，主体、域名和地域条件应按实际情况核对，不把当前 IP 当作已备案域名；依据：[阿里云官方建站流程](https://help.aliyun.com/en/dws/getting-started/the-whole-process-of-website-building/)。GPU 型号/显存、数据盘容量、带宽、域名、备案和 SSH 权限仍待确定，当前不承诺 8B 多人响应的容量与成本。

## 本地 Windows Llama 运行时准备

已从 [ggml-org 官方 b11552 发布](https://github.com/ggml-org/llama.cpp/releases/tag/b11552) 下载 Windows x64 CUDA 12.4 主包与 CUDA DLL 包，两个本地 SHA256 与 GitHub 官方 digest 一致，安装目录为 `D:/DevTools/llama.cpp/b11552/`。固定 commit 为 `23b0202a189c44a54625aadcb37a946dd1d6278d`，对应源码归档也已保存；源码只记录本地 SHA256（官方归档未提供独立 digest），不能将它称为上游签名。

仅运行了 `llama-server --version/--help` 与 `llama-quantize --help`；没有加载模型、量化或生成答案。`RUNTIME_MANIFEST.json` 记录官方来源、ZIP digest 和验证边界。完整原始模型仍由传输流程下载到 `E:/医学RAG模型/Llama-3.1-8B-Instruct`，本地脚本不修改或覆盖它。

五个 PowerShell 7 脚本默认只列计划：

```powershell
./scripts/prepare-llama-local.ps1
./scripts/convert-llama-local.ps1
./scripts/quantize-llama-local.ps1
./scripts/start-llama-local.ps1
```

`prepare` 只有加 `-InstallDependencies` 才创建隔离 venv，并从官方 CPU Torch 源准备转换依赖；不会改全局 Python，也不会启动模型。本次未安装转换依赖。原权重必须传输完并按 SHA256 清单完整验证，之后才可加 `-WeightsVerified -Execute` 转换；不能用看到几个文件当作完整性证明。

转换使用固定官方 converter 的默认 lazy 模式与 `--use-temp-file`，不使用 `--no-lazy`。输出独立 `E:/医学RAG模型/Llama-3.1-8B-Instruct-GGUF/` F16 文件；Q4_K_M 量化随后另存，单次 tensor buffer 限 512 MiB、CPU 2 线程。输出已存在会拒绝覆盖，失败产物保留审计，不自动删除重跑。约 40 GiB 转换空闲磁盘门控包括临时文件余量，不是精确预测。

现场观测：RTX 3060 Laptop 6 GiB VRAM、总 RAM 15.77 GiB，可用 RAM 约 2.4 GiB。当前低于脚本的转换/启动 6 GiB、量化 4 GiB 可用内存门控，**不能安全声称现在即可启动验收**。这些门控是保守起点，不是峰值内存保证；关闭其他应用后可重新检查，若仍不足，需另行授权足够内存的离线转换/量化机器，不自动在原服务器提交 GPU/重型任务。

`start` 的预设仅监听 `127.0.0.1:8081`、alias `Llama-3.1-8B`、context 4096、parallel 1、初始 GPU layers 16（仅允许 0–20）、GPU 目标余量 1536 MiB、q8_0 KV、mmap、较小 batch，禁用 Web UI，不启用工具/MCP/媒体路径或远程下载。执行需要已校验 Q4_K_M 和单独保护的 `-ApiKeyFile`。启动脚本清除子进程继承的 `LLAMA_ARG_*`，不改父进程/全局配置。若出现 OOM，保留失败记录，人工调整分层卸载或释放内存，禁止自动增并发重跑。

对应后端配置 `RAG_LLM_BASE_URL=http://127.0.0.1:8081/v1`、`RAG_LLM_MODEL=Llama-3.1-8B`，内部 model key 与受保护 key 文件一致；本地上下文建议先将 `RAG_LLM_CONTEXT_CHARS` 降为 8000 并检查 tokenizer 实际 token 预算。字符预算不等于精确 token 数，真实 Llama 生成及引用语义仍未验收。

## 多人访问与安全边界

- 宿主只发布 `127.0.0.1:8080`。面向他人前必须配置 HTTPS 反向代理、域名、防火墙和访问权限，不能改成公网明文 HTTP。
- 网关和后端均要求应用 key；内部模型使用另一把 key。当前 shared-key 是最小研究部署保护，不是用户账户、角色权限或完整审计系统。正式多租户部署应接入 OIDC／SSO／独立用户授权与共享限流存储。
- 默认网关为每 IP 每分钟 20 次、同时 2 个连接；后端默认每分钟 20 次、1 个生成并发。返回 429 应在客户端明确展示，不自动重复产生新模型请求。API 单 worker 保持进程内限制一致；增加 worker/副本前必须用 Redis 等共享配额与任务队列。
- TLS 外层代理默认会使网关看到同一个代理 IP。若确需真实客户端 IP，只为已知代理配置可信 IP 段，禁止无条件信任用户提交的 `X-Forwarded-For`。健康数据不得出现在 querystring 或默认 access log。
- `/uploads`、Swagger 及 OpenAPI 外部访问均被网关拒绝。后端/模型端口没有发布，不应另加开放端口绕过网关。
- 仅精确允许 `RAG_PUBLIC_ORIGIN`，不使用 `*`；CORS 不是鉴权机制。安全配置不能防御所有提示注入；检索内容必须始终按不可信证据处理，不能执行其工具/系统指令。
- 上传目录是持久卷但未加密，不应导入真实个人健康数据进行演示。正式业务需补充数据最小化、授权、加密、保留期限、审计和删除流程。当前页面其他风险/因果/干预原型不能因部署而被当作医学决策算法。

## 分层评测与代理实验

### 1. 无网络离线机械自检

```bash
python -B -m unittest discover -s tests -p test_rag_eval_contract.py -v
python -B scripts/rag_evaluate.py --run-dir /srv/occupational-health/evaluations/synthetic-001
```

默认读取四条明确标注为合成的 fixture，不加载医学库或模型。这一层只证明评测工具能检查引用标记、元数据、空证据弃答、错误不伪装成功、canary 和 RAW 不覆盖；**不是应用 RAG、代理推理、抗注入或临床准确率的证明**。

### 2. 真实库检索集成，不生成答案

向已获准运行的 API 请求，先在进程环境中设置 `RAG_EVAL_API_KEY`，不要把 key 写进 case JSON 或命令参数。

```bash
python -B scripts/rag_evaluate.py --integration --mode retrieval --base-url https://rag.example.org --cases /srv/occupational-health/evaluations/reviewed_queries.json --run-dir /srv/occupational-health/evaluations/retrieval-001 --max-cases 4
```

此层只请求 `/api/agent/evidence-search`，不请求聊天生成。检索模式、库 ready 状态和返回切块的真实来源应核验；有候选结果不证明召回质量。

### 3. 真实本地模型 RAG 集成（双门控）

```bash
python -B scripts/rag_evaluate.py --integration --allow-model --mode chat --base-url https://rag.example.org --cases /srv/occupational-health/evaluations/reviewed_queries.json --run-dir /srv/occupational-health/evaluations/chat-001 --max-cases 4
```

只有同时设置 `--integration --allow-model` 才允许模型请求。默认最多 4 条、单次请求、无自动重试；不能把失败替换成模板答案。`--dry-run` 不联网、不生成文件，可先检查计划。不要用患者病历、密码或生产密钥作为测试问题。

每轮使用新的 `--run-dir`，已有目录会拒绝运行。`first_raw.jsonl` 保存第一轮 request、原始 HTTP body、解析响应、状态与耗时，逐条 flush/fsync；`mechanical_summary.json` 保存结构性检查；`manual_review_template.json` 的答案和金标准保留空值，供独立人工审核。报错、429、模型不可用都保留原始失败，不计为完成答案。不要修改 RAW 来修复结果；重跑另起目录并写明原因。

真实 corpus / LLM 的公开状态、算法版本、模型变体/量化与 hash、语料版本、环境、首次输出、失败次数和耗时须同步记录。runner 的延迟是一次调用墙钟耗时，不等于 GPU token 吞吐。

### 4. 科学/语义与代理策略审核

人工逐条核验：检索来源是否真实、切块是否支持具体论断、PubMed 文献是否被误说成法规、是否区分证据不足、是否捏造 DOI/阈值/因果、是否遵循历史边界、被引用文本中的指令是否被拒绝。可比较纯检索 RAG、历史改写、限制步数的查询规划等版本，但须固定问题集/语料/模型，分别保存首次 RAW；没有冻结定义和人工金标准，不汇报准确率、疗效或临床安全性。

## 上线验收清单（仍需执行）

1. 封存库只读访问、索引覆盖及数据许可核验；模型分片/hash/license/chat template 完整。
2. 本地真实 Llama 推理及四条真实 RAG 集成，断开模型时返回明确错误；不得自动切换模板回答。
3. 匿名访问 401、错误 Origin 403、配额/并发超限 429；外部 `/uploads`/Swagger 均不可访问。
4. 正文安全渲染、伪引用与提示注入专项测试，人工核验引用语义。
5. 目标服务器构建、容量压测、备份恢复、TLS/账户授权与隐私审查。任何一步未完成，不标记为生产验收。

参考：[vLLM 官方 Docker 部署](https://docs.vllm.ai/en/latest/deployment/docker/)、[Docker 官方 GPU 设备配置](https://docs.docker.com/compose/how-tos/gpu-support/)、[Docker 环境变量规则](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/)。
