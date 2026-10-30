# Pilot Lab 10｜独立持久任务对账与恢复协调器

**状态：研究候选；只有精确 HEAD 的 GitHub Actions 真运行可证明验证通过。** 继续原仓库 Pilot 09（PR #25）；不重建 Atlas，不修改已冻结的实验材料或生产平台。

## 研究目标与原始发现

Pilot 09 的真实 `SqliteSaver` CHECKPOINT INSERT 前/后故障，能够出现 `StateSnapshot.next=[]`、图状态为 `APPROVED: mock_only`，而本地业务效果 `p07_effects`、Outbox、Audit 仍为零的**调度/业务状态分离**。先前 Pilot 09 的手动受控补偿为可行性实验，但尚未建立独立于图调度器的持久任务队列、并发任务领取和异常自检。

本轮将任务发现/恢复同 LangGraph 的原有 checkpoints 分离，保留对真实 Checkpoint 的只读验真，不凭 `APPROVED` 文本直接放行。

## 实际实现

- `scripts/real_recovery_coordinator.py`：本地合成 SQLite `p10_tasks`，包含持久任务状态（PENDING、LEASED、DONE、BLOCKED）、随机 fencing token、所有者、租约到期、尝试次数及执行结果。
- **真实发现**：逐个核对持久化 LangGraph StateGraph 的状态、任务证据、幂等键、thread_id、审批状态及 next；只有与对应 `p07_approvals` 数据库票据完全一致、尚未产生本地效果、未撤销/未过期/未消费的合成任务才可入队。
- **任务领取**：多个独立进程使用 `BEGIN IMMEDIATE` 原子领取，过期可以重领。旧 token 或过期 Worker 不能提交；消费端使用 SQLite 真实写锁做单机串行化。
- **原子恢复**：将 `p07_effects`、`p07_outbox`、`p07_audit`、批准凭据 consumed 和任务 `DONE` 放在**同一个 SQLite 事务**中。此处并未修改或修复原始 LangGraph 的 scheduler checkpoint，而是构建**独立的合成工作恢复路径**。
- **真实强制退出**：恢复事务 COMMIT 前与 COMMIT 后，通过 `os._exit(90)` 强制结束进程，记录 PID + fsync marker。已提交的任务与账本必须一起存在，未提交则必须一起回滚。
- **负向控制**：伪造/过期 fencing token、原 Owner 租约失效、审批撤销、审批过期、未结束的 graph interrupt 不可入队、不一致审计可查出；两个租户四个不同任务由八个真实进程同时竞争和执行。
- **独立两轮**：每轮全新 SQLite DB 和 subprocess 进程；保存每个阶段的返回码、耗时、异常及固定版本依赖。计时仅作为 CI 观察值，绝不能称作已达到生产 SLO。

## 门禁与信任边界

这个实验仍是**一个主机上的 SQLite 原型**：任务队列与模拟业务账本在同一个 SQLite 文件中，但不依赖 LangGraph 的下个待执行节点才能复原业务效果。因此它验证的是另一条协调/对账恢复路径，不是对 LangGraph checkpointer 内核的修复。

依然没有真实服务器身份、OIDC/RBAC、用户数据、真实消息中间件、客户外部动作、模型 API 或实盘/模拟订单。不证明跨主机时钟一致、数据库备份灾备、网络分区容错和端到端 exactly-once。不得将此原型直接应用于自动交易执行。

## 复现实验

```bash
python -m pip install --only-binary=:all: 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
python scripts/verify_recovery_coordinator.py --output-dir test-results/p10-a
python scripts/verify_recovery_coordinator.py --output-dir test-results/p10-b
```

CI: `.github/workflows/real-upstream-coordinator.yml`。JSON 及 marker 上传至 Actions Artifact，**不上传任何 SQLite 文件或用户数据**。任何预期外的真实失败应导致 CI 红灯；不可用静态伪造 JSON 代替执行。

## 后续门禁

单库依赖与进程意外终止后的已验证任务恢复只是基础。下一阶段才研究不同数据库的原子性边界、租约时钟跳变、多机器协作、独立审计、生产级身份和真实平台权限；涉及认证/生产数据库/订单必须经专门审批。
