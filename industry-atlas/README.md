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

## V1.7 · Progressive Industry Workspace (Draft, 2026-11-03)

**Entry:** [start.html](start.html) → [advisor_v17.html](advisor_v17.html). Built on top of the **unchanged V1.6 editorial snapshot** and reuses all existing V1.0–V1.6 pages, taxonomies, careers, tools and source links. New UI is not a separate platform.

- First open is neutral: **no preselected finance demo incorrectly masquerading as a recommendation**. Submit a concrete industry/task question, or pick an example.
- Contextual example prompts for finance, manufacturing, legal, logistics, agriculture, hospitality, teaching and healthcare. Finance samples remain in securities/asset management and do not mix other industries' specialties.
- **Beginner mode** shows the current next step, two top candidate tools and direct quick actions. **Expert mode** shows all five steps, extended candidates and a navigable capability graph. Switch in-place without losing current progress.
- In-page follow-ups, three-tool comparison, source-linked materials, per-specialty notebook, opt-in browser storage, no forced file download remain available. Unknown requests fail closed with no stale recommendations. Raw user questions are not added to share URLs.
- [build_advisor_v17.py](build_advisor_v17.py) deterministically rebuilds the self-contained page from the frozen V1.6 data/script output; [check_advisor_v17.py](check_advisor_v17.py) exercises 1440/390px Chromium states including the no-match boundary and zero network requests. GitHub Actions also reruns V1.0–V1.6 checks.

**Honest boundary:** This is an offline contextual-rules prototype, **not a live LLM, RAG service or agent execution**. No business data, telemetry, accounts, external writes, API key or paid calls. Browser opt-in local data is not cross-device sync or encrypted account storage. Candidate vendor links are research leads, not independently verified compatibility/security/performance. Source/legal review and a separate Owner deployment approval are mandatory. **PR stays Draft / no merge / no production publication**.

## V1.7.1 · AI Intelligence Radar / Metadata Discovery Queue (2026-11-04)

**User review dashboard:** [intelligence.html](intelligence.html) shows the original 133 editorial reference entries with source links, preliminary industry fit signals, evidence gaps, bilingual controls, responsive search/filters and explicit not-a-live-scan boundaries. Existing curated membership is not a security audit or commercial license approval. Nothing from unreviewed live discoveries is automatically displayed as a recommended product.

**Independent discovery adapter:** [discovery_review.py](discovery_review.py) supports network-free re-ranking of existing `data/catalog.json` and bounded live metadata discovery from **GitHub public repository search** (two queries) and **Hugging Face public models** (one query), plus **arXiv Atom preprint metadata** (one query). At most 4 HTTP requests per cycle, limited payloads, allowlisted HTTPS hosts, no redirects, clear HTTP failures, no third-party code execution, no external writes, no paid model API. A failure preserves the last full queue. The output includes explicit score components, provenance, tentative sector associations, license signals and `approved=false` for every candidate. It is a review queue, never a deployment certificate or true quality benchmark.

**Workflow:** [industry-discovery-review.yml](../.github/workflows/industry-discovery-review.yml) validates on PR and prepares **offline artifacts**. After a separate merge to the default branch, its Thursday 06:43 UTC schedule would additionally query the public live sources and upload a 14-day review artifact (and can be dispatched manually). GitHub schedule and workflow_dispatch are **not active on the unmerged PR branch**. Workflow has `contents:read`; no push, merge, publishing or public deployment. Existing `sync-catalog.yml` remains unchanged and is separate from this higher-quality review gate.

**Validation:** `python -m unittest -v test_discovery_review`, `python discovery_review.py --mode offline --output /tmp/discovery.json`, and `python check_intelligence_ui.py` in an installed Playwright environment. Chromium checks desktop 1440px/mobile 390px, search, industry filter, bilingual mode, evidence warnings and no third-party network calls. Further source types such as vendor release notes, standards and general RSS need independent API/licensing/rate-limit review before addition. arXiv metadata is research discovery only, not peer review or paper-reuse permission.

**Gate:** original Draft PR, no merge/deploy. No actual live source fetch demonstrated until scheduled/explicit workflow runs on a reviewed default-branch release. No claim of fresh live additions to the static page.

## V1.7.2 · Change Evidence, Human Review & In-Page Research Notebook

**Change detection**: `discovery_lifecycle.py --current NEW.json [--previous OLD.json] --output DELTA.json` validates strict, unapproved discovery snapshot contracts. It differentiates fresh observations, meaningful metadata changes (including license/source/sector changes), unchanged entries, and entries **not observed in the latest bounded sample**. It NEVER interprets absence from a top-N API search as confirmed deletion or license revocation. Without a comparable previous snapshot, the output explicitly says `no-prior-baseline` and calls every entry baseline, not new. The source and time scope of the input remain visible. Failures preserve the previous delta artifact.

**Owner review request gate**: `discovery_review_gate.py --queue QUEUE.json --decisions DECISIONS.json --output REQUESTS.json` accepts explicit reviewer-authored review requests (investigate/defer/reject/request-promotion). Promotion *requests* require three distinct audit evidence links (licence, security and sample task test), substantive reviewer rationale and matching candidate identity. Even complete evidence yields only `pending-independent-owner-review`; the gate neither authenticates a reviewer nor verifies those claims, never sets `approved=true`, and cannot edit the curated catalog. **Human verification and separately authorised branch/PR merge remain mandatory.**

**Interactive research desk**: The original [AI Intelligence Radar](intelligence.html) now offers per-resource expandable research checklists, cached last-updated metadata labels, text notes and explicit opt-in same-device persistence; by default notes remain in the current page only. A reviewer may inspect official source links in-page, take notes, switch language, and clear all local notes. Checking a box NEVER certifies vendor security/rights or connects any external system. No upload, user account, model inference or telemetry is performed.

**Automated reports**: `.github/workflows/industry-discovery-review.yml` generates `offline.json`, `offline_delta.json`, `review_requests.json` from a blank decision list, and optionally `live.json` plus `live_delta.json` for **scheduled/explicit runs on a separately reviewed default-branch workflow**. For live comparisons it attempts to read the previous successful artifact with read-only GitHub Actions privileges, and displays a truthful initial baseline if unavailable. Snapshot failures do not push or deploy anything. **No scheduled run is active in this unmerged Draft PR.**

**Testing**: `python -m unittest -v test_discovery_review test_discovery_lifecycle`, plus `python check_intelligence_ui.py` for actual 1440/390px Chromium. All tests are synthetic/offline except local browser use and the inherited GitHub CI runtime; live API capability is not yet a verified operation. Relative recommendation value, commercial licensing and real-world accuracy remain unproven.

**Next gates**: Independent source/robots/ToS and permission review; evidence integrity beyond self-declared links (licence file and release attestation, reproducible benchmark protocol, security assessment); curated migration using Owner-reviewed, auditable PR only; second-snapshot longitudinal evaluation; authenticated per-user notes and YIFALIN Education compatibility. No price-bearing API or production customer data.


## V1.7.4 — task-level evidence relevance, feedback and disabled provider contract (research Draft)

- Open `start.html` → `advisor_v174.html`: preserve frozen `advisor_v17.html` / `advisor_v173.html`. All 32 sectors, 133 specialties, 114 candidate tools, 69 learning gateways and 133 *unapproved/cached* radar reference records remain intact.
- Intent ranking now uses complete-word matching for Latin terms (`it` must not match `orbital`); targeted English editorial aliases are supported. This is rule matching, not a live model or complete bilingual UI.
- The radar only displays sector-scoped items with actual task-word overlap. Each surfaced item shows its matched words and underlying link; an empty result is explicit. Metadata age is not a refreshed verification date; licenses, security, prices and impact remain unverified.
- Users may hide a candidate as irrelevant and restore it for that specialty. The action never alters the curated catalog, changes approvals, or sends telemetry. Persistence still requires explicit same-device opt-in.
- The reproducible builder is `build_advisor_v174.py`. `task_eval_cases_v174.json` contains **30 hand-labelled synthetic / editorial regressions**, including English false-positive controls. They cannot establish field accuracy, commercial suitability, or occupational classification completeness. Real Chromium evaluation: `check_advisor_v174.py` on 1440px and 390px.
- `provider_contract_v174.py` and `test_provider_contract_v174.py` define capped, source-ID-checked request/response structures, a local Mock, and a disabled OpenAI-compatible request-envelope builder. No network client, API credential, spending or live model routing exists. Remote provider use requires a separately authorised authenticated backend, privacy review, rate-limit/cost hard caps and evaluation.
- Draft PR / MERGE HOLD / DEPLOY HOLD. This research branch is not permission to publish or operate on customer inputs.

## V1.7.5 — offline source-grounded metadata retrieval and Mock explainer (Draft / HOLD)

- Open the existing `start.html` → `advisor_v175.html`, or click from `intelligence.html`. Prior V1.7.4 remains frozen, and the original ~5,000 index and 133 pre-existing curated items are unchanged.
- `rag_topics_v175.json`: 15 bounded editorial concept groups (bilingual keyword synonyms). `rag_retrieval_v175.py` uses the **same 133 cached, all-unapproved radar records**, exact sector tags, topic intersections, bounded top-K, stable source hashes and HTTPS input validation. It never makes HTTP calls, fetches source text, runs embeddings or executes third-party Skills.
- The browser now shows inline source references, matched topics, cached metadata date, license **signal only**, and original links; it can produce a deterministic cited **Mock** explanation. Missing cross-sector evidence leads to an explicit abstention, not a fabricated answer. This is metadata retrieval, **not real multi-document RAG or live LLM**.
- `rag_eval_cases_v175.json`: 12 hand-labelled *synthetic* source-hit and abstention test cases. `test_rag_retrieval_v175.py` checks no promotion, source identity/dedup, unsafe URLs, sector isolation, citation consistency, bounded context. `check_advisor_v175.py` runs real Chromium 1440/390 for source links, citation/no-citation paths and zero network egress.
- `build_advisor_v175.py` reproducibly builds the HTML from frozen V1.7.4 and existing data; CI verifies no generated-content drift and preserves all earlier checks.
- Source dates reflect historical **metadata snapshot timestamps**, not independent freshness checks. License SPDX is a candidate signal, not a commercial license review. Evidence ranking is based only on conceptual keyword overlap; it is not precision in real production data, performance benchmarking, price, compatibility or factual endorsement.
- No real model, authenticated backend, remote provider, paid API, new data acquisition, customer data, production release, merge or deployment is authorised. PR stays Draft / HOLD.

## V1.7.6 — source audit, research truth-in-evaluation and hard zero-egress model policy (Draft / HOLD)

- `advisor_v176_template.html`, `advisor_v176.html`, `build_advisor_v176.py`: based on frozen V1.7.5, adds a **task-scoped source audit desk**. Each cited candidate displays an honest cached metadata-age warning (local browser clock), missing/unverified licence signal, lack of live URL check, security audit and measured task effectiveness. A user can review and copy an **unverified** checklist, but never approve a source, auto-certify a licence or submit data. `check_advisor_v176.py` runs real Chromium at 1440px/390px to check copy affordance, no source bleed and no network egress.
- `source_governance_v176.py` creates a deterministic, explicit-as-of-date, **offline** 133-item governance report; each record keeps `license_verified=false`, `security_verified=false`, `link_currently_accessible=null`, `approval=unapproved`, and `real_source_network_checks=0`. `compare_reports` differentiates cached metadata changes from elapsed time; missing in a sample is NOT a source deletion. CLI: `python source_governance_v176.py --as-of YYYY-MM-DD --output /tmp/source_governance.json`.
- `evidence_eval_v176.py` reports the existing synthetic editorial corpus hit@8 / no-evidence abstention, with per-sector breakdown. **It does not report real-world precision, recall or proven source quality.** A future adjudicated human packet requires 25+ consented/anonymized tasks, distinct reviewer attestations, sector tags and source checks, but even structurally valid packets remain `HOLD` until independent authentication and audit.
- `safe_provider_policy_v176.py` is a local Mock-only policy. Any network provider, billing above USD0, data export or customer-data flag raises `RemoteExecutionDisabled`. Limited email/token/phone pattern checks fail closed, but are explicitly *not comprehensive PII detection*. No real API client, keys, model invocation, browser egress, external data purchase or billing has been introduced.
- All earlier 32 sectors, 133 specialties, 114 tools, 69 learning entries, 133 cached-unapproved radar references and frozen HTML prior versions remain preserved.
- Real-world content relevance evaluation, live source freshness, license/security verification, user consent enforcement, authenticated backend/tenant isolation, model quotas and production deployment remain separate uncompleted gates. **No merge, no deployment, no auto-approval; Draft PR release HOLD.**

## V1.7.7 — explicit all-sector coverage review from frozen sources (Draft / HOLD)

- `coverage_review_rules_v177.json` contains 13 **editorial topic → possible industry** mappings. They apply only to the 69 original **unmapped** resource records in `discovery_seed.json`; they **do not update** any original `sector_ids`, source, approval, catalog or production data.
- `coverage_review_v177.py` generates a deterministic human-review queue. It rejects unexpected source populations, invalid HTTPS evidence, duplicate IDs, bad target sectors, duplicate editorial rules, approved sources, and cross-population mutation. Every proposal remains `unapproved-sector-proposal`, `approved=false`, `license_verified=false`, `security_verified=false`, `link_checked_live=false`. CLI: `python coverage_review_v177.py --output /tmp/coverage_review.json`.
- In the existing user-facing page, `advisor_v177.html` separates original editorially tagged sectors, sectors with **only** unreviewed topic-based proposals, and sectors with **no** sources in this 133-item radar snapshot. Users can select any of the 32 sectors, expand a clickable coverage matrix, filter sectors without original tags, inspect source links/rationales, and copy a pending manual-review checklist. **No button claims a proposal is approved.**
- For the frozen 2026-11-04 metadata snapshot: **4/32 sectors have original editor labels**; **69 sources are unmapped**; these 13 conservative topic rules generate proposals for **8 other sectors**, leaving **20 sectors without candidates in this particular radar corpus**. These 8 are ***not*** verified new covered sectors. The existing main Atlas's 32-industry data and 114 candidate tools remain distinct.
- `advisor_v177_template.html`, `build_advisor_v177.py`, `advisor_v177.html`, `test_coverage_review_v177.py` and `check_advisor_v177.py` implement reproducible, offline and fail-closed source disclosure. The browser regression checks both 1440px desktop and 390px mobile, provenance labels, 32 industry controls, candidate isolation, approval non-promotion, and zero external network calls.
- `start.html` and `intelligence.html` link to V1.7.7 on the research branch. V1.7.6 and prior versions remain frozen and accessible.
- This is **NOT** a verified source expansion, live web crawl, independent license audit, job-specific empirical benchmark, production RAG, autonomous product selection, authenticated user approval or customer deployment. 20 unmatched sectors remain a real research coverage gap. Any actual promotion requires independent source rights/safety/task review and an Owner-approved separate PR. **Draft / no merge / no deploy / USD0.**

## V1.7.8 — complete in-page review pagination and missing-sector research handoff (Draft / HOLD)

- **Original problem fixed**: V1.7.7 silently truncated review candidates at 8 per sector and the copy action copied only those 8. V1.7.8 adds real previous/next paging (8 per page) to both **existing editorial tags** and **unapproved proposed mappings**, with accurate per-sector page counters. Copy now includes **all** proposed candidates, not the visible page alone. Switching a sector resets both pagers. The browser does not upload inputs or update source approval. Some candidate names repeat across different original GitHub URLs, so link identity is preferred over display name in regression tests.
- For a source-free sector, the UI shows a dedicated **research gap brief**, sourced only from the existing `advisor_v16_data.json` sector-specific professional domains and workflows, including tasks, KPI and guardrails. Copy creates a human research assignment; **it does not invent external tools, references, licenses or evidence**.
- `sector_gap_briefs_v178.py` generates deterministic offline gap briefs for the **20 sectors with no candidates in the frozen 133-resource radar snapshot**, with zero live calls, zero invented source counts and release gate HOLD. `test_sector_gap_briefs_v178.py` checks coverage, source-free/immutability assertions and provenance.
- `advisor_v178_template.html`, `build_advisor_v178.py`, `advisor_v178.html`, `check_advisor_v178.py` provide reproducible UI on the same original Atlas. Real Chromium tests cover 37 proposals over 5 pages, 14 proposals over 2 pages, existing 24-tagged IT sources over 3 pages, controls, research briefs, sector resets, mobile 390px and desktop 1440px and zero external network.
- Prior 32-sector taxonomy, 133 specialties, 114 main tool candidates, 69 learning links, 133 original unapproved radar resources, 13 unapproved mapping rules and previous advisor versions are **preserved**. Start/intelligence route to the research-branch V1.7.8 page, no production deployment.
- No real source discovery, legal license verification, vendor audit, task suitability proof, genuine human-review signoff, authenticated RAG or API costs. This is a human **research queue** and review UX, not verified 12-sector coverage. **Draft PR / MERGE HOLD / DEPLOY HOLD / USD0.**

## V1.7.9 — external repository metadata evidence ledger, read-only review (Draft / HOLD)

- `external_leads_v179.json` is an isolated, explicit 2026-11-04 date-precision observation ledger of **10 public GitHub repository API lookups**, from 10 different industries that previously had no candidates in the old 133-resource editorial radar snapshot. Each observation records its provider-stable numeric repository ID, canonical repository URL and official API URL, `archived`/`disabled` flags, last repository push time, default branch, SPDX **metadata signal only**, editor review caution and unapproved status. This is **not live availability monitoring**, LICENSE/NOTICE verification, project code safety certification or proven sector/task suitability.
- `external_leads_v179.py` validates identity, canonical HTTPS, duplicate IDs, frozen-data non-overlap, date bounds, sector isolation and every false approval/audit flag. It generates a deterministic, hashed, source-by-source review report with an explicit **HOLD** gate; its snapshot-diff compares metadata observations without claiming an unseen repo was deleted or a changed SPDX field was independently verified. CI has **zero external API calls** and does not automatically update these observations.
- The original user-facing `advisor_v179.html` shows all 10 separately under a clearly labeled public-source *observation* panel, with sector filter, links to GitHub project and its official metadata API, observation date, SPDX uncertainty, tailored human review cues, and a full copyable LICENSE/NOTICE/security/functional testing checklist. Users can jump to the Atlas sector and see that it **still has no frozen-radar source candidate**; this is not auto-promotion of the new lead into the catalog or changing 4/8/20 sector state. No persistent backend approvals exist.
- The immutable source, 32-sector Atlas taxonomy, 133 specialties, 64 workflow patterns, 114 candidate tools, 69 learning references, 133 frozen-unapproved radar observations, 69 original untagged entries, 13 review-only topic maps and previous advisor V1.7.8 are preserved.
- `advisor_v179_template.html`, `build_advisor_v179.py`, `check_advisor_v179.py`, and `test_external_leads_v179.py` add reproducible source embedding, 10 recorded-source review controls, actual Chromium 1440px/390px, full 10-source copy, correct no-coverage after source-panel clicks, no network egress and negative provenance tamper tests.
- `start.html` and `intelligence.html` on this **research branch** route to V1.7.9. The Default branch and existing production site are untouched. No merge, deployment, paid service, source promotion, customer/private data collection, true live model backend, or autonomous repository crawling has been authorised.
- **Next evidence gates:** read actual repository license files/NOTICE/dependency licensing and release integrity, collect independently verified security/ToS/task evaluation, update provenance through a dated, rate-limited, human-reviewed snapshot, then separate Owner-authorized PR for any actual catalog inclusion. A GitHub SPDX response alone does not establish commercial usage rights; `NOASSERTION` must remain unknown.

## V1.8.0 — file-level licence provenance + bounded GitHub drift watcher (Draft / HOLD)

- `license_file_evidence_v180.json` records **ten observed LICENSE/LICENSE.txt/COPYING paths** in the ten research-only public GitHub repositories from V1.7.9, each tied to the earlier observed repository identity and default branch, exact 40-hex Git blob SHA, text cue, source link and observation day (2026-11-04). The files were actually read using read-only repository access. This is evidence of **a file observation**, not legal permission to redistribute a full software package, derivative dependency licensing, medical/automotive certification, security assessment or real industry performance.
- `license_evidence_v180.py` / `test_license_evidence_v180.py`: strict snapshot/sector/identity/branch/path/SHA correlation, no self-asserted legal approval and deterministic read-only report. Explicitly flag **IfcOpenShell** (GitHub repo SPDX `LGPL-3.0`; `COPYING` starts with GPL-3.0) and **OpenTripPlanner** (GitHub API `NOASSERTION`; LICENSE starts LGPLv3-or-later and includes other third-party notices) for mandatory specialist license-scope reconciliation. The remaining eight *text cues* appearing aligned **do not imply their complete dependency/license review succeeded**.
- `source_monitor_v180.py` / `test_source_monitor_v180.py`: no-network offline mode by default and explicit acknowledged live mode. The latter is restricted to **20 read-only GitHub requests maximum** (repository metadata and pinned source-file SHA for each of ten validated, allowlisted repos), with bounded response sizes, timeouts and no redirects; API errors never mean verified deletion, changed SHA/SPDX/default branch are review flags only. No catalog writes, no self-approval, no LLM/API expenses, no production publishing or source promotion. The report is date-stamped and a separate CI artifact rather than being used to edit the frozen `discovery_seed.json`.
- The already-existing `.github/workflows/industry-discovery-review.yml` research-only weekly/manual workflow now includes offline license source validations and, on `schedule`/`workflow_dispatch` **only**, a bounded source metadata/file-SHA monitor. Artifacts are retained for human review and never merged into the current catalog. **Important: the weekly scheduled workflow exists on main but these V1.8.0 changes are still only on this Draft PR branch until a separately authorised merge**, and no manually triggered live monitor is asserted to have run on this branch.
- `advisor_v180_template.html`, `build_advisor_v180.py`, `advisor_v180.html`, `check_advisor_v180.py`: reproducible read-only provenance UI showing all 10 file links and SHAs, visible two-source discrepancy filter, all-source and narrowed-checklist clipboard export, preserved 32-sector original coverage, full pagination and 20 original gap tasks. Real Chromium desktop 1440px and mobile 390px tests check filter/copy/source isolation and zero network egress.
- New research-branch `start.html` and `intelligence.html` link to V1.8.0 and older advisors remain archived; 32 taxonomy sectors, 133 subdomains, 64 editorial workflows, 114 Atlas tool candidates, 69 learning references, 133 unapproved frozen radar source observations and 13 provisional topic mapping rules remain unchanged.
- **Still incomplete:** dependency SCA/CVE, security review, authoritative third-party licensing/NOTICE, acceptance of license terms for any specific commercial use, real customer evidence, authenticated human approvals, model gateway/quotas, merge and production deployment. **Draft / merge HOLD / deploy HOLD / USD0**.
