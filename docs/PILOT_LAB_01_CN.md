# YIFALIN Pilot Lab 01｜从收藏到集成的三项契约实验

> 研究日：2026-10-29。当前是**第一方合成契约基线**，不是三个上游项目的 SDK、解析引擎、LLM 或安全产品实测；没有安装第三方软件、没有进行模型/API 调用、没有任何实盘交易或真实用户数据处理。三个项目在原 Top 30 研究档案中仍然是 `not-tested` 与 `Fork HOLD`。

## 1. 为什么这一步有必要

用户已经通过自己已登录的 GitHub CLI 确认 **30 项 Star API 成功、0 失败**，但收藏并不等于能集成。我们先把后续集成中需要满足的输入/输出契约和不可突破的权限门槛冻结并执行。这样在未来实际安装 LangGraph、Docling、Promptfoo 后，就可以把**真正的上游输出**替换掉当前第一方模拟逻辑，用同一套用例比较，形成可归因的差异记录。

## 2. 24 项固定场景

| 工作流 | 项目 | 固定用例 | 当前直接执行的内容 | 不能据此推断 |
|---|---|---:|---|---|
| 状态/授权 | [LangGraph](https://github.com/langchain-ai/langgraph) | 9 | 第一方有限权限函数：只读操作、必须经 owner_session 的草稿写入、幂等重试、实盘订单永远拒绝 | LangGraph 的 checkpoint、interrupt、网络恢复或生产 Agent 稳定性 |
| 文档/引用 | [Docling](https://github.com/docling-project/docling) | 7 | 合成文档的明文术语匹配及页码引用，不生成 PDF 解析 | Docling 对真实 PDF/表格/公式/OCR 的提取精度 |
| 工具调用/安全 | [Promptfoo](https://github.com/promptfoo/promptfoo) | 8 | 第一方固定工具白名单，对包含恶意指令的未信任文本不执行工具操作 | Promptfoo 实际红队检出率、真实模型的攻击成功率 |

## 3. 运行和复现

所有冻结测试数据在 `data/pilot_lab_cases.json`。所有判断函数在 `scripts/pilot_lab.py`。不依赖环境变量、网络、pip 或 npm 安装。

PowerShell/终端在 Atlas 仓库根目录执行：

```powershell
python scripts/pilot_lab.py
python -m unittest scripts.test_pilot_lab -v
python scripts/build_site.py
```

发布构建**必须**成功完成 24 项基线才能将旧站点替换为新产物。生成的 `_site/data/pilot_lab_results.json` 包含逐例实得值、期望值与总计； `_site/deployment.json` 含 `pilot_contract_cases`、`pilot_contract_passed`、`pilot_upstream_packages_executed`。静态站 `pilot-lab.html` 用原始用例 + 结果 + 发布清单做交叉校验和中英文证据展示。

该基线只验证**当前的第一方程序与预设期望一致**。即使全部通过也不代表模型具备预测价值、第三方组件准确可用或系统达到真实安全要求。这种自定义样例集的通过率不能解释为第三方产品的普遍质量评估。

## 4. 上游来源：已核查的范围

2026-10-29 逐一读取 GitHub 官方上游的根 README 与 LICENSE 文本并记录 blob SHA：

| 项目 | README blob SHA | 根 LICENSE blob SHA | 根 LICENSE 观察 |
|---|---|---|---|
| langchain-ai/langgraph | `97c31e9cb4d8fe56be8d768ce3eb5e22400e897e` | `fc0602feecdd6748623c852ab534e1ca612673c7` | MIT |
| docling-project/docling | `3297b7881575dc853facc5add4cc4c8dccc12f14` | `6684a401bf0f700fd37104ab7c8da340036f7166` | MIT |
| promptfoo/promptfoo | `2a56017c2609e3a92d7d5539147c9c7e620a3420` | `af3fa111d9303b3041d225fb851534e50a4bbec2` | MIT |

**许可证观察限制：** 只阅读根 LICENSE，尚未逐项目核查第三方依赖、模型权重、代码生成数据、云服务条款、商标以及具体商业部署场景。不能凭一项 MIT 标签直接放行整体生产部署。原有 Top 30 档案的许可证状态仍是 `not-reviewed`；本文只是下阶段专项审查的可追溯输入。

## 5. 下一阶段要执行什么

- **LangGraph 真实沙盒：** 先隔离 Python venv、锁定版本、记录安装包与依赖许可证；仅采用 fake tools、无密钥、无网络或出站白名单，跑 checkpoint、interrupt/resume、重复提交与状态恢复。记录运行成本、失败序列、恢复延迟及任务审计。
- **Docling 真实沙盒：** 先用自制、授权的 PDF/扫描样本构建标注；与基线页码、表格单元格、公式位置和断章完整度比较。绝不导入尚未获得使用许可的商业课程视频或 PDF。
- **Promptfoo 真实沙盒：** 首先在 mock provider / 本地测试应答上跑评测配置及可重放红队用例，禁止把真实凭证、用户隐私或交易下单接口交给外部测试。再核查代理插件、数据上传和遥测默认行为。
- **产品落地门禁：** 项目各自完成许可证/依赖审查、可重现第三方真实执行、人工审批路径、必要的商业数据许可、威胁模型、异常处理与回滚后，才另开 PR 对接 YIFALIN 正式平台。 **本 PR 只修改 Atlas 公共目录及第一方实验。**

此页以及实验都不改变原项目的 Star、Fork 或第三方审核状态。
