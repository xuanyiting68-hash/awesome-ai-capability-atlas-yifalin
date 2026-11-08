# Atlas V2.0｜真正执行的研究任务 Runtime（本地只读实验）

这是从「工具检索与静态路线图」迈向**可执行但受权限约束的 AI 研究任务**的工程基线。不是另建 Atlas，不是第三方调用列表，亦不是生产多租户/云端自治 Agent。

## 与旧版有何区别

| 阶段 | V1.6/1.9 | 新 V2.0 Runtime |
|---|---|---|
| 读取任务 | 浏览器显示选型建议 | 读取明确任务 JSON，验证场景/动作白名单 |
| 真实 AI | V1.9 的 E5 可选语义重排 | **执行真正 E5 模型权重**，对当前任务重新编码 17 条文本与现有真实仓库档案 |
| 开源组件 | 作为人工研究候选展示 | 实际调用官方 \`langgraph==1.2.18\` \`StateGraph\` + \`SqliteSaver\`，保存真实节点与中断 |
| 工具接口 | 静态导出 | 真实 allowlist 工具 \`read_public_curated\` + \`neural_rerank\` + \`write_local_report\`，不允许动态任意工具名 |
| 审批 | 页面或 mock 指示 | 新 Python **进程**从 SQLite 真实 checkpoint 恢复，须输入 prepare 阶段生成的**一次性随机本地凭证** |
| 产出 | 网页 JSON、Markdown | 仅经批准后执行**实际**本地 JSON 文件创建，含真实 E5 评分、仓库来源、阻断事项和四步人工审查 |
| 安全边界 | 不触碰外部业务 | **仍然禁止**真实消息、券商订单、第三方代码运行、外部账户、生产部署与付费 API |

注意：一次性随机 token 只是本机能力凭证，**不证明登录的 Owner 身份**。存储 SHA256 摘要，最多 15 分钟有效；被消费后不可重放。如果 token 消费后进程崩溃，任务会 fail-closed，需要人工核对 SQLite 与报告。**不是**生产认证、分布式 ACID 或完整 RBAC。

## 真实执行的例子

先在具有 Python 3.12、Node.js 24 的隔离实验环境执行一次安装（本项目默认浏览器用户无需安装）：

\`\`\`bash
python -m pip install 'langgraph==1.2.18' 'langgraph-checkpoint-sqlite==3.1.2'
npm install --no-save --ignore-scripts '@huggingface/transformers@3.8.1'
\`\`\`

随后执行仓库内两个**公开/合成**任务之一，例如教育场景：

\`\`\`bash
python scripts/agent_research_runtime.py prepare \
  --workspace /tmp/atlas-v20-education \
  --task-file examples/research_agent/education_task.json
\`\`\`

输出 \`PENDING_ONE_TIME_LOCAL_REVIEW\`，同时给出本地临时 \`review_token\`。审查用户必须在独立终端/进程选择：

\`\`\`bash
python scripts/agent_research_runtime.py inspect \
  --workspace /tmp/atlas-v20-education --task-id atlas-edu-01
python scripts/agent_research_runtime.py approve \
  --workspace /tmp/atlas-v20-education \
  --task-id atlas-edu-01 --token 'prepare 输出的一次性凭证'
\`\`\`

报告写入 \`/tmp/atlas-v20-education/reports/atlas-edu-01.json\`。如果选择 \`deny\` 而非 \`approve\`，则不得写入任何报告。生产用户不用运行以上命令；这是开发者可核验的执行安全基线，面向普通用户的服务端界面尚未建设。

**安全要求：** 不要公开本地凭证、sqlite 文件或包含敏感工作目标的证据。CI 自动生成的临时 token 只在内存/子进程交互中使用，公开 artifact 仅包含批准后的**合成任务报告**与去敏摘要，不公开 token 或 DB。

## 源与 AI 结果真实契约

真实 Node 模型工具为 \`scripts/agent_embed_candidates.mjs\`。它从仓库的 133 个 **editorial curated** 项目与 Top 30 来源档案出发，规则过滤前 16 个候选，使用开源 \`Xenova/multilingual-e5-small\` 模型生成 17 条 384D 向量，按余弦相似度排序，返回最多四个原始仓库及证据；每个仓库必须匹配 GitHub 官方 repo URL，不可由模型创建新仓库链接。

- 样本时间：\`data/repo_metadata.json\` 是冻结快照，**不是当日实时 GitHub 信息**；
- 模型比较值：\`similarity_cosine\` 不是安全、兼容、准确率或工作任务成功概率；
- 文件摘要：三个实际读取的来源文件 SHA256 在 Node 模型输出与 Python Graph 内独立核对，resume 之前也要复核；
- 来源边界：所有第三方项目的独立安全审核、商用许可核验、真实接口兼容性均显示为 \`false\` / 阻断；
- 模型负责语义检索，工作流与报告由严格限定的确定性代码构建。**不能称为具有自由规划能力的生成式自治 Agent**。

## 关键负向测试

\`scripts/test_agent_research_runtime.py\` 单独启动 CLI 的不同操作系统进程，验证：

- 非法动作 \`send_order\` / \`send_email\` / \`run_shell\`，伪造 task ID、未知场景、意外字段直接拒绝；
- 真实神经模型工作完毕后，必须存在 LangGraph 的 \`human_review\` 持久 checkpoint；
- 伪造凭证拒绝，拒绝审批后不会产生本地报告，重复使用凭证拒绝；
- 单次合法合成批准后只生成一个新文件，JSON 内有公开仓库、快照 hash、风险门禁、模型维度和执行状态；
- 对已消费/已经完成任务重复 prepare、approve 不能第二次写入报告；
- 原普通 Atlas CI 未安装 LangGraph 时允许明确跳过**本插件可选的上游测试**；专门的 \`agent-research-runtime.yml\` 设置 \`ATLAS_REQUIRE_AGENT_RUNTIME=1\`，上游不存在即严格失败，不能用 skipped 冒充通过。

正式独立 CI 在 GitHub Actions 的临时 runner 实际安装固定版本的 E5 / LangGraph / SQLite SDK；保存正例报告、拒绝审计和许可边界摘要。**生产网站仍是静态 Pages，并不能偷偷获得真实执行权限或持有密钥。**

## 下一阶段仍需做的真正产品工作

1. 安全服务端入口，用户身份、任务权限、数据分类和额度；
2. 实际可审计的工具白名单、外部只读研究/网页检索适配器、明确用户审批，支持权限撤销与请求限速；
3. 真实可用的任务结果呈现和可搜索历史工作空间，独立成本/延迟评估；
4. 合法采购/模型许可证/模型供应链锁定、隔离运行时与非模拟的多租户身份审查；
5. 非模拟端到端用户价值测试：任务完成时间、来源准确率、成功率、人工审核时长与失败归因。

本轮不批准 GitHub 自动 merge 其他 Owner-HOLD 的 PR，不调用真实交易或外发消息，不部署生产 Agent。
