# Pilot Lab 06｜LangGraph 持久检查点与跨进程恢复：真实 SQLite 沙盒

> 2026-10-30。接续 Atlas 已合并的 PR #20 真实 Docling → LangGraph → Promptfoo 合成 E2E。该实验**真实安装并运行 LangGraph 与其官方 SQLite 持久层**，专门研究之前缺失的“重启恢复”和“重复提交保护”。这不是生产 YIFALIN 的实现，未调用任何券商、LLM 或真实 Owner 身份系统。

## 官方技术依据

- [LangGraph SQLite Checkpoint on PyPI](https://pypi.org/project/langgraph-checkpoint-sqlite/)；2026-10-12 的稳定版本 **3.1.2**，官方解释适用于本地开发和轻量部署。
- [官方 SqliteSaver.from_conn_string API](https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver/from_conn_string)；可通过磁盘 SQLite 文件实现持久化。
- [官方 checkpoint SQLite 源码](https://github.com/langchain-ai/langgraph/blob/main/libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/__init__.py)。
- [官方 LangGraph Interrupt 文档](https://docs.langchain.com/oss/python/langgraph/interrupts)；中断会保存执行状态，并通过 Command 恢复。
- 官方特别提示反序列化风险：工作流显式设置 `LANGGRAPH_STRICT_MSGPACK=true`；本实验仍不允许不可信用户写入 checkpoint DB。
- 实际执行版本：`langgraph==1.2.18` 与 `langgraph-checkpoint-sqlite==3.1.2`；真实传递依赖版本在 CI 工件中保存，但尚未 hash 锁定所有依赖。

## 核心行为：不是一次进程里调用两次

`scripts/real_durable_recovery.py` 在正式临时 Runner 的 SQLite 文件中调用 `SqliteSaver.from_conn_string`，`StateGraph` 内使用真正的 `interrupt()` 和 `Command(resume=...)`。

`scripts/verify_durable_recovery.py` **每一步都通过新 Python 子进程执行**：

1. 第一个进程提交模拟草稿意图并中断 → 程序退出；
2. 第二个独立进程通过相同 thread ID 打开数据库，找到持久化 review checkpoint；
3. 第三个进程恢复审批（拒绝/允许） → 检查实际状态和可恢复结果；
4. 使用不同线程但相同 idempotency key 重放模拟提交 → 只允许一次写入 SQLite `commits`；
5. 模拟网页伪造审批、来源不完整、`send_order` 和未完结待审状态 → 必须保持拒绝或中断；
6. **六个真正独立的 Python 子进程**，同时对相同 SQLite 唯一键提交 → 事务使用 `BEGIN IMMEDIATE`、`INSERT OR IGNORE` 和唯一约束，必须得到 1 个成功与 5 个重复拒绝。
7. `journal` 表记录线程、模拟键、决策及 UTC 时间，和最终 `commits` 对账。

每个新进程的 PID、阶段、状态和提交计数保存在 `stages/*.json`；最终生成 `durability-result.json`，然后独立 unittest 再完整复现一遍。CI 只上传合成 JSON/依赖清单，**不上传 SQLite 原始库文件**。

## 13 项严格契约验收

| ID | 真实验证 |
|---|---|
| D01 | 实际中断 + 零账本写入 |
| D02 | 另一个 Python 进程能打开 checkpoint 并找到待审批节点 |
| D03 | 新进程拒绝恢复 → 零提交 |
| D04 | 新进程通过模拟 Owner 审批 → 只新增一个合成提交 |
| D05 | 另一个图线程使用重复键 → 不重复入账 |
| D06 | 伪造来源网页的批准 → 拒绝 |
| D07 | 伪造来源页码 → 审批之前拒绝 |
| D08 | `send_order` → 审批之前拒绝 |
| D09 | 未完结审核能持续保留，进程退出不会“自动批准” |
| D10 | 第二个不同唯一键可以通过模拟审批 |
| D11 | 6 进程同时竞争 ledger key → **1 次成功、5 次拒绝** |
| D12 | SQLite 日志 9 次提交尝试、最终唯一提交键数 3，可对账 |
| D13 | 明确标记未完成真实身份验证、生产上线、模型调用和图并发调度 |

## 结果如何解读

本轮若成功，仅证明 **SQLite 单机文件上、经过正常进程结束的持久 checkpoint 与恢复**，以及 SQLite ledger **同一键至多一次生效**。完全不能解释成：

- 真实 Owner 已通过认证：传入的 `source='owner_session'` 是**模拟字符串，可被任意代码伪造**，不是真实登录、RBAC、MFA 或数字签名。
- 生产级灾难恢复：未在账本写入中间强制 kill -9，未验证操作系统崩溃、磁盘损坏、断电或备份恢复。
- 端到端原子事务：checkpoint 和 ledger 是**两个 SQLite 独立事务**；唯一键只能降低重复生效风险，不能替代 outbox/两阶段事务设计。
- 多主机并发 Agent 调度：测试只并发写同一个 SQLite ledger，不是六个 LangGraph 工作者同时调度同一 thread，也不是 PostgreSQL。
- 上一 PR #20 的 PDF/OCR 或真实 LLM 安全提升：本轮是**独立持久化子系统**；三工具 E2E 已由既有 CI 继续保护，不能声称它在本次工作流内再次端到端运行。

## 后续升级门禁

完成服务端不可伪造身份+RBAC、使用真正持久的用户/组织范围隔离、跨线程并发租约、恢复时延和故障注入、幂等唯一键的真实业务副作用 outbox、SQLite WAL/backup/retention 或转向 PostgreSQL；做模型真实请求和用户资料时需先取得合法处理许可和资源授权。**不得借本实验打开交易下单权限或在生产平台部署未经审查的 Agent。**

验证：[GitHub Actions 工作流](../.github/workflows/real-upstream-durable.yml)；结果以运行对应 commit 的 CI 日志和上传 JSON 工件为准，本文不预先宣称通过。
