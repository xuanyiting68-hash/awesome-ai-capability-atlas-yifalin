# Pilot Lab 09｜在真实 SQLite Checkpointer INSERT 语句内部强制终止进程

**实验状态：以对应最新 HEAD 的 GitHub Actions 真实结果为准。** 接续已合并 PR #24（Pilot Lab 08），不修改或重置此前任何已通过实验。

## 官方依据与研究问题

[LangGraph 官方持久化文档](https://docs.langchain.com/oss/python/langgraph/persistence#durability-modes) 指出 `durability="sync"` 在开始下一个执行步骤前同步保存 checkpoint。官方 [SqliteSaver 3.1.2](https://reference.langchain.com/python/langgraph.checkpoint.sqlite/SqliteSaver) 有 `put` 和 `put_writes` 两条真实写入路径：checkpoint 超步状态和 task pending writes。

Pilot Lab 07 的故障注入是在**业务 commit 节点**运行过程中；本轮进一步从 SQLite 实际 INSERT 语句内部用 connection-local TEMP TRIGGER + UDF 调用 `os._exit(89)`，研究进程突然退出时未提交的 SQLite 操作和 LangGraph 恢复。

## 三个真实故障位置

| Site | SQL 操作 | 退出位置 | 期望的核心性质 |
|---|---|---|---|
| `checkpoint_before` | `checkpoints` | INSERT 前 SQLite trigger | 最近已提交 checkpoint 可读 |
| `checkpoint_after` | `checkpoints` | INSERT 后但外层 SQLite 事务未提交 | 未提交写回滚，历史 checkpoint 仍可读 |
| `writes_after` | `writes` | task pending-write INSERT 后、外层事务未提交 | 未提交 task-write 不破坏持久恢复 |

所有触发位置必须保存进程 PID、fsync 后的 trigger marker，Runner 必须看到独立进程返回码 **89**。只看到 Python 异常或者未发生注入都判失败。

## 首次真实 Runner 发现：checkpoint 可读不等于图任务可继续

第一版 GitHub Actions [run 41022894526](https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin/actions/runs/41022894526) 在 `checkpoint_before` 场景**正确红灯**：`checkpoints` 表仍有 3 条持久记录，`writes` 有 13 条记录，但恢复后的 `StateSnapshot.next=[]`、`outcome="APPROVED: mock_only"`，同时 `effects=outbox=audit=0`、批准未消费。再次运行图并没有自动补全提交。

这不是数据库事务不一致，而是**图调度状态与业务效果之间存在缺口**。本轮不将该状态冒充正常 LangGraph 恢复，必须显式检测 `orphaned_approval_detected`，再使用测试环境中已持久、未撤销、未过期、资源和租户相符的**模拟服务端批准凭证**触发受限本地补偿。补偿调用 Pilot 07 的 `consistent_commit`，共享同一个 effect/outbox/audit/approval SQLite 原子事务和幂等键约束。

**受控补偿不是 LangGraph 原生调度恢复，也不是真实生产身份认证。** 如果无授权、跨租户、凭证撤销或过期，不能补偿。每个故障场景单独记录发生的是图直接恢复还是测试环境本地补偿。第一轮失败日志保留，修复后的独立 CI 才能成为新证据。

## 后续恢复与强制验收

1. 使用真实 `StateGraph`、`interrupt`、`Command(resume)` 和真实 `SqliteSaver` 建立可恢复模拟审批线程。
2. 在独立 Python 进程中向隔离的数据库发放服务端**模拟**批准。
3. 在新进程的真实 Checkpointer 中安装仅该连接存活的 trigger，并恢复图直到被真实 SQLite 回调强制杀死。
4. 从另一个进程打开 SQLite 检查已经持久化的 snapshot、先前 checkpoint、业务账本、outbox 和审计一致性。
5. 根据原始 checkpoint 的 pending review/next 状态尝试图恢复；如检测到已批准但无后继任务且没有业务效果，则显式记录异常并通过验证中的模拟服务端批准执行独立本地补偿。两条路线分别标记，最终检查业务效果**仅一次**、模拟批准消费一次以及 `PRAGMA integrity_check`。
6. 每轮完整执行后在完全新的 SQLite 数据库上再复现一遍，并保留原始运行日志和依赖版本清单。

## 不可越过的边界

这里验证的是 **SQLite 语句执行过程中的进程强制退出**，不是随机切断物理电源、磁盘扇区撕裂、WAL 文件损坏、网络分区或云存储级容灾。人工 SQL 触发器是故障注入机制，不代表自然故障发生概率。

真实商业用户身份、权限系统、金融账户、LLM 请求和外部投递均未接入。每轮实验只能说明该实验环境下的 checkpoint 恢复与本地 SQLite 事务一致性，**不证明生产灾难恢复或端到端 exactly-once**。

## 复现实验

```bash
python -m pip install --only-binary=:all: 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
python scripts/verify_checkpoint_faults.py --output-dir test-results/p09-a
python scripts/verify_checkpoint_faults.py --output-dir test-results/p09-b
```

CI: `.github/workflows/real-upstream-checkpoint-faults.yml`。只上传 JSON、故障标记和依赖，不上传数据库文件。

**下一门禁：**独立仓库中跨进程 checkpoint writer 锁竞争；连续随机时点故障统计；过期租约与不同主机时钟问题；真实持久化 outbox consumer 失败补偿；独立复核第三方 SDK 更新是否改变契约。
