# Atlas V1.9｜真实开源多语言 AI 语义检索（浏览器端可选）

## 可操作入口

网站：[/semantic-studio.html](../semantic-studio.html)。从 Atlas 首页进入，在中文或英文输入框写业务目标，点击「先用规则筛选」查看现有可解释项目排序；只有点击 **「✦ 启用本地 AI 语义重排」** 才启动 Web Worker，从公开 CDN 加载 Transformers.js 并从 Hugging Face 下载 Multilingual E5 Small 权重文件。可随时停止并恢复规则结果，选择项目后可临时交接至 Mission Studio 继续设计阶段性方案。

**为什么这次不是又一个规则模拟？** 神经推理使用真正的第三方模型 \`Xenova/multilingual-e5-small\` 与 \`@huggingface/transformers@3.8.1\` 的 ONNX WASM feature-extraction pipeline，运行真正的神经网络权重，返回 384 维 embedding。其中文/英文训练背景以及 \`query: …\` / \`passage: …\` 的非对称检索前缀来自 [上游模型卡](https://huggingface.co/intfloat/multilingual-e5-small) 和 [官方 Transformers.js API](https://huggingface.co/docs/transformers.js/pipelines)。使用量化权重（q8），减少浏览器开销，但无法保证所有手机或地区能正常获取依赖。

## 实现与数据边界

1. 默认页面不加载外部 JS 或模型。先从站点自己发布的 \`data/curated.json\`、\`data/repo_metadata.json\`、\`data/research_briefs.json\` 读取 **133 个编辑精选**项目、Top 30 来源档案和固定维护快照。
2. 通过已验证的 \`mission-engine.js\` 对目标进行主题/类型/用途初筛。新模型**只重新排列该规则初筛的前 32 个**；它不重新筛选全部 5,000 条目录，也不生成不存在的仓库或编造新项目证据。该范围限制是为保护浏览器内存/CPU。
3. 在用户确认后，单独 \`semantic-worker.js\` 启动固定版本 SDK，加载指定的公开模型 \`Xenova/multilingual-e5-small\`；将当前目标加 \`query:\` 前缀，将项目名称、中文简介、用途、分类等原来源字段加 \`passage:\` 前缀，批次提取并标准化 384 维向量。工作线程把向量返回本地 UI，通过 \`semantic-core.js\` 求 cosine，相对排序展示到小数点 4 位。
4. **余弦相似度不是概率、信心度、质量评级或真实用户转化率**。原 \`evidence\` 来源覆盖值、GitHub 历史推送信息、未知许可证、archived 标记、安全未审等阻断独立保留；AI 排序不改变任何授权门禁。
5. 仅通过用户点击显式下载模型/SDK。浏览器会向 jsDelivr 和 Hugging Face 发出**固定资源地址**的获取请求，提供方仍能看到网络 IP、user agent 等下载元数据；**业务查询文本不会作为请求参数或模型 API body 上传**，在本机 Web Worker 计算。页面亦不启用第三方网站统计。如果使用企业私密信息，仍建议避免直接输入公共网页；不假设浏览器扩展、操作系统没有其他监控。
6. 模型有加载失败、运行不支持、内存/网络限制、无效向量或用户终止时，必须维持基本的纯本地规则候选。不会将失败伪装成模型已完成，也不会要求 API Key 或自动付费。
7. 浏览器只持有模型中间向量于当前工作进程；不把用户查询或 embeddings 存入远程服务器。若用户点击“在工作台设计实施流程”，目标与最多五个已有精选仓库只写入同源 \`sessionStorage\`，在 Mission Studio 成功读取后删除。与云账号同步、远程 Agent 不同。

## 实测与可验证证据

- \`tests/semantic-core.test.cjs\`：证明 133 条来源有效，候选最多 32 条，向量维度/有限值/唯一仓库等输入契约不会被伪造或注入。
- \`scripts/verify_real_semantic_model.mjs\`：GitHub Actions 在无真实用户数据、只读权限的临时 Ubuntu Runner 安装固定 SDK；**实际**调用 Multilingual E5 pretrained model，计算四个合成样本（含中文输入、中文课程相同文本、无关金融句、英文课程句），逐项验证模型得到 384 维 finite 向量、完全相同语义片段明显高于不相关片段，记录真实输出 cosine 和模型/SDK 版本。
- \`.github/workflows/real-semantic-model.yml\`：独立负向契约与真实模型两项测试，保留 \`test-results/semantic-real-model.json\`；只保存合成数据推理证据，不保存权重或私人问题。
- \`tests/deployed-smoke.cjs\`：在三种宽度实际加载 UI，验证初始只采用规则匹配、不会自动下载，用户可手动选择项目及交接方案、公开源链接正常、无横向溢出；浏览器中对外部模型完整下载的成功应以独立实测为准，**不能用 UI 模拟 Worker 的正例宣称模型真实运行**。
- \`scripts/build_site.py\` / \`deployment.json\`：正式站发布时把 SDK 功能边界（明确 opt-in、32 项候选范围、远程推理调用次数 0、已验证 Agent 集成数 0）写入公开 manifest。

## 重要限制与下一阶段门禁

- **它是有真正开源模型的“语义检索”能力，不是可长时间自主工作的生成式 AI Agent，也不等于模型可以执行业务。** 静态 GitHub Pages 无法安全存放 API Key、运行后台工作进程，不能通过把密钥写进前端来假装服务器能力。
- 模型会下载权重与 WASM 运行时，首次流量可能超过 **100MB**；手机/低内存设备可能失败，跨地区 CDN、模型权重站点可能不可达。停止 Worker 不保证浏览器立刻取消底层缓存中的已发网络请求。
- 浏览器加载公开第三方模型及 JS，本轮测试**不是**模型全依赖软件供应链审计；\`Xenova/multilingual-e5-small\` 未锁定具体权重的不可变 commit SHA，需后续安全复核、版本锁定和模型文件 hash pinning，不承诺完整防供应链攻击。
- 本轮不调用付费推理 API、不创建真正的企业客户，不依赖个人密钥，不下单，不处理真实财务信息；跨行业推荐有效性尚没有标注数据集进行 NDCG、MRR 或 A/B 用户研究验证。
- 下一步应准备一个**单租户、端到端安全隔离的真正 Agent Runtime 服务端参考实现**（模型/工具多供应商适配器、可追踪运行、工具白名单、确认/额度门禁、人工审批、可回滚）；上线生产及接入付费/敏感系统必须单独授权。
