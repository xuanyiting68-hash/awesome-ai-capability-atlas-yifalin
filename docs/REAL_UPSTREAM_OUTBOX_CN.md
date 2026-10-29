# Pilot Lab 08｜SQLite Outbox ACK Gap、消费者去重、锁竞争与恢复

状态：研究分支实验；**准确通过次数只能从 GitHub Actions 对应 SHA 的日志与 JSON 中读取**。从 Pilot Lab 07 的已合并同期 checkpoint、SQLite 原子事务、模拟审批继续，不重建知识库，也不进入生产。

## 研究问题

Pilot Lab 07 将一个合成业务效果、outbox 和审计放在单个 SQLite 事务中，因此能够在本地保护一致性；但发给另一事务域的消费者之后，发送方可能在 ACK 前崩溃。此时无法用一个 SQLite 本地事务跨两个数据域实现真正的端到端 exactly-once。Pilot 08 专门实测这个 ACK gap 与可靠重试，不宣称解决分布式事务。

## 已实现的可执行技术设计

- **真实上游 Agent 生产者**：固定 LangGraph 1.2.18 + checkpoint-sqlite 3.1.2，复用 Pilot 07 的 `durability="sync"`、`interrupt`、`Command(resume)` 和 SQLite 持久审批，生成真实合成任务和本地 `p07_outbox`。
- **消费者独立 SQLite 文件**：`p08_inbox` 通过 `PRIMARY KEY(tenant,idem)` 做本地消费幂等，同一个 payload 重发只能产生一份收件记录；与 sender DB 不共享事务。
- **发送方租约与 fencing token**：`BEGIN IMMEDIATE` 原子 claim，使用真实 wall clock 的租约和随机 claim token；过期重试更换 token，旧 worker 的 ACK 必须被拒绝；只接受严格匹配的合成 `synthetic_draft` payload。
- **强制崩溃点**：消费者事务提交前或提交后、发送方 ACK 之前，`os._exit(87)` 且落盘 marker，绝不把正常异常伪装成强制崩溃。
- **多进程竞争**：8 个独立 Python worker 同时竞争同一 outbox；此外真实 `BEGIN IMMEDIATE` 锁持有进程与 waiter 竞争，验证 SQLite busy_timeout 的实际表现。
- **侦测与隔离**：跨租户相同 key 允许各自单独消费；消费者 receipt 丢失须能查出已 ACK 却缺少收件证据；异常或危险类型 payload 必须拒绝，而非执行。
- **保存**：测试过程的 JSON、每阶段返回码、耗时、强制退出 marker、Python 依赖清单进 GitHub Actions Artifacts，排除任何 SQLite 数据库文件。

## 严格范围说明

| 语义 | 已设计的验证边界 | 禁止引申 |
|---|---|---|
| at-most-once | **消费者 SQLite inbox** 在同一租户/同一幂等键下只保留一条 | 不证明下游真实动作只执行一次 |
| at-least-once | 只在本地有恢复 worker 和有效重试时，测试重复投递与 ACK 收敛 | 不证明永续调度或网络最终可达 |
| exactly-once | 同一个接收端 SQLite unique key 的**本地效果** | 不证明不同数据库、HTTP、金融账户或第三方服务端到端恰好一次 |
| 服务端身份 | 继续使用先前已标注为模拟的 owner/tenant 批准 | 不是真实 OIDC、MFA、RBAC |
| 网络与生产 | 无外部网络接收、无真实平台部署、无交易、无真实用户信息 | 不得声称金融生产系统可用 |

## 如何复现

```bash
python -m pip install --only-binary=:all: 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
python scripts/verify_outbox_dispatch.py --output-dir test-results/p08-a
python scripts/verify_outbox_dispatch.py --output-dir test-results/p08-b
```

文件：
- `scripts/real_outbox_dispatch.py`：可执行的本地 Outbox / Inbox / ACK 协议。
- `scripts/verify_outbox_dispatch.py`：独立进程、真实 sqlite、故障、竞争与不变量。
- `.github/workflows/real-upstream-outbox.yml`：真实安装并运行 SDK、重复复核及归档。

### 尚未通过的下一技术门禁

当前仍不验证真实消息中间件、消费者无法回滚的副作用、自动补偿、时钟漂移/网络分区、外部 HTTP 幂等性、真正的身份签发或 SLO 长周期测量。后续应在免费隔离环境继续测试真实 checkpoint 数据库写入过程中的断电式故障、端到端确认/重试策略、锁竞争负载与故障注入概率统计。**所有 CI 绿灯不能被称作生产安全认证。**
