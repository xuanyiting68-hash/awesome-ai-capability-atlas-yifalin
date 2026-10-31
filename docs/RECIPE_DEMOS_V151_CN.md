# Atlas V1.5.1｜三个真正可运行的第一方离线合成演示

## 界限与承诺

这是 V1.5 能力组合研究工作台的**运行证据层**，并不是第三方 Tools/Skills/MCP 的真实互联互通实验，更不是生产部署。演示不连接真实人、券商、课程平台、API、LLM、云服务或数据库。使用 **Python 3.12 标准库**和仓库内原创/合成输入；`verified_3rd_party_integrations = 0` 永远保持为零，除非未来有明确的独立证据及审批。

GitHub Pages 页面显示的结果不由开发者手填：`scripts/build_site.py` 每次真实运行 `verify_from_files`，必须与 `data/recipe_demo_contract.json` 中已固定的预期吻合，才能生成新的 `data/recipe_demo_results.json` 并部署。线上报告包括程序实际输出和失败边界。GitHub Actions 还在两个独立步骤中启动各 4 个 CLI Python 进程进行再次校验，留存 JSON artifact。

## 三条可复制的执行命令

在项目根目录，无需 pip install：

```bash
python examples/recipe_demos/run_demo.py --scenario leads
python examples/recipe_demos/run_demo.py --scenario education
python examples/recipe_demos/run_demo.py --scenario finance
python examples/recipe_demos/run_demo.py --scenario all --out /tmp/atlas-demo.json
python scripts/verify_recipe_demos.py --output-dir test-results/recipe-a
python -m unittest scripts.test_recipe_demos -v
```

### 1. 合规获客：隐私/同意/匿名分类

调用已有 `examples/consent_lead_triage/run_demo.py` 的 `triage_records`，合成输入 `examples/consent_lead_triage/synthetic_leads.json`，固定参考时刻 `2026-10-27T00:00:00Z`。

预期：8 条匿名测试记录，3 条通过同意、用途、未退订、90 天与去重门禁，5 条阻断；结果只包括匿名 ID、类别与待人工复核标签；**无手机、邮箱、原始问题和外发消息**。测试包含同一 ID 冲突与撤销同意的 fail-closed 行为。

实际执行的是 Atlas 自己编写的分类及同意规则，**不是** Formbricks、Typebot、Twenty 或 Cal.com 的实际安装、接口互通、CRM 写入或预约。

### 2. AI 教育：有依据的答案提取与无依据弃答

输入 `examples/recipe_demos/synthetic_fixtures.json` 中三段完全虚构、版权自有的讲义片段，以及四道预先定义的问题。实验不是一个对话大模型：严格执行字符串片段、source_id 与 answer_span 校验；三道题的来源片段必须出现在对应讲义原文中，第四道缺乏依据的“保证就业”问题必须弃答。

预期：3 条有来源的直接提取片段 + 1 条弃答，`generated_answers=0`、`llm_calls=0`。负向测试篡改引用、杜撰回答、重复题号，均应失败。

**不代表** Docling ↔ RAGFlow ↔ Open edX ↔ Whisper 的已完成集成，也不证明真实教育质量提升、OCR 或扫描课件能力。

### 3. 金融研究：历史时序边界与成本后样本外核验

输入 20 个**纯虚构**的每日价格样本，原始标签显式标为 `SYNTHETIC_XAU_DEMO_NOT_MARKET`，不是 XAUUSD 行情。冻结训练边界为索引 10，在索引 10–18 产生 9 个样本外方向判断。预测函数只能使用 `price[t-1]` 和 `price[t-2]`；`price[t+1]` 只用于事后计算，绝不能进入预测。

成本固定为 6 bps 点差 + 4 bps 佣金 + 6 bps 滑点（合计 16 bps / 假设交易）。两位小数舍入后的可复算结果：

| 指标 | 合成样本结果 |
|---|---:|
| 样本外决策数 | 9 |
| 方向对应正确次数 | 3 |
| 毛收益 bps 合计 | +10.21 |
| 成本后 bps 合计 | **−133.79** |
| 券商订单 | 0 |

**这些不是实际金融价格、回测收益预测或模型优势证据。** 小样本也不具备任何统计显著性主张。总和只是逐期假设头寸回报的演示指标，不能据此估计账户收益、成交质量或真实策略表现。负向测试禁止负费用、无穷值、非合成来源和无效时间切分。

## 发布与信任门禁

- `data/recipe_demo_contract.json` 保存冻结预期；修改结果必须提供独立原因和复核，不允许为“绿灯”随意调低标准。
- `scripts/verify_recipe_demos.py` 比较真实 Python 模块执行与各场景独立 CLI 结果；拒绝伪造的合规、分数与集成状态。
- `scripts/test_recipe_demos.py` 包含固定指标、源引用篡改、无依据回答、撤回同意、未来数据泄漏界限、负成本、非有限价格及合同数据伪造测试。
- `scripts/build_site.py` 先执行所有数据契约/演示检查，再生成静态发布文件；失败则不替换旧的 Pages 产物。
- `.github/workflows/recipe-demos.yml` 没有运行第三方 SDK/工具，没有请求线上 API，保存两次独立、无个人信息的 JSON 证据。

产品的后续重点应是真实用户反馈、组合工作台可用性和有许可的独立第三方模块试用，而不是把第一方规则脚本包装成“已实现超级智能集成”。
