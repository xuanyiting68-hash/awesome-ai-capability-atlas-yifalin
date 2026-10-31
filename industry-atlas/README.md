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