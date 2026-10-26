# V1.4 · Top 30 研究与 Fork 决策实验室

> 本文是**待验证研究队列**，不是安全认证、实测排行榜或已获商用许可清单。2026-10-26 从既有精选与业务蓝图提炼，按用户业务优先级人工排序，不以 Stars 代替质量。

## 立即可用的数据

- [Top 30 研究队列](../data/top30_evaluation.csv) — 30 个项目、15 个机器可读字段
- [V1.3 来源和风险说明](SOURCE_AND_REVIEW_CN.md)
- [六套业务组合蓝图](BLUEPRINTS_CN.md)
- [完整 5,000 条索引](../data/catalog.csv)

## 评分定义：研究价值与可落地性分开

每维度 0–5 分。**未取得可验证证据的维度应标记 unknown，不得臆造 5 分。**

| 维度 | 权重 | 可复核标准 |
|---|---:|---|
| 业务适配 | 20% | 对金融AI、教育或合规增长是否解决真实痛点 |
| 复现质量 | 20% | 锁定版本、示例输入、测试、独立运行结果 |
| 维护与生态 | 15% | 近期提交、Issue、稳定发布及社区支持 |
| 授权明确性 | 15% | LICENSE 原文、依赖许可、模型与素材授权 |
| 安全与权限 | 15% | SAST/依赖扫描、沙箱最小权限、数据边界 |
| 集成复杂度与成本 | 10% | 部署时长、算力/API费用、技术负债 |
| 可迁移与长期价值 | 5% | 标准接口、数据可导出、可替换性 |

计算方法：仅当七维证据齐备，计算 `weighted_score = sum(weight × points/5)`，最高 100。
未齐备时不排名为 verified；可按业务优先度排研究队列，但不得对外称为质量综合分。

## 许可、安全与 Fork 决策

| 状态 | 定义 | 下一步 |
|---|---|---|
| DISCOVERY | 只发现项目/目录条目 | 检查仓库与维护情况 |
| TRIAGE | 基本功能、发布时间、许可证已初审 | 进行依赖和数据流审查 |
| SANDBOX | 在不接触真实凭据的环境运行样例 | 记录 SHA、命令、成本、输出、失败案例 |
| APPROVED_FOR_PILOT | 安全、授权、质量边界明确，负责人审批 | 在测试用户/模拟环境小范围使用 |
| PRODUCTION_REVIEW | 另行完成生产安全和法律审查 | 按正式部署审批流程操作 |

**Fork ≠ 可商用，也 ≠ 适合生产。** 特别关注可见许可证与依赖、云模型数据留存、商业视频素材、社媒渠道官方 API、付费订阅限制、金融业务牌照问题。

## 首批六个可复现实验包

### A. 原创短视频工厂

`研究资料 → 独立核查与脚本 → 本人出镜 → faster-whisper 字幕 → Remotion/FFmpeg 生成 → 人工审批 → 官方渠道发布`

验收：10 条内部测试片、字幕准确率人工抽检、版权清单、剪辑节约时间；财经内容呈现独立推导，不给买卖指令。

### B. 自媒体运营系统

`选题 → 内容日历 → 各平台原创适配 → 审批 → Postiz 及获授权渠道 → PostHog 归因`

验收：每次发布均有审批与可回溯 URL；禁自动刷量、群发和绕开渠道授权。国内平台应单独核验是否支持 API。

### C. 合规获客与 CRM

`Formbricks 用户主动留资 → 明示同意/退订 → n8n 去重 → Twenty CRM → Chatwoot 工单 → 指标分析`

验收：可撤回同意、客户数据隔离、DSAR/数据删除流程、工单解决率。严禁采集私人数据并自动骚扰。

### D. 金融 AI 研究台

`OpenBB 数据核对 → Qlib 特征与模型 → vectorbt/Lean 回测 → 交易成本/滑点 → 样本外验证 → 模拟盘`

验收：数据来源和授权留痕、避免未来函数、对照基线、费用敏感性、分行情失效检测。**不连接真实资金账户**。

### E. 双语金融 AI 教育

`已授权教材 → Docling/MarkItDown → LlamaIndex/RAGFlow → 中英双语问答 → 人工题库验证`

验收：来源可追溯、答案正确率和幻觉率、学习者反馈、版权/教学资料访问权限。

### F. Agent 研发与安全

`GitHub Issue → Codex/Claude Code/OpenHands 之一 → LangGraph 编排 → PR → Promptfoo 安全回归 → 人工审批`

验收：独立 worktree、禁止泄露密钥、成本预算、任务重试、审查证据、可回滚。不给 Agent 默认生产密钥或自动合并权限。

## 每个 Top 30 项目应补充的实际证据

```yaml
repo: owner/name
commit_sha: null
license_spdx: null
license_legal_review: not-reviewed
latest_release: null
last_push_utc: null
security_scan_ref: null
dependency_scan_ref: null
sandbox_run_command: null
sandbox_run_output: null
benchmark_dataset: null
quality_metric: null
cost_aud_per_run: null
business_owner: null
approval: pending
```

## V1.4 后续验收标准

1. 30/30 记录按 GitHub 原始证据补齐有效 SHA、许可和最新维护信息；
2. 标出许可证冲突、维护停滞、存在未知风险的项目，避免虚假的统一质量分；
3. 六个实验包各有可执行的隔离 Demo 与数据流/风险说明；
4. 网站新增「Top 30」「已验证 / 待验证」「可 Fork / 需审批」筛选；
5. 所有推荐都可追踪证据，且任何自动采集失败均不会被填造的数字掩盖。

> 截至本文件创建，30 个项目仅为研究选择，不代表完成上述验收。
