# Atlas V1.5｜能力组合研究工作台（Capability Recipe Studio）

> **真实状态**：六个组合都是“可由读者按步骤手动复现和验收的参考方案”，不是已经部署、获得安全审计或者商业许可证批准的产品。当前 `verified_integration_count = 0`。

## 为什么接续现有目录而不是重新造一个平台

- 使用 `data/curated.json` 中 **133 个编辑精选**作为候选仓库唯一表；它们的 `verification=repository-exists` 只证明目录内仓库经编辑核实存在，**不证明安全**。
- 使用 `data/blueprints.json` 中已冻结的六类业务蓝图，精确保留工具和风险门禁，避免出现新建的未经研究的集成方案。
- 使用 `data/research_briefs.json` 中 Top 30 的官方来源研究（只作桌面研究，不冒充执行结果）。
- 使用 `data/repo_metadata.json` 的本地公开 GitHub 元数据快照作时间提示，页面展示 **snapshot 时间戳**，不假设数据是实时。
- 与已有 Atlas 首页、Top 30、Project 与 Pilot Lab 页面共享导航；`atlas_favorites_v1` 仍是原有仓库收藏格式 `repo:owner/name`，不会用新格式覆盖。
- 新的组合收藏使用 `atlas_recipe_favorites_v1`；两个收藏都仅存当前浏览器 localStorage，**不是 GitHub Star / Fork，更非跨设备账号同步**。

## 六个面向真实业务目标的研究组合

| 配方 | 已有蓝图 | 来源（候选工具；不是实际集成） | 需要手动留存的验收成果 |
|---|---|---|---|
| 视频创作 | video | Remotion / FFmpeg / faster-whisper / Postiz | 授权素材、样片、字幕抽检与审批记录 |
| 自媒体运营 | social | Postiz / n8n / PostHog | 原创内容日历、批准记录、合成归因记录 |
| 合规获客 | leads | Formbricks / Typebot / Twenty / Cal.com | 同意标识、去重、撤销证明、模拟预约 |
| 客服 CRM | crm | Twenty / Chatwoot / Mautic / PostHog | 合成工单、权限隔离与退订控制 |
| 金融 AI 研究 | finance | Qlib / RD-Agent / LEAN / Phoenix | 研究假设、时序切分、成本/OOS 审计 |
| 互动教育 | education | Docling / RAGFlow / Open edX / Whisper.cpp | 授权课程片段、可溯源练习、复盘记录 |

每套 `data/capability_recipes.json` 中的结构化字段包括：业务场景、难度、输入、五阶段人工复现步骤、工具候选、每步留存标记、产出、验收失败条件、审批门禁，以及不可越过的停止条件。**步骤只是设计/研究方法**，不是已执行的第三方安装教程；涉及数据与权限的环境变量、API 密钥、具体商业条款均必须在真实部署前单独核验。

**V1.5.1 已新增三项真实执行的第一方离线合成演示：** `leads` 复用原同意与去重引擎，`education` 检查原创讲义的原文引用及弃答，`finance` 进行纯虚构价格的严格时间切分与成本后核算。运行器为 `examples/recipe_demos/run_demo.py`，冻结验收合同为 `data/recipe_demo_contract.json`；发布时生成的可复核结果为 `data/recipe_demo_results.json`。完整方法与预期请见 [V1.5.1 可复现演示](RECIPE_DEMOS_V151_CN.md)。**执行的是本站第一方标准库示例，不是所列二十个第三方工具的端到端集成。** 视频、自媒体和 CRM 三套仍只有人工复现设计。

## 研究证据覆盖分（0–100；不等于软件质量或风险评级）

以**组件仓库**为单位显示明细，并对每套组合取组件分数算术平均。数据来源和规则完全可重算：

| 轴 | 上限 | 计分证据 |
|---|---:|---|
| 编辑精选仓库存在 | 10 | 该仓库在 `curated.json` 且 `verification=repository-exists` |
| Top 30 官方 README 研究 | 20 | `research_briefs.json` 中存在 `official-github-readme` |
| 官方 README 不可变 Blob 引用 | 10 | Research Brief 中有 40 位 commit/blob SHA 引用 |
| 元数据近期有更新 | 20 | **相对元数据快照时间**，最近推送 ≤90 天为 20；91–365 天为 10；更早或无数据为 0 |
| 单独上游组件隔离实验 | 25 | 目前仅 Docling 的单组件本地原生 PDF 实测，有 `docs/REAL_UPSTREAM_PILOT_DOCLING_CN.md` 与独立 CI 证据；**不是组合 E2E** |
| 完整商业许可及安全审查 | 15 | 所有第三方候选当前都未完成，统一为 **0** |

满分 100 只是评分轴上限，不是已有工具达到 100；尤其“在 GitHub 上近期更新”只证明代码推送活动，不代表社区稳定、代码安全或交付质量。绝不将原有编辑推荐 `score:99` 混用为可部署质量评分。

需要注意：

1. 这个评分**衡量的是研究证据覆盖程度**，不能比较不同领域软件的实际效果；高分仍可能需要严格安全/许可审查。
2. 最多 25 分的隔离测试只用于**单组件**。即使 Docling 已在固定 SDK、合成 PDF 的沙盒内验证，也不说明和 RAGFlow / Open edX 等组件已经完成 E2E 集成。
3. 元数据来自固定快照，可能过时。页面显示 `generated_at_utc`；超过 60 天会提示更新核验。只读访问仓库本地 JSON，无实时 GitHub API 请求。
4. 现有 `.github/workflows/repo-metadata.yml` 每周三定时同步 GitHub 公开元数据，并依既有流程发布快照；它**不会自动复审许可证、安全性或真实兼容性**。如自动更新被平台权限或限流阻止，用户看到的是最后成功提交的快照，不能宣称实时。

## 交互和导出

`recipes.html` 按场景、难度、关键字匹配与排序，支持本地保存组合、本地保存仓库（复用原 `atlas_favorites_v1`）、展开每个组合的可检查步骤、复制过滤链接和导出**研究清单 JSON**。导出携带快照时间和状态声明，不携带 API 密钥、用户个人数据或实时账户信息。

## 验收和发布门禁

- `scripts/validate_recipes.py` **拒绝**未经来源核对的新仓库、伪造集成通过、冒称安全审查、缺失人工门禁、虚构 demo 路径和超出 100 的评分轴。
- `scripts/test_recipes.py` 对上述负向行为建立独立回归。
- `scripts/build_site.py` 在发布时检查配方契约，将 `recipes.html` 和 JSON 归档到 Pages，并在 `deployment.json` 明示配方数、来源仓库数、已验证组合数。
- `tests/deployed-smoke.cjs` 在 GitHub Pages 的真实 Chrome 中检查移动端、场景筛选、配方和仓库收藏同步、双语、证据分与原有页面共存。
- 任何认证/RBAC、跨设备收藏、第三方工具执行、真实 API 或生产业务自动化，都是**未来独立安全审查及授权范围**，不能因为页面上线而默认为获批准。

## 下一个里程碑建议

在可维护的数据合约之上，精选 2–3 个有清楚用户需求的组合建立**完全免费的离线合成运行包**（含可重复脚本、输出检查和逐次 CI 记录）；不同场景的安全/许可门禁不能用“有 README”“有 Star”替代。更多资源只应通过增量验证纳入，而不应追求 5,000 全部深度测试。
