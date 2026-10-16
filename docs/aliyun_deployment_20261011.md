# 阿里云固定配置的独立轻量部署（2026-10-11）

> 历史现场记录：以下“当前”均指 2026-10-11 的记录时点，不是 4.1 风险模型版本的实时状态或上线回执。4.1 本次仅发布源码分支，未执行云端部署；请参考 [4.1 版本说明](RELEASE_4.1_RISK_MODEL.md)。私有配置和本地操作备份不随仓库发布。

## 当前实际上线状态

根任务已通过经人工核对指纹的专用 SSH 完成真实部署。入口为 [知微网站](http://8.148.158.242/zhiwei/)。这台实例保持原配置；新空 460 GiB 数据盘已按明确授权初始化为 ext4 并独立挂载到 `/data/zhiwei`，UUID 为 `25986262-9cf2-4d7b-a42f-40861c30ac5d`。30 GiB 系统盘和原网站目录未格式化或迁移。

实际采用独立 host runtime：`/data/zhiwei/runtime/venv`、私有提取的 Nginx、`zhiwei-api.service` 和 `zhiwei-nginx.service`。Docker Hub 连接失败，因此下文 Docker profile 仅是准备方案，未运行；未改 Docker daemon／镜像源。新 API 只监听回环 `127.0.0.1:18000`，HTTP 80 新入口将 `/` 代理到既有 3000，将 `/zhiwei/` 用于新站。原 3000、3001、8501 仍返回 HTTP 200，旧容器没有重启。

已通过基本页面、静态 JS/CSS MIME、鉴权、公开 NHANES 一键群体导入检查；未完成浏览器图形操作验证，也不是系统性 RAG 或临床验收。HTTP 演示入口不加密，仅使用公开／匿名演示数据。网站独立访问口令在服务器 `/data/zhiwei/private/deployment.env` 的 `RAG_API_KEY`，不是模型 API Key；管理员可在已登录 Workbench 执行 `grep '^RAG_API_KEY=' /data/zhiwei/private/deployment.env` 查看并私下分发。

完整闭合 corpus gzip（26,555,436,386 字节）正在由 E 盘传输，SHA256 为 `daf563e03864fd9c8261659ab77012583da215e8e69349efc983d2eb1eacba7c`，解压后预期 64,232,280,064 字节。E 盘原件保留，未复制活库 WAL。`zhiwei-corpus-restore.service` 是一次性、有时限、无网络的恢复任务：等最终上传文件，再做完整 SHA、gzip CRC、大小、只读结构及空间检查；`.part` 不作为正式库使用。资源限制为 256 MiB／50% CPU，独立收据 `/data/zhiwei/corpus/restore_receipt.json` 如实记录等待／失败／通过。传输和校验完成前不能声称检索已就绪。

新 API 开启 `RAG_REQUIRE_RESTORE_RECEIPT=true`：即使正式 DB 文件出现，也必须每次读取完整 `PASS/completed` 收据才能进入 SQLite。恢复收据只含公开语料元数据与检查结果，0644 允许 API 只读；包含密钥的部署环境文件仍是 0600，权限未放宽。

用户指定 `deepseek-v4.1-flash` 的一次交互式 Token Plan 连接探测已返回 HTTP 200／正确模型／`OK`，用量 9 输入与 1 输出 token。仅确认技术连通，未将提供的个人套餐密钥持久化或接入共享网站；当前共享生成配置 `RAG_LLM_ENABLED=false`。生成仍待允许网站后端用途的接口，不能把探测通过说成端到端 RAG 已上线。固定资源下服务器先用既有 FTS5/BM25，不是 MedCPT+BM25 双路已上线。

如需撤回本次新站入口，只停止 `zhiwei-nginx.service`、`zhiwei-api.service`；原 3000／3001／8501 继续保持原状。暂停恢复只操作 `zhiwei-corpus-restore.service`，不要格式化盘、删除语料或执行宽泛的容器关闭／系统重启。既有 SSH key、公钥、数据盘和所有备份保留，另按用户指令处理。

以下为部署前 profile 与验证历史；与上述当前实况不一致处，以本节为准。

本 profile 子任务当时只准备本地配置，未由该子任务操作服务器。后续根任务的实际操作见上节。

## 已确定的方向与尚未确定的信息

用户选择：现有阿里云 ECS 承载整站和检索，生成调用已有外部 Ollama／OpenAI 兼容模型接口，不新增实例。用户提供截图显示约 3.4 GiB 总内存、1.5 GiB available、无 swap。后续主任务已核对新空盘 `/dev/nvme1n1`（serial `7xvisc5rkfdijwwg01d0`），用户已批准对此准确目标初始化、挂载；这属于独立的根任务操作，本 profile／预检不会执行它。实际完成的文件系统和挂载点仍以操作后的服务器输出为准。

当前轻量方案是**完整闭合 SQLite FTS5/BM25 检索＋外部真实模型生成**。不是 MedCPT+BM25 双路已经部署，也不是阿里云本机运行 Llama-3.1-8B。没有可靠切块时保留已实现的一般知识回答和“检索信息不足”提示，不伪造引用；外部模型不可达或鉴权失败仍明确报错。

此前给定的是 Token Plan 个人版 endpoint。阿里云官方明确将个人版限定于编程／智能体工具的交互使用，**不能用于自定义应用程序后端**，因此它不能接入本网站，即使用户可以在编程客户端调用、用户仅 5–10 人也不改变该限制。[官方使用范围](https://help.aliyun.com/zh/model-studio/token-plan-personal-overview)。本分任务未读取、接收或调用真实密钥，example 已撤回个人版地址，恢复 `https://REPLACE_WITH_APPLICATION_ALLOWED_MODEL_HOST/v1`，provider 保留 `openai_compatible`。

需改用允许网站应用后端的按量服务／已授权外部接口；不能仅把个人版 key 换一个 URL 使用。模型名仍保留用户选择的 `deepseek-v4.1-flash`，但该模型在最终合规 endpoint、账号与地域的可用性未确认，模板不是可运行配置。实际 API key 不在模板中；接口使用权、出站可达性、`/models` readiness 和响应模型名匹配仍需主任务安全确认。`localhost`／`127.0.0.1` 在容器中不是用户本地电脑。通过外部模型回答会把问题及必要证据切块送给该服务，不默认发送完整上传表格，演示阶段勿输入身份信息或个人病历。

## 独立部署范围

新增 `deploy/aliyun-compose.yaml` 使用独立项目名 `occupational-health-aliyun`：

- `api`：现有 FastAPI 镜像、单 worker、显式 BM25，挂闭合语料只读，上传目录独立可写。1 GiB 内存、1 CPU、单次生成和批量导入、较小数据集缓存。容器限制旨在保护原网站，不构成吞吐或峰值内存保证；大清洗任务仍可能触及限额，应分批处理。
- `web`：本地预生成的 Nuxt 静态页面和现有 Nginx 网关，128 MiB／0.25 CPU。只监听服务器回环 `127.0.0.1:8080`（最终需核实未占用；可改独立回环端口）。不公开 API／模型端口。
- bridge 网络保留外网出站；不能沿用旧 GPU compose 的 `internal: true`。API 不安装 MedCPT／Torch，不加载 HF 权重，不做 74 GB 向量全扫。
- 保留当前 shared Bearer 体验门禁：浏览器输入访问 token，经网关原样转发给 API。模型 key 只由 API 使用，不进前端包，不注入匿名请求。
- 原站不会被同名容器替代，原数据库／进程／安全组保持不变。没有默认改 80/443，也不接管当前已有的 3000/3001/8501 等服务。

`api` 镜像从现有 `deploy/backend.Dockerfile` 以 `INSTALL_MEDCPT=false` 在开发／构建机器预构建；镜像包含 `backend/app/data` 的公开 NHANES 样本。`web` 用新增 `deploy/frontend-prebuilt.Dockerfile` 只打包预生成 `.output/public`。小 ECS 不运行 Node／pnpm 构建。Compose 仅使用版本化镜像，不自行下载模型／构建前端。

## 语料与磁盘要求

优先迁移已存在的 E 盘闭合导出中的 `UNIFIED_MANIFEST_PORTABLE.json`、`00_catalog/EXPORT_PROGRESS.json`、`00_catalog/SNAPSHOT_PROVENANCE.json`、manifest 指定的 `corpus_database`。数据库约 64.23 GB（十进制），已带 FTS；保留原相对目录轴和元数据，不为部署重写检索库。BM25 当前不需要复制其余向量、原模型权重或量化模型。完整导出原件继续保留在 E 盘。

数据应位于**已核实、已挂载的独立持久数据盘**，不能误落到 30 GiB 系统盘。新空盘初始化授权已限于上述准确 device／serial；不得把此授权扩展到系统盘、其他盘或任何未知内容盘。本 profile 仍不含 `mkfs`、分区、清盘或挂载命令，磁盘工作由根任务独立执行并核对结果。

配置中 `ALIYUN_DATA_ROOT` 指向实际数据盘挂载点；`RAG_CORPUS_HOST_PATH` 和 `RAG_UPLOADS_HOST_PATH` 为其独立子目录。上传目录由 API UID 10001 拥有且不对其他用户开放，不能放在只读语料里。保留至少 8 GiB 空闲是本 profile 的最低运行／上传余量，不是 Docker 镜像在系统盘的空间验收；Docker root 和原服务可用内存也须单独核实。

## 域名或同端口子路径

最新根任务信息：目前没有 80 端口监听，旧网站仍在 3000；拟以**新独立** 80 入口将根路径 `/` 代理至既有 3000，将 `/zhiwei/` 代理至本项目回环 8080。这个拓扑不占用或替换既有 3000，不迁移旧网站或旧数据库；截至本分任务复核，它仍是准备方案，不是公网入口回执。原根路径代理需完整保留旧站的 assets／API／WebSocket 行为，发布前分别检查直接 3000 和新增 80 根路径。不得覆盖未知原站配置，80 空闲也不证明云安全组已允许或 HTTPS 已提供。

可采用同一现有入口下的 `/zhiwei/`：在开发机生成静态站前设置 `NUXT_APP_BASE_URL=/zhiwei/` 和 `NUXT_PUBLIC_API_BASE=/zhiwei`；外层代理须剥离 `/zhiwei/` 前缀，将 `/zhiwei/api/...` 转发为容器网关的 `/api/...`，且 assets 请求同样剥离。这两个 Nuxt 值是**构建期**设置，容器运行时仅改 `ALIYUN_BASE_PATH` 不会重写静态页面。新路径先在副本配置中验证，不影响根路径原网站。`RAG_PUBLIC_ORIGIN` 仍仅为实际 scheme/host/port，不含 `/zhiwei/`。

外层代理如果由宿主机 Nginx 承担，可以直接使用 `127.0.0.1:3000`／`127.0.0.1:8080`；如果是另一个 bridge 容器，其 `127.0.0.1` 指向自身，不能这样直接连接宿主机回环服务。不要为绕过这个问题公开 API／8080、改旧网站监听地址或接管旧容器网络。具体代理执行由主任务选择已核对可用的独立入口方式。

新增 `deploy/aliyun-gateway.conf` 和 `deploy/aliyun-gateway-compose.yaml` 提供独立 host-network 网关选项。项目名为 `occupational-health-aliyun-gateway`，只挂自身配置只读，不挂旧配置／Docker socket，不改旧容器。host network 让这里的回环地址确实属于该服务器；它仅由 Nginx 新监听 HTTP:80，不公开新的 API／模型端口。启动前读取 `/proc/net/tcp`／`tcp6` 检查是否已有 LISTEN:80，已有监听立即拒启，随后先 `nginx -t`；root 已报告 80 空闲仍不能跳过这个启动检查。保留旧根路径／API／assets／WebSocket，并将新前缀请求剥离转发到 8080；`/zhiwei` 用 308 跳转到 `/zhiwei/`。访问日志关闭、运行错误日志丢弃，避免记录 token／请求内容；syntax 检查仍保留终端诊断。网关 128 MiB/read-only/tmpfs 和最小必要 capabilities 是保护边界，不是吞吐保证。

外层采用流式请求，26 MiB envelope 配合 API 25 MiB 文件限制；**内层网关 `/api/` 同样需要 `proxy_request_buffering off`**，否则内层 16 MiB tmpfs 可能因大上传缓存不足失败。本分任务没有替根修改内层模板，实际发布前需确认此项已处理。

如果改用独立域名／原 IP 根路径入口，则按实际入口重新预生成根路径版本。现有证书、域名和 HTTPS 状态未知，不能宣称已有安全公网入口；仅 HTTP:80 的体验入口会以明文传访问 token／用户数据，应仅用于公开演示数据并明确此限制，正式个人数据应经 HTTPS。

## 部署包白名单

完整 Git 工作树、D 盘研究材料和 E 盘整体导出都不应递归打包。推荐分为三个明确包：

1. 应用版本包：`deploy/aliyun-compose.yaml`、`deploy/aliyun.env.example`、两份被使用的 Dockerfile／对应 dockerignore、`deploy/nginx/default.conf.template`、`scripts/aliyun_preflight.py`、本文；如果选新增 80 host-network 网关，再显式加入 `deploy/aliyun-gateway.conf`、`deploy/aliyun-gateway-compose.yaml`。同时包含预构建版本化 API／web 镜像的导出文件和非敏感版本／SHA256 清单。若源码一并留作维护，只允许 `backend/app/**`（包括 NHANES 公共 CSV 和来源 manifest）、两份 requirements、以及生成静态页面所需的前端源码／锁文件；统一排除 `__pycache__`、`.pyc`、未发布输出。
2. 静态前端构建输入：仅已按 `/zhiwei/`＋API `/zhiwei` 生成的 `my-nuxt-app/.output/public/**`，不得把 `.output/server`、`node_modules`、开发日志或进程快照带进去。Docker ignore 默认拒绝所有文件，只放行这个目录与网关模板。
3. BM25 资料包：只取闭合 portable manifest、两份 snapshot/export receipt 和 manifest 指定 DB；保留相对目录。不要带 WAL/SHM/journal、未完成下载 `.part`、向量 shards、FAISS 构建临时文件、HF 权重或原服务器活库。

所有包禁止含实际 `.env`／部署配置、API key、SSH private key、公私密钥备份、浏览器状态、用户上传健康表、旧服务数据库或旧站配置秘密。真实配置通过专用受限通道另行创建于服务器私有目录（0600），不包含在 tar／镜像／前端 JavaScript 中。`aliyun.env.example` 是例外，只含占位 token／endpoint 和非敏感模型名；最终 endpoint 必须允许应用后端使用。不得仅靠后缀过滤确保安全，应以白名单构建并逐文件核对打包清单。

## 只读预检与执行边界

`deploy/aliyun.env.example` 只包含占位信息。真实配置存到独立私有文件（0600），禁止提交 Git、放进 Nuxt build、在参数中展开 token 或打印 Compose 展开配置。

在**确认挂载、闭合语料已传完、独立私有上传目录和真实模型配置就绪之后**，以下只读命令可从服务器上的本项目根执行：

```bash
python -B scripts/aliyun_preflight.py --env-file /srv/zhiwei/private/aliyun.env
docker compose --env-file /srv/zhiwei/private/aliyun.env -f deploy/aliyun-compose.yaml config --quiet
```

路径仅为示例，不是已经存在的服务器目录。预检不读旧站秘密，不联网，不 COUNT、不全库 hash、不运行检索或模型、不安装、不写文件。它检查精简 .env 语法和 token 字符、镜像版本、外部模型 base URL、已有持久挂载、空间余量、上传目录 ownership、闭合 snapshot 收据、相对 DB 路径、WAL/SHM/journal 禁止项及小量 schema 查询确认 `chunks_fts` 的 FTS5 和所需字段。外部 HTTP 仅允许明确确认的私网 IP；默认 HTTPS。预检 PASS 只是准备门槛，不证明传输内容完整、外部服务可达、模型质量、RAG 语义或网站上线。

后续实际执行顺序：只读检查原服务／磁盘 → 保留原配置备份 → 上传版本化镜像与闭合 BM25 资料 → 私有配置与预检 → 只起独立项目并在回环端口测试 → 最小追加已确认的外层入口 → 先语法检查后 reload（不是 restart） → 校验原站和新站分别可用。任何阶段失败只回滚这次新增入口／独立容器，不删除原资料，不使用宽泛 `docker compose down` 或系统重启。

## 本地验证范围

`tests/test_aliyun_deployment.py` 使用小型临时 SQLite 和静态配置检查，无实际模型、网络、Docker 容器或完整语料扫描。真实 Docker 镜像、Nginx reload、公网入口、外部模型连通性和原站无回归需要接通后独立确认；不能把离线测试通过写作部署完成。

本轮本地结果：本 profile 的 53 个离线测试通过；`docker compose --env-file deploy/aliyun.env.example -f deploy/aliyun-compose.yaml config --quiet` 通过（只核对语法，示例占位值不能上线）。另合跑旧 `test_rag_demo_deployment.py` 时，既有 Bearer 静态断言仍要求 `sessionApiKey` 字面值，而当前客户端已改为候选参数 `apiKey`，因此旧套件出现 1 个过时断言失败；未在本 profile 范围内修改它。

后续新增独立 HTTP 网关后，本 profile 离线测试扩展至 60 个并全部通过，新增 gateway Compose 的 `config --quiet` 同样通过；这些检查仍未启动容器或模拟实际 Nginx 代理。当前预生成 index 已只读确认 `baseURL=/zhiwei/` 和 `apiBase=/zhiwei`，但实际上传镜像／浏览器和旧站回归需发布后分别核验。
