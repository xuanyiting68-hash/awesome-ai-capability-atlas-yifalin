# Atlas 自动元数据更新｜受保护主分支与可审查候选改造

## 真实故障证据

2026-11-04 UTC 的 GitHub Actions 运行 [41809206198](https://github.com/xuanyiting68-hash/awesome-ai-capability-atlas-yifalin/actions/runs/41809206198)：

- 133 个公开仓库元数据同步步骤成功；
- Top 30 来源证据更新及 Python 检验成功；
- 自动 commit 本地成功，但 `git push origin HEAD:main` 被 GitHub 远端拒绝：`fatal error in commit_refs_rules`；
- 因而 `main` 仍是旧的元数据快照。此前未上传新的 JSON 工件，无法通过网站直接恢复本次更新结果。

不能把这次失败称为 GitHub API 限流、Python 程序失败或已发布了最新资料。原站 `data/repo_metadata.json` 的时间戳仍表示最后一次真正提交成功的快照。

## 修正后的工作方式

1. 每周三 UTC 02:34 或 Owner 主动触发 `.github/workflows/repo-metadata.yml`；以 `main` 的合法仓库数据为输入，只调用 GitHub 公开仓库 REST 端点（无购买或使用私人客户数据）。
2. 运行现有 Python 目录、研究、元数据契约检查；然后实际执行 `scripts/sync_repo_metadata.py` 和 `scripts/build_top30_evidence.py`，最后再次核对 30 项证据和 133 个仓库的绑定。
3. 成功后**先**上传 `atlas-metadata-refresh-review-candidate` artifact，包含两个真实生成的 JSON，保留 30 天。若后续因分支规则或 Bot 权限被拒绝，生成的数据也可在 Actions 中追溯和下载。
4. 后续不再直接推送 `main`；尝试新建 `data/metadata-refresh-<run ID>` 分支和 Draft PR。该 PR 不会自动合并、不会标为“安全审查完成”，也不会直接触发线上网站发布。
5. 如果 GitHub Actions Bot 没有创建 PR 的权限，或仓库规则禁止 Bot 创建任何引用，本流程**仍可能红灯**；但审核通过的候选工件已保存。是否能自动提交 Draft PR 需要下一次真实计划/手动运行独立证据，不能因为 YAML 合并就宣称已具备自动持续更新。
6. `pull_request` 验证 job 仅赋予 `contents:read`，不执行提交；单独的定时工作 job 才获得 `contents:write` 和 `pull-requests:write`，不对未审查的 PR 内容开放写权限。

## 谁可以合并？什么时候网站会更新？

只有在最新来源快照、Top 30 对账、修改清单、许可证/安全声明、保护规则和页面 CI 均通过后，才可人工或由获授权的项目审查者将 Draft PR 标为 Ready 并合并。合并到 `main` 后，现有 Pages 主分支发布流程负责重新构建及线上 smoke。**不能把仓库维护活动/Star 变化等价于能力已验证、安全认证或商业许可通过**。

## 下一阶段改进方向

应为每个来源记录添加采集时间、最后成功验证时间、可用性/错误类型、质量/安全独立审查状态、历史变化、自动退役规则，以及可订阅的变更追踪。任何项目源端 404 或 License 改变都应先隔离为人工审核事项，而不是自动切换为推荐或已经可运行。
