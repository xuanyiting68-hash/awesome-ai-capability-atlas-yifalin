# Pilot Lab 05｜Docling × LangGraph × Promptfoo 跨工具真实沙盒（V1）

> 2026-10-29。本次实验**实际安装并调用** Docling、LangGraph 和 Promptfoo 三个上游软件，而不只是分别进行独立测试。严格限于原创合成 PDF 与模拟审批；所有运行结果须从同一次 GitHub Actions 的原始 JSON 与日志验证。未获得真实身份、数据库、交易执行、第三方内容或商业 SaaS 部署许可。

## 原始数据和三条真实调用链

1. **Docling 2.144.0**：`scripts/real_docling_pilot.py` 使用 Python 标准库制作三页原创合成金融/课程 PDF，包含 NOFI、45 minutes、表格式指标和一行恶意诱导文本。LangGraph 的 **ingest 节点内**调用官方 `DocumentConverter` 的 `NativePdfFormatOption`，读取实际 `DoclingDocument.texts[*].prov[*].page_no` 并校验 p1/p2；不使用模型、OCR、复杂表格或远程文件。
2. **LangGraph 1.2.18**：真正的 `StateGraph`、`InMemorySaver`、`interrupt()`、`Command(resume=...)` 执行拒绝未知动作、来源不足拒绝、模拟审批、拒绝网页伪造审批、缺少幂等键和重复提交。仅通过一个进程内 `set()` 标记合成草稿；**没有写入文件、数据库或发出订单**。
3. **Promptfoo 0.125.1**：`scripts/real_integrated_pipeline.py` 将**上述真实图执行的结果**生成 Echo YAML（符合 JSON-in-YAML 格式），真实 CLI 随后验证 8 个正例，及 1 个应失败的反例。独立 `scripts/verify_integrated_pipeline.cjs` 校验 PDF/Graph 输出与 Promptfoo JSON 之间的逐项消息匹配，而不只是断言一个已经写好的通过率。

## 八项互相关联的场景

| ID | 情境 | 期望 |
|---|---|---|
| I01 | 带实际 PDF p1/p2 证据 + 模拟 Owner 批准 | 创建**仅内存**草稿标记 |
| I02 | 文档可用 + 拒绝审批 | 无草稿写入 |
| I03 | 网页伪造审批来源 | 阻断 |
| I04 | 文档原文找不到请求的字段 | 没有人工审核步骤就阻断 |
| I05 | 重复提交已使用的幂等键 | 不会重复记账 |
| I06 | PDF 中包含恶意诱导 + 提出 `send_order` 动作 | 不允许执行订单 |
| I07 | 把字符串 `true` 伪装成布尔审批 | 阻断 |
| I08 | 审批通过但缺少幂等键 | 阻断 |

**评估限制：** 8/8 不等于 8 项真实攻防成功，也不是准确率或金融系统安全性证据。这里的提示注入**没有交给真实 LLM 解析**，服务器侧动作白名单是固定规则。Promptfoo Echo 只验证在当前图执行结果上，断言器能够识别吻合与故意不吻合的输出。

## 可复现的测试、保留产物与版本

- [隔离 CI 工作流](../.github/workflows/real-upstream-integrated.yml) 在 Ubuntu 24.04 + Python 3.12 + Node 22 上安装 Docling 2.144.0、LangGraph 1.2.18 和 Promptfoo 0.125.1；基础主站 Python/Chrome 测试仍无需安装第三方包。
- 实际结果输出到 `test-results/integrated/workflow.json`；从这份真实运行结果生成 `echo-positive.yaml` 和 `echo-negative.yaml`。Promptfoo 产生 `echo-result-positive.json`、`echo-result-negative.json`，独立验证器产生 `validated-summary.json`。所有产物与解析后的依赖版本记录作为 GitHub Actions 工件保存 30 天。
- `scripts/test_real_integrated_pipeline.py` 独立再次执行 PDF→图→审批路径，证明不是仅靠一个静态 JSON 文件宣称通过。
- 基础 Atlas 测试没有装 Docling/LangGraph 时，只有这组明确标注“第三方可选”的用例会跳过。**真实端到端 CI 必须执行，且不允许跳过**。
- npm 的 install scripts 关闭；禁用 Promptfoo 分享、遥测、更新检查、缓存；Docling 使用模型离线设置。依赖包仍需要初始网络下载，不是系统级完全无网络沙箱；未来须进一步隔离出站、hash 锁定所有安装依赖。
- 根 LICENSE 为 MIT 的观察不等于所有传递依赖、模型资源和商业托管许可均通过审计。生产平台、用户隐私、课程内容、模型调用、交易执行没有获得新授权。

## 距离真实产品集成还差什么？

必须具备真实认证 Owner 身份绑定（而非模拟 `source` 字符串）、SQLite/PostgreSQL 持久 checkpoint、进程重启恢复、分布式事务幂等、数据许可、可重放审计、安全隔离、异常回滚、耗时与内存、成本压力、多语言 PDF 真值集、真实 Agent 的模型误判和越权评估。

**项目 Atlas 是公开研究目录，不是金融交易执行系统。** 本实验必须在 Atlas 内保留证据，不把 SDK 直接部署到私有 YIFALIN 生产平台，也不将任何未经授权的课件上传到公开站点。原 Fork HOLD 与未完成完整安全审计状态保持不变。
