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
