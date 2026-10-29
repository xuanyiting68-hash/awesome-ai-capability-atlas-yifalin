# YIFALIN Pilot Lab 02｜LangGraph 官方 SDK 真实沙盒验证

> 本实验有别于 Pilot Lab 01 的纯第一方契约判定。此版本**确实安装并运行第三方 LangGraph 软件**，但只在 GitHub Actions 临时 Ubuntu Runner 中，用模拟字典代替 Owner 审批、内存对象代替草稿写入，没有真实模型、API 密钥、金融账户、真实订单或生产用户信息。

## 研究对象与版本

- 官方仓库：[langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
- 固定上游版本：**1.2.18**，GitHub [Release](https://github.com/langchain-ai/langgraph/releases/tag/1.2.18)（2026-10-26）
- 官方文档：[中断/恢复](https://docs.langchain.com/oss/python/langgraph/interrupts)、[持久性与检查点](https://docs.langchain.com/oss/python/langgraph/persistence)
- 已读仓库根 LICENSE 为 MIT；此事实**不是**完整依赖许可清算或生产安全审核。
- 执行环境：GitHub Actions `ubuntu-24.04`、Python 3.12、`pip install --only-binary=:all: --no-cache-dir langgraph==1.2.18`。实际解析出的传递依赖版本由工作流 `pip freeze --all` 输出至测试工件。传递依赖尚未 hash 锁定。
- 操作范围：访问上游发行软件包的公共仓库/包索引仅发生在安装阶段；**程序自身不调用外部网络工具**，不存在真实模型或交易下单动作。

## 真正调用哪些上游 API？

脚本 `scripts/real_langgraph_pilot.py` 直接使用：

1. `StateGraph`、`START`、`END` 构建状态执行图；
2. `InMemorySaver` 实际保存线程状态；
3. `interrupt()` 暂停需要审批的操作；
4. `Command(resume=...)` 真实恢复等待中的图；
5. `graph.get_state()` 读取中断和完成线程的检查点。

10 项独立断言：

| ID | 校验点 | 预期 |
|---|---|---|
| LG01 | 公开项目读取 | 只读完成 |
| LG02 | 模拟 `send_order` 请求 | 被 guard 拒绝，不可访问提交节点 |
| LG03 | 访问凭证等未知动作 | 拒绝 |
| LG04 | 草稿操作等待审批 | Graph 真实中断并留下检查点，零副作用 |
| LG05 | 审批拒绝后恢复 | 不会写入草稿 |
| LG06 | 来源为不可信网页的伪造审批 | 不会通过 |
| LG07 | 可信模拟会话审批后恢复 | 在内存集合中写入一个模拟草稿标记 |
| LG08 | 重复提交同一幂等键 | 不会重复写入 |
| LG09 | 缺少幂等键 | 即便模拟审批也不写入 |
| LG10 | 已完成线程状态 | 没有待执行节点 |

**解释限制：** 脚本中的 `owner_session` 只是测试负载里提供的字符串，并非真实身份验证、登录认证、RBAC 或签名审批。真实产品必须将审批事件绑定经认证 Owner 的服务端身份与不可伪造审计记录；绝不能直接相信网页或 LLM 发来的 `source` 字段。

`InMemorySaver` 与模拟 ledger 仅在单个 Python 进程里存在，不能证明跨进程崩溃恢复、持久事务幂等性和长期调度稳定性。不能用它替代金融系统的风险网关、真实订单权限、生产数据库或生产稳定性验收。

## 运行与获取证据

项目根目录执行：

```powershell
python -m pip install --only-binary=:all: --no-cache-dir langgraph==1.2.18
python scripts/real_langgraph_pilot.py
python -m unittest scripts.test_real_langgraph_contract -v
```

GitHub Actions 工作流：[Verify real LangGraph upstream (isolated)](../.github/workflows/real-upstream-langgraph.yml)。成功时会提供 `real-langgraph-1_2_18-synthetic-evidence` 工件，其中包含 JSON 逐例结果和 `pip freeze`。**必须以当前分支和执行记录中的真实绿灯为准，不能凭本文件宣称已经成功。**

本实验没有 Fork 上游、没有将上游代码复制进 Atlas，也没有更改此前 Top 30 研究的 `Fork HOLD` 状态。

## 下一阶段必须通过的门禁

- 独立核查第三方依赖许可证、发行工件 hash、安装期网络/遥测行为及漏洞通告；
- 增加受控 SQLite/Postgres checkpoint，重启进程后重放，并记录租约、并发幂等、故障恢复和延迟；
- 接入服务端真实认证、RBAC 和审计账本，而非模拟文本审批；
- 用 mock tools 与不可信 Prompt Injection 数据进行黑盒评测，保证即使 LLM 判错也不会打开放行规则；
- 只有在授权、安全、可观测性、数据治理、性能、回滚均有证据的情况下，才对生产 YIFALIN 创建独立集成 PR。

> **真实 API 运行通过 ≠ 产品可用 ≠ 金融风险可控 ≠ 正式部署授权。**
