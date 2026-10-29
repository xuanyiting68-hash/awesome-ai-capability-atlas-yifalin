# ◈ Global AI Capability Atlas | 全球 AI Skills · Agents · Projects 图谱

> Find → Evaluate → Bookmark → Fork → Build.  **发现、评估、收藏、Fork、二次开发。**

一个可以直接打开的静态网页 + 可审计的 CSV/JSON 数据目录 + 标准库 Python 采集脚本 + GitHub Actions 自动更新。目前已发布网页、精选数据、采集快照、脚本、校验和工作流。

## 目前交付（2026-10-26）

| 层级 | 规模 | 内容 | 验证边界 |
|---|---:|---|---|
| 编辑精选 | **133 个仓库** | Skills、Agents、MCP、框架、AI/量化项目、评测工具 | 已通过 GitHub 连接核实仓库存在且未归档；**不等于完成安全审计/实测** |
| 上游候选发现层 | **30 个分类文件** | 来源于 `VoltAgent/awesome-openclaw-skills` | 同日按链接格式计约 5,150 条，可能重复或日后发生变动；均为**第三方、未审计记录** |
| 网站与同步脚本 | **上限 5,000 条总索引** | 保留 133 个编辑精选，剩余名额按来源分类轮询去重收录 | 需要联网同步。若来源失败，只显示实际可用条目，绝不捏造记录 |

**务必区分：**“已被目录索引 / repository-exists / security-audited / battle-tested / licensed-for-commercial-use” 是不同的状态。本项目目前只对 133 个精选 GitHub 项目完成了存在性与未归档状态的核验。目录候选不经过人工实测。

## V1.4.4 · 可核验发布与巡检

发布产物包含源提交清单 `deployment.json`，发布前验证数据，发布后及每日通过 Chromium 巡检站点。仅打包公共页面和数据，不发布开发依赖。详见 [发布验证记录](docs/V1_4_4_RELEASE_MONITORING_CN.md)。

## 独立审计与可复现的第一方工作流样例

- [2026-10-27 独立质量审计与修复记录](docs/INDEPENDENT_AUDIT_2026-10-27_CN.md)：说明数据可信边界、缺失页面及版本与 CI 核验，任何测试通过均不替代第三方许可证审查。
- [合规留资 → 匿名分流 → 人工复核（合成数据）](examples/consent_lead_triage/README.md)：使用 Python 标准库运行，无账号连接、无自动外发；仅用于验证权限/撤回门禁，并不代表生产获客/CRM 集成成功。

## 交互式 AI 能力关系图（Top 30）

[打开能力关系图](network.html)——可视化 10 个已有业务领域与 Top 30 候选项目的分类关系，基于 `data/top30_evaluation.csv`、`data/research_briefs.json` 和实际发布清单渲染。支持关键词、领域、来源档案筛选、URL 分享及鼠标/键盘导航。手机端呈现可操作项目卡片，主图不引入重型可视化依赖。

**关系边只表示编辑业务分类，不表示技术依赖、API 连接、商业许可或安全认证。** 有官方资料档案不代表有实际复现。全体 Fork HOLD。

## Top 30 全覆盖：30 份来源可追溯编辑研究档案（非实测）

在 [Top 30 研究室](top30.html) 打开任意 Top 30 项目（包括 Qlib、OpenBB、LEAN、Codex、Claude Code、OpenHands、n8n、RAGFlow、Postiz、PostHog 等）的[项目详情页](project.html?repo=microsoft%2Fqlib)，可查看官方 README/文档、双语适用判断、关键能力、待执行实验步骤、指标和适用限制。研究内容位于 `data/research_briefs.json`，其证据门禁由 `scripts/validate_research_briefs.py` 和 CI 强制检查。官方 README 的 Git Blob SHA 用于不可变的来源文本快照追踪。

2026-10-29 的目录核验发现 OpenBB 和 OpenHands 的 GitHub 上游组织已变更，LEAN 使用小写 `readme.md`，OpenBB/Chatwoot 使用 `develop` 默认分支；这些差异由显式的 canonical repo、分支和文件名门禁检查。原有 Top 30 项目标识仍保留，以防冻结 CSV/元数据出现未经审查的漂移。部分项目的第二个官方链接是仓库自身的维护者指南，而不是独立的文档站。

**30 份全部仍是 Curated 编辑研究，不是 Reviewed / Reproduced / Production Candidate。** 现有 30 项依然全部 Fork HOLD，不把 GitHub SPDX 当作法律许可意见。

```bash
python scripts/validate_research_briefs.py
python -m unittest scripts.test_research_briefs -v
```

## V1.4.3 · 双语项目研究工作台

[进入 Top 30 研究室](top30.html) · [验证与交付记录](docs/V1_4_3_WORKSPACE_CN.md)

研究室支持中英界面与双语检索、共享本地收藏、四项对比、可分享筛选、CSV 导出和逐项证据。GitHub 元数据与证据快照日期不一致时停用证据展示。项目仍待许可、安全和复现实测审查，Fork 决策均为 HOLD。

开发验证：Python 数据检查 + 固定版本 Playwright 的 17 个浏览器场景，CI 保留桌面与移动截图。完整目录翻译、300–500 项深度审查及业务工作流集成仍待后续完成。

## V1.3 · 跨生态发现与技术蓝图

- 来源扩大到 Anthropic / OpenAI / Microsoft / GitHub Copilot / 社区 Agent Skills / n8n 工作流 / MCP 目录，按 URL 去重，并保留 133 条编辑精选。
- **实际记录数、各来源份额及失败来源，请看 data/provenance.json，而非宣传数字**。本项目的上游候选资源均未完成安全及商业授权审查。
- 新版网页可按来源生态筛选，查看六套 [业务技术蓝图](docs/BLUEPRINTS_CN.md)；另见 [风险与来源说明](docs/SOURCE_AND_REVIEW_CN.md)。
- 采集只读取公开路径/元数据，不安装第三方 Skill；第三方内容归原项目作者所有。

## V1.2 · 项目情报与来源透明度

- 资源网站已通过 GitHub Pages 部署工作流；静态快照从 `data/catalog.json` 加载。
- 每周更新 `data/repo_metadata.json`，查看编辑精选仓库的 GitHub Stars、Forks、最近 Push、是否归档和 GitHub 检出的许可证标识；网页支持按 Stars 排序。
- **来源提醒**：截至首次落库，4,867 条批量候选均来自 VoltAgent 的 OpenClaw 社区目录，而 133 条编辑精选来自多个项目和框架；本站尚未达到各生态均衡覆盖。
- GitHub Stars、许可证识别与仓库存在性都不能替代真实质量测试、安全审计或商业使用许可核验。

## 首次线上采集核验（2026-10-26）

- **5,000 条实际落库**：133 个编辑精选 + 4,867 条外部候选索引；30/30 个分类文件采集成功。
- 生成 `data/catalog.json`、`data/catalog.csv`、`data/provenance.json`、`data/excluded.json`，详情以 `data/provenance.json` 为准。
- 本次只读取公开目录文本，未安装或运行第三方 Skills；外部候选 **未经安全与许可证审查**。
- 资源索引已经提交到主分支。实际 Pages 发布状态以仓库 Actions 的部署结果为准；分支内的开发成果不自动代表线上版本。

## 快速使用

1. 解压项目，双击 `index.html`，无需安装依赖。离线立即可检索 **133 个精选项目**。
2. 浏览器联网且允许访问 GitHub Raw 时，页面自动载入 30 个公开分类，最多显示 **5,000 条**（含精选 133 个）。也可点击「重新同步全球目录」。
3. 支持中文及英文搜索、类型/领域/级别筛选、金融量化专区、收藏、显示更多、导出筛选结果为 CSV/JSON。
4. `data/curated.csv` 是离线精选表；推荐在正式部署后使用 `data/catalog.csv` 作为有来源记录的完整索引。

## 一次性生成完整数据快照

```bash
python scripts/harvest.py
```

生成：`data/catalog.json`、`data/catalog.csv`、`data/provenance.json`、`data/excluded.json`。**运行脚本只下载分类 Markdown，不安装、不执行第三方 Skills。** Python 3.10+ 标准库即可。默认某个分类失败时保持原快照，不覆盖成部分结果。上游链接的有效性、许可证以及安全性需后续独立验证。

## 正式 GitHub 仓库

正式公开仓库：https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin 。本资源索引与 YIFALIN 现有产品和交易仓库隔离。

可在根目录打开 `index.html` 浏览离线精选项目。GitHub Pages 部署通过仓库的 Pages 工作流启用；需在仓库 Settings → Pages 中选择 GitHub Actions。

## 新增：视频、自媒体运营、全智能获客及客户维护

新增五个独立筛选分类：**AI视频制作、自媒体运营、智能获客、客户关系维护、增长分析**。重点不是无授权自动群发，而是合法发现用户真实需求、原创内容生产、平台允许的分发、主动咨询收集、可追踪 CRM 服务和第一方转化评估。

- 详细路线：[AI Growth Operating System](docs/GROWTH_OPERATING_SYSTEM_CN.md)
- 分类与项目入口：[增长业务五大专区项目索引](docs/GROWTH_COLLECTIONS_CN.md)
- 额外精选条目：`data/expansion_seed.json`，会与首批资源合并，不依赖在线访问即可检索。

## 优先研究方向

**金融 AI：** `microsoft/qlib`、`AI4Finance-Foundation/FinRL`、`AI4Finance-Foundation/FinRobot`、`TauricResearch/TradingAgents`、`OpenBB-finance/OpenBB`、`QuantConnect/Lean`、`polakowo/vectorbt`。

**研发自动化：** `openai/codex`、`anthropics/claude-code`、`All-Hands-AI/OpenHands`、`langchain-ai/langgraph`、`browser-use/browser-use`、`github/gh-aw`。

**教育 AI：** `run-llama/llama_index`、`docling-project/docling`、`microsoft/markitdown`、`infiniflow/ragflow`、`microsoft/ai-agents-for-beginners`。

**产品与运营：** `langgenius/dify`、`n8n-io/n8n`、`activepieces/activepieces`、`firecrawl/firecrawl`。

**视频与增长：** `remotion-dev/remotion`、`harry0703/MoneyPrinterTurbo`、`gitroomhq/postiz-app`、`TwentyHQ/twenty`、`chatwoot/chatwoot`、`mautic/mautic`、`posthog/posthog`。

**安全评测：** `promptfoo/promptfoo`、`confident-ai/deepeval`、`langfuse/langfuse`、`Arize-ai/phoenix`、`modelcontextprotocol/inspector`。

这些属于“值得研究 / 评估 Fork 价值”，不是建议全部安装或直接赋予生产密钥。

## Fork/复用审查门槛

- **许可证：** 是否允许商用、修改、分发及闭源产品集成？项目若无 LICENSE，默认不能直接推断有授权。
- **维护状态：** 最近更新、Issue 响应、发布频率、依赖漏洞、是否已归档。
- **真实能力：** 能否在隔离沙箱内复现？是否有端到端测试、基准和失败案例？
- **运行边界：** 是否要求网络、Shell、写文件、浏览器 Cookie、云端或实盘交易权限？避免默认全权限。
- **数据合规：** PII、商业数据、金融数据和版权限制；禁止悄悄上传用户材料。
- **输出质量：** 来源引用、对照实验、审计日志、回滚、人工审批和成本预算。
- **独立验证：** 在模拟环境评测金融策略；实盘连接必须有风控闸门与法律合规评估，不因 GitHub 热度而获得豁免。

## 设计选择与限制

- 采用静态站点；资源链接可点击，收藏存在浏览器本地存储。更换浏览器不会自动同步收藏。
- 不引用上游 README 的大段原文，仅使用标题、链接与简短描述作为索引；尊重来源和项目许可。
- 来源 30 个分类由单一外部汇总者提供，存在收录偏差、过期和重复。需要继续增加独立来源并做交叉核验。
- 自动发现层以英文元数据为主；编辑精选附中文用途和优先级。推荐分数为本站编辑的主观研究优先度，**不是安全分或投资绩效分**。
- 本仓库不会自动执行或安装第三方内容，也不提供绕过权限、合规和交易风险边界的功能。

## 后续贡献

可以通过 Issue 或 PR 推荐项目：必须提供 GitHub URL、类别、核心能力、可复现演示、许可证、维护状态、建议使用场景与潜在风险。先进入候选列表，经过审查后才进入编辑精选。

**Sources:** [Agent Skills Standard](https://agentskills.io/) · [Anthropic Skills](https://github.com/anthropics/skills) · [OpenAI Skills](https://github.com/openai/skills) · [MCP Registry](https://github.com/modelcontextprotocol/registry) · [VoltAgent Agent Skills](https://github.com/VoltAgent/awesome-agent-skills) · [VoltAgent OpenClaw Directory](https://github.com/VoltAgent/awesome-openclaw-skills)

> This is an independent curated index. Upstream packages and their licenses remain with their respective authors. No affiliation implied. Not investment advice.