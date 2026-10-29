# Pilot Lab 07｜真实强制崩溃、SQLite 事务一致性及服务端模拟审批

**状态：研究分支候选，所有运行结果以对应精确 HEAD 的 GitHub Actions 日志和 JSON 工件为准。** 接续合并的 Pilot Lab 06（PR #21），保留原有合成基线，不接入 YIFALIN 生产环境。

## 代码与实际执行边界

- `scripts/real_crash_consistency.py` 复用 Pilot 06 的 **真实 LangGraph 1.2.18 StateGraph / interrupt / Command / SqliteSaver**（SQLite saver 3.1.2）。
- `scripts/verify_crash_consistency.py` 在**不同 Python 子进程**创建 checkpoint、发放模拟批准、恢复节点；利用真实 `os._exit(86)` 立即杀死执行中的进程，不以普通异常或正常退出冒充崩溃。
- 注入位置：事务开始前、SQLite INSERT 完成但 COMMIT 前、COMMIT 之后而图节点返回之前。独立子进程重启后检查未提交的事务回滚，以及已提交的本地效果没有重做。
- `p07_effects`、`p07_outbox`、`p07_audit` 和 `p07_approvals.consumed` 在**同一个 SQLite BEGIN IMMEDIATE 事务**里写入；(tenant,idempotency_key) 有唯一约束。恢复后核对 effect/outbox/audit 的数量与 payload 一致性。
- 服务端**模拟**身份：`alpha_owner` 与 `beta_owner` 仅可批准各自 tenant 的 synthetic_draft；`alpha_viewer` 不可批准；批准有期限、撤销与消费状态。图中的 `source=owner_session` 仍是未经认证的**测试字符串**，单凭它无法触发新效果。
- 所有数据均由测试本地生成；不联网调用模型、不分发信息、不读取真实资料、不调用交易权限、不触碰生产认证/RBAC。

## 故障恢复的严格解释

| 位置 | SQLite 状态预期 | LangGraph 重放目标 |
|---|---|---|
| before_transaction | 零本地效果 | 恢复后可应用一次 |
| before_commit | 进程突然退出，SQLite 回滚全部未提交写入 | 恢复后 effect/outbox/audit/approval 一次性提交 |
| after_commit | effect/outbox/audit/approval 已提交；图节点尚未更新 checkpoint | 重放只查询现有唯一键并返回已提交，无第二次本地效果 |

**本地事务原子性不等于端到端 exactly-once。** Outbox 仍然没有外部消费者/收件方确认或失败重试；`at-most-once` 只适用于本地 SQLite 唯一键所保护的效果，不能推出外部消息恰好一次投递。其他尚未覆盖事项：真正 checkpoint 写入过程的 crash hook、进程之外的断电、磁盘损坏、SQLite 多主机部署、真实 OIDC/MFA、真实用户隔离、并发 LangGraph thread 调度、业务补偿。

## 复现命令

在**隔离的 CI / 虚拟环境**中安装固定版本：

```bash
python -m pip install --only-binary=:all: 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
python scripts/verify_crash_consistency.py --output-dir test-results/p07-a
python scripts/verify_crash_consistency.py --output-dir test-results/p07-b
```

CI 工作流为 `.github/workflows/real-upstream-crash.yml`。上传合成 JSON / 强制退出 marker / 依赖清单，**排除数据库文件**。每个验收用例失败应使 CI 红灯，不允许替换为预先编造的绿色静态 JSON。

## 下一阶段门禁

本研究仍不能升级为真实业务工具。先补齐 checkpoint 持久化期间注入、审批签名/真实后端身份绑定、SQLite 锁竞争/繁忙恢复、任务租约与多进程恢复、Outbox dispatcher 端到端投递语义（含消费者去重）、故障恢复延迟分布，以及真实无敏感数据的独立复现。认证、生产会员/权限/数据库结构变更需要单独审批。
