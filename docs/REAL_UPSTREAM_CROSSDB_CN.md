# Pilot Lab 11｜跨 SQLite 数据库故障、参考时钟偏差与独立审计

**状态：研究分支，运行成功与否以指定 HEAD 的真实 GitHub Actions 日志为准。** 接续已合并 Pilot 10（PR #26），原始 Atlas、研究结果和生产系统保持不变。

## 为什么做这一轮

Pilot 10 已在**同一个 SQLite 事务**内完成恢复任务、合成业务效果、Outbox、源审计及批准消费；但消息抵达**另一数据库**、另一个审计服务之前不能使用同一个原子事务。为了不把单库原子性说成端到端 exactly-once，本轮使用实际不同 SQLite 文件，把三个事务域的强制崩溃位置逐一复核。

## 实验范围与真实执行

- **发送方数据库**：真实 LangGraph 1.2.18 + SqliteSaver 3.1.2 在 Pilot 09 的 checkpoint 内部被 SQL 触发器真实 `os._exit(89)` 杀死；Pilot 10 独立任务协调器恢复并在本地 SQLite 原子写入 `p07_effects`、`p07_outbox`、`p07_audit`。不更改原图调度结果。
- **接收端数据库**：真实 `p08_inbox`，`PRIMARY KEY(tenant,idem)` 防止相同合成消息重复落库；这是**本地唯一收件记录**，不等于银行、邮件、订单等真实外部效果只执行一次。
- **独立审计数据库**：新增 `p11_audit_events`，包含每个源 ACK 的独立事件、payload 的 SHA-256、上一事件摘要及当前链摘要。三份数据库互不共享 COMMIT。
- **真实强制退出**：在接收端 COMMIT 前、COMMIT 后但源 ACK 前、源 ACK 后但独立审计记录前执行 `os._exit(91)`，保存 fsync marker；新进程重开所有库并验证。故障窗口中应明确报告未完成，而非冒充三库一致。
- **受限审计补记**：源 ACK 已存在但审计缺失时，仅在发送方原始效果/Outbox/审计、接收方收据 payload 全部相符时，写入明确标注 `RECONCILED_ACK` 的独立观察记录；不伪造已收到的外部确认或新的收据，补记重复运行应幂等。
- **时钟偏差负向实验**：将工作进程本地时钟人为快进及倒退 3600 秒，并与同一主机 SQLite 数据库时钟比对；超容忍窗口直接拒绝 claim/process；已持有有效 token 的 worker 不能通过时钟偏移绕过门禁。这个实验**不是**真实 NTP 变动、多主机时钟一致性，也不验证跨地域节点时钟。
- **篡改负向实验**：人为删除接收端收据后，不得用审计补记凭空重建；修改审计链哈希必须能够由第三库本地独立校验检测到。

## 验收标准

实际程序：`scripts/real_crossdb_reliability.py` 与 `scripts/verify_crossdb_reliability.py`。先真实生成 Agent checkpoint 强制崩溃及 Pilot 10 恢复效果，再对同一合成任务跨库投递、故障注入和审计。测试失败为红灯，不替换静态绿色结果。CI 每次在新的三份 SQLite 数据库上运行完整实验，再做第二次独立全量复现；上传过程日志、退出码、marker 和依赖版本，**排除原始数据库文件**。

```bash
python -m pip install --only-binary=:all: 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
python scripts/verify_crossdb_reliability.py --output-dir test-results/p11-a
python scripts/verify_crossdb_reliability.py --output-dir test-results/p11-b
```

CI: `.github/workflows/real-upstream-crossdb.yml`。

## 不能越界宣称的能力

**并未证明跨数据库事务的原子性**；恰恰是显式展示不同数据库可出现收据已落盘、ACK 缺失或独立审计缺失的中间状态。审计哈希链没有外部可信锚点或签名，能检测本地单行改动，但有写权限的攻击者可以整链重写或删除。SQLite 参考时钟仅在单台机器上，不能代替真实的分布式授时、安全认证或 Byzantine 容错。

不存在网络收发、真实外部消息中间件、真实用户、客户资产、LLM、模拟/实盘金融订单或生产 RBAC/OIDC。保持所有受限接口关闭。实验中的一致性指标仅能证明该合成、单主机、固定版本研究条件下观察到的恢复结果。

## 下一研究门禁

在负成本和合规边界内，可再研究多进程服务失联的任务再派发策略、数据库之外的不可逆副作用与补偿、密钥管理及外部审计锚点设计、真实不同主机时钟与网络分区。但任何真实认证、生产数据库、收费模型或订单/实盘连接都需单独授权和独立安全验收。
