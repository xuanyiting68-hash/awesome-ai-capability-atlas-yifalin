# YIFALIN Atlas｜Star、Fork、集成与商业复用门禁

本文件适用于 Top 30 全部官方来源**编辑研究**。不代表第三方软件已运行、许可证已批准、Star/Fork 已执行；不构成法律意见。

## 三种动作

| 操作 | 用途 | 当前建议 |
|---|---|---|
| Star | 账号收藏原始项目 | 建议 30 项收藏；目前账号状态未知，**未核实执行** |
| Fork | 在个人账号创建自己的上游副本并承担维护 | 全部 HOLD，先核验实际需求、完整 LICENSE、依赖与安全 |
| Integration | 使用受控 API、适配接口与受授权数据，提供 YIFALIN 功能 | 八个 P0 候选仅设计合成数据或隔离试点 |

公开允许 Fork 不意味着具有任意商业再分发或修改授权，也不代表可以把第三方代码打包成自有产品。

## 真实交付与保留边界

- Top 30 官方来源编辑档案：data/research_briefs.json
- 30 项 Star/集成建议计划：data/adoption_plan.json
- 可视化能力分类：network.html
- 收藏与集成界面：adoption.html
- 本项目**没有实际修改你的 GitHub Stars，也没有创建 Fork**。
- 目前 0 项经过独立第三方许可审查、0 项真正集成、0 项 Fork 获批。

## 一次性 Star 操作（必须本人已认证 GitHub CLI）

1. 安装 GitHub CLI：https://cli.github.com/
2. 在本人的终端执行：gh auth login
3. 在已检出的 Atlas 仓库根目录预览：python scripts/star_atlas_repos.py
4. 确认计划包含 30 个正确项目后执行：python scripts/star_atlas_repos.py --apply
5. 如仅想收藏优先 8 项：python scripts/star_atlas_repos.py --apply --priority-only
6. 查看 GitHub 账号的 Stars 页面核对。

**默认是 DRY RUN：不会联网，也不会修改 GitHub 账号。** 必须显式提供 --apply。已授权的 gh CLI 使用 GitHub 官方 REST PUT Star API；重复运行应具备幂等性。不要将令牌或密码写进项目文件。

## 八个 P0 隔离研究候选

| 项目 | 待验证的业务赋能 | 第一阶段实验 |
|---|---|---|
| microsoft/qlib | 金融研究数据和因子 | 冻结样本、无交易接口、严格 OOS |
| microsoft/RD-Agent | 金融研究 Agent | 隔离因子提案、权限与泄漏审查 |
| langchain-ai/langgraph | Agent 编排 | 人工审批、任务恢复与审计轨迹 |
| docling-project/docling | 金融/课程 PDF | 授权样本的公式表格和引用准确率 |
| remotion-dev/remotion | 原创金融知识视频 | 原创素材、离线渲染、版权检查 |
| formbricks/formbricks | 合规用户反馈 | 匿名/合成问卷、撤回与数据删除 |
| posthog/posthog | 增长和留存研究 | 合成漏斗事件、去重、隐私控制 |
| promptfoo/promptfoo | AI 安全和质量 | 模拟 API 的权限边界和提示注入回归 |

候选不等于已通过安全、许可或商业复用评审。n8n 的 fair-code/Sustainable Use License、Remotion 的使用协议、Formbricks 等产品的社区版与商业条款必须依完整版本与实际部署用途单独核对，不能以 GitHub SPDX 标签直接放行。

## Fork 放行门槛

只有当项目具有明确维护需求，而非单纯想要收藏，才考虑 Fork。必须逐项目完成：完整 LICENSE/NOTICE、依赖和权限审查、源码和安装脚本审查、商标和商业分发权利审核、拟议改动与上游同步策略、隔离运行复现、独立 Owner 审批。

除非真的需要维护独立副本，优先采用**API 连接、可替换的适配器、文档索引和版本锁定**。禁止把未经授权的第三方代码、媒体或课程内容直接混入 Atlas 或 YIFALIN 生产平台。禁止未经审批接触生产秘钥、真实用户数据或交易订单。

## 官方依据

- [GitHub Stars](https://docs.github.com/en/get-started/exploring-projects-on-github/saving-repositories-with-stars)
- [GitHub Forks](https://docs.github.com/en/pull-requests/reference/forks)
- [GitHub Licensing](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository)
- [GitHub Starring REST API](https://docs.github.com/en/rest/activity/starring)
