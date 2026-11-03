# 全行业 AI 转型与能力图谱 V1.0

本项目把 **行业 → 岗位 → 痛点 → 场景 → 工具 → 试点计划 → KPI/治理** 做成可使用的离线静态网页，而不仅是工具名录。

## 运行

直接双击 `index.html`，可离线使用。浏览器支持本地收藏、筛选、行业/工具详情、交叉矩阵、生成 4 周试点+90天路径、导出 CSV/JSON 和 Markdown 计划。无需登录、服务器、API Key 或依赖。

- `index.html` 独立网页（含数据快照）
- `data.json` 可供二次开发的数据
- `industries.csv` 行业研究表
- `tools.csv` 工具 / Agent / Skill / 知识库目录
- `skills/*/SKILL.md` 14 个第一方行业工作流程模板（未实测）
- `roles.csv` 典型岗位实体；`graph.json` / `edges.csv` 显式关联图，可导入图数据库
- `build.py` 网页和数据构建源（Python 3.10+ 标准库；执行 `python build.py`）

## 首批覆盖

- 行业数：32
- 工具/公开资源入口：114
- 场景：23
- 第一方工作流 Skills：14
- 来源文档入口：13
- 数据快照：2026-11-01

## 边界声明

1. 本次是 **编辑整理的产品/项目链接与行业适配假说**，不是对所有 URL 的当日可用性、厂商承诺、收费、质量或许可逐项审计。
2. 行业未来方向是推演，不是事实或财务预测；30–90天计划是建议模板，不代表任何客户已经部署。
3. 本项目不安装 Skills/MCP，不向第三方发送数据，不接入真实业务账户，更不授权自动下单、诊疗、作出法律/行政决定。
4. 每个案例正式上线前应进行数据治理、授权、质量评测、采购/许可、人工审批与回滚审查。
5. 优先将该行业应用层与既有 [YIFALIN Global AI Capability Atlas](https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin) 的真实资源目录双向关联，避免复制维护 5000 条索引。

## 未来结构化数据字段

`industry_id, role_id, scenario_id, tool_id, workflow_id, source_url, source_checked_at, last_evaluated_at, maturity, data_classification, deployment_mode, jurisdiction, license, pricing_verified_at, evidence_level, benchmark_id, review_owner`

最重要的验收：**从场景到可执行工作流 / 对照试验，而不是单纯增加条目数量。**

## V1.1 · 行业 AI 专家工作台（新增）

打开 `expert.html` 按行业/岗位/场景检索64套五步工作流，含专业审核、工具与技能映射、跨行业迁移、ROI情景测算和 Markdown / CSV 导出。离线运行，无API、无敏感数据上传。数据源为 `workflows.json` / `workflows.csv`，生成器为 `upgrade_v11.py`。新增6个核验过官方产品页面的候选工具，但没有独立商用与安全实测。

运行：`python build.py` 后执行 `python validate.py && python check.py && python check_expert.py && python check_workflows.py`。

所有64套均属于编辑研究假说而非真实客户案例，工具推荐不是已验证兼容性保证；ROI 是用户输入的算术情景、不是已实现收益。

## V1.2 | AI Career & Competency Mobility

The standalone [career.html](career.html) is an offline-first, mobile-responsive companion to the 32-industry Expert Studio. It includes **225 existing occupational/role labels**, **50 emerging or editorial composite AI roles**, **22 transferable competency tags**, **69 learning/documentation gateways** and **675 editorial transition suggestions** (three per source role). These are *not* verified vacancy counts, occupational forecasts, salaries, certifications, real personal skills or job-placement probabilities.

On page: industry/role selection, editable self-assessment of existing competencies, target-role exploration, displayed overlaps and gaps, curated source-linked learning entries, four-week practice plan, Markdown portfolio plan and CSV gap export. Automatic action levels L0-L4 explicitly require authentication, approval, audit and testing before any real system access. No data leaves the page and no third-party skills are executed.

Machine-readable datasets: `careers.json`, `current_roles_v12.csv`, `new_ai_roles_v12.csv`, `learning_resources_v12.csv`, `migration_routes_v12.csv`. Built from editorial occupation labels; **O*NET/ESCO mappings have not been completed**. Training portals and vendor tools are discovery links, not audited course licenses or certified compatible modules.

References: [WEF Future of Jobs 2025](https://www.weforum.org/publications/the-future-of-jobs-report-2025), [O*NET](https://www.onetcenter.org/database.html), [ESCO](https://esco.ec.europa.eu/en/classification), [Microsoft WTI](https://www.microsoft.com/en-us/worklab/work-trend-index/2025-the-year-the-frontier-firm-is-born), [OpenAI Academy](https://academy.openai.com/pages/courses), [NIST AI RMF](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence).

Validation: `python validate_career.py` and optional pinned Playwright browser smoke `python check_career.py`. **Draft PR / merge HOLD** until exact-head CI passes, sources and rights are reviewed, and an owner approves publication.


## V1.3 · 行业标准与完整职业目录入口（独立分类层）

[打开 taxonomy.html](taxonomy.html) · [来源、验证边界和分类缺口](TAXONOMY_V1_3_README.md)

- 依据中国 `GB/T 4754—2017` 整理 **20/20 门类、97/97 大类**；473 中类和 1,382 小类**尚未导入**，不可称为全深度覆盖。
- 职业索引采用《职业分类大典（2022 年版）》的 **8 大类、1,639 职业**标准总量作为目标；详细名称、编码通过用户明确点击加载来自第三方公开镜像（或本地文件导入），**未逐条官方核验、未在本站再发布整份镜像**。只导入职业分类，不导入主观替代概率。
- 32 行业应用专题 / 225 编辑岗位 / 50 研究型新职能是不同于官方职业代码的编辑层；禁止相加凑“覆盖率”，禁止无依据建立行业—职业确定性映射。
- 可按层级检索、导出，按 8 大职业类别查看经人工批准的起步 AI 试点；外部职业信息的读取仅在用户点击后进行。
- ILO ISCO-08、联合国 ISIC Rev.5、澳洲 OSCA、美国 O*NET、EU ESCO 的来源入口已经列出，尚未宣称跨地区编码已经交叉对齐。

**合并与上线继续 HOLD**，直到 CI、来源/许可、可访问性、内容核验和生产发布审查结束。


## V1.4 · 一句话智能导航与站内对话（无需下载）

- **[打开 discover.html](discover.html)**：无需先选行业即可检索，例如 `量化金融`、`证券资管`、`制造业设备预测性维护`、`教师备课`。主页给出上下文匹配的行业与专业方向、直接打开的工具/知识链接、职业候选与四步人工审批试点。
- 原应用分类 32 个行业专题下面新增 **133 个经过显式父行业约束的专业方向**。行业子方向是编辑业务分类，**不是** GB/T 4754-2017 的第三、四级官方统计编码。特别修正“量化金融 → 证券与资管 → 量化金融与因子研究”；证券研究、资产管理、市场微观结构等只显示在证券与资管下。
- 在页内展示方案、风险、学习库与官方来源链接；下载 Markdown / JSON 仅位于可选折叠菜单。支持会话式后续指引（怎么学/工具/自动化/岗位/风险）、有边界的能力 SVG 关系图、手机页面、可分享查询 URL。
- `discover_v14_data.json` 为匹配所用的冻结编辑数据；`check_discover_v14.py` 对覆盖量、财务归类、跨行业污染、跳转、图谱与手机屏幕做真实 Chromium 回归。
- **能力与证据边界：** 使用浏览器内确定性关键字和关联评分，不调用大模型 API，不是实时智能对话；不装第三方 Skills、不连接券商、不执行生产自动化或订单。资源推荐是候选，不是已验证供应商适用性。网站未做生产发布/外部数据授权实测。
- 源文件均嵌入网页，离线打开也可使用；如需让外部访客无需下载地访问，应进行独立静态站发布评审。

**Merge/Deploy HOLD** 直到本分支最新 HEAD 的完整工作流通过、产品/安全/链接与移动端审查完成；不要合并或部署此 Draft PR。


## V1.5 · 一句话任务顾问 / Context-Aware Advisor

**入口：** [advisor.html](advisor.html)（静态、自包含、无需登录和下载安装）。旧版 [discover.html](discover.html) 保留作为 V1.4 的界面对照。行业图谱、专家工作台、分类页与职业中心都有新入口。

**新增功能**

1. 一个输入框直接匹配行业专题 → **该行业所属**的编辑专业方向 → 具体业务任务；行业词与专业别名分层评分，页面展示命中依据和候选替代方向；手工行业调整后专业下拉只含该行业记录。无法识别时不沿用上次行业内容。
2. 当前页面直接呈现五步试点清单、可以勾选的进度、相关工具与知识链接、岗位提示和交互式能力关系图。**下载 Markdown 是可选动作**。
3. 页内追问保留已选行业/专业上下文，支持如何开始、工具来源、学习顺序、自动化边界、风险与匹配依据。回复由已收录资料及确定性规则生成，不是自由生成的大语言模型回答；相关工具页面可直接打开来源。
4. 点击“复制给 AI 助手的完整任务说明”生成一段包含业务背景、候选来源、试点步骤、评测和安全门槛的文本，可自行粘贴到有权使用的 AI 服务。网页不会自动向 ChatGPT 或任何第三方发送输入。
5. 勾选进度与当前任务**仅在用户主动开启本地保存时**存储在浏览器 localStorage；清除本地记录不影响任何服务器，因为该静态页面没有服务端用户账户。

**数据与构建：** 保留 32 个编辑行业专题、133 个业务专业方向、114 个工具候选、69 个学习资源，全部来自既有 `discover_v14_data.json`。新文件 `advisor_v15_data.json`、`advisor_v15_template.html`、`build_advisor_v15.py` 和 `check_advisor_v15.py` 可重建并验证自包含网页。通过 `python build_advisor_v15.py && python check_advisor_v15.py` 验证；GitHub Actions 额外检查输出文件无意外漂移及 1440px/390px Chromium UI 回归。

**验收边界：** 分类仅是 AI 业务应用层，**不等于国家行业细类或国际职业编码**。工具和课程仅为编辑候选，未完成许可证、隐私、性能、价格、兼容性等独立评估。没有连接模型 API、CRM、邮件、券商或业务数据库；没有 Agent 自动执行、实盘下单、法律/医疗专业结论，商业 ROI 未经验证。

**待交付的真正 AI 模型服务**需要独立的受认证服务端，包含检索引用验证、限额与成本控制、用户授权、敏感数据脱敏、角色权限、审计及独立评测。严禁在公开 HTML 内嵌模型密钥。当前 PR 保持 Draft 和 Merge HOLD，不直接生产发布。

## V1.6 | Guided Workspace (2026-11-03)

**Start:** [start.html](start.html) → [advisor_v16.html](advisor_v16.html). The original Atlas index, V1.5 advisor, career and taxonomy views remain available. This is a product UX layer, **not a real LLM/Agent deployment**.

User-facing improvements:
- Intent-first chips (explore / learn / compare tools / automation); natural-language industry and specialty resolution remains bounded and explainable, without fabricating missing matches.
- Next-best-action card, checkable five-step pilot, and editable in-page evidence notes. Notes/progress/favorites are separated by specialty, retained while switching topics within a session.
- At most three source-linked candidate tools can be compared in place; descriptions/why-matched/verification caveats are not audited benchmark scores.
- Inline feedback (helpful or needs work) is stored only in local page state or optional same-device storage; **no telemetry or submission**.
- Mobile bottom navigation and larger touch targets, keyboard Ctrl/⌘+Enter, reduced-motion support, optional local persistence with honest failure on unsupported origins.
- Personal task text is **not** auto-appended to share URLs. The user must explicitly opt in before task text, notes and history are written to browser localStorage.
- Links go to existing source sites; no real customer data, remote models, CRM writes, trading, diagnostics, or production execution.

**Sources/build/tests:** `advisor_v16_template.html`, `advisor_v16_data.json`, `patch_advisor_v16.py`, `build_advisor_v16.py`, `check_advisor_v16.py`. Run `python patch_advisor_v16.py && python build_advisor_v16.py && python check_advisor_v16.py`. Browser persistence tests use a simulated localStorage object; they do not prove cross-device sync.

**Status:** separate research branch / Draft PR, no merge, no automatic deployment. Future genuine AI assistant integration needs a secure server-side model gateway, explicit identity and permissions, audit logs, rate limits, privacy notice, evaluation and real-world acceptance evidence.
