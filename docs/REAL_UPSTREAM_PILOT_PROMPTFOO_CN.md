# YIFALIN Pilot Lab 04｜Promptfoo 官方评测引擎真实 Echo 沙盒

> 本项目沿用前三阶段的分层证据：24 项第一方契约基线、LangGraph 真 SDK 状态恢复、Docling 真 SDK 合成 PDF。这一阶段调用**真实 Promptfoo CLI 0.125.1 的评测执行器**，但始终使用原生 **Echo provider**，它只回显合成输入而不调用大模型。没有尝试“模拟了一次红队就证明模型安全”的错误宣传。

## 一、真实 upstream 和运行方式

- 官方：[promptfoo/promptfoo](https://github.com/promptfoo/promptfoo)，版本 [0.125.1](https://github.com/promptfoo/promptfoo/releases/tag/0.125.1)，2026-10-25。
- 官方 [Echo Provider 文档](https://www.promptfoo.dev/docs/providers/echo/) 明确规定它回显输入、成本 0、不会调用外部推理 API。禁止在本实验中使用 `similar`、`llm-rubric`、`redteam` 等可能尝试连接模型或远程 grading 的断言。
- 临时 Ubuntu Runner/Node.js 22，安装 `promptfoo@0.125.1`，禁用 npm lifecycle scripts、Promptfoo 更新检查和遥测，并通过 `--no-share --no-cache` 运行。
- 仅使用仓库下两份人工创建的合成 YAML：
  - `examples/promptfoo_echo/promptfooconfig.yaml`：8 个应该成功的合成工具权限文本回显与规则验证。
  - `examples/promptfoo_echo/promptfoo-negative.yaml`：**1 个故意失败的反例**，把文本 `BLOCK: trading.send_order` 错误要求包含 `ALLOW: trading.send_order`，用于证明真实评测引擎可识别违反断言的输出。
- `scripts/verify_real_promptfoo.cjs` 读取 Promptfoo 本身生成的 **JSON 原始结果**，验证 8 项成功、1 项反例失败，并生成 `test-results/real-promptfoo-summary.json`，保存带版本及无实际 API 调用的明示边界。
- 不接入任何 OpenAI/Anthropic API、邮箱、券商或用户数据。安装依赖期间 npm 使用公共包镜像下载，评测配置自身只依赖 Echo。

## 二、验证重点和不可推断项

| 能验证 | 不能据此声称 |
|---|---|
| 官方 Promptfoo CLI 能加载 YAML、解析插值和运行确定性断言 | AI 系统能够在真实攻击环境下识别恶意提示 |
| Echo 已对合成文本运行 8 个通过断言 | LangGraph / 真实交易 Agent 自动被攻破或防护成功 |
| 对故意写错的断言产生 1 个失败 | 自动化红队在生产用户、真实模型下的查全率、查准率 |
| 正反样本结果可解析为 JSON 并在 CI 中留档 | 模型质量、付费成本、数据隐私或完整安全审计 |

对实际 AI 模型做红队前还需独立创建测试边界：模拟 provider、权限不可被 LLM 决策绕过的服务端网关、人员审批、不可变事件记录；任何外部模型调用、付费、数据发送都必须另行经授权。

## 三、运行与证据

在独立测试环境：

```bash
npm install --no-save --ignore-scripts --no-audit --no-fund promptfoo@0.125.1
./node_modules/.bin/promptfoo eval -c examples/promptfoo_echo/promptfooconfig.yaml --no-cache --no-share -o test-results/real-promptfoo-positive.json
./node_modules/.bin/promptfoo eval -c examples/promptfoo_echo/promptfoo-negative.yaml --no-cache --no-share -o test-results/real-promptfoo-negative.json
node scripts/verify_real_promptfoo.cjs
```

**第二条反例运行的失败是实验要求，不是 CI 可以随意忽略的失败。** 独立 verifier 必须证明真实 JSON 里存在 1 项失败，否则构建不允许通过。可核查 [独立 GitHub Actions 工作流](../.github/workflows/real-upstream-promptfoo.yml) 和自动上传的原始结果文件。

## 四、边界及升级条件

- 不是模型安全红队成果，不把 Echo 测试的 8/8 说成现实防御成功率；
- 根 LICENSE 及仓库宣传“开源”不等于全部依赖、商业托管服务及数据权利获许可；
- 不接入生产 YIFALIN 平台，不处理客户身份与私人交易数据，原 Fork HOLD 不变；
- 下阶段可以基于真实 Agent 的隔离 mock API adapter，测量未经授权工具调用是否被**服务器端独立**拒绝，再安排审批与真实模型评测。

> CI 状态和工件是唯一完成证据，未通过不得声称已通过。
